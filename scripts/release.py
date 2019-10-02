import argparse
import os
import platform
import subprocess
import sys


def running_on_macos():
    return platform.system() == 'Darwin'


def running_on_windows():
    return platform.system() == 'Windows'


def running_on_linux():
    return platform.system() == 'Linux'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Build a new release")
    parser.add_argument('version', help="version tag")

    args = parser.parse_args()

    add_data_contents = 'config.default.py:.'
    if running_on_windows():
        add_data_contents = 'config.default.py;.'

    # The Python interpreter name and path differs depending on the environment
    interpreter_path = sys.executable

    script_path = os.path.abspath(__file__ + '/../set_version_for_release.py')
    subprocess.run([interpreter_path, script_path, args.version], check=True)

    sys.exit(
        subprocess.run(
            ['pyinstaller', 'main.py', '--add-data', add_data_contents, '--hidden-import=configparser',
             '--noconfirm', '--onefile', '--name', 'sessh'], check=True
        ).returncode
    )
