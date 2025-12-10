# CHANGELOG

<!-- version list -->

## v0.3.0 (2025-12-09)

### Bug Fixes

- Clean up imports for Python 3.9+ compatibility
  ([`8254854`](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/82548547b8f8298f1793f338476edcf61f98a4e7))

- Handle validation errors in pandas integration when errors='coerce'
  ([`4f092f7`](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/4f092f7074f1a4291a1a080ade0bbf4ea31cd054))

- Make version reading more robust to prevent import errors
  ([`4850090`](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/485009021e2d80e798c90925e8572519a38fbfb0))

- Resolve GitHub Actions workflow failures
  ([`a04042b`](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/a04042bf9efdffcd53a1e4405b4abf07c392faf3))

- Update release workflow to handle git config and build properly
  ([`b19902b`](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/b19902b8e92405bb73acb4bf5f8ad09f758aaa94))

### Chores

- Configure semantic-release for automated releases
  ([`67d7732`](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/67d7732b8b1d25d9f2a598fa540e927ae5b8b520))

- Update uv.lock after formatting
  ([`0547d8c`](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/0547d8ca504c1c4034e362ef23eef095a98e9fa5))

### Code Style

- Format code with ruff
  ([`381b33e`](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/381b33ef4d9409704d10a84b72f25cc77b14a65b))

### Continuous Integration

- Force minor version bump for semantic-release
  ([`7e84ddb`](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/7e84ddb6f2342bca60f82309ef3ed60a8b5e6be6))

### Documentation

- Add UV installation and development instructions
  ([`fd1d35f`](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/fd1d35f3caf9fe6543ee8456a85d74a5995081a8))

- Update README badges to show correct workflow statuses
  ([`6679580`](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/6679580ab034fae4a2668eaa9cb28406f2c27459))

### Features

- Add automatic Address1, Address2, and FullAddress properties to Address model
  ([`13f33e6`](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/13f33e6f36f3700eed6189bea6467a7b83082be6))

- Add RawInput field to Address model to capture original input string
  ([`5c702b0`](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/5c702b050c3e13400360007be3dfffad3b899e8f))

- Reinstated GitHub release workflow with semantic-release
  ([`d6e66de`](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/d6e66dedac2bb1f772fb6e1ee572fcc80f98058f))

### Refactoring

- Use model_validator instead of properties for Address formatting fields
  ([`be5dc3c`](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/be5dc3c19629a1d72ca1d571fae9d12bb5ff30d0))


## v0.2.0 (2025-12-08)

- Initial Release
