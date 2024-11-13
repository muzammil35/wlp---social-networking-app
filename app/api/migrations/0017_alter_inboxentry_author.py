# Generated by Django 5.0.1 on 2024-03-17 23:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_remove_author_followers_follow_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inboxentry',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.author'),
        ),
    ]
