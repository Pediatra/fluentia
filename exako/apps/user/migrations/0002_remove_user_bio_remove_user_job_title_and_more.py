# Generated by Django 5.1 on 2024-09-25 20:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='bio',
        ),
        migrations.RemoveField(
            model_name='user',
            name='job_title',
        ),
        migrations.RemoveField(
            model_name='user',
            name='locale',
        ),
    ]
