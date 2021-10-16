from django.db.models import (
    CharField,
    DateTimeField,
    ForeignKey,
    Model,
    RESTRICT,
    TextField,
)


class Station(Model):
    name = CharField(max_length=255, db_index=True)
    code = CharField(max_length=255, db_index=True)

    def __str__(self):
        return self.name


class Show(Model):
    name = CharField(max_length=255, db_index=True)
    description = TextField(max_length=255)

    def __str__(self):
        return self.name


class Artist(Model):
    name = CharField(max_length=255, db_index=True)

    def __str__(self):
        return self.name


class Track(Model):
    name = CharField(max_length=255, db_index=True)

    def __str__(self):
        return self.name


class Playlist(Model):
    show = ForeignKey(Show, on_delete=RESTRICT)
    start_time = DateTimeField(db_index=True)


class PlaylistItem(Model):
    playlist = ForeignKey(Playlist, on_delete=RESTRICT)
    track = ForeignKey(Track, on_delete=RESTRICT)
    start_time = DateTimeField()

    def __str__(self):
        return self.track.name
