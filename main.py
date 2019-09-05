#!/usr/bin/env python3

import argparse
import os
import platform
import subprocess
import sys
from configparser import ConfigParser, RawConfigParser
from enum import Enum
from typing import List, Dict, Optional, Generator

import boto3
import texttable as tt

import connector

aws_region = os.environ.get('AWS_REGION', 'eu-west-1')
boto3.setup_default_session(region_name=aws_region)


class ConnectionType(Enum):
    SSH = 'SSH'
    SESSION_MANAGER = 'Session Manager'


class Instance:
    def __init__(self, instance_id: str, name: str, public_ip: Optional[str], private_ip: Optional[str], launch_time,
                 connection_type: ConnectionType, ssh_key: Optional[str], state: str):
        self.instance_id = instance_id
        self.name = name
        self.private_ip = private_ip
        self.public_ip = public_ip
        self.launch_time = launch_time
        self.connection_type = connection_type
        self.ssh_key = ssh_key
        self.state = state

    def is_running(self) -> bool:
        return self.state == 'running'

    def supports_ssh(self) -> bool:
        """
        Is SSH used to connect to this instance.

        Note: Does NOT check whether access would be allowed by security group configuration.
        """
        return self.connection_type == ConnectionType.SSH and self.ssh_key is not None

    def supports_session_manager(self) -> bool:
        return self.connection_type == ConnectionType.SESSION_MANAGER


class InstancesRepository:
    def __init__(self):
        self._ec2_metadata = Ec2MetadataClient()
        self._ssm_metadata = SsmMetadataClient()
        self._instances = self._fetch_instance_metadata()

    def running(self) -> List[Instance]:
        return [i for i in self._instances if i.is_running()]

    def _fetch_instance_metadata(self) -> List[Instance]:
        # Sort list by name
        return sorted(self._merge_instance_metadata(), key=lambda i: i.name.casefold())

    def _merge_instance_metadata(self) -> Generator[Instance, None, None]:
        for instance_metadata in self._ec2_metadata.running():
            ssm_metadata = self._ssm_metadata.by_id(instance_metadata.instance_id)

            if ssm_metadata:
                connection_type = ConnectionType.SESSION_MANAGER
            else:
                connection_type = ConnectionType.SSH

            yield Instance(instance_metadata.instance_id, instance_metadata.get_name(), instance_metadata.public_ip,
                           instance_metadata.private_ip, instance_metadata.launch_time, connection_type,
                           instance_metadata.ssh_key_name, instance_metadata.state)

    def find_running_by_instance_name(self, name: str) -> List[Instance]:
        return [i for i in self._instances if i.name == name and i.is_running()]

    def find_running_by_instance_id(self, instance_id: str) -> List[Instance]:
        return [i for i in self._instances if i.instance_id == instance_id and i.is_running()]


class Ec2InstanceMetadata:
    def __init__(self, instance_id: str, public_ip: Optional[str], private_ip: Optional[str], state: str,
                 launch_time: str, ssh_key_name, tags: List[Dict[str, str]]):
        self.instance_id = instance_id
        self.private_ip = private_ip
        self.public_ip = public_ip
        self.state = state
        self.launch_time = launch_time
        self.ssh_key_name = ssh_key_name
        self._tags = tags

    def is_running(self) -> bool:
        return self.state == 'running'

    def get_name(self) -> str:
        """Get the instance name based on the tag with the key "Name"."""
        for tag in self._tags:
            if tag['Key'] == 'Name':
                return tag['Value']

        return "-No name set-"


class Ec2MetadataClient:
    def __init__(self):
        self._client = boto3.client('ec2')
        self._instances = self._fetch_metadata()

    def all(self) -> Generator[Ec2InstanceMetadata, None, None]:
        return self._instances

    def running(self) -> List[Ec2InstanceMetadata]:
        return [i for i in self._instances if i.is_running()]

    def _fetch_metadata(self) -> Generator[Ec2InstanceMetadata, None, None]:
        response = self._client.describe_instances(MaxResults=50)
        # with open('./responses/ec2.json', 'rb') as j:
        # response = json.load(j)

        for reservations in response['Reservations']:
            for instance in reservations['Instances']:
                yield Ec2InstanceMetadata(
                    instance['InstanceId'],
                    instance.get('PublicIpAddress'),
                    instance.get('PrivateIpAddress'),
                    instance['State']['Name'],
                    instance['LaunchTime'],
                    instance.get('KeyName'),
                    instance['Tags']
                )


class SsmMetadataClient:
    def __init__(self):
        self._client = boto3.client('ssm')
        self._instances = self._fetch_metadata()

    def all(self) -> Dict[str, Dict]:
        return self._instances

    def by_id(self, instance_id) -> Optional[Dict]:
        if instance_id not in self._instances:
            return None

        return self._instances[instance_id]

    def _fetch_metadata(self) -> Dict[str, Dict]:
        response = self._client.describe_instance_information(MaxResults=50)
        # with open('./responses/ssm.json', 'rb') as j:
        #     response = json.load(j)

        return {i['InstanceId']: i for i in response['InstanceInformationList']}


class InstancesDisplayer:
    @staticmethod
    def display(instances: List[Instance]):
        table = tt.Texttable(120)
        table.header(["Name", "Instance ID", "Launch time", "Connection type"])

        for instance in instances:
            connection_type = InstancesDisplayer.generate_connection_type(instance)

            table.add_row([instance.name, instance.instance_id, instance.launch_time, connection_type])

        print(table.draw())

    @staticmethod
    def generate_connection_type(instance: Instance) -> str:
        if instance.supports_ssh():
            connection_type = f"SSH ({instance.ssh_key})"
        elif instance.supports_session_manager():
            connection_type = "Session Manager"
        else:
            connection_type = "Unknown"
        return connection_type


def list_instances() -> int:
    instances = InstancesRepository().running()
    InstancesDisplayer.display(instances)

    return 0


def choose_instance(instances: List[Instance]) -> Instance:
    while True:
        table = tt.Texttable(120)
        table.header(["", "Instance ID", "Launch time", "Connection type"])

        for i, instance in enumerate(instances):
            table.add_row([i, instance.instance_id, instance.launch_time,
                           InstancesDisplayer.generate_connection_type(instance)])

        print(table.draw())
        choice = input('Select an instance to connect to [0]: ') or 0

        try:
            return instances[int(choice)]
        except (IndexError, ValueError):
            pass


class EnvironmentChecker:
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


class AccountMetadataClient(object):
    def __init__(self):
        self._client = boto3.client('sts')
        self._metadata = self._fetch_metadata()

    def get_account_id(self) -> str:
        return self._metadata['Account']

    def _fetch_metadata(self) -> Dict[str, str]:
        return self._client.get_caller_identity()


class UserConfiguration:
    def __init__(self):
        self._environment = EnvironmentChecker()
        self._config_file_path = self._generate_path_to_config_file()
        self._configuration = self._load()

    def _load(self):
        if self._configuration_file_exists():
            return self._parse_configuration()

        self._create_empty_configuration_file()

    def _configuration_file_exists(self) -> bool:
        return os.path.isfile(self._config_file_path)

    def _parse_configuration(self) -> Optional[RawConfigParser]:
        config = ConfigParser()
        config.read(self._config_file_path)

        return config

    def _generate_path_to_config_file(self) -> str:
        filename = 'sessh.ini'
        folder_name = 'sessh'

        if self._environment.running_on_windows():
            return os.path.expandvars(f'%APPDATA%/{filename}')

        if self._environment.running_on_linux() or self._environment.running_on_macos():
            configured_config_home = os.environ.get('XDG_CONFIG_HOME')

            if configured_config_home:
                return os.path.join(configured_config_home, folder_name, filename)

            return os.path.expanduser(f'~/.config/{folder_name}/{filename}')

    def _create_empty_configuration_file(self):
        os.makedirs(os.path.dirname(self._config_file_path), exist_ok=True, mode=0o770)
        open(self._config_file_path, 'a').close()

    def get_bastion_connection_details_for_account(self, account_id: str) -> str:
        section_name = 'bastions'

        if not self._configuration.has_section(section_name):
            raise RuntimeError(f"There is no bastion configuration for account {account_id}. Add the configuration in "
                               f"{self._config_file_path}")

        return self._configuration.get(section_name, account_id)


def connect_to_instance(name_or_id: str, connect_to_public_ip_address: bool) -> int:
    environment = EnvironmentChecker()
    configuration = UserConfiguration()

    instances = InstancesRepository()

    # Instance ID specified
    if name_or_id.startswith('i-'):
        matching_instances = instances.find_running_by_instance_id(name_or_id)
    else:
        matching_instances = instances.find_running_by_instance_name(name_or_id)

    number_running_instances = len(matching_instances)
    if number_running_instances == 0:
        print(f"There are no running instances for {name_or_id}.")
        return 1

    if number_running_instances == 1:
        matching_instance = matching_instances[0]
    else:
        print(f"There are {number_running_instances} running instances matching {name_or_id}.")
        matching_instance = choose_instance(matching_instances)

    if matching_instance.supports_ssh():
        client = AccountMetadataClient()

        if connect_to_public_ip_address:
            if matching_instance.public_ip is None:
                print(f"Instance {matching_instance.instance_id} does not have a public IP. You could try connecting "
                      f"to the private IP address via a bastion.")

                return 10

            return connector.SshDirectConnector(matching_instance.public_ip).connect()

        else:
            bastion_for_account = configuration.get_bastion_connection_details_for_account(client.get_account_id())

            return connector.SshBastionConnector(bastion_for_account, matching_instance.private_ip).connect()

    if matching_instance.supports_session_manager():
        if not environment.aws_cli_tools_installed():
            print("The AWS Command Line Tools must be installed. Visit https://aws.amazon.com/cli/ for instructions.")
            print("You can also connect to the instance in your browser by visiting "
                  "https://eu-west-1.console.aws.amazon.com/systems-manager/managed-instances?region=eu-west-1")
            return 2

        if not environment.aws_cli_session_manager_plugin_installed():
            print("The Session Manager Plugin for the AWS CLI must be installed. Visit "
                  "https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html "
                  "for instructions.")
            print("You can also connect to the instance in your browser by visiting "
                  "https://eu-west-1.console.aws.amazon.com/systems-manager/managed-instances?region=eu-west-1")
            return 3

        return connector.SessionManagerConnector(matching_instance.instance_id).connect()

    print(f"{matching_instance.instance_id} doesn't seem to support SSH or Session Manager so I can't help you, "
          f"unfortunately.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='action')
    list_command = subparsers.add_parser('list')
    connect_command = subparsers.add_parser('connect')
    connect_command.add_argument('instance', help='EC2 instance ID or EC2 instance name')
    connect_command.add_argument('--public', '-p', help='Connect to the public IP address instead of the private one',
                                 action='store_true', default=False)
    args = parser.parse_args()

    if args.action == 'list':
        sys.exit(list_instances())

    if args.action == 'connect':
        sys.exit(connect_to_instance(args.instance, args.public))
