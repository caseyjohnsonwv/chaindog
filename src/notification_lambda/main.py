import json
from os import getenv
from re import findall
import boto3
from boto3.dynamodb.conditions import Key
from dynamodb_json import json_util as djson


aws_region = getenv('aws_region') or 'us-east-2'
source_bucket = getenv('source_bucket') or 'wait-time-bucket-dev'
sns_topic_arn = getenv('sns_topic_arn') or 'arn:aws:sns:us-east-2:076218402253:sms_topic_dev'
watch_table_name = getenv('watch_table_name') or 'Watches_dev'
dynamodb_index_name = getenv('dynamodb_index_name') or 'search_by_park_id'


def lambda_handler(event=None, context=None):
    message = json.loads(event['Records'][0]['Sns']['Message'])
    s3_key = message['Records'][0]['s3']['object']['key']
    park_id = int(findall('\d+', s3_key)[0])

    # get active watches from watch table
    dynamodb = boto3.resource('dynamodb', region_name=aws_region)
    table = dynamodb.Table(watch_table_name)
    watches = table.query(
        IndexName=dynamodb_index_name,
        KeyConditionExpression=Key('park_id').eq(park_id),
    )['Items']
    ride_ids = ','.join([str(int(item['ride_id'])) for item in watches])
    print(f"{len(watches)} watches open for park_id = {park_id}")
    if len(watches) == 0:
        return

    # get wait times for rides actively being watched
    expression = f"select * from s3object[*].waits.lands[*].rides[*] as s where s.id in ({ride_ids})"
    print(expression)
    s3 = boto3.client('s3')
    r = s3.select_object_content(
            Bucket=source_bucket,
            Key=s3_key,
            ExpressionType='SQL',
            Expression=expression,
            InputSerialization={'JSON': {"Type": "Lines"}},
            OutputSerialization={'JSON': {}}
    )
    for item in r['Payload']:
        if 'Records' in item:
            records = item['Records']['Payload'].decode('utf-8')
            records = [json.loads(record) for record in records.strip().split('\n')]

    # use two pointer logic to publish watches on sns if their conditions have been met
    # both lists are sorted by default thanks to dynamodb range key
    sns = boto3.client('sns')
    closed_watches = 0
    w,r = 0,0
    while r < len(records):
        while w < len(watches) and watches[w]['ride_id'] == records[r]['id']:
            watch = djson.loads(watches[w])
            if int(records[r]['wait_time']) <= int(watch['wait_time_minutes']) and records[r]['is_open']:
                print(f"Closing {watch} ::: current = {records[r]['wait_time']}")
                msg = f"The line for {watch['ride_name']} is currently {records[r]['wait_time']} minutes!"
                data = {
                    'message' : msg,
                    'target_phone_number' : watch['phone_number'],
                }
                sns.publish(
                    TargetArn=sns_topic_arn,
                    Message=json.dumps(data),
                )
                table.delete_item(
                    Key={'watch_id':watch['watch_id']}
                )
                closed_watches += 1
            else:
                print(f"Skipping {watch} ::: current = {records[r]['wait_time']}")
            w += 1
        r += 1
    print(f"Closed {closed_watches} watches")