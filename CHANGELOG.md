## [Unreleased]
### Changed
- Replace personal GitHub API token with one owned by Jenkins user.

## [v1.0.0]
### Fixed
- Remove debugging output.
- Use configured SSH keys for direct SSH connections (ones not using a bastion).

## [v1.0.0-beta.30]
### Added
- The path to bastion SSH keys can be specified in the configuration file. You will not have to manually add any keys to the SSH authentication agent as long as the keys for the bastion and destination host are specified in the configuration.

## [v1.0.0-beta.28]
### Fixed
- No longer crashes when no command argument has been specified.
- Using Ctrl+C to abort a command will be passed to the remote terminal, rather than terminating sessh. 

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
