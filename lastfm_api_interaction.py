import requests
import requests_async

BASE_URL = 'https://ws.audioscrobbler.com/2.0/'
API_KEY = 'ad4d0de2cdf0e6dd6cf56fc18a34a251'
API_SECRET = '6828afef9f2a0169a1b4654d323c5ecc'


# after migration to Quart
# async def is_artist_playing_genres_async(genres, artist, strict=False):
#     toptags = (await requests_async.get(BASE_URL,
#                                         params={'format': 'json',
#                                                 'method': 'artist.getTopTags',
#                                                 'artist': artist,
#                                                 'autocorrect': int(not strict),
#                                                 'api_key': API_KEY})).json()
#     if 'toptags' in toptags.keys():
#         return genres in [i['name'] for i in toptags['toptags']['tag']]
#     else:
#         return strict


def is_artist_playing_genres(genres, artist, strict=False):
    toptags = requests.get(BASE_URL,
                           params={'format': 'json',
                                   'method': 'artist.getTopTags',
                                   'artist': artist,
                                   'autocorrect': int(not strict),
                                   'api_key': API_KEY}).json()
    if 'toptags' in toptags.keys():
        tagnames = [i['name'] for i in toptags['toptags']['tag']]
        for g in genres.split(','):
            if g in tagnames:
                return True
        return False
    else:
        return strict
