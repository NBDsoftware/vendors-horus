"""
Vendors Horus Block
"""

import os.path

from HorusAPI import Extensions, PluginBlock, PluginVariable, VariableTypes

# Input CSV

vendors_input = PluginVariable(
    id="vendors_input",
    name="Input CSV with IDs",
    type=VariableTypes.FILE,
    description="CSV file with ZINC IDs.",
)

vendors_output = PluginVariable(
    id="vendors_output",
    name="Output ZINC vendors",
    description="CSV file with ZINC vendors.",
    type=VariableTypes.FILE,
    allowedValues=["csv"],
)


def extract_vendors(block: PluginBlock):
    """
    Extract ZINC vendors from a CSV file containing ZINC IDs.
    """

    import pandas as pd
    from bs4 import BeautifulSoup
    from collections import defaultdict

    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.common.exceptions import TimeoutException

    service = Service()
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("start-maximized")

    driver = webdriver.Chrome(service=service, options=options)

    def norm(s: str) -> str:
        return " ".join(s.split())

    def wait_for_any_layout(driver, timeout=25):
        wait = WebDriverWait(driver, timeout)

        def ready(d):
            # NEW vendor table headers exist
            has_vendor_hdr = (
                    d.find_elements(By.XPATH, "//table//thead//th[normalize-space()='Catalog Name']") and
                    d.find_elements(By.XPATH, "//table//thead//th[normalize-space()='Supplier code']")
            )
            if has_vendor_hdr:
                return True

            # OLD layout exists
            if d.find_elements(By.CSS_SELECTOR, "div.catalogs dl.dl-delimited dt"):
                return True

            # still loading
            if d.find_elements(By.CSS_SELECTOR, ".spinner-border"):
                return False

            # keep waiting
            return False

        wait.until(ready)

    rows = []

    ids = pd.read_csv(block.inputs[vendors_input.id]).iloc[:, 0]

    for i in ids:
        url = f"https://cartblanche22.docking.org/substance/{i}"
        driver.get(url)

        try:
            wait_for_any_layout(driver, timeout=35)
        except TimeoutException:
            rows.append({"molecule_id": i})
            continue

        root_html = driver.find_element(By.CSS_SELECTOR, "#root").get_attribute("outerHTML")
        soup = BeautifulSoup(root_html, "html.parser")

        vendor_ids = defaultdict(list)

        vendor_table = None
        for t in soup.select("table"):
            headers = [norm(th.get_text(" ", strip=True)) for th in t.select("thead th")]
            if len(headers) >= 2 and headers[0] == "Catalog Name" and headers[1] == "Supplier code":
                vendor_table = t
                break

        if vendor_table:
            for tr in vendor_table.select("tbody tr"):
                tds = tr.find_all("td")
                if len(tds) < 2:
                    continue

                vendor = norm(tds[0].get_text(" ", strip=True))
                code_el = tds[1].select_one("button, a")
                code = norm(code_el.get_text(" ", strip=True) if code_el else tds[1].get_text(" ", strip=True))

                if vendor and code:
                    vendor_ids[vendor].append(code)

        else:
            print(f"Could not find vendors table for compound {i}")

        for vendor, codes in vendor_ids.items():
            vendor_ids[vendor] = list(dict.fromkeys(codes))

        row = {"molecule_id": i}
        for vendor, codes in vendor_ids.items():
            row[vendor] = " ".join(codes)  # or ",".join(codes)

        rows.append(row)

    driver.quit()

    results = pd.DataFrame(rows)
    results.drop_duplicates().to_csv(new_filename)

    block.setOutput(vendors_output.id, new_filename)

    Extensions().loadCSV(new_filename, "results")


extract_vendors_block = PluginBlock(
    id="vendors",
    name="Extract ZINC Vendors",
    description="Extract ZINC Vendors from CSV file.",
    action=extract_vendors,
    inputs=[vendors_input],
    variables=[vendors_input],
    outputs=[vendors_output],
    category="ZINC",
)
