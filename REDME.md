# ZINC Vendors Horus Plugin

A Horus plugin that extracts ZINC vendor information from a CSV file containing ZINC IDs and outputs the vendor data to a new CSV file.

## Usage

1. Load the plugin in Horus
2. Provide a CSV file containing ZINC IDs as input
3. Specify the output location for the vendor information CSV
4. Run the extraction process

## Input Format

The input CSV file should contain ZINC compound IDs. The plugin will process these IDs to retrieve vendor information from the ZINC database.

## Output Format

The output CSV file will contain vendor information for the provided ZINC compounds, including relevant vendor details and availability data.

## Installation

### Building the Plugin

To build the plugin package:

```bash
./build_plugin.sh
```

This will create a `vendors_horus.hp` file that can be installed in Horus.

### Development Setup

For development with autocompletions and linting tools:

```bash
pip install -r dev-requirements.txt
```
