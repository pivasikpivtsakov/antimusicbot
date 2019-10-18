import calendar
import sys
import time
import traceback

import firebase_functions
import lastfm_api_interaction
import operations_queue_db_utils
import peer_utils
import vk_api_interaction
from commands import commands_dict, setting_names
from program_strings import error_general_title, error_general, greeting, response_genre_found, \
    response_genre_not_found, start_find_shit, response_listener_found, settings_start, settings_genres_set_to


class DoubleRequestError(Exception):
    def __init__(self, request: str):
        self.request_str = request

    def __repr__(self):
        return 'Request was sent second time:\n{0}' % self.request_str


def handle_messages(data: dict):
    data_object = data['object']
    try:
        if 'action' in data['object'].keys():
            handle_action_message(data['object'])
        else:
            if data['object']['date'] + 4 < calendar.timegm(time.gmtime()):
                raise DoubleRequestError(str(data))
            handle_content_message(data['object'])

    except DoubleRequestError as dre:
        print(dre)
    except Exception as e:
        firebase_functions.send_firebase_notification_to_devices(error_general_title, str(e),
                                                                 {'peer_id': str(data_object['peer_id']),
                                                                  'from_id': 'id' + str(
                                                                      data_object['from_id'])})
        vk_api_interaction.send_message_id(data_object['peer_id'], error_general)
        print(traceback.format_exc(), file=sys.stderr)


def handle_action_message(data_object):
    action = data_object['action']  # action {type, <member_id>, <text>, ...}
    peer_id: int = data_object['peer_id']
    action_type = action['type']
    if action_type == 'chat_invite_user':
        member_id = action['member_id']
        if vk_api_interaction.invited_self(member_id):
            vk_api_interaction.send_message_id(peer_id, greeting)
            peer_utils.peer_storage.insert_peer(peer_id)


def check_audios(genre: str, message_audios: list) -> list:
    of_selected_genre = []
    for audio in message_audios:
        if 'main_artists' in audio.keys():
            artists = [i['name'] for i in audio['main_artists']]
        else:
            artists = list()
            artists.append(audio['artist'])
        for artist in artists:
            if lastfm_api_interaction.is_artist_playing_genres(genre, artist):
                of_selected_genre.append(audio)
                break
    return of_selected_genre


def handle_content_message(data_object):
    peer_id: int = data_object['peer_id']
    from_id: int = data_object['from_id']
    parsed_message = vk_api_interaction.parse_message(data_object['text'])
    # common commands

    if parsed_message.command == commands_dict['setup']:
        try:
            first_space_index = parsed_message.params.index(' ')
        except ValueError:
            vk_api_interaction.send_message_id(peer_id, settings_start)
            return
        if first_space_index + 1 == len(parsed_message.params) - 1:
            vk_api_interaction.send_message_id(peer_id, settings_start)
        else:
            setting_name = parsed_message.params[:first_space_index]
            setting_values = parsed_message.params[first_space_index + 1:len(parsed_message.params)]
            if setting_name == setting_names['genres']:
                peer_utils.peer_storage.edit_peer(peer_id, setting_values)
                vk_api_interaction.send_message_id(peer_id, settings_genres_set_to % setting_values)
        # TODO: keyboard

    if vk_api_interaction.is_private_message(peer_id, from_id):
        if parsed_message.command == commands_dict['findshit']:
            vk_api_interaction.send_message_id(peer_id, start_find_shit)
            operations_queue_db_utils.put_info_for_peer(data_object)

        else:
            message_audios = vk_api_interaction.get_message_audios(data_object)
            if len(message_audios) > 5:
                operations_queue_db_utils.put_info_for_peer(data_object)
            else:
                has_audios = bool(message_audios)
                bad_audios = check_audios(peer_utils.peer_storage[peer_id]['forbidden_genres'], message_audios)
                if bad_audios:
                    vk_api_interaction.send_message_id(peer_id, response_genre_found + ': ' + ', '.join(
                        [i['artist'] for i in bad_audios]))
                elif has_audios:
                    vk_api_interaction.send_message_id(peer_id, response_genre_not_found)

    else:  # conversation
        message_audios = vk_api_interaction.get_message_audios(data_object)
        if check_audios(peer_utils.peer_storage[peer_id]['forbidden_genres'], message_audios):
            vk_api_interaction.send_message_id(peer_id, response_listener_found % vk_api_interaction.mention(
                'id' + str(from_id)))
            vk_api_interaction.remove_chat_user_with_default_error_handler(peer_id, from_id)
