# Generated by Django 5.0.3 on 2024-11-08 06:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demoapp', '0010_complaintcounter'),
    ]

    operations = [
        migrations.AlterField(
            model_name='complaint',
            name='claim_type',
            field=models.CharField(choices=[('Under Warranty', 'Under Warranty'), ('Chargeable', 'Chargeable')], max_length=20, null=True),
        ),
    ]
