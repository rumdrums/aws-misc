#!/usr/bin/env python

import yaml
import json
import argparse

def convert_to_json(yaml_file, output_file=None):
  base_file_name = yaml_file[:yaml_file.rfind('.')]
  if output_file is None:
    output_file = '/tmp/'
  output_file = output_file + base_file_name + '.json'
  with open(yaml_file) as infile:
    input = yaml.load(infile)
  with open(output_file, 'w') as outfile:
    print(output_file)
    json.dump(input, outfile,indent=1)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='convert yaml to json')
  parser.add_argument('--yaml-file', required=True, help="full path to yaml file to be converted")
  parser.add_argument('--output', help="output dest FOLDER")
  args = parser.parse_args()
  convert_to_json(args.yaml_file)

