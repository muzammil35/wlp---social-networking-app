# Generated by Django 5.0.1 on 2024-03-26 06:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0026_merge_20240324_2118'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='origin',
            field=models.URLField(blank=True, max_length=400),
        ),
        migrations.AlterField(
            model_name='post',
            name='source',
            field=models.URLField(blank=True, max_length=400),
        ),
    ]
