import json
from os import getenv
import boto3


source_bucket = getenv('source_bucket')
park_id = int(getenv('park_id'))


def lambda_handler(event=None, context=None):
    s3 = boto3.client('s3')

    r = s3.select_object_content(
            Bucket=source_bucket,
            Key=f"{park_id}.json",
            ExpressionType='SQL',
            Expression="select * from s3object[*].waits.lands[*].rides[*] as s where s.name = 'Blue Streak'",
            InputSerialization={'JSON': {"Type": "Lines"}},
            OutputSerialization={'JSON': {}}
    )

    for event in r['Payload']:
        if 'Records' in event:
            records = event['Records']['Payload'].decode('utf-8')
            j = json.loads(records)
            print(j)
