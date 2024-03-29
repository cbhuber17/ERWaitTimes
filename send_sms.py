"""Module for sending SMS messages through Twilio account."""

import os
from datetime import datetime, timedelta
from twilio.rest import Client


def send_sms(body, last_sms_time):
    """Sends an SMS using my twilio account.  Used for communicating if an exception happened in production.
    :param: body (str) The message contents of the SMS.
    :param: last_sms_time (datetime) The last time an SMS was sent.
    :return: now (datetime) Time of the SMS text. """

    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']

    now = datetime.now()

    if last_sms_time is None or (now - last_sms_time) > timedelta(days=1):

        try:
            client = Client(account_sid, auth_token)

            message = client.messages.create(
                body=body,
                from_=os.environ['MY_TWILIO_NUM'],
                to=os.environ['MY_PHONE_NUM']
            )

        except Exception as e:
            print(f"Exception happened in send_sms() attempting to send: {body}.")
            print(e)
    else:
        print(f"Only sending one SMS per day.  Error is: {body}.")

    return now


# -------------------------------------------------------------------------------------------------

def sms_exception_message(msg, e, last_sms_time):
    """Prints the exception to the screen and sends the message/exception details by SMS.
    :param: msg (str) A high-level description of the exception.
    :param: e (Exception) The trace stack error message.
    :param: last_sms_time (datetime) The last time an SMS was sent.
    :return: None"""

    print(msg)
    print(e)
    print(send_sms(msg + '\n' + str(e), last_sms_time))
