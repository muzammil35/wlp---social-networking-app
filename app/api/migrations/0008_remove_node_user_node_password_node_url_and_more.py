# Generated by Django 5.0.1 on 2024-03-13 03:12

import uuid
import django
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_author_followers_alter_author_profile_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='node',
            name='user',
        ),
        migrations.AddField(
            model_name='node',
            name='password',
            field=models.CharField(default=' ', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='node',
            name='url',
            field=models.URLField(default=' '),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='node',
            name='username',
            field=models.CharField(default='defaultPassword', max_length=200),
            preserve_default=False,
        ),
    ]
