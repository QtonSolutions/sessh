import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Create next release notes section for future release")
    parser.add_argument('changelog', help="path to CHANGELOG.md")
    parser.add_argument('version', help="version of sessh that was previously released")

    args = parser.parse_args()

    with open(args.changelog, 'r+') as changelog_file:
        changelog = changelog_file.readlines()
        del changelog[0]
        changelog.insert(0, f'## [{args.version}]\n')
        changelog.insert(0, '\n')
        changelog.insert(0, '## [Unreleased]\n')

        changelog_file.truncate()
        changelog_file.seek(0)
        changelog_file.writelines(changelog)
