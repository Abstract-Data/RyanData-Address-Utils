# RyanData Address Utils

[![Tests](https://github.com/Abstract-Data/RyanData-Address-Utils/actions/workflows/tests.yml/badge.svg)](https://github.com/Abstract-Data/RyanData-Address-Utils/actions/workflows/tests.yml)
[![Ruff](https://github.com/Abstract-Data/RyanData-Address-Utils/actions/workflows/lint.yml/badge.svg)](https://github.com/Abstract-Data/RyanData-Address-Utils/actions/workflows/lint.yml)
[![MyPy](https://github.com/Abstract-Data/RyanData-Address-Utils/actions/workflows/typecheck.yml/badge.svg)](https://github.com/Abstract-Data/RyanData-Address-Utils/actions/workflows/typecheck.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python address parser built for Ryan Data that uses `usaddress` to parse US addresses into structured Pydantic models with ZIP code and state validation.

## Installation

```bash
pip install git+https://github.com/Abstract-Data/RyanData-Address-Utils.git
```

With pandas support:

```bash
pip install "ryandata-address-utils[pandas] @ git+https://github.com/Abstract-Data/RyanData-Address-Utils.git"
```

## Quick Start

```python
from ryandata_address_utils import AddressService, parse

# Simple parsing
result = parse("123 Main St, Austin TX 78749")

if result.is_valid:
    print(result.address.StreetName)   # "Main"
    print(result.address.ZipCode)      # "78749"
    print(result.to_dict())            # All fields as dict
else:
    print(result.validation.errors)

# Or use the full service
service = AddressService()
result = service.parse("456 Oak Ave, Dallas TX 75201")
```

## Key Features

- **Parse US addresses** into 26 structured components
- **Validate ZIP codes** against real US ZIP code database (~33,000 ZIPs)
- **Validate states** - abbreviations and full names
- **Pandas integration** for batch processing
- **Extensible architecture** - swap parsers, data sources, validators
- **Builder pattern** for programmatic address constructionYes

## Pandas Integration

```python
import pandas as pd
from ryandata_address_utils import AddressService

df = pd.DataFrame({
    "address": [
        "123 Main St, Austin TX 78749",
        "456 Oak Ave, Dallas TX 75201",
    ]
})

service = AddressService()
result = service.parse_dataframe(df, "address") # <-- This is where your named address column goes, and then it'll parse and add the split cols to the dataframe
print(result[["AddressNumber", "StreetName", "ZipCode"]])
```

### Options

```python
# Skip validation (for non-US addresses)
result = service.parse("123 Main St", validate=False)

# Add prefix to new columns
result = service.parse_dataframe(df, "address", prefix="addr_")
```

## Build Addresses Programmatically

```python
from ryandata_address_utils import AddressBuilder

address = (
    AddressBuilder()
    .with_street_number("123")
    .with_street_name("Main")
    .with_street_type("St")
    .with_city("Austin")
    .with_state("TX")
    .with_zip("78749")
    .build()
)
```

## API Reference

### AddressService (Main Interface)

```python
from ryandata_address_utils import AddressService

service = AddressService()

# Parse single address
result = service.parse("123 Main St, Austin TX 78749")
result.is_valid       # True if parsing and validation succeeded
result.address        # Address model
result.validation     # ValidationResult with any errors

# Parse batch
results = service.parse_batch(["addr1", "addr2", "addr3"])

# Parse DataFrame
df = service.parse_dataframe(df, "address_column")

# ZIP lookups
info = service.lookup_zip("78749")
city, state = service.get_city_state_from_zip("78749")
```

### Address Model Fields

| Field | Description | Example |
|-------|-------------|---------|
| `AddressNumber` | Street number | "123" |
| `StreetName` | Street name | "Main" |
| `StreetNamePostType` | Street type | "St", "Ave" |
| `StreetNamePreDirectional` | Direction before | "North" |
| `StreetNamePostDirectional` | Direction after | "SE" |
| `SubaddressType` | Unit type | "Apt", "Suite" |
| `SubaddressIdentifier` | Unit number | "2B" |
| `PlaceName` | City | "Austin" |
| `StateName` | State (validated) | "TX" |
| `ZipCode` | ZIP (validated) | "78749" |
| `USPSBoxType` | PO Box type | "PO Box" |
| `USPSBoxID` | PO Box number | "1234" |

### ZIP Code Utilities

```python
from ryandata_address_utils import (
    get_city_state_from_zip,
    get_zip_info,
    is_valid_zip,
    is_valid_state,
    normalize_state,
)

# Look up city/state from ZIP
city, state = get_city_state_from_zip("78749")  # ("Austin", "TX")

# Get detailed ZIP info
info = get_zip_info("78749")
print(info.city, info.state_id, info.county_name)

# Validation
is_valid_zip("78749")     # True
is_valid_state("Texas")   # True
normalize_state("Texas")  # "TX"
```

## Extensible Architecture

The package uses Protocols and Factories for extensibility:

```python
from ryandata_address_utils import (
    AddressService,
    ParserFactory,
    DataSourceFactory,
)

# Use custom data source
custom_source = DataSourceFactory.create("csv", csv_path="/path/to/zips.csv")
service = AddressService(data_source=custom_source)

# Register custom parser
ParserFactory.register("custom", MyCustomParser)
parser = ParserFactory.create("custom")
```

## Development

```bash
git clone https://github.com/Abstract-Data/RyanData-Address-Utils.git
cd RyanData-Address-Utils

# Install with dev dependencies
make install-dev

# Run tests
make test

# Run linter
make lint
```

## License

MIT
