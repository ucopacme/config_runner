import json
import boto3
import orgcrawler
from orgcrawler.utils import jsonfmt, yamlfmt
from orgcrawler.cli.utils import (
    setup_crawler,
    format_responses,
)


def setup_config_client(region, account):
    return boto3.client('config', region_name=region, **account.credentials)

def create_configuration_recorder(client, kwargs):
    response = client.put_configuration_recorder(ConfigurationRecorder=kwargs)
    return response

def create_delivery_channel(client, kwargs):
    response = client.put_delivery_channel(DeliveryChannel=kwargs)
    return response

def get_configuration_recorder(client):
    response = client.describe_configuration_recorders()
    if response['ConfigurationRecorders']:
        response.pop('ResponseMetadata')
        return response
    return None

def get_delivery_channel(client):
    response = client.describe_delivery_channels()
    if response['DeliveryChannels']:
        response.pop('ResponseMetadata')
        return response
    return None

def make_delivery_channel_bucket(region, account, bucket_name):
    s3 = boto3.resource('s3', region_name=region, **account.credentials)
    bucket = s3.Bucket(bucket_name)
    bucket.create(
        ACL='private',
        CreateBucketConfiguration={'LocationConstraint': region},
    )
    policy_document = {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Sid': 'AWSConfigBucketPermissionsCheck',
                'Effect': 'Allow',
                'Principal': {'Service': ['config.amazonaws.com']},
                'Action': ['s3:GetBucketAcl'],
                'Resource': f'arn:aws:s3:::{bucket_name}',
            },
            {
                'Sid': 'AWSConfigBucketDelivery',
                'Effect': 'Allow',
                'Principal': {'Service': ['config.amazonaws.com']},
                'Action': ['s3:PutObject'],
                'Resource': f'arn:aws:s3:::{bucket_name}/AWSLogs/{account.id}/*',
            }
        ]
    }
    bucket_policy = bucket.Policy()
    bucket_policy.put(Policy=json.dumps(policy_document))
    return bucket

def make_delivery_channel_topic(region, account, topic_name):
    client = boto3.client('sns', region_name=region, **account.credentials)
    sns = boto3.resource('sns', region_name=region, **account.credentials)
    response = client.create_topic(
        Name=topic_name,
        Attributes={
            'DisplayName': 'AWS Config Notification Topic'
        },
        #Tags=[
        #    {
        #        'Key': 'string',
        #        'Value': 'string'
        #    },
        #]
    )
    topic = sns.Topic(response['TopicArn'])
    sns_policy_doc = {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Sid': 'AWSConfigSNSPolicy',
                'Effect': 'Allow',
                'Action': ['sns:Publish'],
                'Principal': {'Service': ['config.amazonaws.com']},
                'Resource': topic.arn,
            }
        ]
    }
    topic.set_attributes(
        AttributeName='Policy',
        AttributeValue=json.dumps(sns_policy_doc),
    )
    return topic


'''
            "PolicyName": "AWSConfigServiceRolePolicy",
            "Arn": "arn:aws:iam::aws:policy/aws-service-role/AWSConfigServiceRolePolicy",
'''
def make_config_service_role(region, account, policy_arn):
    client = boto3.client('iam', region_name=region, **account.credentials)
    iam = boto3.resource('iam', region_name=region, **account.credentials)
    response = client.create_role(
        Path='/aws-service-role/config.amazonaws.com/',
        RoleName='AWSServiceRoleForConfig',
        AssumeRolePolicyDocument=json.dumps({
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Action': ['sts:AssumeRole'],
                    'Principal': {'Service': ['config.amazonaws.com']},
                }
            ]
        }),
        Description='Allows Config to call AWS services and collect resource configurations on your behalf',
        #Tags=[
        #    {
        #        'Key': 'string',
        #        'Value': 'string'
        #    },
        #]
    )
    role = iam.Role('AWSServiceRoleForConfig')
    #role.load()
    role.attach_policy(PolicyArn=policy_arn)
    return role





def main():
    pass


