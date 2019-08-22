import boto3
import time
def lambda_handler(event, context):
    clientSSM = boto3.client('ssm')
    DB_INSTANCE_NAMES = clientSSM.get_parameter(Name='testList')['Parameter']['Value'].split(',')
    MAX_SNAPSHOTS = int(clientSSM.get_parameter(Name='RDSMaxSnapshotNumber')['Parameter']['Value'])
    clientRDS = boto3.client('rds')
    for DB_INSTANCE_NAME in DB_INSTANCE_NAMES:
        db_snapshots = clientRDS.describe_db_snapshots(
            SnapshotType='manual',
            DBInstanceIdentifier= DB_INSTANCE_NAME
        )['DBSnapshots']
        if len(db_snapshots) >= MAX_SNAPSHOTS:
            oldest_snapshot = db_snapshots[0]
            for db_snapshot in db_snapshots:
                if oldest_snapshot['SnapshotCreateTime'] > db_snapshot['SnapshotCreateTime']:
                    oldest_snapshot = db_snapshot
            clientRDS.delete_db_snapshot(DBSnapshotIdentifier=oldest_snapshot['DBSnapshotIdentifier'])
        clientRDS.create_db_snapshot(
            DBSnapshotIdentifier=DB_INSTANCE_NAME + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()),
            DBInstanceIdentifier=DB_INSTANCE_NAME
        )

