from django.db.models import (
    CharField,
    DateTimeField,
    ForeignKey,
    Model,
    RESTRICT,
    TextField,
)


class R2PModel(Model):
    def has_permission(self, **_):
        return True

    class Meta:
        abstract = True


class Station(R2PModel):
    name = CharField(max_length=255, db_index=True)
    code = CharField(max_length=255, db_index=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/stations/{self.pk}/'


class Show(R2PModel):
    name = CharField(max_length=255, db_index=True)
    description = TextField(max_length=255)
    station = ForeignKey(Station, on_delete=RESTRICT, null=True, related_name='shows')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/shows/{self.pk}/'


class Artist(R2PModel):
    name = CharField(max_length=255, db_index=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/artists/{self.pk}/'


class Track(R2PModel):
    name = CharField(max_length=255, db_index=True)
    artist = ForeignKey(Artist, on_delete=RESTRICT, related_name='tracks', null=True)
    spotify_uri = TextField(default=None, null=True)
    spotify_url = TextField(default=None, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/tracks/{self.pk}/'


class Playlist(R2PModel):
    show = ForeignKey(Show, on_delete=RESTRICT, related_name='playlists')
    start_time = DateTimeField(db_index=True)

    def get_absolute_url(self):
        return f'/playlists/{self.pk}/'

    def __str__(self):
        return f'{self.show} - {self.start_time}'


class PlaylistItem(R2PModel):
    playlist = ForeignKey(Playlist, on_delete=RESTRICT, related_name='songs')
    track = ForeignKey(Track, on_delete=RESTRICT)
    start_time = DateTimeField()

    def __str__(self):
        return self.track.name
