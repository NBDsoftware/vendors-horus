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

    # --------------------------------------------------------------------
    #  Create Dummy HTML package
    # --------------------------------------------------------------------
    import importlib.machinery
    import importlib.util
    import sys
    import types

    if "html" not in sys.modules or not hasattr(sys.modules["html"], "parser"):
        parser_stub = types.ModuleType("html.parser")

        class _DummyHTMLParser:
            pass

        parser_stub.HTMLParser = _DummyHTMLParser
        parser_spec = importlib.util.spec_from_loader(
            "html.parser",
            loader=importlib.machinery.SourceFileLoader(
                "html.parser", "<stub>"
            ),
        )
        parser_stub.__spec__ = parser_spec
        sys.modules["html.parser"] = parser_stub

        html_pkg = types.ModuleType("html")
        html_pkg.__path__ = []
        html_pkg.parser = parser_stub
        html_spec = importlib.util.spec_from_loader(
            "html", loader=None, is_package=True
        )
        html_pkg.__spec__ = html_spec
        sys.modules["html"] = html_pkg

    import importlib
    from collections import defaultdict

    import pandas as pd
    from bs4 import BeautifulSoup
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    service = Service()
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(800)
    print("set timeout at 800")
    ids = pd.read_csv(block.inputs[vendors_input.id]).iloc[:, 0]

    df3 = pd.DataFrame(columns=["URL"])

    for i in ids:
        url = f"https://zinc.docking.org/substances/{i}"
        driver.get(url)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.catalogs dl.dl-delimited")
                )
            )
        except Exception:
            print(f"[WARN] Vendors not founf for {i}")
            continue

        soup = BeautifulSoup(driver.page_source, "lxml")
        vendors_dl = soup.select_one("div.catalogs dl.dl-delimited")
        if vendors_dl is None:
            print(f"[WARN] Vendors not found for {i}")
            continue

        vendor_ids = defaultdict(list)

        for dt in vendors_dl.select("dt"):
            vendor = dt.get_text(strip=True)
            dd = dt.find_next_sibling("dd")

            ids = [a.get_text(strip=True) for a in dd.select("a")]
            ids = list(dict.fromkeys(ids))

            vendor_ids[vendor].extend(ids)

        row_idx = len(df3)  # nueva fila
        df3.loc[row_idx, "URL"] = url

        for vendor, ids in vendor_ids.items():
            if vendor not in df3.columns:
                df3[vendor] = 0
            df3.at[row_idx, vendor] = " ".join(ids)

        for col in df3.columns:
            if col not in ("URL", *vendor_ids.keys()):
                df3.at[row_idx, col] = 0

    driver.quit()
    print("Scraping finished.")
    input_csv = block.inputs[vendors_input.id]
    new_filename = os.path.basename(input_csv) + "_results.csv"

    results = pd.DataFrame(df3)
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
