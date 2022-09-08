import json
from os import getenv
import phonenumbers as pn
from twilio.rest import Client


twilio_account_sid = getenv('twilio_account_sid')
twilio_auth_token = getenv('twilio_auth_token')
twilio_phone_number = getenv('twilio_phone_number')


def lambda_handler(event=None, context=None):
    data = json.loads(event['Records'][0]['Sns']['Message'])
    
    msg = data['message']
    target_phone_number = data['target_phone_number']
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
