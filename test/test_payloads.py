import json
import boto3
import botocore
from moto import (
    mock_organizations,
    mock_sts,
    mock_config,
    mock_s3,
    mock_sns,
    mock_iam,
)

from orgcrawler.utils import yamlfmt
from orgcrawler.cli.utils import setup_crawler
from .utils import (
    ORG_ACCESS_ROLE,
    SIMPLE_ORG_SPEC,
    build_mock_org,
)

from config_runner import payloads

RECORDER_ATTRIBUTES = {
        'name': 'config_test',
        'roleARN': 'config_test',
        'recordingGroup': {
            'allSupported': True,
            'includeGlobalResourceTypes': True,
            'resourceTypes': [],
        }
    }


CHANNEL_ATTRIBUTES = {
    'name': 'config_test',
    's3BucketName': 'config_test',
    's3KeyPrefix': 'config_test',
    'snsTopicARN': 'config_test',
    'configSnapshotDeliveryProperties': {
        'deliveryFrequency': 'One_Hour',
    }
}

#@mock_sts
#@mock_organizations
#@mock_config
#def test_setup_config_client():
#    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
#    crawler = setup_crawler(ORG_ACCESS_ROLE)
#    account = crawler.accounts[0]
#    region = crawler.regions[0]
#    client = payloads.setup_config_client(region, account)
#    assert isinstance(client, object)
#    assert hasattr(client, 'describe_configuration_recorders')
#
#def setup_test_client():
#    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
#    crawler = setup_crawler(ORG_ACCESS_ROLE)
#    account = crawler.accounts[0]
#    region = crawler.regions[0]
#    client = payloads.setup_config_client(region, account)
#    return client
#
#@mock_sts
#@mock_organizations
#@mock_config
#def test_create_configuration_recorder():
#    client = setup_test_client()
#    response = payloads.create_configuration_recorder(client, RECORDER_ATTRIBUTES)
#    print(response)
#    assert response is not None
#    assert response['ResponseMetadata']['HTTPStatusCode'] == 200
#
#@mock_sts
#@mock_organizations
#@mock_config
#def test_get_configuration_recorder():
#    client = setup_test_client()
#    response = payloads.get_configuration_recorder(client)
#    assert response is None
#    payloads.create_configuration_recorder(client, RECORDER_ATTRIBUTES)
#    response = payloads.get_configuration_recorder(client)
#    assert isinstance(response, dict)
#    assert response['ConfigurationRecorders'][0] == RECORDER_ATTRIBUTES
#
#@mock_sts
#@mock_organizations
#@mock_config
#def test_create_delivery_channel():
#    client = setup_test_client()
#    payloads.create_configuration_recorder(client, RECORDER_ATTRIBUTES)
#    response = payloads.create_delivery_channel(client, CHANNEL_ATTRIBUTES)
#    print(response)
#    assert response is not None
#    assert response['ResponseMetadata']['HTTPStatusCode'] == 200
#
#@mock_sts
#@mock_organizations
#@mock_config
#def test_get_delivery_channel():
#    client = setup_test_client()
#    response = payloads.get_delivery_channel(client)
#    assert response is None
#    payloads.create_configuration_recorder(client, RECORDER_ATTRIBUTES)
#    payloads.create_delivery_channel(client, CHANNEL_ATTRIBUTES)
#    response = payloads.get_delivery_channel(client)
#    assert isinstance(response, dict)
#    assert response['DeliveryChannels'][0] == CHANNEL_ATTRIBUTES

@mock_sts
@mock_organizations
@mock_s3
def test_setup_config_client():
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    crawler = setup_crawler(ORG_ACCESS_ROLE)
    account = crawler.accounts[0]
    region = crawler.regions[0]
    bucket = payloads.make_delivery_channel_bucket(region, account, 'config_test')
    #print(bucket)
    #print(bucket.Policy().policy)
    #print(dir(bucket))
    assert isinstance(bucket, object)
    assert bucket.name == 'config_test'
    assert isinstance(bucket.Policy().policy, str)
    policy_document = json.loads(bucket.Policy().policy)
    assert policy_document['Statement'][0]['Sid'] == 'AWSConfigBucketPermissionsCheck'
    assert policy_document['Statement'][1]['Sid'] == 'AWSConfigBucketDelivery'
    #assert False

@mock_sts
@mock_organizations
@mock_sns
def test_setup_config_client():
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    crawler = setup_crawler(ORG_ACCESS_ROLE)
    account = crawler.accounts[0]
    region = crawler.regions[0]
    topic = payloads.make_delivery_channel_topic(region, account, 'config_test')
    #print(topic)
    #print(topic.attributes)
    assert isinstance(topic, object)
    assert topic.arn.rpartition(':')[2] == 'config_test'
    assert isinstance(topic.attributes['Policy'], str)
    sns_policy_document = json.loads(topic.attributes['Policy'])
    assert sns_policy_document['Statement'][0]['Sid'] == 'AWSConfigSNSPolicy'
 
@mock_sts
@mock_organizations
@mock_iam
def test_setup_config_client():
    org_id, root_id = build_mock_org(SIMPLE_ORG_SPEC)
    crawler = setup_crawler(ORG_ACCESS_ROLE)
    account = crawler.accounts[0]
    region = crawler.regions[0]
    client = boto3.client('iam', region_name=region, **account.credentials)
    response = client.create_policy(
        PolicyName='AWSConfigServiceRolePolicy',
        Path='/aws-service-role/',
        PolicyDocument=json.dumps({
            'Version': '2012-10-17',
            'Statement': [
                {   
                    'Effect': 'Allow',
                    'Action': 'config:*',
                    'Resource': "*",
                }
            ]
        }),
        Description='mock policy for testing test_setup_config_client()',
    )
    role = payloads.make_config_service_role(region, account, response['Policy']['Arn'])
    print(role)
    #print(dir(role))
    print(role.name)
    print(role.path)
    #print(next(role.attached_policies.all()))
    print(role.assume_role_policy_document)
    assert isinstance(role, object)
    #assert topic.arn.rpartition(':')[2] == 'config_test'
    #assert isinstance(topic.attributes['Policy'], str)
    #sns_policy_document = json.loads(topic.attributes['Policy'])
    #assert sns_policy_document['Statement'][0]['Sid'] == 'AWSConfigSNSPolicy'
    assert False   #assert False
