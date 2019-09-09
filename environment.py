import platform
import subprocess


class Checker:
    @staticmethod
    def running_on_macos() -> bool:
        return platform.system() == 'Darwin'

    @staticmethod
    def running_on_windows() -> bool:
        return platform.system() == 'Windows'

    @staticmethod
    def running_on_linux() -> bool:
        return platform.system() == 'Linux'

    @staticmethod
    def aws_cli_tools_installed_on_macos_or_linux() -> bool:
        return subprocess.run(['command', '-v', 'aws'], capture_output=True).returncode == 0

    @staticmethod
    def aws_cli_session_manager_plugin_installed_on_macos_or_linux() -> bool:
        return subprocess.run(['command', '-v', 'session-manager-plugin'], capture_output=True).returncode == 0

    @staticmethod
    def aws_cli_tools_installed_on_windows() -> bool:
        return subprocess.run(['where', 'aws'], capture_output=True).returncode == 0

    @staticmethod
    def aws_cli_session_manager_plugin_installed_on_windows() -> bool:
        return subprocess.run(['where', 'session-manager-plugin'], capture_output=True).returncode == 0

    def aws_cli_tools_installed(self) -> bool:
        if self.running_on_macos() or self.running_on_linux():
            return self.aws_cli_tools_installed_on_macos_or_linux()
        if self.running_on_windows():
            return self.aws_cli_tools_installed_on_windows()

        print("Unable to determine the operating system for your computer. I support Linux, macOS, and Windows.")

        return False

    def aws_cli_session_manager_plugin_installed(self) -> bool:
        if self.running_on_macos() or self.running_on_linux():
            return self.aws_cli_session_manager_plugin_installed_on_macos_or_linux()
        if self.running_on_windows():
            return self.aws_cli_session_manager_plugin_installed_on_windows()

        print("Unable to determine the operating system for your computer. I support Linux, macOS, and Windows.")

        return False

    def is_running_on_supported_os(self) -> bool:
        return self.running_on_macos() or self.running_on_windows() or self.running_on_linux()
