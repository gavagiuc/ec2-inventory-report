#!/usr/bin/env python
#   Prerequisites:
#       Python v <=2.7.13
#       pip <= 9.0.1
#       pip install demjson
#
#   Usage : python ec2-price-json-generator.py
#
#   Generate price.json file with custom EC2 Instace details from AWS Pricing
#
import os
import re
import json
import time
from collections import defaultdict, OrderedDict

import requests
import demjson

LINUX_PRICING_URLS = [
    # Deprecated instances (JSON format)
    'https://aws.amazon.com/ec2/pricing/json/linux-od.json',
    # Previous generation instances (JavaScript file)
    'https://a0.awsstatic.com/pricing/1/ec2/previous-generation/linux-od.min.js',
    # New generation instances (JavaScript file)
    'https://a0.awsstatic.com/pricing/1/ec2/linux-od.min.js'
]

EC2_REGIONS = [
    'us-east-1',
    'us-east-2',
    'us-west-1',
    'us-west-2',
    'us-gov-west-1',
    'eu-west-1',
    'eu-west-2',
    'eu-central-1',
    'ca-central-1',
    'ap-southeast-1',
    'ap-southeast-2',
    'ap-northeast-1',
    'ap-northeast-2',
    'ap-south-1',
    'sa-east-1',
    'cn-north-1',
]

INSTANCE_SIZES = [
    'micro',
    'small',
    'medium',
    'large',
    'xlarge',
    'x-large',
    'extra-large'
]

RE_NUMERIC_OTHER = re.compile(r'(?:([0-9]+)|([-A-Z_a-z]+)|([^-0-9A-Z_a-z]+))')

PRICING_FILE_PATH = './price.json'
PRICING_FILE_PATH = os.path.abspath(PRICING_FILE_PATH)


def scrape_ec2_pricing():
    result = {}
    result['regions'] = []
    result['prices'] = defaultdict(OrderedDict)
    result['models'] = defaultdict(OrderedDict)

    for url in LINUX_PRICING_URLS:
        response = requests.get(url)

        if re.match('.*?\.json$', url):
            data = response.json()
        elif re.match('.*?\.js$', url):
            data = response.content
            match = re.match('^.*callback\((.*?)\);?$', data,
                             re.MULTILINE | re.DOTALL)
            data = match.group(1)
            # demjson supports non-strict mode and can parse unquoted objects
            data = demjson.decode(data)

        regions = data['config']['regions']

        for region_data in regions:

            region_name = region_data['region']

            if region_name not in result['regions']:
                result['regions'].append(region_name)

            libcloud_region_name = region_name
            instance_types = region_data['instanceTypes']

            for instance_type in instance_types:
                sizes = instance_type['sizes']
                for size in sizes:

                    price = size['valueColumns'][0]['prices']['USD']
                    if str(price).lower() == 'n/a':
                        # Price not available
                        continue

                    if not result['models'][libcloud_region_name].has_key(size['size']):
                        result['models'][libcloud_region_name][size['size']] = {}
                        result['models'][libcloud_region_name][size['size']]['CPU'] = int(size['vCPU'])

                        if size['ECU'] == 'variable':
                            ecu = 0
                        else:
                            ecu = float(size['ECU'])

                        result['models'][libcloud_region_name][size['size']]['ECU'] = ecu

                        result['models'][libcloud_region_name][size['size']]['memoryGiB'] = float(size['memoryGiB'])

                        result['models'][libcloud_region_name][size['size']]['storageGB'] = size['storageGB']

                    result['prices'][libcloud_region_name][size['size']] = float(price)

    return result


def update_pricing_file(pricing_file_path, pricing_data):
    ##    with open(pricing_file_path, 'r') as fp:
    #        content = fp.read()

    data = {'compute': {}}  # json.loads(content)
    data['updated'] = int(time.time())
    data['compute'].update(pricing_data)

    # Always sort the pricing info
    data = sort_nested_dict(data)

    content = json.dumps(data, indent=4)
    lines = content.splitlines()
    lines = [line.rstrip() for line in lines]
    content = '\n'.join(lines)

    with open(pricing_file_path, 'w') as fp:
        fp.write(content)


def sort_nested_dict(value):
    """
    Recursively sort a nested dict.
    """
    result = OrderedDict()

    for key, value in sorted(value.items(), key=sort_key_by_numeric_other):
        if isinstance(value, (dict, OrderedDict)):
            result[key] = sort_nested_dict(value)
        else:
            result[key] = value

    return result


def sort_key_by_numeric_other(key_value):
    """
    Split key into numeric, alpha and other part and sort accordingly.
    """
    return tuple((
                     int(numeric) if numeric else None,
                     INSTANCE_SIZES.index(alpha) if alpha in INSTANCE_SIZES else alpha,
                     other
                 ) for (numeric, alpha, other) in RE_NUMERIC_OTHER.findall(key_value[0]))


def main():
    print('Scraping EC2 pricing data')

    pricing_data = scrape_ec2_pricing()
    update_pricing_file(pricing_file_path=PRICING_FILE_PATH,
                        pricing_data=pricing_data)

    print('Pricing data updated')


if __name__ == '__main__':
    main()
