import boto3
import time
import re
from botocore.exceptions import ClientError
def lambda_handler(event, context):
    # Input the Maximum number of AMI you want to keep
    MAX_AMI = 2
    # Input the list of EC2 Instance ID seperated by comma (e.x. ['i-1234567','i-7654321'])
    EC2_IDS = ['i-1234567', 'i-765431']
    EC2 = boto3.resource('ec2')
    clientEC2 = boto3.client('ec2')
    for EC2_ID in EC2_IDS:
        EC2_Client_Instance = clientEC2.describe_instances(
            InstanceIds=[EC2_ID]
        )
        EC2_EBS_number = len(EC2_Client_Instance['Reservations'][0]['Instances'][0]['BlockDeviceMappings'])
        First_EBS_Volume = EC2_Client_Instance['Reservations'][0]['Instances'][0]['BlockDeviceMappings'][0]['Ebs'][
            'VolumeId']
        ebs_snapshots = clientEC2.describe_snapshots(
            Filters=[
                {
                    'Name': 'volume-id',
                    'Values': [First_EBS_Volume]
                },
            ],
        )['Snapshots']
        snapshots_createdBy_AMI = []
        for ebs_snapshot in ebs_snapshots:
            if ebs_snapshot['Description'].find('Created by CreateImage') != -1:
                snapshots_createdBy_AMI.append(ebs_snapshot)
        # check if the number of AMI is more than MAX_AMI, if true, delete the oldest AMI
        for i in range(0, len(snapshots_createdBy_AMI) - MAX_AMI + 1):
            # find the oldest AMI ID
            oldest_snapshot = snapshots_createdBy_AMI[0]
            for snapshot_createdBy_AMI in snapshots_createdBy_AMI:
                if oldest_snapshot['StartTime'] > snapshot_createdBy_AMI['StartTime']:
                    oldest_snapshot = snapshot_createdBy_AMI
            oldest_snapshot_description = oldest_snapshot['Description']
            rule = r'(ami\-.*) from'
            AMI_ID = re.findall(rule, oldest_snapshot_description)[0]
            # deregister this AMI
            try:
                clientEC2.deregister_image(ImageId=AMI_ID)
            except ClientError as e:
                print(e)
            # delete all snapshots created by this AMI
            all_oldest_snapshots = clientEC2.describe_snapshots(
                Filters=[
                    {
                        'Name': 'description',
                        'Values': ['*' + AMI_ID + '*']
                    }
                ]
            )['Snapshots']
            for all_oldest_snapshot in all_oldest_snapshots:
                clientEC2.delete_snapshot(SnapshotId=all_oldest_snapshot['SnapshotId'])
        Instance = EC2.Instance(EC2_ID)
        image = Instance.create_image(
            Name=EC2_ID + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
        )
