# Generated by Django 5.0.1 on 2024-03-13 02:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_alter_author_github_alter_author_profile_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='followers',
            field=models.ManyToManyField(blank=True, related_name='following', to='api.author'),
        ),
        migrations.AlterField(
            model_name='author',
            name='profile_image',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]