# Generated by Django 4.2.5 on 2023-11-03 21:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('deploytest', '0007_remove_listing_images_remove_listing_place_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('author', models.ForeignKey(limit_choices_to={'groups__name': 'Administrator'}, on_delete=django.db.models.deletion.CASCADE, related_name='authored_messages', to=settings.AUTH_USER_MODEL)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_messages', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
