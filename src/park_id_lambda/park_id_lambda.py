import json
from os import getenv
import boto3
import requests


queue_url = getenv('queue_url')
parks_url = 'https://queue-times.com/parks.json'


def lambda_handler(event=None, context=None):
    j = requests.get(parks_url).json()
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