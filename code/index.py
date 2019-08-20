import boto3
import time
def lambda_handler(event, context):
    MAX_SNAPSHOTS = 5
    DB_INSTANCE_NAME = 'test'
    clientRDS = boto3.client('rds')
    db_snapshots = clientRDS.describe_db_snapshots(
        SnapshotType='manual',
    )['DBSnapshots']

    if len(db_snapshots) >= MAX_SNAPSHOTS:
        oldest_snapshot = db_snapshots[0]
        for db_snapshot in db_snapshots:
            if db_snapshots[0]['SnapshotCreateTime'] > db_snapshot['SnapshotCreateTime']:
                oldest_snapshot = db_snapshot
        clientRDS.delete_db_snapshot(DBSnapshotIdentifier=oldest_snapshot['DBSnapshotIdentifier'])
    create_snapshot = clientRDS.create_db_snapshot(
        DBSnapshotIdentifier=DB_INSTANCE_NAME + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()),
        DBInstanceIdentifier=DB_INSTANCE_NAME
    )