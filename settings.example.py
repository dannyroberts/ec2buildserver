import ec2
ec2.credentials.from_file('credentials.csv')
ec2.credentials.REGION_NAME = 'us-east-1'

ACCESS_KEY_ID = ec2.credentials.ACCESS_KEY_ID
SECRET_ACCESS_KEY = ec2.credentials.SECRET_ACCESS_KEY
REGION_NAME = ec2.credentials.REGION_NAME

AMI = 'ami-fa2c3992'  # Ubuntu 12.04
INSTANCE_TYPE = 'm1.small'
SECURITY_GROUPS = ['default']
KEY_NAME = 'build'
