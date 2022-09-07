import json
import boto3

def query_s3(expression:str, s3_key:str, bucket:str) -> list:
    s3 = boto3.client('s3')
    r = s3.select_object_content(
            Bucket=bucket,
            Key=s3_key,
            ExpressionType='SQL',
            Expression=expression,
            InputSerialization={'JSON': {"Type": "Lines"}},
            OutputSerialization={'JSON': {}}
    )
    records = []
    for item in r['Payload']:
        if 'Records' in item:
            records = item['Records']['Payload'].decode('utf-8')
            records = [json.loads(record) for record in records.strip().split('\n')]
    return records