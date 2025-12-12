# RyanData Address Utils - Architecture Overview

This document explains the architecture of the `ryandata-address-utils` package after the SOLID/DRY refactoring.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER APPLICATION                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             AddressService                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • parse()              • parse_auto()         • parse_international()│   │
│  │  • parse_batch()        • lookup_zip()         • get_city_state_from_zip()│
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│         ┌────────────────────────────┼────────────────────────────┐         │
│         ▼                            ▼                            ▼         │
│  ┌─────────────┐          ┌──────────────────┐          ┌─────────────┐    │
│  │   Parser    │          │  TransformationTracker │          │  Validator  │    │
│  │  Protocol   │          │  (tracks changes)  │          │  Protocol   │    │
│  └─────────────┘          └──────────────────┘          └─────────────┘    │
│         │                            │                            │         │
└─────────┼────────────────────────────┼────────────────────────────┼─────────┘
          │                            │                            │
          ▼                            ▼                            ▼
┌─────────────────┐    ┌─────────────────────────┐    ┌─────────────────────┐
│    Parsers      │    │         Core            │    │     Validators      │
│  ┌───────────┐  │    │  ┌─────────────────┐   │    │  ┌───────────────┐  │
│  │USAddress  │  │    │  │ZipCodeNormalizer│   │    │  │ZipCodeValidator│  │
│  │ Parser    │  │    │  └─────────────────┘   │    │  └───────────────┘  │
│  └───────────┘  │    │  ┌─────────────────┐   │    │  ┌───────────────┐  │
│  ┌───────────┐  │    │  │AddressFormatter │   │    │  │StateValidator │  │
│  │libpostal  │  │    │  └─────────────────┘   │    │  └───────────────┘  │
│  │(optional) │  │    │  ┌─────────────────┐   │    │  ┌───────────────┐  │
│  └───────────┘  │    │  │PluginFactory    │   │    │  │CompositeValidator│
│                 │    │  └─────────────────┘   │    │  └───────────────┘  │
└─────────────────┘    └─────────────────────────┘    └─────────────────────┘
          │                            │                            │
          └────────────────────────────┼────────────────────────────┘
                                       │
                                       ▼
                        ┌─────────────────────────┐
                        │       Data Layer        │
                        │  ┌─────────────────┐   │
                        │  │  CSVDataSource  │   │
                        │  │  (uszips.csv)   │   │
                        │  └─────────────────┘   │
                        │  ┌─────────────────┐   │
                        │  │   constants.py  │   │
                        │  │ (STATE_NAMES)   │   │
                        │  └─────────────────┘   │
                        └─────────────────────────┘
```

## Package Structure

```
ryandata_address_utils/
├── __init__.py              # Public API exports
├── service.py               # AddressService (main facade)
├── protocols.py             # Protocol definitions (interfaces)
├── pandas_ext.py            # Pandas DataFrame integration
├── setup_cli.py             # CLI for libpostal setup
│
├── core/                    # Reusable utilities (SOLID extracted)
│   ├── __init__.py
│   ├── address_formatter.py # Full address computation (DRY)
│   ├── factory.py           # Generic PluginFactory base (DRY)
│   ├── tracking.py          # TransformationTracker (SRP)
│   ├── zip_normalizer.py    # ZIP parsing/validation (DRY)
│   ├── process_log.py       # ProcessEntry, ProcessLog
│   ├── errors.py            # Base error classes
│   ├── results.py           # ValidationResult, ValidationError
│   └── validation/          # Generic validation framework
│       ├── base.py          # BaseValidator
│       ├── composite.py     # CompositeValidator
│       └── protocols.py     # ValidatorProtocol
│
├── models/                  # Data models (SRP split from monolith)
│   ├── __init__.py          # Re-exports all public symbols
│   ├── address.py           # Address, InternationalAddress
│   ├── builder.py           # AddressBuilder (fluent API)
│   ├── enums.py             # AddressField enum
│   ├── errors.py            # RyanDataAddressError
│   └── results.py           # ParseResult, ZipInfo
│
├── parsers/                 # Parser implementations
│   ├── __init__.py
│   ├── base.py              # BaseAddressParser (template method)
│   ├── factory.py           # ParserFactory (extends PluginFactory)
│   └── usaddress_parser.py  # USAddressParser implementation
│
├── data/                    # Data sources
│   ├── __init__.py
│   ├── base.py              # BaseDataSource
│   ├── factory.py           # DataSourceFactory (extends PluginFactory)
│   ├── constants.py         # Centralized STATE_NAME_TO_ABBREV (DRY)
│   ├── csv_source.py        # CSVDataSource implementation
│   └── uszips.csv           # ZIP code database
│
└── validation/              # Address-specific validators
    ├── __init__.py
    ├── base.py              # ValidationBase (Pydantic mixin)
    └── validators.py        # ZipCodeValidator, StateValidator
```

## Data Flow Diagram

```
┌──────────────┐
│ Raw Address  │
│   String     │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│                    AddressService.parse()                     │
└──────────────────────────────────────────────────────────────┘
       │
       ├─────────────────────────────────────────┐
       │                                         │
       ▼                                         ▼
┌──────────────────┐                  ┌─────────────────────┐
│  USAddressParser │  (or libpostal)  │  InternationalParser│
│    .parse()      │                  │    (libpostal)      │
└────────┬─────────┘                  └──────────┬──────────┘
         │                                       │
         └───────────────┬───────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   Address Model     │
              │  (Pydantic Model)   │
              │                     │
              │ • ZipCodeNormalizer │◄─── Validates & normalizes ZIP
              │ • AddressFormatter  │◄─── Computes Address1/2/Full
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │TransformationTracker│
              │                     │
              │ • track_zip_*       │──► Records normalization
              │ • track_state_*     │    operations to ProcessLog
              │ • track_whitespace_*│
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  CompositeValidator │
              │                     │
              │ ┌─────────────────┐ │
              │ │ZipCodeValidator │ │──► Checks ZIP exists in DB
              │ └─────────────────┘ │
              │ ┌─────────────────┐ │
              │ │ StateValidator  │ │──► Checks state is valid
              │ └─────────────────┘ │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │     ParseResult     │
              │                     │
              │ • address: Address  │
              │ • validation: Result│
              │ • process_log: Log  │◄─── Contains transformation audit
              │ • error: Exception? │
              └─────────────────────┘
```

## Key Design Patterns

### 1. Facade Pattern (AddressService)
`AddressService` provides a simplified interface to the complex subsystem of parsers, validators, and data sources.

```python
service = AddressService()
result = service.parse("123 Main St, Austin TX 78749")
```

### 2. Strategy Pattern (Protocols)
Protocols define interfaces allowing different implementations to be swapped:

```python
# Any class implementing AddressParserProtocol can be used
service = AddressService(parser=CustomParser())
```

### 3. Factory Pattern (PluginFactory)
Generic factory base class for extensible component creation:

```python
# Register custom implementations
ParserFactory.register("custom", CustomParser)
parser = ParserFactory.create("custom")
```

### 4. Composite Pattern (CompositeValidator)
Validators can be combined and run as a single unit:

```python
validator = CompositeValidator([
    ZipCodeValidator(data_source),
    StateValidator(data_source),
])
```

### 5. Builder Pattern (AddressBuilder)
Fluent interface for programmatic address construction:

```python
address = (
    AddressBuilder()
    .with_street_number("123")
    .with_street_name("Main")
    .with_city("Austin")
    .with_state("TX")
    .with_zip("78749")
    .build()
)
```

### 6. Template Method (BaseAddressParser, BaseDataSource)
Abstract base classes define the skeleton of algorithms with hooks for customization.

## SOLID Principles Applied

| Principle | Implementation |
|-----------|----------------|
| **S**ingle Responsibility | `TransformationTracker`, `ZipCodeNormalizer`, `AddressFormatter` each handle one concern |
| **O**pen/Closed | Protocols allow extension without modification; factories support plugin registration |
| **L**iskov Substitution | All implementations satisfy their protocol contracts |
| **I**nterface Segregation | Focused protocols: `AddressParserProtocol`, `DataSourceProtocol`, `ValidatorProtocol` |
| **D**ependency Inversion | `AddressService` depends on protocols, not concrete implementations |

## DRY Improvements

| Concern | Before | After |
|---------|--------|-------|
| State mappings | Duplicated in 3 files | `data/constants.py` |
| ZIP validation | 4 different implementations | `core/zip_normalizer.py` |
| Full address computation | 3 duplicated methods | `core/address_formatter.py` |
| Factory boilerplate | 2 identical factories | `core/factory.py` (PluginFactory base) |

## Usage Examples

### Basic Parsing
```python
from ryandata_address_utils import AddressService

service = AddressService()
result = service.parse("123 Main St, Austin TX 78749")

if result.is_valid:
    print(result.address.StreetName)  # "Main"
    print(result.address.ZipCode5)    # "78749"
```

### With Transformation Tracking
```python
result = service.parse("123 main st, austin texas 78749")

# See what was normalized
for entry in result.aggregate_logs():
    print(f"{entry['field']}: {entry['message']}")
# state: State name normalized from full name to abbreviation
```

### Pandas Integration
```python
import pandas as pd
from ryandata_address_utils import AddressService

df = pd.DataFrame({"address": ["123 Main St, Austin TX 78749"]})
service = AddressService()
result_df = service.parse_dataframe(df, "address")
```

### Custom Validators
```python
from ryandata_address_utils import AddressService, CompositeValidator

# Create custom validation chain
validator = CompositeValidator([
    ZipCodeValidator(data_source, check_state_match=True),
    StateValidator(data_source),
    # Add your own validators here
])

service = AddressService(validator=validator)
```
