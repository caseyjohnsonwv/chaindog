from datetime import datetime, timedelta
from os import getenv
from urllib.parse import unquote_plus
import uuid
import boto3
from boto3.dynamodb.conditions import Key, Attr
import phonenumbers as pn
import pytz
from twilio.twiml.messaging_response import MessagingResponse
from nlp_utils import detect_deletion_message, extract_park_name, extract_ride_name, extract_wait_time, NLPException
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
    body = reduce_to_ascii(payload['Body'])
    phone_number = pn.format_number(
        pn.parse(payload['From'], "US"),
        pn.PhoneNumberFormat.E164,
    )

    # grab any existing watches for this phone number
    dynamodb = boto3.resource('dynamodb', region_name=aws_region)
    table = dynamodb.Table(watch_table_name)
    watches = table.query(
        IndexName=dynamodb_index_name,
        KeyConditionExpression=Key('phone_number').eq(phone_number),
    )['Items']

    # DELETE logic
    if detect_deletion_message(body):
        # extract ride name from all possible watches
        possible_names = {w['ride_name'] : i for i,w in enumerate(watches)}
        try:
            ride_name = extract_ride_name(body, list(possible_names.keys()))
            watch = watches[possible_names[ride_name]]
        except (IndexError, KeyError, NLPException):
            msg = f"Whoops, we couldn't find an open watch for that ride! If this is a mistake, try rephrasing your message."
            return create_response(msg)

        # delete the watch if it exists
        print(f"Deleting ::: {watch}")
        msg = f"Got it! We are no longer watching the line on {watch['ride_name']}."
        table.delete_item(
            Key={'watch_id':watch['watch_id']}
        )
        return create_response(msg)

    # get park data
    user_current_park = None
    if len(watches) > 0:
        # look up full park record from one of the open watches
        user_current_park = watches[0]['park_name']
        park_name_sanitized = user_current_park.replace("'", "''")
        expression = f"select * from s3object[*][*].parks[*] as s where s.name = '{park_name_sanitized}'"
        park_record = query_s3(expression, 'parks.json', source_bucket)[0]
    else:
        # otherwise deduce park_name and park_id from message
        expression = f"select * from s3object[*][*].parks[*] as s"
        results = query_s3(expression, 'parks.json', source_bucket)
        try:
            park_name = extract_park_name(body, [r['name'] for r in results])
        except NLPException:
            msg = f"Whoops, we couldn't figure out what park you're asking about! Try rephrasing your message."
            return create_response(msg)
        for r in results:
            if r['name'] == park_name:
                park_record = r
                break
    s3_key = f"wait-times/{park_record['id']}.json"
    print(f"{park_record['name']} ::: {s3_key}")

    # ensure current request is for same park as existing watches
    if user_current_park and user_current_park != park_record['name']:
        print(f"ISSUE: Requested watch for {park_record['name']}, but user is at {watches[0]['park_name']}")
        msg = f"Our records show that you are watching rides at {watches[0]['park_name']}! Please cancel those watches before requesting rides at another park."
        return create_response(msg)

    # extract ride_name from message
    expression = f"select s.name from s3object[*].waits.lands[*].rides[*] as s"
    results = query_s3(expression, s3_key, source_bucket)
    ride_name = extract_ride_name(body, [r['name'] for r in results])

    # query full record for just this one ride
    ride_name_sanitized = ride_name.replace("'", "''").lower()
    expression = f"select * from s3object[*].waits.lands[*].rides[*] as s where lower(s.name) = '{ride_name_sanitized}' limit 1"
    ride_record = query_s3(expression, s3_key, source_bucket)[0]
    print(f"{ride_name} ::: wait_time = {ride_record['wait_time']} (is_open = {ride_record['is_open']})")
    
    # filter watches down to just thie requested ride
    watches = [w for w in watches if w['ride_name'] == ride_name]
    watch = watches[0] if len(watches) > 0 else None

    # set up timezones / datetimes
    utc = pytz.timezone('UTC')
    tz = pytz.timezone(park_record['timezone'])
    expiration = datetime.now().astimezone(utc) + timedelta(seconds=watch_expiration_window_seconds)
    expiration_readable = expiration.astimezone(tz).strftime('%-I:%M')
    target_wait_time = int(extract_wait_time(body))

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
            msg = f"Our data shows that {ride_record['name']} at {park_record['name']} is currently closed - try again later!"
        return create_response(msg)

    # ensure line is long enough to warrant a watch
    elif ride_record['wait_time'] <= target_wait_time:
        print(f"ISSUE: line already short enough")
        msg = f"The line for {ride_record['name']} at {park_record['name']} is currently {ride_record['wait_time']} minutes!"
        # if user has a watch open, tell them and keep watching
        if watch:
            user_exp = datetime.fromisoformat(watch['expiration']).astimezone(tz).strftime('%-I:%M')
            msg = ' '.join([msg, f"We'll keep watching for a wait under {watch['wait_time_minutes']} minutes until {user_exp}."])
        return create_response(msg)

    # if watch exists, update it with new wait time
    if watch:
        # vary message if times are the same
        if watch['wait_time_minutes'] == target_wait_time:
            print(f"Duplicate watch request from user ::: {watch}")
            msg = f"You're already watching {ride_record['name']} for a line shorter than {watch['wait_time_minutes']} minutes! Currently {ride_record['wait_time']} min. We'll extend your watch until {expiration_readable}."
        else:
            msg = f"Updated your {ride_record['name']} watch to {target_wait_time} minutes and extended until {expiration_readable}! Currently {ride_record['wait_time']} min."
        # extend watch and update target time if needed
        table.update_item(
            Key = {
                'watch_id' : watch['watch_id']
            },
            UpdateExpression = 'SET wait_time_minutes = :wt_min, expiration = :exp_ts',
            ExpressionAttributeValues = {
                ':wt_min' : target_wait_time,
                ':exp_ts' : expiration.isoformat()
            }
        )
        print(f"Updated watch {watch['watch_id']} in Dynamo")
        return create_response(msg)

    # else, create a new one
    else:
        watch = {
            'watch_id' : str(uuid.uuid4()),
            'park_id' : park_record['id'],
            'park_name' : park_record['name'],
            'ride_id' : ride_record['id'],
            'ride_name' : ride_record['name'],
            'wait_time_minutes' : target_wait_time,
            'phone_number' : phone_number,
            'expiration' : expiration.isoformat()
        }
        table.put_item(Item=watch)
        print(f"Created watch in Dynamo: {watch}")
        msg = f"Now watching {ride_record['name']} at {park_record['name']} until {expiration_readable} for a line shorter than {target_wait_time} minutes! Currently {ride_record['wait_time']} min. Powered by https://queue-times.com/parks/{park_record['id']}."
        return create_response(msg)
    
