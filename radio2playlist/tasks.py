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


def scrape():
    url = 'https://listenapi.planetradio.co.uk/api9.2/stations_nowplaying/SE?StationCode%5B%5D=rok&premium=1&_o=exactly'
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
            defaults=dict(
                description=x['stationOnAir']['episodeDescription'],
            ),
        )
        artist, _ = Artist.objects.get_or_create(name=x['stationNowPlaying']['nowPlayingArtist'])
        track, _ = Track.objects.get_or_create(name=x['stationNowPlaying']['nowPlayingTrack'])
        playlist, _ = Playlist.objects.get_or_create(show=show, start_time=x['stationOnAir']['episodeStart'])
        playlist_item, _ = PlaylistItem.objects.get_or_create(playlist=playlist, track=track, start_time=x['stationNowPlaying']['nowPlayingTime'])


if __name__ == '__main__':
    scrape()
