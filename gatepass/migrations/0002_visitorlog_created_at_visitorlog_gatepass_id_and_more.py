# Generated by Django 5.0.3 on 2024-11-12 07:37

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gatepass', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='visitorlog',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='visitorlog',
            name='gatepass_id',
            field=models.CharField(blank=True, editable=False, max_length=255),
        ),
        migrations.AddField(
            model_name='visitorlog',
            name='serial_number',
            field=models.PositiveIntegerField(blank=True, editable=False, null=True),
        ),
    ]
