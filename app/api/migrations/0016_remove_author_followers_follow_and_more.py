# Generated by Django 5.0.1 on 2024-03-17 20:53

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_post_count'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='author',
            name='followers',
        ),
        migrations.CreateModel(
            name='Follow',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('pending', models.BooleanField(default=True)),
                ('followed', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followed', to='api.author')),
                ('follower', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='follower', to='api.author')),
            ],
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('followed', 'follower'), name='unique follow relationship'),
        ),
    ]
