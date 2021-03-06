![sessh](./assets/sessh.png)

Command line tool to help start sessions on AWS EC2 instances. 

## Installation
### macOS
1. Install [Homebrew](https://brew.sh)
2. Add our custom tap: `brew tap qtonsolutions/tap`
3. Install _sessh_: `brew install sessh`
4. Done! _sessh_ is now available in your terminal.

> *Updating* Run `brew update && brew upgrade sessh` to upgrade to the latest version of _sessh_.

### Windows
1. Download the latest release from the [releases](https://github.com/QtonSolutions/sessh/releases/) page and uncompress it.
2. Move the file to a folder in your `%PATH%`
3. Done! `sessh.exe` is now available in your command prompt.

> *Updating* You will need to manually download the latest version and replace the old binary.

## Usage
### Quick start
1. Make sure your AWS credentials are available in your terminal.
   1. macOS/Linux
      1. `export AWS_PROFILE=account-name` (recommended)
      2. `export AWS_ACCESS_KEY_ID=aabbcc AWS_SECRET_ACCESS_KEY=secret`
   2. Windows PowerShell
      1. `$env:AWS_PROFILE = "account-name"` (recommended)
      2. `$env:AWS_ACCESS_KEY_ID = "aabbcc"; $env:AWS_SECRET_ACCESS_KEY = "secret"`
2. List instances for the chosen AWS account
     
     `$ sessh list` 

3. Connect to the instance by name or instance ID
   1. `$ sessh connect "instance-name"`
   2. `$ sessh connect "i-0123456789abcdefg`

   > *Note:* Make sure the SSH key has been added to your SSH keychain before trying to connect to an instance with the SSH instance type.

### Configuration
Configuration is managed in a configuration file, with a small number of overrides that are specific with command line arguments.

The configuration file file is stored in `~/.config/sessh/config.py` on macOS and Linux, and `%APPDATA%/sessh/config.py` on Windows. A default template is created when you first run the script.

### Listing instances
`sessh list` outputs a table with details of the running EC2 instances for the AWS account your credentials are associated with.

The "Connection type" column shows the method which _sessh_ has determined will be best to connect using. Session Manager is always preferred, even if SSH is also available.

### Connecting to instances
`sessh connect [instance id|instance name]` attempts to connect to the instance using either Session Manager or SSH, depending on what _sessh_ thinks is available.

For SSH connections, _sessh_ will by default assume you want to connect via a bastion. It requires you to configure the bastion connection details (username and IP address/hostname). 

If you do not need to connect to the host via a bastion, add the `--public` flag and _sessh_ will connect directly to the public IP address of the instance.

#### When more than one instance has the same name
Running `sessh connect "instance-name"` when more than one instance has the same name will display a list of matching instances. Choose the one you want to connect to, with the first being the default.

```bash
$ sessh connect "horizontally-scaled-application"
There are 2 running instances matching horizontally-scaled-application.
+---+---------------------+---------------------------+-----------------+
|   |     Instance ID     |        Launch time        | Connection type |
+===+=====================+===========================+=================+
| 0 | i-0123456789abcdefg | 2019-05-09 13:09:08+00:00 | Session Manager |
+---+---------------------+---------------------------+-----------------+
| 1 | i-1123456789abcdefg | 2019-05-09 13:09:08+00:00 | Session Manager |
+---+---------------------+---------------------------+-----------------+
Select an instance to connect to [0]:
```

### Notes
- _sessh_ does not check whether the security group configuration would prevent you from connecting via SSH.
- _sessh_ is not able to tell whether it should connect to the private IP address via a bastion, or to the public interface. Pass the `--public` argument if no bastion is required to connect to the instance.

# Development
Please update the `CHANGELOG.md` file when making a change to _sessh_. The following sections should be used:
- *Added* for new features.
- *Changed* for changes in existing functionality.
- *Deprecated* for soon-to-be removed features.
- *Removed* for now removed features.
- *Fixed* for any bug fixes.
- *Security* in case of vulnerabilities.

# Building executables
[PyInstaller](http://www.pyinstaller.org) is used to create single executable files to make installing _sessh_ simpler.

Executables can only be built for the environment that PyInstaller is run in. E.g. a macOS version can only be built in macOS. Executables are currently automatically built by [https://travis-ci.org/QtonSolutions/sessh](Travis CI).

## Steps
1. Create a new release tag, follow the Github recommendation below. You can also check the previous [releases](https://github.com/QtonSolutions/sessh/releases/) to see examples.
2. Push the tag and wait for the [Travis CI build](https://travis-ci.org/QtonSolutions/sessh) to complete.

> It’s common practice to prefix your version names with the letter v. Some good tag names might be v1.0 or v2.3.4.
> If the tag isn’t meant for production use, add a pre-release version after the version name. Some good pre-release versions might be v0.2-alpha or v5.9-beta.3.
