# Generated by Django 5.0.3 on 2024-10-15 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demoapp', '0004_delete_complaintsystem_alter_complaint_images'),
    ]

    operations = [
        migrations.AlterField(
            model_name='complaint',
            name='images',
            field=models.TextField(null=True),
        ),
    ]
