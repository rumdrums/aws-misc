#!/usr/bin/env python

import boto3
import pprint
import yaml
import re
 
class Account:
  def __init__(self, acct_num, client):
    self.client = client
    self.acct_num = acct_num
    self.vpcs = self.get_vpcs()
    self.subnets = self.get_subnets()
    self.instances = self.get_instances()

  def get_vpcs(self):
    vpcs = [ i for i in self.client.describe_vpcs()['Vpcs'] ]
    return vpcs
    
  def get_subnets(self):
    subnets = [ i for i in self.client.describe_subnets()['Subnets'] ]
    return subnets

  def get_instances(self):
    instances = [ [ j for j in i['Instances'] ] for i in self.client.describe_instances()['Reservations'] ]
    return instances
 
  def get_dict(self):
    account_dict = {}
    account_dict['account_number'] = self.acct_num
    account_dict['vpcs'] = self.vpcs
    account_dict['subnets'] = self.subnets
    account_dict['instances'] = self.instances
    return account_dict

    return 

#  def get_recursive_dict(self):
#    account_dict = {}
#    account_dict['account_number'] = self.acct_num
#    account_dict['vpcs'] = [ i.get_dict() for i in self.vpcs ] 
#    return account_dict
      
def assume_role(account_number, role_name):
  sts_client = boto3.client('sts')
  role_arn = 'arn:aws:iam::%s:role/Administrator' % account_number
  assumedRoleObject = sts_client.assume_role(
    RoleArn=role_arn,
    RoleSessionName="AssumeRoleSession1"
  )
  credentials = assumedRoleObject['Credentials']
  return {
    'aws_access_key_id': credentials['AccessKeyId'],
    'aws_secret_access_key': credentials['SecretAccessKey'],
    'aws_session_token': credentials['SessionToken'],
  }

def assume_admin(account_number):
  return assume_role(account_number, 'Administrator')

def print_account_stuff(account_info):
  for acct in account_info:
    print("account: %s" % acct),
    for vpc in account_info[acct].vpcs:
      print("vpc: %s vpcname: %s" % (vpc.vpc_id, vpc.vpc_name)),
      for subnet in vpc.subnets:
        print("Subnet: %s" % subnet.subnet_id),

def write_to_yaml(account_info, file_name):
  with open(file_name, 'w') as f:
    yaml.safe_dump(account_info, f, encoding='utf-8', allow_unicode=True)
    #f.write(yaml.dump(account_info, default_flow_style=False))
    
def get_account_array(account_numbers):
  account_info = {}
  account_array = []
  for acct in account_numbers:
    account_info[acct] = {}
    credentials = assume_admin(acct)
    ec2 = boto3.client('ec2', **credentials)
    account_info[acct] = Account(acct, ec2)
    account_array.append(account_info[acct].get_dict())
  #pprint.pprint(account_array)
  return account_array 

def get_subnets_from_vpc_ids(account_array, vpc_ids):
  subnets = []
  for account in account_array:
    for subnet in account['subnets']:
      for vpc_id in vpc_ids:
        if subnet['VpcId'] == vpc_id:
          subnets.append(dict(subnet_id=subnet['SubnetId'], vpc_id=vpc_id))
  return subnets


def get_vpcs_by_name_regex(account_array, pattern):
  """ parse account_info dict and get those whose names match given regex """

  prog = re.compile('%s' % pattern)

  keepers = []
  for account in account_array:
    for vpc in account['vpcs']:
      if 'Tags' in vpc:
        for tag in vpc['Tags']:
          if tag['Key'] == 'Name':
            if prog.search(tag['Value']):
              keepers.append(vpc)
  return keepers

def main():
  import argparse
  parser = argparse.ArgumentParser(description='dictify aws inventory')
  parser.add_argument('--account', required=True, nargs="+", help="account number(s)")
  args = parser.parse_args() 

  account_numbers = args.account
  account_array = get_account_array(account_numbers)
  write_to_yaml(account_array, '/tmp/out.yaml')

if __name__ == '__main__':
  main()
