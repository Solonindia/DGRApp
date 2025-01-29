# Generated by Django 5.0.3 on 2025-01-28 10:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demoapp', '0016_delete_yearlyserialnumber'),
    ]

    operations = [
        migrations.AlterField(
            model_name='complaint',
            name='priority',
            field=models.CharField(choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low'), ('Rejected', 'Rejected')], default='Medium', max_length=10),
        ),
    ]
