# Release Notes for v0.3.0

## Features
- **Enhanced Error Handling**: Added `RyanDataAddressError` and `RyanDataValidationError` classes that inherit from Pydantic's error types while including package identification for better error tracing
- **Automatic Address Formatting**: Implemented automatic Address1, Address2, and FullAddress property computation using Pydantic model validators
- **Raw Input Preservation**: Added RawInput field to Address model to capture original input strings
- **Automated Releases**: Reinstated GitHub Actions release workflow with semantic-release for automated versioning and releases

## Fixes  
- **Pandas Integration**: Fixed validation error handling in pandas integration methods when `errors='coerce'` is used
- **Workflow Issues**: Resolved GitHub Actions workflow failures and cache problems
- **Import Compatibility**: Cleaned up imports for Python 3.9+ compatibility
- **Version Handling**: Made version reading more robust to prevent import errors
- **Git Configuration**: Fixed release workflow git configuration issues

## Documentation
- **UV Support**: Added comprehensive UV installation and development instructions
- **Badge Updates**: Updated README badges to reference correct GitHub Actions workflows

## Refactoring
- **Model Validators**: Replaced property-based address formatting with Pydantic model validators for better performance and consistency

## Chores
- **Code Formatting**: Applied ruff formatting across entire codebase
- **Dependency Updates**: Updated uv.lock and project dependencies
- **CI/CD**: Configured semantic-release for automated releases

---

**Full Changelog**: https://github.com/Abstract-Data/RyanData-Address-Utils/compare/v0.2.0...v0.3.0
