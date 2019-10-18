import firebase_admin
from firebase_admin import messaging
from flask import json
from google.auth import exceptions

import program_strings

try:
    firebase_app = firebase_admin.initialize_app()
    scheme = open('/home/futurebass/mysite/device_tokens.json')
    json_obj = dict(json.load(scheme))
    scheme.close()
    device_tokens = set(json_obj['tokens'])
except exceptions.DefaultCredentialsError:
    print('Default Credentials Error; maybe loaded once more')


def store_tokens():
    lscheme = open('/home/futurebass/mysite/device_tokens.json', 'r')
    json_obj = json.load(lscheme)
    lscheme.close()
    json_obj['tokens'] = list(device_tokens)
    lscheme = open('/home/futurebass/mysite/device_tokens.json', 'w')
    json.dump(json_obj, lscheme)
    lscheme.close()


def send_firebase_notification_to_devices(title: str, body: str, data=None):
    print(firebase_app.credential.get_access_token().access_token)
    inactive_tokens = set()
    for token in device_tokens:
        message = messaging.Message(
            token=token, notification=messaging.Notification(title, body),
            android=messaging.AndroidConfig(data=dict({'click_action': 'FLUTTER_NOTIFICATION_CLICK'}, **data)))
        try:
            response = messaging.send(message)
            print('Message Sent, Response: ' + response)
        except messaging.ApiCallError as e:
            print('inactive token: ', token)
            inactive_tokens.add(token)
    device_tokens.difference_update(inactive_tokens)
    store_tokens()


def push_new_token(request):
    data = dict(json.loads(request.data))
    print(data)
    if 'secret' not in data.keys() or data['secret'] != program_strings.secret:
        return 'not a beercupnotifications app'
    # TODO: scheduled task
    device_tokens.add(data['token'])
    store_tokens()
    return 'ok'
