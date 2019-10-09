import logging
import os
import shutil
import sys
from typing import Optional, List

import environment


def resource_path(relative_path):
    """ Get absolute path to resource. Works for development and for PyInstaller created binaries."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Fall back to current directory if sys._MEIPASS is not set
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class UserConfiguration:
    def __init__(self, environment: environment.Checker):
        self._logger = logging.getLogger(__name__)
        self._environment = environment
        self._config_file_path = self._generate_path_to_config_file()
        self.configuration = self._load()

    def _load(self):
        if not self._configuration_file_exists():
            self._logger.debug(
                f"Configuration file not found at {self.get_file_path()} so the default one will be created"
            )
            self._create_initial_configuration_file()

        # Append user configuration path and import it
        sys.path.append(os.path.abspath(os.path.dirname(self.get_file_path())))
        import config

        return config

    def _configuration_file_exists(self) -> bool:
        return os.path.isfile(self._config_file_path)

    def _generate_path_to_config_file(self) -> str:
        filename = 'config.py'
        folder_name = 'sessh'

        if self._environment.running_on_windows():
            return os.path.expandvars(f'%APPDATA%/{folder_name}/{filename}')

        if self._environment.running_on_linux() or self._environment.running_on_macos():
            configured_config_home = os.environ.get('XDG_CONFIG_HOME')

            if configured_config_home:
                return os.path.join(configured_config_home, folder_name, filename)

            return os.path.expanduser(f'~/.config/{folder_name}/{filename}')

    def _create_initial_configuration_file(self):
        directory_path = os.path.dirname(self.get_file_path())
        self._logger.debug(f"Creating configuration file folders: {directory_path}")
        os.makedirs(directory_path, exist_ok=True, mode=0o770)
        self._logger.debug(f"Copying template configuration to {self.get_file_path()}")
        shutil.copyfile(resource_path('config.default.py'), self.get_file_path())

    def get_table_configuration(self) -> dict:
        return self.configuration.GENERAL['list']['table_headings']

    def get_bastion_configuration_details_for_account(self, account_alias: str) -> dict:
        for bastion_configuration in self.configuration.BASTIONS:
            if bastion_configuration['aws_account_alias'] == account_alias:
                return bastion_configuration

        raise RuntimeError(f"There is no bastion configuration for account alias {account_alias}. Add the "
                           f"configuration in {self.get_file_path()}")

    def get_bastion_connection_details_for_account_id(self, account_id: str) -> str:
        account_alias = self.get_account_alias(account_id)
        bastion_configuration = self.get_bastion_configuration_details_for_account(account_alias)
        bastion_user = bastion_configuration['bastion_user']
        bastion_host = bastion_configuration['bastion_host']

        return f'{bastion_user}@{bastion_host}'

    def get_account_alias(self, account_id: str) -> str:
        if account_id not in self.configuration.GENERAL['aws']['accounts']:
            raise RuntimeError(f"There is no AWS account alias configuration for account {account_id}. Add the "
                               f"configuration to GENERAL['accounts']['{account_id}'] in {self.get_file_path()}")

        return self.configuration.GENERAL['aws']['accounts'][account_id]['alias']

    def get_default_region(self) -> str:
        return self.configuration.GENERAL['aws']['region']

    def get_file_path(self) -> str:
        return self._config_file_path

    def get_ssh_key_paths_for_account_id(self, account_id: str) -> Optional[List[str]]:
        account_alias = self.get_account_alias(account_id)
        bastion_configuration = self.get_bastion_configuration_details_for_account(account_alias)

        if 'ssh_keys' in bastion_configuration:
            return bastion_configuration['ssh_keys']
