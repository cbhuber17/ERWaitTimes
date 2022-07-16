"""Module for sending SMS messages through Twilio account.
"""
import os
from twilio.rest import Client


def send_sms(body):
    """Sends an SMS using my twilio account.  Used for communicating if an exception happened in production.
    :param: body (str) The message contents of the SMS.
    :return: message.sid (str)"""

    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']

    try:
        client = Client(account_sid, auth_token)

        message = client.messages.create(
            body=body,
            from_=os.environ['MY_TWILIO_NUM'],
            to=os.environ['MY_PHONE_NUM']
        )

        print(message)
        return message.sid

    except Exception as e:
        print(f"Exception happened in send_sms() attempting to send: {body}.")
        print(e)
