import json
from os import getenv, remove
import boto3
import requests
from s3_select_wrapper import reduce_to_ascii


queue_url = getenv('queue_url')
destination_bucket = getenv('destination_bucket')
parks_url = 'https://queue-times.com/parks.json'


def lambda_handler(event=None, context=None):
    j = requests.get(parks_url).json()

    key = 'parks.json'
    local_file = f"/tmp/{key}"
    data = reduce_to_ascii(json.dumps(j, ensure_ascii=False))
    with open(local_file, 'w') as f:
        f.write(data)
    s3 = boto3.resource('s3')
    s3.meta.client.upload_file(local_file, destination_bucket, key)
    remove(local_file)
    print(f"Fetched and uploaded {key}")
    
    sqs = boto3.client('sqs')
    for grouping in j:
        for park in grouping['parks']:
            print(park)
            sqs.send_message(
                QueueUrl = queue_url,
                MessageBody = (
                    json.dumps(park)
                )
            )
