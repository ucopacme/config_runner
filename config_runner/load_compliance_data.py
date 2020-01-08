#!/usr/bin/env python

import io
import sys
import datetime

import yaml
import json
import boto3
import botocore
from botocore.exceptions import ClientError
import click

import orgcrawler
from orgcrawler.utils import jsonfmt, yamlfmt
from orgcrawler.cli.utils import (
    setup_crawler,
    format_responses,
)

#DEFAULT_REGION = 'us-east-1'
DEFAULT_REGION = 'us-west-2'


def paginate(client, method, **kwargs):
    paginator = client.get_paginator(method.__name__)
    for page in paginator.paginate(**kwargs).result_key_iters():
        for result in page:
            yield result


def truncate_sechub_rule_name(rule_name):
    if rule_name.startswith('securityhub'):
        return rule_name.rpartition('-')[0]
    return rule_name


def get_resource_count(item):
    if 'ComplianceContributorCount' in item['Compliance']:
        return item['Compliance']['ComplianceContributorCount'].get('CappedCount', 0)
    return None


def is_in_scope(spec, rule_name):
    return rule_name in spec.get('config_rules')


def timestamp():
    return datetime.datetime.utcnow().isoformat()


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--master-role', '-r',
    required=True,
    help='IAM role to assume for accessing AWS Organization Master account.'
)
@click.option('--aggregation-account', '-a',
    required=True,
    help='Name or Id of config rule aggregation account.',
)
@click.option('--reporting-account',
    default='',
    help='Name or Id of account where s3 bucket lives. defaults to "aggregation-account"',
)
@click.option('--bucket-name', '-b',
    default='compliance_data',
    help='Name of the s3 bucket where to upload config rule compliance data.'
)
@click.option('--spec-file', '-f',
    default='./spec.yaml',
    show_default=True,
    type=click.File('r'),
    help='Path to file containing config rule names.'
)
def main(master_role, aggregation_account, reporting_account, bucket_name, spec_file):
    if not reporting_account:
        reporting_account = aggregation_account
    print(master_role, aggregation_account, reporting_account, bucket_name, spec_file)

    # parse spec file
    spec = yaml.safe_load(spec_file.read())
    #print(yamlfmt(spec['config_rules']))
    #print()
    #print(yamlfmt([truncate_sechub_rule_name(rule_name) for rule_name in spec['config_rules']]))

    # get account names and alias using orgcrawler
    crawler = setup_crawler(
        master_role,
        regions=DEFAULT_REGION,
    )
    #print(yamlfmt([a.dump() for a in crawler.accounts]))


    # get aggregation name
    account = crawler.org.get_account(aggregation_account)
    #print(account.dump())
    botoConfig = botocore.client.Config(connect_timeout=2, read_timeout=10, retries={"max_attempts": 2})
    client = boto3.client('config', config=botoConfig, region_name=DEFAULT_REGION, **account.credentials)
    response = client.describe_configuration_aggregators(
        #ConfigurationAggregatorNames=[
        #    'string',
        #],
    )
    #print(response)
    aggrigator_name = next(
        (agg['ConfigurationAggregatorName'] for agg in response['ConfigurationAggregators']),
        None,
    )
    #print(aggrigator_name)

    # get compliance data
    if aggrigator_name is not None:
        compliance_generator = paginate(
            client,
            client.describe_aggregate_compliance_by_config_rules,
            ConfigurationAggregatorName=aggrigator_name,
        )
        #print(next(compliance_generator))

    else:
        sys.exit('could not determine ConfigurationAggregatorName')

    # assemble config rule compliance data
    text_stream = io.StringIO()

    for item in compliance_generator:
        rule_name = truncate_sechub_rule_name(item['ConfigRuleName'])
        if is_in_scope(spec, rule_name):
            compliance_data = dict(
                ConfigRuleName=rule_name,
                ComplianceType=item['Compliance']['ComplianceType'],
                ComplianceContributorCount=get_resource_count(item),
                AccountId=item['AccountId'],
                AwsRegion=item['AwsRegion'],
                AccountName=crawler.org.get_account_name_by_id(item['AccountId']),
            )
            text_stream.write(json.dumps(compliance_data) + '\n')
        #else:
        #    print('out of scope: ', compliance_data['AccountName'], rule_name)
    #print(text_stream.getvalue())

    # upload to s3
    obj_path = 'aggregate_compliance_by_config_rules/{}/compliance_data.json'.format(timestamp()) 
    #print(obj_path)
    account = crawler.org.get_account(reporting_account)
    bucket_name = bucket_name + '-' + account.id
    print(bucket_name)
    s3_client = boto3.client('s3', region_name=DEFAULT_REGION, **account.credentials)
    try:
        s3_client.create_bucket(
            ACL = 'private',
            Bucket = bucket_name,
            CreateBucketConfiguration = {'LocationConstraint':DEFAULT_REGION}
        )
    except s3_client.exceptions.BucketAlreadyOwnedByYou as e:
        pass

    s3_client.put_object(
        Bucket = bucket_name,
        Key = obj_path,
        Body = text_stream.getvalue(),
    )

if __name__ == '__main__':
    main()

