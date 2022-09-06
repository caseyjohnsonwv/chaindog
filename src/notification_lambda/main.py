from datetime import datetime, timedelta
import json
from os import getenv
from re import findall
import boto3
from boto3.dynamodb.conditions import Key
from dynamodb_json import json_util as djson
import pytz


aws_region = getenv('aws_region')
source_bucket = getenv('source_bucket')
sns_topic_arn = getenv('sns_topic_arn')
watch_table_name = getenv('watch_table_name')
dynamodb_index_name = getenv('dynamodb_index_name')
watch_extension_window_seconds = int(getenv('watch_extension_window_seconds'))


def push_sms(message, phone_number):
    sns = boto3.client('sns')
    data = {
        'message' : message,
        'target_phone_number' : phone_number,
    }
    sns.publish(
        TargetArn=sns_topic_arn,
        Message=json.dumps(data),
    )


def query_s3(expression:str, s3_key:str) -> list:
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
    records = []
    for item in r['Payload']:
        if 'Records' in item:
            records = item['Records']['Payload'].decode('utf-8')
            records = [json.loads(record) for record in records.strip().split('\n')]
    return records


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

    # determine if park is still open - assume closed if all coasters are closed
    expression = f"select count(s.rides) as num_open_rides from s3object[*].waits.lands[*] as s where s.name = 'Coasters' and True in s.rides[*].is_open"
    res = query_s3(expression, s3_key)
    
    # if park is closed, expire all alerts for this park
    if res[0]['num_open_rides'] == 0:
        print('Closing all watches ::: park is closed')
        for watch in watches:
            msg = f"It looks like {watch['park_name']} is closed now! We're closing your open watch for {watch['ride_name']}. The line did not get shorter than {watch['wait_time_minutes']} minutes."
            table.delete_item(
                Key={'watch_id':watch['watch_id']}
            )
            push_sms(msg, watch['phone_number'])
        return

    # if park is still open, get wait times for rides actively being watched
    expression = f"select * from s3object[*].waits.lands[*].rides[*] as s where s.id in ({ride_ids})"
    records = query_s3(expression, s3_key)

    # set up timestamps to extend watches if needed
    expression = f"select s.timezone as tz from s3object[*].park as s"
    res = query_s3(expression, s3_key)
    tz = pytz.timezone(res[0]['tz'])
    utc = pytz.timezone('UTC')
    now_utc = datetime.now().astimezone(utc)
    expiration_soon = now_utc + timedelta(minutes=5)
    new_expiration = now_utc + timedelta(seconds=watch_extension_window_seconds)
    new_expiration_readable = new_expiration.astimezone(tz).strftime('%-I:%M')
    
    # use two pointer logic to publish watches on sns if their conditions have been met
    # both lists are sorted by default thanks to dynamodb range key
    w,r = 0,0
    while r < len(records):
        while w < len(watches) and watches[w]['ride_id'] == records[r]['id']:
            watch = djson.loads(watches[w])
            expiration = datetime.fromisoformat(watch['expiration']).astimezone(utc)

            # condition for a watch to be extended
            # ie, ride is closed and watch is about to expire
            if not records[r]['is_open'] and expiration <= expiration_soon:
                print(f"Extending {watch} ::: {watch['ride_name']} is closed")
                msg = f"It looks like {watch['ride_name']} is closed right now! We've extended your watch for a line shorter than {watch['wait_time_minutes']} minutes until {new_expiration_readable}."
                table.update_item(
                    Key = {
                        'watch_id' : watch['watch_id']
                    },
                    UpdateExpression = 'SET expiration = :exp_ts',
                    ExpressionAttributeValues = {
                        ':exp_ts' : new_expiration.isoformat()
                    }
                )
                push_sms(msg, watch['phone_number'])

            
            # condition for a watch to be expired
            # ie, expiration has passed
            elif expiration <= now_utc:
                print(f"Expiring {watch} ::: expiration timestamp has passed")
                msg = f"Your watch for {watch['ride_name']} has expired! The line did not get shorter than {watch['wait_time_minutes']} minutes."
                table.delete_item(
                    Key={'watch_id':watch['watch_id']}
                )
                push_sms(msg, watch['phone_number'])


            # condition for a watch to be closed
            # ie, line is short enough
            elif int(records[r]['wait_time']) <= int(watch['wait_time_minutes']):
                print(f"Closing {watch} ::: current = {records[r]['wait_time']}")
                msg = f"The line for {watch['ride_name']} is currently {records[r]['wait_time']} minutes!"
                table.delete_item(
                    Key={'watch_id':watch['watch_id']}
                )
                push_sms(msg, watch['phone_number'])

            # no conditions met
            else:
                print(f"Skipping {watch} ::: current = {records[r]['wait_time']}")
            w += 1
        r += 1
