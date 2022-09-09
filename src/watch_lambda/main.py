from datetime import datetime, timedelta
from os import getenv
from urllib.parse import unquote_plus
import uuid
import boto3
from boto3.dynamodb.conditions import Key, Attr
import phonenumbers as pn
import pytz
from twilio.twiml.messaging_response import MessagingResponse
from s3_select_wrapper import query_s3, reduce_to_ascii


aws_region = getenv('aws_region')
source_bucket = getenv('source_bucket')
watch_table_name = getenv('watch_table_name')
dynamodb_index_name = getenv('dynamodb_index_name')
watch_expiration_window_seconds = int(getenv('watch_expiration_window_seconds'))


def create_response(message):
    response = MessagingResponse()
    response.message(message)
    xml = response.to_xml()
    print(xml)
    return xml


def lambda_handler(event=None, context=None):
    payload = {k:unquote_plus(v) for k,v in event.items()}
    # TODO: currently assuming "park \n ride \n wait time" - use NLP instead
    body = reduce_to_ascii(payload['Body'])
    park_name, ride_name, target_wait_time = [n.strip() for n in body.split('\n')]
    target_wait_time = int(target_wait_time)
    phone_number = pn.format_number(
        pn.parse(payload['From'], "US"),
        pn.PhoneNumberFormat.E164,
    )

    # use park name to get park id [s3 select]
    park_name_sanitized = park_name.replace("'","''").lower()
    expression = f"select * from s3object[*][*].parks[*] as s where lower(s.name) = '{park_name_sanitized}' limit 1"
    park_record = query_s3(expression, 'parks.json', source_bucket)[0]
    print(f"{park_name} ::: park_id = {park_record['id']}")

    # use park id to query wait time by ride name [s3 select]
    ride_name_sanitized = ride_name.replace("'", "''").lower()
    expression = f"select * from s3object[*].waits.lands[*].rides[*] as s where lower(s.name) = '{ride_name_sanitized}' limit 1"
    s3_key = f"wait-times/{park_record['id']}.json"
    ride_record = query_s3(expression, s3_key, source_bucket)[0]
    print(f"{ride_name} ::: wait_time = {ride_record['wait_time']} (is_open = {ride_record['is_open']})")
    
    # grab any existing watches for this ride/phone combination
    dynamodb = boto3.resource('dynamodb', region_name=aws_region)
    table = dynamodb.Table(watch_table_name)
    watches = table.query(
        IndexName=dynamodb_index_name,
        KeyConditionExpression=Key('phone_number').eq(phone_number),
        FilterExpression=Attr('ride_id').eq(ride_record['id']),
        Limit=1,
    )['Items']

    # set up timezones / datetimes
    utc = pytz.timezone('UTC')
    tz = pytz.timezone(park_record['timezone'])
    expiration = datetime.now().astimezone(utc) + timedelta(seconds=watch_expiration_window_seconds)
    expiration_readable = expiration.astimezone(tz).strftime('%-I:%M')
    
    # ensure ride is open
    if not ride_record['is_open']:
        expression = f"select count(s.rides) as num_open_rides from s3object[*].waits.lands[*] as s where True in s.rides[*].is_open"
        res = query_s3(expression, s3_key, source_bucket)
        # tell user the park is closed
        if res[0]['num_open_rides'] == 0:
            print(f"ISSUE: {park_record['name']} is closed")
            msg = f"Our data shows that {park_record['name']} is currently closed!"
        # tell user the ride is closed
        else:
            print(f"ISSUE: {ride_record['name']} is closed")
            msg = f"Our data shows that {ride_record['name']} is currently closed - try again later!"
        return create_response(msg)

    # ensure line is long enough to warrant a watch
    elif ride_record['wait_time'] <= target_wait_time:
        print(f"ISSUE: line already short enough")
        msg = f"The line for {ride_record['name']} is currently {ride_record['wait_time']} minutes!"
        # if user has a watch open, tell them and keep watching
        if len(watches) > 0:
            user_exp = datetime.fromisoformat(watches[0]['expiration']).astimezone(tz).strftime('%-I:%M')
            msg = ' '.join([msg, f"We'll keep watching for a wait under {watches[0]['wait_time_minutes']} minutes until {user_exp}."])
        return create_response(msg)

    # if watch exists, update it with new wait time
    if len(watches) == 1:
        data = watches[0]
        # vary message if times are the same
        if data['wait_time_minutes'] == target_wait_time:
            print(f"Duplicate watch request from user ::: {data}")
            msg = f"You're already watching {ride_record['name']} for a line shorter than {data['wait_time_minutes']} minutes! Currently {ride_record['wait_time']} min. We'll extend your watch until {expiration_readable}."
        else:
            msg = f"Updated your {ride_record['name']} watch to {target_wait_time} minutes and extended until {expiration_readable}! Currently {ride_record['wait_time']} min."
        # extend watch and update target time if needed
        table.update_item(
            Key = {
                'watch_id' : data['watch_id']
            },
            UpdateExpression = 'SET wait_time_minutes = :wt_min, expiration = :exp_ts',
            ExpressionAttributeValues = {
                ':wt_min' : target_wait_time,
                ':exp_ts' : expiration.isoformat()
            }
        )
        print(f"Updated watch {data['watch_id']} in Dynamo")
        return create_response(msg)

    # else, create a new one
    elif len(watches) == 0:
        data = {
            'watch_id' : str(uuid.uuid4()),
            'park_id' : park_record['id'],
            'park_name' : park_record['name'],
            'ride_id' : ride_record['id'],
            'ride_name' : ride_record['name'],
            'wait_time_minutes' : target_wait_time,
            'phone_number' : phone_number,
            'expiration' : expiration.isoformat()
        }
        table.put_item(Item=data)
        print(f"Created watch in Dynamo: {data}")
        msg = f"Now watching {ride_record['name']} until {expiration_readable} for a queue time of {target_wait_time} minutes or less! Currently {ride_record['wait_time']} min. Powered by https://queue-times.com/parks/{park_record['id']}."
        return create_response(msg)
    
    # else, this should not happen ??? catch this error and do nothing to database
    else:
        print(f"ISSUE: Multiple watches open --> {watches}")
