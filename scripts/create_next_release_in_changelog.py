import argparse
import os
import subprocess


def set_up_github_credentials():
    github_auth_token = os.environ["GH_TOKEN"]
    subprocess.run(['git', 'config', 'credential.helper', 'store --file=.git/credentials'])
    with open('.git/credentials', 'w') as credentials_file:
        credentials_file.write(f'https://{github_auth_token}:@github.com')
    subprocess.run(['git', 'config', '--local', 'user.name', 'Travis CI'])
    subprocess.run(['git', 'config', '--local', 'user.email', 'travis@travis-ci.org'])


def update_changelog():
    with open(args.changelog, 'r+') as changelog_file:
        changelog = changelog_file.readlines()
        del changelog[0]
        changelog.insert(0, f'## [{args.version}]\n')
        changelog.insert(0, '\n')
        changelog.insert(0, '## [Unreleased]\n')

        changelog_file.truncate()
        changelog_file.seek(0)
        changelog_file.writelines(changelog)


def commit_and_push(version):
    subprocess.run(['git', 'checkout', 'develop'])
    subprocess.run(['git', 'add', 'CHANGELOG.md'])
    subprocess.run(['git', 'commit', '-m', f'Update for release {version}'])
    subprocess.run(['git', 'push'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Create next release notes section for future release")
    parser.add_argument('changelog', help="path to CHANGELOG.md")
    parser.add_argument('version', help="version of sessh that was previously released")

    args = parser.parse_args()

    set_up_github_credentials()
    update_changelog()
    commit_and_push(args.version)
