# Generated by Django 5.1 on 2024-09-02 04:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demoapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='complaint',
            name='id',
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
    ]
