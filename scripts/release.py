import argparse
import os
import subprocess
import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Build a new release")
    parser.add_argument('version', help="version tag")

    args = parser.parse_args()

    # The Python interpreter name and path differs depending on the environment
    interpreter_path = sys.executable

    script_path = os.path.abspath(__file__ + '/../set_version_for_release.py')
    subprocess.run([interpreter_path, script_path, args.version], check=True)

    sys.exit(
        subprocess.run(
            ['pyinstaller', 'main.py', '--add-data', f'config.default.py{os.pathsep}.', '--hidden-import=configparser',
             '--noconfirm', '--onefile', '--name', 'sessh'], check=True
        ).returncode
    )
