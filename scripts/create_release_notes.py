import argparse
import re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract release notes for unreleased version")
    parser.add_argument('changelog', help="path to CHANGELOG.md")
    parser.add_argument('release_notes', help="path to release notes to use for release")

    args = parser.parse_args()

    with open(args.changelog, 'r') as changelog_file, open(args.release_notes, 'w') as release_notes:
        changelog = changelog_file.read()
        start = r'^## \[Unreleased\]'
        last_release = r'^## [\d'
        parts = re.split(r'^## .+', changelog, flags=re.MULTILINE)
        unreleased_release_notes = parts[1].strip()

        release_notes.write(unreleased_release_notes)
