import os
from urllib.parse import (
    quote_plus,
)

import httpx

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'radio2playlist.settings')
    import django
    django.setup()


from radio2playlist.models import (
    Artist,
    Playlist,
    PlaylistItem,
    Show,
    Station,
    Track,
)

SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_URL = 'https://api.spotify.com/v1/'

replacements = {
    ('Kenny Loggins', 'Dangerzone'): ('Kenny Loggins', 'Danger zone'),
    ('Pink and Willow Sage Hart', 'Cover Me In Sunshine'): ('Pink', 'Cover Me In Sunshine'),
    ('Meat Loaf ( ) Cher', 'Dead Ringer For Love'): ('Meat loaf', 'Dead Ringer For Love'),
    ('Abba', 'Dreamworld'): ('Abba', 'Dream world'),
    ('Ulf Lundell', 'Jag vill ha dig'): ('Ulf Lundell', 'Jag vill ha dej'),
    ('Timbuktu', 'Alla Vill Till Himlen Men Ingen Vill Dö'): ('Timbuktu', 'Alla Vill Till himmelen Men Ingen Vill Dö'),
    ('Orup', 'Jag Blir Heller Jagad Av Vargar'): ('Orup', 'Jag Blir Hellre Jagad Av Vargar'),
    ('Martin Stenmarck', '7milakliv'): ('Martin Stenmarck', 'Sjumilakliv'),
    ('Margeret', 'Cool Me Down'): ('Margaret', 'Cool Me Down'),
}


def scrape():
    station_codes = [x.code for x in Station.objects.all()]
    url = 'https://listenapi.planetradio.co.uk/api9.2/stations_nowplaying/SE?premium=1&_o=exactly&' + '&'.join([f'StationCode%5B%5D={x}' for x in station_codes])
    data = httpx.get(
        url=url,
        headers={
            'Pragma': 'no-cache',
            'Accept': 'application/json, text/plain, */*',
            'Origin': 'https://radioplay.se',
            'Cache-Control': 'no-cache',
            'Accept-Language': 'en-us',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, li, Gecko) Version/14.1.2 Safari/605.1.15',
            'Referer': 'https://radioplay.se/',
        }
    ).json()

    for x in data:
        station, _ = Station.objects.get_or_create(code=x['stationCode'])
        show, _ = Show.objects.get_or_create(
            name=x['stationOnAir']['episodeTitle'],
            station=station,
            defaults=dict(
                description=x['stationOnAir']['episodeDescription'],
            ),
        )
        artist_name = x['stationNowPlaying']['nowPlayingArtist']
        if not artist_name:
            continue
        track_name = x['stationNowPlaying']['nowPlayingTrack']
        if not track_name:
            continue
        artist, _ = Artist.objects.get_or_create(name=artist_name)
        track, _ = Track.objects.get_or_create(name=track_name, artist=artist)
        playlist, _ = Playlist.objects.get_or_create(show=show, start_time=x['stationOnAir']['episodeStart'])
        playlist_item, _ = PlaylistItem.objects.get_or_create(playlist=playlist, track=track, start_time=x['stationNowPlaying']['nowPlayingTime'])


def sanitize(name):
    return name.replace("'", '').replace('´', '')


def get_access_token():
    auth_response = httpx.post(SPOTIFY_AUTH_URL, data={
        'grant_type': 'client_credentials',
        'client_id': os.environ['DOKKU_SPOTIFY_CLIENT_ID'],
        'client_secret': os.environ['DOKKU_SPOTIFY_SECRET'],
    })
    auth_response_data = auth_response.json()
    return auth_response_data['access_token']


def spotify_search(access_token, q):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    print(f'   {q}')
    r = httpx.get(f'{SPOTIFY_API_URL}search?type=track&q={quote_plus(q)}', headers=headers)
    try:
        return r.json()['tracks']['items']
    except KeyError:
        return []


def backfill_spotify_ids():
    access_token = get_access_token()

    def search(artist_name, track_name):
        search_string = f'artist:"{artist_name}" track:"{sanitize(track_name)}"'
        return spotify_search(access_token, search_string)

    def search_freetext(artist_name, track_name):
        search_string = f'{artist_name} {sanitize(track_name)}'
        return spotify_search(access_token, search_string)

    for track in Track.objects.filter(spotify_uri=None).order_by('?')[:10]:
        artist_name = track.artist.name
        if artist_name == 'Pink' or artist_name.startswith('Pink '):
            artist_name = artist_name.replace('Pink', 'P!nk')

        if track.name.endswith('-3.00'):
            track.name = track.name[:-len('-3.00')]

        print(artist_name, ' - ', track.name)

        if (artist_name, track.name) in replacements:
            artist_name, track.name = replacements[(artist_name, track.name)]

        items = search(artist_name, track.name)
        if not items and ' and ' in track.artist.name:
            items = search(artist_name.replace(' and ', '&'), track.name)
        if not items and ' and ' in track.artist.name:
            items = search(artist_name.partition(' and ')[0], track.name)
        if not items and ' and ' in track.artist.name:
            items = search(artist_name.partition(' and ')[-1], track.name)
        if not items and ' ft. ' in track.artist.name:
            items = search(artist_name.partition(' ft. ')[-1], track.name)
        if not items and ' ft. ' in track.artist.name:
            items = search(artist_name.partition(' ft. ')[0], track.name)
        if not items:
            items = search_freetext(artist_name, track.name)
        for t in items:
            track.spotify_uri = t['uri']
            track.spotify_url = t['href']
            track.save()
            print('     FOUND!')
            break


if __name__ == '__main__':
    scrape()
    backfill_spotify_ids()
