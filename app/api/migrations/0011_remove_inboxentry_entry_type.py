# Generated by Django 5.0.1 on 2024-03-13 20:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_merge_0007_image_0009_author_host_author_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inboxentry',
            name='entry_type',
        ),
    ]