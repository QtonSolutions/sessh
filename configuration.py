import os
import shutil
import sys

import environment


class UserConfiguration:
    def __init__(self, environment: environment.Checker):
        self._environment = environment
        self._config_file_path = self._generate_path_to_config_file()
        self.configuration = self._load()

    def _load(self):
        if not self._configuration_file_exists():
            self._create_initial_configuration_file()

        # A user configuration path and import it
        sys.path.append(os.path.abspath(os.path.dirname(self._config_file_path)))
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
        os.makedirs(os.path.dirname(self._config_file_path), exist_ok=True, mode=0o770)
        shutil.copyfile('./config.default.py', self._config_file_path)

    def get_table_configuration(self) -> dict:
        return self.configuration.GENERAL['list']['table_headings']

    def get_bastion_connection_details_for_account(self, account_id: str) -> str:
        account_alias = self.get_account_alias(account_id)

        for bastion_configuration in self.configuration.BASTIONS:
            if bastion_configuration['aws_account_alias'] == account_alias:
                bastion_user = bastion_configuration['bastion_user']
                bastion_host = bastion_configuration['bastion_host']

                return f'{bastion_user}@{bastion_host}'

        raise RuntimeError(f"There is no bastion configuration for account {account_id}. Add the configuration in "
                           f"{self._config_file_path}")

    def get_account_alias(self, account_id: str) -> str:
        if account_id not in self.configuration.GENERAL['aws']['accounts']:
            raise RuntimeError(f"There is no AWS account alias configuration for account {account_id}. Add the "
                               f"configuration in {self._config_file_path}")

        return self.configuration.GENERAL['aws']['accounts'][account_id]['alias']

    def get_default_region(self) -> str:
        return self.configuration.GENERAL['aws']['region']
