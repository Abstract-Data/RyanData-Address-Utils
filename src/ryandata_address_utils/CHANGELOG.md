# Changelog

## [0.8.0](https://github.com/Abstract-Data/RyanData-Address-Utils/compare/address-utils-v0.7.2...address-utils-v0.8.0) (2026-08-05)


### Features

* Add automatic Address1, Address2, and FullAddress properties to Address model ([13f33e6](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/13f33e6f36f3700eed6189bea6467a7b83082be6))
* Add GitHub releases and semantic versioning ([23d910d](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/23d910d6bbc9156f056ab07bd6033657e3373918))
* add international marker to Address and map intl parses ([b8a1cfc](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/b8a1cfc112120192c66682d9b83b0dbe4c7942c0))
* add libpostal docker image and api entrypoint ([51093eb](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/51093ebbe1b4eb6ec433bafb031711943be22510))
* add libpostal normalization and international markers ([b164103](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/b1641037462af1792485944a5776f29209d1bef7))
* Add loc property to RyanDataAddressError and enhance cleaning metrics tracking ([dd1903d](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/dd1903dd3c088dd0037411490e48e92692643162))
* Add partial address validation with component cleaning ([f1f89f5](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/f1f89f574cd259e8372296f221f39ca81d99228a))
* Add RawInput field to Address model to capture original input string ([5c702b0](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/5c702b050c3e13400360007be3dfffad3b899e8f))
* add strict international libpostal fallback ([1ba3ad7](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/1ba3ad7ae6c0eb2d77d1b8b946b9229bbaf14f19))
* add ZipCode5/ZipCode4 support and validation ([afcf1b0](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/afcf1b0e0dbad02ab37d807d44ad9892fd71911b))
* Cleaning operations are tracked with timestamps and reasons ([f1f89f5](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/f1f89f574cd259e8372296f221f39ca81d99228a))
* Enhanced ParseResult with cleaning report methods ([f1f89f5](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/f1f89f574cd259e8372296f221f39ca81d99228a))
* integrate abstract-validation-base library ([2762bd7](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/2762bd7a478c48b43ae0e247f744636a89b96759))
* New allow_partial=True enables cleaning of invalid optional components ([f1f89f5](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/f1f89f574cd259e8372296f221f39ca81d99228a))
* Set up CodeCov coverage reporting ([27f8783](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/27f878335b9ce017b03870452b214fddc7be7291))
* SOLID/DRY refactoring with unified ProcessLog system ([0d9a248](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/0d9a248537c89100d158638fb94e6767d75c306e))


### Bug Fixes

* Clean up imports for Python 3.9+ compatibility ([8254854](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/82548547b8f8298f1793f338476edcf61f98a4e7))
* fallback to libpostal on US validation failure ([d9251c3](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/d9251c308945bbd7b2d03160778fd6ecde3f0ade))
* Handle validation errors in pandas integration when errors='coerce' ([4f092f7](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/4f092f7074f1a4291a1a080ade0bbf4ea31cd054))
* Make version reading more robust to prevent import errors ([4850090](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/485009021e2d80e798c90925e8572519a38fbfb0))
* Resolve GitHub Actions workflow failures ([a04042b](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/a04042bf9efdffcd53a1e4405b4abf07c392faf3))
* Revert type annotations to Optional[X] for Python 3.9 compatibility ([eff3066](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/eff3066d4e6f60cd9929ce50f30e45aab1a3e05d))
* Sync __version__ in __init__.py with pyproject.toml (0.7.2) ([434da84](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/434da84b916de503f78b0427bdbc69d179efe904))
* update trogon init_tui API and test CLI invocations ([6c03b62](https://github.com/Abstract-Data/RyanData-Address-Utils/commit/6c03b6242484f898ffa274e54c1487c0ee818dc0))
