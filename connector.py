import logging
import os
from typing import Optional, List


class SessionManagerConnector:
    """Connect to an EC2 instance using Systems Manager Session Manager."""

    def __init__(self, instance_id: str, region: str):
        self._logger = logging.getLogger(__name__)
        self._instance_id = instance_id
        self._region = region

    def connect(self) -> int:
        self._logger.debug(f"Connecting directly to {self._instance_id} using Session Manager")

        return os.system(f'aws ssm start-session --target "{self._instance_id}" --region "{self._region}"')


class SshBastionConnector:
    """Connect to an EC2 instance via a bastion, using the private IP address."""

    def __init__(self, bastion_connection: str, private_ip_address: str, ssh_key_paths: Optional[List[str]]):
        self._logger = logging.getLogger(__name__)
        self._bastion_connection = bastion_connection
        self._private_ip_address = private_ip_address
        self._ssh_key_paths = ssh_key_paths

    def connect(self) -> int:
        target = self._get_target_user_and_host()
        key_details = _get_readable_ssh_key_details(self._ssh_key_paths)
        key_inclusion = _get_ssh_key_inclusion_argument(self._ssh_key_paths)
        self._logger.debug(f"Connecting to {target} via {self._bastion_connection} using SSH, with {key_details}")

        return os.system(f'ssh {key_inclusion} -J {self._bastion_connection} {target}')

    def _get_ssh_key_inclusion_argument(self):
        return f"-i {' '.join(self._ssh_key_paths)}" if self._ssh_key_paths else ''

    def _get_readable_ssh_key_details(self):
        return ', '.join(self._ssh_key_paths) \
            if self._ssh_key_paths \
            else "any keys in the SSH authentication agent"

    def _get_target_user_and_host(self) -> str:
        return f'ec2-user@{self._private_ip_address}'


class SshDirectConnector:
    """Connect to an EC2 instance via a bastion, using the public IP address."""

    def __init__(self, public_ip_address: str, ssh_key_paths: Optional[List[str]]):
        self._logger = logging.getLogger(__name__)
        self._public_ip_address = public_ip_address
        self._ssh_key_paths = ssh_key_paths

    def connect(self) -> int:
        target = self._get_target_user_and_host()
        key_details = _get_readable_ssh_key_details(self._ssh_key_paths)
        key_inclusion = _get_ssh_key_inclusion_argument(self._ssh_key_paths)

        self._logger.debug(f"Connecting directly to {target} using SSH, with {key_details}")

        return os.system(f'ssh {key_inclusion} {target}')

    def _get_target_user_and_host(self) -> str:
        return f'ec2-user@{self._public_ip_address}'


def _get_ssh_key_inclusion_argument(ssh_key_paths: Optional[List[str]]) -> str:
    return f"-i {' '.join(ssh_key_paths)}" if ssh_key_paths else ''


def _get_readable_ssh_key_details(ssh_key_paths: Optional[List[str]]) -> str:
    return ', '.join(ssh_key_paths) if ssh_key_paths else "any keys in the SSH authentication agent"
