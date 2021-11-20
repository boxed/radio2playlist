from django.urls import (
    include,
    path,
)
from iommi import Table
from iommi.admin import Admin
from .path import decoded_path

from radio2playlist.models import (
    Playlist,
    PlaylistItem,
    Show,
    Station,
    Track,
)

urlpatterns = [
    decoded_path('', Table(
        auto__model=Station,
        columns__name__cell__url=lambda row, **_: row.get_absolute_url(),
    ).as_view()),

    decoded_path('stations/<int:station_pk>/', Table(
        auto__model=Show,
        rows=lambda request, **_: request.url_params['station'].shows.all(),
        columns__name__cell__url=lambda row, **_: row.get_absolute_url(),
    ).as_view()),

    decoded_path('shows/<int:show_pk>/', Table(
        auto__model=Playlist,
        rows=lambda request, **_: request.url_params['show'].playlists.all(),
        columns__show__cell__url=lambda row, **_: row.get_absolute_url(),
    ).as_view()),

    decoded_path('playlists/<int:playlist_pk>/', Table(
        auto__model=PlaylistItem,
        auto__include=['track__artist', 'track'],
        rows=lambda request, **_: request.url_params['playlist'].songs.all().order_by('start_time'),
    ).as_view()),

    decoded_path('without_spotify_uri/', Table(
        auto__rows=Track.objects.filter(spotify_uri=None),
        auto__include=['artist', 'name'],
    )),

    decoded_path('without_spotify_url/', Table(
        auto__rows=Track.objects.filter(spotify_url=None),
        auto__include=['artist', 'name'],
    )),

    path('admin/', include(Admin.urls())),
]
