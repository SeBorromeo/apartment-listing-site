# Generated by Django 4.2.5 on 2023-11-01 02:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('deploytest', '0006_delete_signature'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='listing',
            name='images',
        ),
        migrations.RemoveField(
            model_name='listing',
            name='place_id',
        ),
    ]
