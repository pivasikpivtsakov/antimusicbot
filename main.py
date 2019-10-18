from flask import Flask, json, request

import firebase_functions
import message_handling
from program_strings import secret, confirmation

app = Flask(__name__)


@app.route('/vkCallback', methods=['POST'])
def processing():
    # parse json from post-request
    data = dict(json.loads(request.data))
    # for logging purposes
    print(str(request.data, encoding='utf-8'))
    try:
        # bind server to vk group
        if data['type'] == 'confirmation':
            return confirmation
        # validate request
        if data['secret'] != secret:
            return 'not vk'
        # callback api
        if data['type'] == 'message_new' or data['type'] == 'message_edit':
            message_handling.handle_messages(data)
            return 'ok'
    except KeyError:
        return 'not vk'


@app.route('/receiveNotificationSubscriberToken', methods=['POST'])
def push_token_to_list():
    return firebase_functions.push_new_token(request)


@app.route('/lastfmAuth', methods=['POST'])
def lastfm_auth():
    pass


if __name__ == '__main__':
    app.run()
