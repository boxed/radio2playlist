# Generated by Django 3.2.8 on 2021-11-12 19:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radio2playlist', '0004_auto_20211017_1924'),
    ]

    operations = [
        migrations.AddField(
            model_name='track',
            name='spotify_uri',
            field=models.TextField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='track',
            name='spotify_url',
            field=models.TextField(default=None, null=True),
        ),
    ]
