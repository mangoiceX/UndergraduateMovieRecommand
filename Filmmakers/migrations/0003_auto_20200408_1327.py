# Generated by Django 2.2.3 on 2020-04-08 05:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Filmmakers', '0002_auto_20200402_2006'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='celebrity',
            name='create_time',
        ),
        migrations.RemoveField(
            model_name='celebrity',
            name='is_delete',
        ),
        migrations.RemoveField(
            model_name='celebrity',
            name='update_time',
        ),
    ]
