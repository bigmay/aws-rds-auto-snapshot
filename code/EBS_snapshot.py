import boto3
import time
def lambda_handler(event, context):
    MAX_SNAPSHOTS = 5
    EBS_VOLUME_IDS = ['test']
    clientEC2 = boto3.client('ec2')
    for EBS_VOLUME_ID in EBS_VOLUME_IDS:
        ebs_snapshots = clientEC2.describe_snapshots(
            Filters=[
                {
                    'Name': 'volume-id',
                    'Values': [EBS_VOLUME_ID]
                },
            ],
        )['Snapshots']
        for i in range(0, len(ebs_snapshots) - MAX_SNAPSHOTS + 1):
            oldest_snapshot = ebs_snapshots[0]
            for ebs_snapshot in ebs_snapshots:
                if oldest_snapshot['StartTime'] > ebs_snapshot['StartTime']:
                    oldest_snapshot = ebs_snapshot
            clientEC2.delete_snapshot(SnapshotId=oldest_snapshot['SnapshotId'])
            ebs_snapshots.remove(oldest_snapshot)
        clientEC2.create_snapshot(
            Description=EBS_VOLUME_ID + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()),
            VolumeId=EBS_VOLUME_ID
        )