import os
import shutil
import yaml
import orgcrawler

ORG_ACCESS_ROLE='myrole'
MASTER_ACCOUNT_ID='123456789012'

SIMPLE_ORG_SPEC="""
root:
  - name: root
    accounts:
    - account01
    - account02
    - account03
    child_ou:
      - name: ou01
        child_ou:
          - name: ou01-sub0
      - name: ou02
        child_ou:
          - name: ou02-sub0
      - name: ou03
        child_ou:
          - name: ou03-sub0
"""
def mock_org_from_spec(client, root_id, parent_id, spec):
    for ou in spec:
        if ou['name'] == 'root':
            ou_id = root_id
        else:
            ou_id = client.create_organizational_unit(
                ParentId=parent_id,
                Name=ou['name'],
            )['OrganizationalUnit']['Id']
        if 'accounts' in ou:
            for name in ou['accounts']:
                account_id = client.create_account(
                    AccountName=name,
                    Email=name + '@example.com',
                )['CreateAccountStatus']['AccountId']
                client.move_account(
                    AccountId=account_id,
                    SourceParentId=root_id,
                    DestinationParentId=ou_id,
                )
        if 'child_ou' in ou:
            mock_org_from_spec(client, root_id, ou_id, ou['child_ou'])


def build_mock_org(spec):
    org = orgcrawler.orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    client = org._get_org_client()
    client.create_organization(FeatureSet='ALL')
    org_id = client.describe_organization()['Organization']['Id']
    root_id = client.list_roots()['Roots'][0]['Id']
    mock_org_from_spec(client, root_id, root_id, yaml.load(spec)['root'])
    return (org_id, root_id)

def clean_up(org=None):
    if org is None:
        org = orgcrawler.orgs.Org(MASTER_ACCOUNT_ID, ORG_ACCESS_ROLE)
    if os.path.isdir(org._cache_dir):
        shutil.rmtree(org._cache_dir)

