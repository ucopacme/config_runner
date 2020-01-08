# head -1 aggregate_compliance_by_config_rules/2020-01-08T19\:52\:12.601838/compliance_data.json 
#{"ConfigRuleName": "securityhub-iam-password-policy-symbol-check", "ComplianceType": "COMPLIANT", "ComplianceContributorCount": null, "AccountId": "011208821250", "AwsRegion": "us-west-2", "AccountName": "ucpath-prod"}


CREATE EXTERNAL TABLE IF NOT EXISTS aggregate_compliance_data (
  ConfigRuleName string,
  ComplianceType string,
  ComplianceContributorCount string,
  AccountId string,
  AwsRegion string,
  AccountName string
)
ROW FORMAT serde 'org.openx.data.jsonserde.JsonSerDe'
with serdeproperties ( 'paths'='ConfigRuleName, ComplianceType, ComplianceContributorCount, AccountId, AwsRegion, AccountName' )
LOCATION 's3://is3-compliance-data-921671357694/aggregate_compliance_by_config_rules/2020-01-08T19:52:12.601838';
