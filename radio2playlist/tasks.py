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

SPOTIFY_CLIENT_ID = '2f7e8eb1b1b84a3a80db398619220e71'
SPOTIFY_CLIENT_SECRET = '46a9a8d1be0a4efba595675326333d15'
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


def backfill_spotify_ids():
    auth_response = httpx.post(SPOTIFY_AUTH_URL, data={
        'grant_type': 'client_credentials',
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET,
    })
    auth_response_data = auth_response.json()
    access_token = auth_response_data['access_token']
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    for track in Track.objects.filter(spotify_uri=None):
        search_string = f'artist:"{track.artist.name}" track:"{track.name}"'
        print(search_string)
        r = httpx.get(f'{SPOTIFY_API_URL}search?type=track&q={quote_plus(search_string)}', headers=headers)
        for t in r.json()['tracks']['items']:
            if t['artists'][0]['name'].lower() != track.artist.name.lower():
                continue
            track.spotify_uri = t['uri']
            track.spotify_url = t['href']
            track.save()
            break


if __name__ == '__main__':
    scrape()
    backfill_spotify_ids()
