config_runner
=============

Orgcrawler payload functions for managing AWS config service resources

Things I want to be able to report
----------------------------------

for each account/region:

- list all rules by ConfigRuleName
- list all rules with all resources fully compliant by ConfigRuleName
- list all rules with any non-compliant resources by ConfigRuleName
- list all rules with any non-compliant resources by ConfigRuleName and non-compliant resource count
- list all rules with any non-compliant resources by ConfigRuleName and non-compliant resource arn
- list total count of all non-compliant config rules
- list total count of all non-compliant resources

for each config rule:

- list all accounts/regions where rule is deployed
- list all accounts/regions where rule is fully compliant
- list all accounts/regions where rule is not fully compliant
- for each account/region:

  - list count of all compliant resources
  - list count of all non-compliant resources
  - list arn of all compliant resources
  - list arn of all non-compliant resources

- for all accounts/regions:

  - list total count of all non-compliant resources
  - list total count of all non-compliant resources

