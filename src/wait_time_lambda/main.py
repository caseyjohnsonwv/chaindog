import json
from os import getenv, remove
import boto3
import requests


destination_bucket = getenv('destination_bucket')
base_url = 'https://queue-times.com/parks'


def lambda_handler(event=None, context=None):
    for record in event['Records']:
        park = json.loads(record['body'])
        park_id = park['id']
        key = f"{park_id}.json"
        local_file = f"/tmp/{key}"
        print(f"Fetching {park['name']}")

        url = f"{base_url}/{park_id}/queue_times.json"
        j = requests.get(url).json()
        data = [park, j]
        with open(local_file, 'w') as f:
            json.dump(data, f)

        s3 = boto3.resource('s3')
        s3.meta.client.upload_file(local_file, destination_bucket, key)
        remove(local_file)
        print(f"Fetched and uploaded {park['name']}")


if __name__ == '__main__':
    lambda_handler()