# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-30 00:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eveauth', '0004_auto_20170930_0038'),
    ]

    operations = [
        migrations.AddField(
            model_name='alliance',
            name='last_updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='character',
            name='last_updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='corporation',
            name='last_updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
