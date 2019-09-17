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
    add_data_contents = 'config.default.py;.'
    if running_on_windows():
        add_data_contents = 'config.default.py;.'

    sys.exit(
        subprocess.run(
            ['pyinstaller', 'main.py', '--add-data', add_data_contents, '--hidden', '-import=configparser',
             '--noconfirm', '--onefile', '--name sessh']
        ).returncode
    )
