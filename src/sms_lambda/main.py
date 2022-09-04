from datetime import datetime
import json
from os import getenv
import phonenumbers as pn
from twilio.rest import Client


twilio_account_sid = getenv('twilio_account_sid')
twilio_auth_token = getenv('twilio_auth_token')
twilio_phone_number = getenv('twilio_phone_number')


def lambda_handler(event=None, context=None):
    for ev in event['Records']:
        data = json.loads(ev['Sns']['Message'])
        watch = data['watch']
        record = data['record']
        
        # create text message
        target_phone_number = watch['phone_number']
        expiration = datetime.fromisoformat(watch['expiration'])
        if expiration < datetime.now():
            msg = f"Your watch for {watch['ride_name']} has expired - the line did not get shorter than {watch['wait_time_minutes']} minutes!"
        else:
            msg = f"The line for {watch['ride_name']} is currently {record['wait_time']} minutes!"
        print(f"Message for {target_phone_number}: '{msg}'")

        # send text message
        client = Client(twilio_account_sid, twilio_auth_token)
        client.messages.create(
            body = msg,
            from_= pn.format_number(
                pn.parse(twilio_phone_number, "US"),
                pn.PhoneNumberFormat.E164
            ),
            to= pn.format_number(
                pn.parse(target_phone_number, "US"),
                pn.PhoneNumberFormat.E164
            ),
        )
