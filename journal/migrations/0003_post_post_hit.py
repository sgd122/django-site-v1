# Generated by Django 3.1.4 on 2020-12-12 04:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0002_auto_20201211_2323'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='post_hit',
            field=models.PositiveIntegerField(default=0),
        ),
    ]