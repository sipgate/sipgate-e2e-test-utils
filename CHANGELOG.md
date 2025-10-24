# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2025-10-24

### Fixed

- use `jsonrpc` field for V2.0 requests/responses, as per spec (#e322213)

### Added

- convenience shorthands for `JsonRpcVersion` (#29c60a9)

### Changed

- invalid requests/responses will now cause a `ParseError` (#cb894b8)

## [2.0.1] - 2025-09-29

### Fixed

- JobD helper now uses new XML Responses (#cdae9ce)
- JSON RPC request fails on non-string method name (#7b1274b)

## [2.0.0] - 2025-09-29

### Added

- `fault` field in XML Responses (#ce91845)
- JSON RPC request/response serialization/parsing (#c074ce4)

### Changed

- Construction of XML Responses (#b7dd289)

### Removed

- `fault_code` and `fault_string` in XML Responses (in favour of `fault` field) (#ce91845)

## [1.3.0] - 2025-08-29

### Added

- waiting helpers (#317f670)

## [1.2.1] - 2025-08-28

### Fixed

- include jobd_functions.xml in build (#80e65c4)

## [1.2.0] - 2025-08-28

### Added

- clear_all_tables SQLAlchemy helper (#1966761)

## [1.1.0] - 2025-08-28

### Added

- XML RPC response serialization (#7223e96)
- JobD helper (#a88a343)

### Changed

- allow omitting empty dict for RPC requests (#f575a1e)

## [1.0.0] - 2025-08-26

### Added

- added [http-request-recorder](https://github.com/sipgate/http-request-recorder) matchers for XML/JSON RPC requests (#5edb323).
- added sipgate-flavoured XML RPC request/response parsing/serialization (#58f6a75).

[3.0.0]: https://github.com/sipgate/http-request-recorder/compare/v2.0.1...v3.0.0
[2.0.1]: https://github.com/sipgate/http-request-recorder/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/sipgate/http-request-recorder/compare/v1.3.0...v2.0.0
[1.3.0]: https://github.com/sipgate/http-request-recorder/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/sipgate/http-request-recorder/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/sipgate/http-request-recorder/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/sipgate/http-request-recorder/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/sipgate/http-request-recorder/releases/tag/v1.0.0

