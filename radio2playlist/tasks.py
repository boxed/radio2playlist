import os
from urllib.parse import (
    quote_plus,
    urlencode,
)

import httpx

if __name__ == '__main__':
    import os
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


def backfill_spotify_ids():
    auth_response = httpx.post(SPOTIFY_AUTH_URL, data={
        'grant_type': 'client_credentials',
        'client_id': os.environ['DOKKU_SPOTIFY_CLIENT_ID'],
        'client_secret': os.environ['DOKKU_SPOTIFY_SECRET'],
    })
    auth_response_data = auth_response.json()
    access_token = auth_response_data['access_token']
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    def search(artist_name, track_name):
        search_string = f'artist:"{artist_name}" track:"{sanitize(track_name)}"'
        r = httpx.get(f'{SPOTIFY_API_URL}search?type=track&q={quote_plus(search_string)}', headers=headers)
        try:
            return r.json()['tracks']['items']
        except KeyError:
            return []
    def search_freetext(artist_name, track_name):
        search_string = f'{artist_name} {sanitize(track_name)}'
        r = httpx.get(f'{SPOTIFY_API_URL}search?type=track&q={quote_plus(search_string)}', headers=headers)
        try:
            return r.json()['tracks']['items']
        except KeyError:
            return []
    for track in Track.objects.filter(spotify_uri=None)[:10]:
        artist_name = track.artist.name
        if artist_name == 'Pink' or artist_name.startswith('Pink '):
            artist_name = artist_name.replace('Pink', 'P!ink')
        print(artist_name, ' - ', track.name)
        items = search(artist_name, track.name)
        if not items:
            items = search(artist_name.replace(' and ', '&'), track.name)
        if not items and ' and ' in track.artist.name:
            items = search(artist_name.partition(' and ')[0], track.name)
        if not items and ' and ' in track.artist.name:
            items = search(artist_name.partition(' and ')[-1], track.name)
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
