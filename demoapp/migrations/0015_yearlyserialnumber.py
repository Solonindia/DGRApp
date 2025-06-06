# Generated by Django 5.0.3 on 2025-01-04 04:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demoapp', '0014_alter_complaint_complaint_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='YearlySerialNumber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField(unique=True)),
                ('last_serial_number', models.PositiveIntegerField(default=0)),
            ],
        ),
    ]
