# Generated by Django 5.0.3 on 2024-09-11 12:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('demoapp', '0004_complaint_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='complaint',
            name='user',
        ),
    ]
