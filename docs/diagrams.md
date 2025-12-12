# RyanData Address Utils - Visual Diagrams

These diagrams can be rendered using:
- GitHub (automatic rendering in markdown)
- VS Code with Mermaid extension
- [Mermaid Live Editor](https://mermaid.live)

---

## 1. Component Architecture

```mermaid
graph TB
    subgraph "User Application"
        APP[Application Code]
    end

    subgraph "Public API"
        SVC[AddressService]
        PARSE[parse / parse_auto / parse_batch]
    end

    subgraph "Core Services"
        TRACKER[TransformationTracker]
        ZIPNORM[ZipCodeNormalizer]
        ADDRFMT[AddressFormatter]
        FACTORY[PluginFactory]
    end

    subgraph "Parsers"
        PFACTORY[ParserFactory]
        USPARSER[USAddressParser]
        LIBPOSTAL[libpostal - optional]
    end

    subgraph "Validators"
        COMPVAL[CompositeValidator]
        ZIPVAL[ZipCodeValidator]
        STATEVAL[StateValidator]
    end

    subgraph "Data Layer"
        DFACTORY[DataSourceFactory]
        CSVDATA[CSVDataSource]
        CONSTANTS[constants.py]
        USZIPS[(uszips.csv)]
    end

    subgraph "Models"
        ADDRESS[Address]
        INTLADDR[InternationalAddress]
        PARSERESULT[ParseResult]
        ZIPINFO[ZipInfo]
    end

    APP --> SVC
    SVC --> PARSE
    PARSE --> TRACKER
    PARSE --> PFACTORY
    PARSE --> COMPVAL

    PFACTORY --> USPARSER
    PFACTORY --> LIBPOSTAL
    PFACTORY -.-> FACTORY

    USPARSER --> ADDRESS
    LIBPOSTAL --> INTLADDR

    TRACKER --> CONSTANTS
    TRACKER --> PARSERESULT

    COMPVAL --> ZIPVAL
    COMPVAL --> STATEVAL

    ZIPVAL --> DFACTORY
    STATEVAL --> DFACTORY

    DFACTORY --> CSVDATA
    DFACTORY -.-> FACTORY
    CSVDATA --> USZIPS
    CSVDATA --> CONSTANTS

    ADDRESS --> ZIPNORM
    ADDRESS --> ADDRFMT

    PARSERESULT --> ADDRESS
    PARSERESULT --> INTLADDR

    style SVC fill:#4CAF50,color:white
    style FACTORY fill:#2196F3,color:white
    style TRACKER fill:#FF9800,color:white
    style ZIPNORM fill:#FF9800,color:white
    style ADDRFMT fill:#FF9800,color:white
    style CONSTANTS fill:#9C27B0,color:white
```

---

## 2. Parse Flow Sequence

```mermaid
sequenceDiagram
    participant App as Application
    participant Svc as AddressService
    participant Parser as USAddressParser
    participant Model as Address Model
    participant Tracker as TransformationTracker
    participant Validator as CompositeValidator
    participant Data as DataSource

    App->>Svc: parse("123 Main St, Austin TX 78749")

    Svc->>Parser: parse(address_string)
    Parser->>Model: Address.model_validate(parsed_data)

    Note over Model: ZipCodeNormalizer validates ZIP
    Note over Model: AddressFormatter computes FullAddress

    Model-->>Parser: Address instance
    Parser-->>Svc: ParseResult(address=...)

    Svc->>Tracker: track_all(result, raw_input)
    Note over Tracker: Records normalizations to ProcessLog
    Tracker-->>Svc: (mutations to result.process_log)

    Svc->>Validator: validate(address)
    Validator->>Data: get_zip_info(zip_code)
    Data-->>Validator: ZipInfo or None
    Validator-->>Svc: ValidationResult

    Svc-->>App: ParseResult (complete)
```

---

## 3. Class Hierarchy

```mermaid
classDiagram
    class AddressParserProtocol {
        <<protocol>>
        +parse(address_string) ParseResult
        +parse_batch(addresses) list~ParseResult~
    }

    class DataSourceProtocol {
        <<protocol>>
        +get_zip_info(zip_code) ZipInfo
        +is_valid_zip(zip_code) bool
        +is_valid_state(state) bool
        +normalize_state(state) str
    }

    class ValidatorProtocol {
        <<protocol>>
        +validate(address) ValidationResult
        +name str
    }

    class BaseAddressParser {
        <<abstract>>
        #_parse_impl(address_string) Address
        +parse(address_string) ParseResult
        +parse_batch(addresses) list~ParseResult~
    }

    class USAddressParser {
        +name str
        #_parse_impl(address_string) Address
    }

    class BaseDataSource {
        <<abstract>>
        #_load_data()
        #_get_zip_info_impl(zip) ZipInfo
        +get_zip_info(zip) ZipInfo
        +is_valid_zip(zip) bool
    }

    class CSVDataSource {
        +csv_path str
        #_load_data()
        #_get_zip_info_impl(zip) ZipInfo
    }

    class BaseValidator~T~ {
        <<abstract>>
        +name str
        +validate(item) ValidationResult
    }

    class CompositeValidator~T~ {
        -validators list~BaseValidator~
        +validate(item) ValidationResult
        +add_validator(validator)
    }

    class ZipCodeValidator {
        -data_source DataSourceProtocol
        +validate(address) ValidationResult
    }

    class StateValidator {
        -data_source DataSourceProtocol
        +validate(address) ValidationResult
    }

    class PluginFactory~T~ {
        <<abstract>>
        +_registry dict
        +register(name, impl)$
        +create(name, kwargs)$ T
    }

    class ParserFactory {
        +create(type)$ AddressParserProtocol
    }

    class DataSourceFactory {
        +create(type)$ DataSourceProtocol
    }

    AddressParserProtocol <|.. BaseAddressParser
    BaseAddressParser <|-- USAddressParser

    DataSourceProtocol <|.. BaseDataSource
    BaseDataSource <|-- CSVDataSource

    ValidatorProtocol <|.. BaseValidator
    BaseValidator <|-- CompositeValidator
    BaseValidator <|-- ZipCodeValidator
    BaseValidator <|-- StateValidator

    PluginFactory <|-- ParserFactory
    PluginFactory <|-- DataSourceFactory
```

---

## 4. Package Dependencies

```mermaid
graph LR
    subgraph "External"
        PYDANTIC[pydantic]
        USADDR[usaddress]
        POSTAL[libpostal - optional]
        PANDAS[pandas - optional]
    end

    subgraph "ryandata_address_utils"
        CORE[core/]
        MODELS[models/]
        PARSERS[parsers/]
        DATA[data/]
        VALIDATION[validation/]
        SERVICE[service.py]
        PROTOCOLS[protocols.py]
    end

    SERVICE --> CORE
    SERVICE --> MODELS
    SERVICE --> PARSERS
    SERVICE --> DATA
    SERVICE --> VALIDATION
    SERVICE --> PROTOCOLS

    MODELS --> CORE
    MODELS --> PYDANTIC

    PARSERS --> MODELS
    PARSERS --> CORE
    PARSERS --> USADDR

    DATA --> MODELS
    DATA --> CORE

    VALIDATION --> MODELS
    VALIDATION --> CORE

    SERVICE -.-> POSTAL
    SERVICE -.-> PANDAS

    style SERVICE fill:#4CAF50,color:white
    style CORE fill:#2196F3,color:white
```

---

## 5. Data Model Structure

```mermaid
erDiagram
    ParseResult ||--o| Address : contains
    ParseResult ||--o| InternationalAddress : contains
    ParseResult ||--|| ProcessLog : has
    ParseResult ||--o| ValidationResult : has

    Address ||--o{ AddressField : has_components
    Address ||--|| ZipCodeResult : validated_by

    ProcessLog ||--o{ ProcessEntry : contains

    ValidationResult ||--o{ ValidationError : contains

    ParseResult {
        string raw_input
        Address address
        InternationalAddress international_address
        Exception error
        ValidationResult validation
        ProcessLog process_log
    }

    Address {
        string AddressNumber
        string StreetName
        string StreetNamePostType
        string PlaceName
        string StateName
        string ZipCode5
        string ZipCode4
        string FullAddress
    }

    ProcessEntry {
        string entry_type
        string field
        string message
        string original_value
        string new_value
        string timestamp
    }

    ValidationError {
        string field
        string message
        string value
    }
```

---

## 6. Transformation Tracking Flow

```mermaid
flowchart TD
    INPUT["Raw Input: '123 main st, austin texas 78749'"]

    subgraph "Parsing Phase"
        PARSE[USAddressParser.parse]
        MODEL[Address Model Creation]
        ZIP_NORM[ZipCodeNormalizer]
        ADDR_FMT[AddressFormatter]
    end

    subgraph "Tracking Phase"
        TRACK_ALL[TransformationTracker.track_all]
        TRACK_ZIP[track_zip_normalization]
        TRACK_STATE[track_state_normalization]
        TRACK_WS[track_whitespace_normalization]
        TRACK_COMMA[track_comma_normalization]
    end

    subgraph "Process Log"
        LOG[ProcessLog]
        ENTRY1["state: 'texas' → 'TX'"]
        ENTRY2["full_address: normalized"]
    end

    INPUT --> PARSE
    PARSE --> MODEL
    MODEL --> ZIP_NORM
    MODEL --> ADDR_FMT

    MODEL --> TRACK_ALL
    TRACK_ALL --> TRACK_ZIP
    TRACK_ALL --> TRACK_STATE
    TRACK_ALL --> TRACK_WS
    TRACK_ALL --> TRACK_COMMA

    TRACK_STATE --> ENTRY1
    ADDR_FMT --> ENTRY2

    ENTRY1 --> LOG
    ENTRY2 --> LOG

    LOG --> RESULT[ParseResult with audit trail]

    style INPUT fill:#FFE082
    style RESULT fill:#A5D6A7
    style LOG fill:#90CAF9
```

---

## How to View These Diagrams

### Option 1: GitHub
Simply push this file to GitHub - it renders Mermaid diagrams automatically.

### Option 2: VS Code
Install the "Markdown Preview Mermaid Support" extension.

### Option 3: Online
Copy the Mermaid code blocks to [mermaid.live](https://mermaid.live) for interactive editing and PNG/SVG export.

### Option 4: Generate Images
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Generate PNG
mmdc -i docs/diagrams.md -o docs/architecture.png
```
