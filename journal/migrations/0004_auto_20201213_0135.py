# Generated by Django 3.1.4 on 2020-12-13 01:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0003_post_post_hit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='caption',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
    ]
