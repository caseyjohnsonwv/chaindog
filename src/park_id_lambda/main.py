import json
from os import getenv, remove
import boto3
import requests


queue_url = getenv('queue_url')
destination_bucket = getenv('destination_bucket')
parks_url = 'https://queue-times.com/parks.json'


def lambda_handler(event=None, context=None):
    j = requests.get(parks_url).json()

    key = 'parks.json'
    local_file = f"/tmp/{key}"
    with open(local_file, 'w') as f:
        json.dump(j, f)
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


if __name__ == '__main__':
    lambda_handler()