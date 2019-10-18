import random

import requests
import vk_api

from commands import commands_dict
from program_strings import group_token, ment_str, club_id, public_id, num_id, kate_user_agent, vk_api_base_address, \
    kate_token, error_not_admin, error_trying_to_kick_admin, group_name

session = vk_api.VkApi(token=group_token)
api = session.get_api()


class OptionalString:
    pass


class BotArgumentsError(Exception):
    def __init__(self, arg=''):
        self.arg = arg

    def __repr__(self):
        return 'Wrong argument ' + self.arg


class ParsedMessage:
    def __init__(self, command: str, params: str):
        self.command = command
        self.params = params

    def params_as_list(self, types: list, many=False):
        param_list = self.params.split(' ')
        if many:
            types *= len(param_list)
        if not (len(param_list) <= len(types) <= len(param_list) + types.count(OptionalString)):
            raise BotArgumentsError(param_list[-1])
        parsed_params_list = []
        for i in range(len(types)):
            if types[i] == int:
                if param_list[i].isdigit():
                    parsed_params_list.append(int(param_list[i]))
                else:
                    raise BotArgumentsError(param_list[i])
            elif types[i] == str:
                parsed_params_list.append(param_list[i])
            elif types[i] == OptionalString:
                if i < len(param_list):
                    parsed_params_list.append(param_list[i])
        return parsed_params_list


def parse_message(message, cmd_dict=None) -> ParsedMessage:
    message = remove_bot_mention(message.lower().strip(' '))
    if cmd_dict is None:
        cmd_dict = commands_dict
    for i in cmd_dict.values():
        if message.startswith(i):
            return ParsedMessage(i, message[len(i) + 1:] if len(i) + 1 < len(message) else '')
    return ParsedMessage('', '')


def send_message_id(peer_id, message, attachment='', reply_to=0):
    api.messages.send(peer_id=peer_id, message=message,
                      random_id=random.randint(-2 ** 31, 2 ** 32 - 1), attachment=attachment, reply_to=reply_to)


class AwaitableVKMessageSender:
    def __init__(self, peer_id, message, attachment='', reply_to=0):
        self.peer_id = peer_id
        self.message = message
        self.attachment = attachment
        self.reply_to = reply_to

    def __await__(self):
        api.messages.send(peer_id=self.peer_id, message=self.message,
                          random_id=random.randint(-2 ** 31, 2 ** 32 - 1), attachment=self.attachment,
                          reply_to=self.reply_to)
        return (yield)


async def send_message_id_async(peer_id, message, attachment='', reply_to=0):
    await AwaitableVKMessageSender(peer_id, message, attachment, reply_to)


class MentionError(Exception):
    """Specially to use in mention function"""

    def __init__(self, single_id=''):
        self.single_id = single_id

    def __str__(self):
        return 'IDs are incorrect'


def mention(screen_name='', first_name='', last_name='', name_case='nom', screen_names=None):
    if screen_names:
        res = ''
        try:
            users = api.users.get(user_ids=','.join(
                screen_names), fields='screen_name', name_case=name_case)
            for i in range(len(users)):

                if 'deactivated' in dict(users[i]).keys():
                    continue

                def _format_ment_str():
                    # do not use screen_names[i] because not all of them are valid
                    return ment_str % (users[i]['screen_name'], users[i]['first_name'] + ' ' + users[i]['last_name'])

                if i == len(users) - 1 and len(users) > 1:
                    res += 'и ' + _format_ment_str()
                elif i == len(users) - 2 or len(users) == 1:
                    res += _format_ment_str() + ' '
                else:
                    res += _format_ment_str() + ', '
        except vk_api.ApiError as e:
            if e.code == 113:
                for i in range(len(screen_names)):
                    if i == len(screen_names) - 1:
                        res += 'и ' + mention(screen_names[i])
                    elif i == len(screen_names) - 2:
                        res += mention(screen_names[i]) + ' '
                    else:
                        res += mention(screen_names[i]) + ', '
        if res:
            return res
        else:
            raise MentionError()
    elif first_name != '' and last_name != '':
        return ment_str % (screen_name, first_name + ' ' + last_name)
    elif first_name != '' and last_name == '':
        return ment_str % (screen_name, first_name)
    elif first_name == '' and last_name == '':
        try:
            user = api.users.get(user_ids=screen_name,
                                 fields='', name_case=name_case)[0]
            return ment_str % (screen_name, user['first_name'] + ' ' + user['last_name'])
        except vk_api.ApiError as e:
            if e.code == 113:
                user = api.groups.getById(group_id=screen_name)[0]
                if user['name'] == group_name:
                    raise MentionError(screen_name)
                return ment_str % (screen_name, user['name'])


def remove_bot_mention(s: str):
    return s.replace(ment_str % (club_id, '@' + club_id) + ' ', '', 1) \
        .replace(ment_str % (club_id, '@' + public_id), '', 1) \
        .replace(ment_str % (public_id, '@' + public_id), '', 1)


def get_mentioned_id(string: str) -> str:
    # forms:
    # [screen_name|text]
    # idid
    # id
    if string.startswith('['):
        return string.replace('[', '').split('|')[0]
    elif not string.startswith('id') and string.isnumeric():
        return 'id' + string
    else:
        return string


def is_private_message(peer_id, from_id):
    return peer_id == from_id


def get_top_level_audios(data_object: dict) -> list:
    return [i['audio'] for i in data_object['attachments'] if i['type'] == 'audio']


def get_message_audios(message: dict) -> list:
    """
    walks through vk message object,
    collects audios from attachments and
    does this for all nested fwd_messages and reply_message
    """
    res = get_top_level_audios(message)
    # vk does not support nested replies, but has nested forwarded messages
    if 'reply_message' in message.keys():
        res.extend(get_message_audios(message['reply_message']))
    # handle fwd_messages
    if 'fwd_messages' in message.keys():
        for msg in message['fwd_messages']:
            res.extend(get_message_audios(msg))
    return res


def invited_self(member_id):
    return member_id == -num_id


def remove_chat_user_with_default_error_handler(peer_id: int, member_id: int):
    try:
        api.messages.removeChatUser(chat_id=peer_id - 2000000000, member_id=member_id)
    except vk_api.ApiError as e:
        if e.code == 925:
            send_message_id(peer_id, error_not_admin)
        elif e.code == 15:
            send_message_id(peer_id, error_trying_to_kick_admin)


class VKAudioError(Exception):
    def __init__(self, scheme=''):
        self.scheme = scheme

    def __str__(self):
        return self.scheme


class VKAudioAccessDeniedError(VKAudioError):
    """
    Error 201
    https://vk.com/dev.php?method=errors
    """

    def __str__(self):
        return 'Access to users audio is denied'


class VKAudio:
    """
    Provides access to Audio API
    https://web.archive.org/web/20161216125506/https://vk.com/dev/audio.get
    """

    def __init__(self):
        self.audio_session = requests.session()
        self.audio_session.headers = {'User-Agent': kate_user_agent}

    def get(self, owner_id: int = None, album_id: int = None, audio_ids: list = None, need_user: bool = None,
            offset: int = None, count: int = None) -> dict:
        params = {'access_token': kate_token, 'v': '5.101',
                  'owner_id': owner_id,
                  'audio_ids': ','.join(audio_ids) if audio_ids is not None else None,
                  'album_id': album_id,
                  'need_user': need_user,
                  'offset': offset,
                  'count': count}
        response = self.audio_session.get(vk_api_base_address + 'audio.get',
                                          params=params)
        j = response.json()
        if 'response' in j.keys():
            return j['response']
        else:
            if 'error' in j.keys():
                if j['error']['error_code'] == 201:
                    raise VKAudioAccessDeniedError()
            raise VKAudioError(str(j))
            # to be continued...
