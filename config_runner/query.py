import json
import boto3
import botocore
import orgcrawler
from orgcrawler.utils import jsonfmt, yamlfmt
from orgcrawler.cli.utils import (
    setup_crawler,
    format_responses,
)


def setup_config_client(region, account):
    return boto3.client('config', region_name=region, **account.credentials)


def config_describe_rules(region, account):     # pragma: no cover
    '''
    usage example:

      orgcrawler -r OrganizationAccountAccessRole orgcrawler.payloads.config.describe_rules

      orgcrawler -r OrganizationAccountAccessRole \
              --regions us-west-2 orgcrawler.payloads.config.describe_rules | jq -r '
              .[] | .Account,
              (.Regions[] | ."us-west-2".ConfigRules[].ConfigRuleName),
              ""' | tee config_rules_in_accounts.us-west-2
    '''
    client = boto3.client('config', region_name=region, **account.credentials)
    response = client.describe_config_rules()
    rules = response['ConfigRules']
    while 'NextToken' in response:
        response = client.describe_config_rules(NextToken=response['NextToken'])
        rules += response['ConfigRules']
    return dict(ConfigRules=rules)


def compliance_by_rule(region, account, rule_name):
    '''
    usage example:

      orgcrawler -r OrganizationAccountAccessRole --regions us-west-2 -f query.py compliance_by_rule securityhub-iam-password-policy-symbol-check
      orgcrawler -r OrganizationAccountAccessRole --regions us-west-2 -f query.py compliance_by_rule securityhub-iam-password-policy-symbol-check |
        jq -r '.[] | .Account, .Regions[].Output.EvaluationResults[].ComplianceType'

    '''

    botoConfig = botocore.client.Config(connect_timeout=2, read_timeout=10, retries={"max_attempts": 2})
    client = boto3.client('config', config=botoConfig, region_name=region, **account.credentials)
    rules = config_describe_rules(region, account)['ConfigRules']
    # returns the first matching name
    full_rule_name = next((r['ConfigRuleName'] for r in rules if r['ConfigRuleName'].startswith(rule_name)), None)
    if full_rule_name is not None:
        response = client.get_compliance_details_by_config_rule(
            ConfigRuleName=full_rule_name,
        )
        evaluations = response['EvaluationResults']
        while 'NextToken' in response:
            response = client.get_compliance_details_by_config_rule(
                ConfigRuleName=full_rule_name,
                NextToken=response['NextToken'],
            )
            evaluations += response['EvaluationResults']
        return dict(EvaluationResults=evaluations)
    else:
        return dict(EvaluationResults={})



'''
Traceback (most recent call last):
  File "/home/agould/git-repos/github/ucopacme/orgcrawler/orgcrawler/crawlers.py", line 98, in run_payload_in_account
    response.payload_output = execution.payload(region, account, *args)
  File "/home/agould/git-repos/github/ucopacme/config_runner/config_runner/query.py", line 52, in compliance_by_rule
    ConfigRuleName=full_rule_name,
  File "/home/agould/python-venv/python3.7/lib/python3.7/site-packages/botocore/client.py", line 357, in _api_call
    return self._make_api_call(operation_name, kwargs)
  File "/home/agould/python-venv/python3.7/lib/python3.7/site-packages/botocore/client.py", line 661, in _make_api_call
    raise error_class(parsed_response, operation_name)
botocore.exceptions.ClientError: An error occurred (ThrottlingException) when calling the GetComplianceDetailsByConfigRule operation (reached max retries: 4): Rate exceeded
'''
