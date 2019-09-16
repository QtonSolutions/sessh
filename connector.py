import logging
import subprocess


class SessionManagerConnector:
    """Connect to an EC2 instance using Systems Manager Session Manager."""

    def __init__(self, instance_id: str, region: str):
        self._logger = logging.getLogger(__name__)
        self._instance_id = instance_id
        self._region = region

    def connect(self) -> int:
        self._logger.debug(f"Connecting directly to {self._instance_id} using Session Manager")
        return subprocess.run(
            ['aws', 'ssm', 'start-session', '--target', self._instance_id, '--region', self._region]
        ).returncode


class SshBastionConnector:
    """Connect to an EC2 instance via a bastion, using the private IP address."""

    def __init__(self, bastion_connection: str, private_ip_address: str):
        self._logger = logging.getLogger(__name__)
        self._bastion_connection = bastion_connection
        self._private_ip_address = private_ip_address

    def connect(self) -> int:
        target = self._get_target_user_and_host()
        self._logger.debug(f"Connecting to {target} via {self._bastion_connection} with SSH")
        return subprocess.run(['ssh', '-J', self._bastion_connection, target]).returncode

    def _get_target_user_and_host(self) -> str:
        return f'ec2-user@{self._private_ip_address}'


class SshDirectConnector(object):
    """Connect to an EC2 instance via a bastion, using the public IP address."""

    def __init__(self, public_ip_address: str):
        self._logger = logging.getLogger(__name__)
        self._public_ip_address = public_ip_address

    def connect(self) -> int:
        target = self._get_target_user_and_host()
        self._logger.debug(f"Connecting directly to {target} with SSH")
        return subprocess.run(['ssh', target]).returncode

    def _get_target_user_and_host(self) -> str:
        return f'ec2-user@{self._public_ip_address}'
