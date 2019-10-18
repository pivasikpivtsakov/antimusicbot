import asyncio
import threading
from ast import literal_eval
from time import sleep

import MySQLdb

import lastfm_api_interaction
import message_handling
import peer_utils
import vk_api_interaction
from commands import commands_dict
from program_strings import response_genre_found, response_genre_not_found, error_audio_access_denied, \
    error_audio_unknown


async def main():
    print('task started')
    conn = MySQLdb.connect(host='futurebass.mysql.pythonanywhere-services.com', user='futurebass',
                           password='pivotrulez1234567891011121315', database='futurebass$peer_ids',
                           use_unicode=True, charset='utf8')
    vk_audio = vk_api_interaction.VKAudio()
    while True:
        cursor = conn.cursor()
        try:  # is connection opened; if no, open it
            cursor.execute("""SELECT MIN(id) FROM operations_queue;""")
            conn.commit()
        except MySQLdb.InterfaceError as e:
            conn = MySQLdb.connect(host='futurebass.mysql.pythonanywhere-services.com', user='futurebass',
                                   password='pivotrulez1234567891011121315', database='futurebass$peer_ids',
                                   use_unicode=True, charset='utf8')
            print(e, flush=True)
            sleep(0.1)
            continue
        min_id = cursor.fetchone()[0]
        if min_id is None:  # db is empty
            sleep(0.1)
            continue
        cursor.execute("""SELECT data_object
                            FROM operations_queue
                            WHERE id=%s;""", (min_id,))
        conn.commit()
        data_object = literal_eval(cursor.fetchone()[0])
        print(data_object, flush=True)
        cursor.execute("""DELETE 
                              FROM operations_queue
                              WHERE id=%s;""", (min_id,))
        conn.commit()

        # bot job here
        peer_id: int = data_object['peer_id']
        from_id: int = data_object['from_id']
        parsed_message = vk_api_interaction.parse_message(data_object['text'])
        if vk_api_interaction.is_private_message(peer_id, from_id):

            if parsed_message.command == commands_dict['findshit']:
                def finder():
                    try:
                        audios = vk_audio.get(owner_id=from_id)
                    except vk_api_interaction.VKAudioAccessDeniedError:
                        vk_api_interaction.send_message_id(peer_id, error_audio_access_denied)
                        return
                    except vk_api_interaction.VKAudioError:
                        vk_api_interaction.send_message_id(peer_id, error_audio_unknown)
                        return
                    genre_artists = []
                    for i in audios['items']:
                        if lastfm_api_interaction.is_artist_playing_genres(peer_utils.peer_storage[peer_id]
                                                                           ['forbidden_genres'], i['artist']):
                            genre_artists.append(i['artist'])
                    vk_api_interaction.send_message_id(peer_id, 'идеологически неправильные аудиозаписи: ' +
                                                       ', '.join(set(genre_artists)))

                finder_thread = threading.Thread(target=finder)
                finder_thread.start()

            else:
                def checker():
                    message_audios = vk_api_interaction.get_message_audios(data_object)
                    bad_audios = message_handling.check_audios(peer_utils.peer_storage[peer_id]['forbidden_genres'],
                                                               message_audios)
                    has_audios = bool(message_audios)
                    if bad_audios:
                        vk_api_interaction.send_message_id(peer_id, response_genre_found + ': ' + ', '.join(
                            [i['artist'] for i in bad_audios]))
                    elif has_audios:
                        vk_api_interaction.send_message_id(peer_id, response_genre_not_found)

                checker_thread = threading.Thread(target=checker)
                checker_thread.start()

        else:
            pass

        sleep(0.1)


if __name__ == '__main__':
    asyncio.run(main())
