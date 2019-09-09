GENERAL = {
    'aws': {
        'region': 'eu-west-1',
        'accounts': {
            '012345678901': {
                'alias': 'aws-account-alias',
            },
            '10987654321': {
                'alias': 'other-aws-account',
            },
        }
    },
    'list': {
        # Which table headings should be displayed.
        # The column order set here will be respected in the script output.
        'table_headings': {
            'Name': True,
            'Instance ID': True,
            'Launch time': True,
            'Private IP': False,
            'Public IP': False,
            'Connection type': True,
        }
    }
}

# Connection configuration for bastions
BASTIONS = [
    {
        'aws_account_alias': 'aws-account-alias',
        'bastion_host': 'bastion.dev.example.com',
        'bastion_user': 'ec2-user',
    },
    {
        'aws_account_alias': 'other-aws-account',
        'bastion_host': 'bastion.staging.example.com',
        'bastion_user': 'ec2-user',
    },
]
