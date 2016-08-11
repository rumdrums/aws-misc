#!/usr/bin/env python

import boto3
import pprint
import yaml

class Instance:
  def __init__(self, instance_id, client):
    self.instance_id = instance_id
    self.client = client

class Subnet:
  def __init__(self, subnet_id, client):
    self.subnet_id = subnet_id
    self.client = client
    #self._subnet = client.describe_subnets(SubnetIds=[self.subnet_id])
    self.instances = self.get_instances()
   
  def get_dict(self):
    subnet_dict = {}
    subnet_dict['id'] = self.subnet_id
    subnet_dict['instances'] = self.instances
    return subnet_dict

  def get_instances(self):
    instance_ids = [ i['InstanceId'] for i in self.client.describe_instances() if i['SubnetId'] == self.subnet_id ]
    return instance_ids

class Vpc:
  def __init__(self, vpc_id, client):
    self.vpc_id = vpc_id
    self.client = client
    self.subnets = self.get_subnets()
    self._vpc = client.describe_vpcs(VpcIds=[self.vpc_id])
    self.vpc_name = self.get_vpc_name()

  def get_subnets(self):
    subnet_ids = [ i['SubnetId'] for i in self.client.describe_subnets()['Subnets'] if i['VpcId'] == self.vpc_id ] 
    return [ Subnet(i, self.client) for i in subnet_ids ]

  def get_dict(self):
    vpc_dict = {}
    vpc_dict['id'] = self.vpc_id
    vpc_dict['name'] = self.vpc_name
    vpc_dict['subnets'] = [ i.get_dict() for i in self.subnets ]
    return vpc_dict

  def get_vpc_name(self):
   # FIXME: exception handling if key doesn't exist:
   if 'Tags' in self._vpc['Vpcs'][0]:
     return [ i['Value'] for i in self._vpc['Vpcs'][0]['Tags'] if i['Key'] == 'Name' ][0]
 
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
    f.write(yaml.dump(account_info, default_flow_style=False))
    
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
