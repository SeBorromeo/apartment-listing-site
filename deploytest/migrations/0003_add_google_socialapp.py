# Generated by Django 4.2.5 on 2023-10-07 22:59

from django.db import migrations, transaction
from django.conf import settings

SOCIALAPP_NAME = 'google-oauth2-app'


def make_google_socialapp(apps, schema_editor):
    SocialApp = apps.get_model('socialaccount', 'SocialApp')

    with transaction.atomic():
        # very bad temporary solution: credentials in settings
        new_app = SocialApp(
            name=SOCIALAPP_NAME,
            provider='google',
            client_id=settings.SOCIALAPP_GOOGLE_CLIENT_ID,
            secret=settings.SOCIALAPP_GOOGLE_CLIENT_SECRET
        )
        new_app.save()


def add_sites_to_socialapp(apps, schema_editor):
    SocialApp = apps.get_model('socialaccount', 'SocialApp')
    Site = apps.get_model('sites', 'Site')

    google_app = SocialApp.objects.get(name=SOCIALAPP_NAME)

    sites = Site.objects.all()
    with transaction.atomic():
        google_app.sites.add(*sites)
        google_app.save()


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('deploytest', '0002_make_site_for_socialapp'),
        ('socialaccount', '0005_socialtoken_nullable_app'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(make_google_socialapp),
        migrations.RunPython(add_sites_to_socialapp)
    ]
