#!/usr/bin/env python3

import sys

import argparse
import boto3
import logging
import os
import platform
import shutil
import texttable as tt
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Generator

import configuration
import connector
import environment
from __init__ import __version__

environment_checker = environment.Checker()
user_configuration = configuration.UserConfiguration(environment_checker)

aws_region = os.environ.get('AWS_DEFAULT_REGION', user_configuration.get_default_region())


class ConnectionType(Enum):
    SSH = 'SSH'
    SESSION_MANAGER = 'Session Manager'


class Instance:
    def __init__(self, instance_id: str, name: str, public_ip: Optional[str], private_ip: Optional[str],
                 launch_time: datetime, connection_type: ConnectionType, ssh_key: Optional[str], state: str):
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

    def connection_details(self) -> str:
        if self.supports_ssh():
            connection_type = f"SSH ({self.ssh_key})"
        elif self.supports_session_manager():
            connection_type = "Session Manager"
        else:
            connection_type = "Unknown"

        return connection_type


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
                 launch_time: datetime, ssh_key_name, tags: List[Dict[str, str]]):
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
        paginator = self._client.get_paginator('describe_instances')
        page_iterator = paginator.paginate()

        for page in page_iterator:
            for reservations in page['Reservations']:
                for instance in reservations['Instances']:
                    yield Ec2InstanceMetadata(
                        instance['InstanceId'],
                        instance.get('PublicIpAddress'),
                        instance.get('PrivateIpAddress'),
                        instance['State']['Name'],
                        instance['LaunchTime'],
                        instance.get('KeyName'),
                        instance.get('Tags', {})
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
        paginator = self._client.get_paginator('describe_instance_information')
        page_iterator = paginator.paginate()

        metadata = {}

        for page in page_iterator:
            for instance_info in page['InstanceInformationList']:
                instance_id = instance_info['InstanceId']
                metadata[instance_id] = instance_info

        return metadata


class InstancesDisplayer:
    header_mappings = {
        'Name': lambda i: i.name,
        'Instance ID': lambda i: i.instance_id,
        'Launch time': lambda i: i.launch_time,
        'Private IP': lambda i: i.private_ip,
        'Public IP': lambda i: i.public_ip,
        'Connection type': lambda i: i.connection_details(),
    }
    """Maps the table column heading to a lambda that returns the relevant value from the Instance"""

    def __init__(self, table_column_configuration: dict):
        self._table_column_configuration = table_column_configuration

    def display(self, instances: List[Instance]):
        table = self._start_table()

        table.header(self.get_chosen_headers())

        for instance in instances:
            table.add_row(self.get_instance_details(self.get_chosen_headers(), instance))

        print(table.draw())

    def _start_table(self) -> tt.Texttable:
        # Make the table at least 120 columns wide, but bigger if the terminal is currently wider.
        terminal_columns = shutil.get_terminal_size().columns
        table_width = max(terminal_columns, 120)
        table = tt.Texttable(table_width)

        return table

    def get_chosen_headers(self) -> List[str]:
        """Get the headers that have been chosen by the user in the configuration file."""
        chosen_headers = []

        for header, is_chosen in self._table_column_configuration.items():
            if is_chosen:
                chosen_headers.append(header)

        return chosen_headers

    def get_instance_details(self, chosen_headers: List[str], instance: Instance) -> List[str]:
        instance_details = []

        for header_name in chosen_headers:
            instance_details.append(self.get_instance_value_for_header(header_name, instance))

        return instance_details

    def get_instance_value_for_header(self, header_name, instance: Instance) -> Optional[str]:
        return self.header_mappings[header_name](instance)

    def display_indexed(self, instances: List[Instance]):
        table = self._start_table()

        # Add a # as the first column so a user can choose the instance they want to connect to
        headers = ['#']
        headers.extend(self.get_chosen_headers())
        table.header(headers)

        for index, instance in enumerate(instances):
            instance_index = str(index)
            instance_details = [instance_index]
            instance_details.extend(self.get_instance_details(self.get_chosen_headers(), instance))
            table.add_row(instance_details)

        print(table.draw())


def list_instances() -> int:
    instances = InstancesRepository().running()
    InstancesDisplayer(user_configuration.configuration.GENERAL['list']['table_headings']).display(instances)

    return 0


def choose_instance(instances: List[Instance]) -> Instance:
    displayer = InstancesDisplayer(user_configuration.get_table_configuration())

    while True:
        displayer.display_indexed(instances)

        # Pick first instance as the default
        choice = input('Select an instance to connect to [0]: ') or 0

        try:
            return instances[int(choice)]
        except (IndexError, ValueError):
            pass


class AccountMetadataClient(object):
    def __init__(self):
        self._client = boto3.client('sts')
        self._metadata = self._fetch_metadata()

    def get_account_id(self) -> str:
        return self._metadata['Account']

    def _fetch_metadata(self) -> Dict[str, str]:
        return self._client.get_caller_identity()


def connect_to_instance(name_or_id: str, connect_to_public_ip_address: bool) -> int:
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
            bastion_for_account = user_configuration.get_bastion_connection_details_for_account(client.get_account_id())

            return connector.SshBastionConnector(bastion_for_account, matching_instance.private_ip).connect()

    if matching_instance.supports_session_manager():
        if not environment_checker.aws_cli_tools_installed():
            print("The AWS Command Line Tools must be installed. Visit https://aws.amazon.com/cli/ for instructions.")
            print("You can also connect to the instance in your browser by visiting "
                  "https://eu-west-1.console.aws.amazon.com/systems-manager/managed-instances?region=eu-west-1")
            return 2

        if not environment_checker.aws_cli_session_manager_plugin_installed():
            print("The Session Manager Plugin for the AWS CLI must be installed. Visit "
                  "https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html "
                  "for instructions.")
            print("You can also connect to the instance in your browser by visiting "
                  "https://eu-west-1.console.aws.amazon.com/systems-manager/managed-instances?region=eu-west-1")
            return 3

        return connector.SessionManagerConnector(matching_instance.instance_id,
                                                 user_configuration.get_default_region()).connect()

    print(f"{matching_instance.instance_id} doesn't seem to support SSH or Session Manager so I can't help you, "
          f"unfortunately.")


def version_information() -> int:
    print(f"sessh/{__version__} Python/{platform.python_version()}")
    print(f"Configuration file path: {user_configuration.get_file_path()}")

    return 0


if __name__ == '__main__':
    common_arguments = argparse.ArgumentParser(add_help=False)
    common_arguments.add_argument('--debug', help="output debug information", action='store_true', default=False)

    parser = argparse.ArgumentParser(description="Command line tool to help start sessions on AWS EC2 instances")
    parser.add_argument('--version', help="display version information", action='store_true', default=False)
    subparsers = parser.add_subparsers(dest='action')
    list_command = subparsers.add_parser('list', help="list running EC2 instances", parents=[common_arguments])
    connect_command = subparsers.add_parser('connect', help="connect to a running EC2 instance",
                                            parents=[common_arguments])
    connect_command.add_argument('instance', help="EC2 instance ID or EC2 instance name")
    connect_command.add_argument('--public', '-p', help="connect to the public IP address instead of the private one",
                                 action='store_true', default=False)

    args = parser.parse_args()

    try:
        if args.version:
            sys.exit(version_information())

        logging_level = logging.DEBUG if args.debug else logging.WARNING
        logging.basicConfig(level=logging_level)

        boto3.setup_default_session(region_name=aws_region)

        if args.action == 'list':
            sys.exit(list_instances())

        if args.action == 'connect':
            sys.exit(connect_to_instance(args.instance, args.public))
    except Exception as e:
        if args.debug:
            raise e

        print(e)
        sys.exit(1)

    parser.print_help()
