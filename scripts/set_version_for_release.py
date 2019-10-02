import argparse
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Write the version number to __init__.py so it is available in sessh")
    parser.add_argument('version', help="version tag")

    args = parser.parse_args()

    init_path = os.path.abspath(__file__ + '/../../__init__.py')

    with open(init_path, 'r+') as init_file:
        lines = init_file.readlines()

        for line_no, content in enumerate(lines):
            if content.startswith('__version__ ='):
                lines[line_no] = f'__version__ = "{args.version}"\n'
                break

        init_file.seek(0)
        init_file.truncate()
        init_file.writelines(lines)
