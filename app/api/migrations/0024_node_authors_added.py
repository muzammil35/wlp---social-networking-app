# Generated by Django 5.0.1 on 2024-03-23 20:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0023_remove_comment_contenttype'),
    ]

    operations = [
        migrations.AddField(
            model_name='node',
            name='authors_added',
            field=models.BooleanField(default=False),
        ),
    ]