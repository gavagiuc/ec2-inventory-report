# EC2-Inventory

Python script to generate a xlsx report containing all EC2 instances in AWS account.

Generated report has the following table header:

|Instance Type | Platform| Public IP | Private IP | Instance State | LaunchTime | AWS Account | CPU | CPU Utilization Avg | ECU | memory GiB | Volume | Size GiB | Volume | Size GiB | Volume | Size GiB | Volume | Size GiB | Volume | Size GiB | 
|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|

Prerequisites:
```
pip install openpyxl boto3
price.json file ( can be regenerated using python ec2-price-json-generator.py)
```
Run via Python:
```
python inventory.py AWS-profile-name
```

