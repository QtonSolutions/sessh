## [Unreleased]
### Fixed
- No longer crashes when no command argument has been specified. 

## [v1.0.0-beta.26]
### Added
- Display help and version information.
- Catch exceptions and show more user friendly message.
- `--debug` argument for extra logging output.
- `--debug` will cause exceptions to be re-raised for easier debugging. 

### Fixed
- Support instances without tags.
- Paginate EC2 and SSM results.

## [1.0.0 Alpha 3]
### Fixed
- Configuration template file now available in binary so it can be copied to config directory on first run.

## [1.0.0 Alpha 2]
### Added
- Use configured AWS region when connecting using SSM.

### Changed
#### User configuration using Python file
- List table headers
- Default AWS region
- Bastion configuration
