# Generated by Django 5.0.3 on 2024-09-25 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demoapp', '0006_complaint_remarks'),
    ]

    operations = [
        migrations.AddField(
            model_name='complaint',
            name='pdf_upload',
            field=models.FileField(blank=True, null=True, upload_to='pdfs/'),
        ),
    ]
