# Generated by Django 4.2.5 on 2023-12-03 00:46

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deploytest', '0016_listing_place_id_alter_utilities_cable_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='square_feet',
            field=models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Square feet'),
        ),
    ]
