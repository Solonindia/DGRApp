# Generated by Django 5.0.3 on 2024-11-07 07:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demoapp', '0005_alter_complaint_images'),
    ]

    operations = [
        migrations.AddField(
            model_name='complaint',
            name='serial_number',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]