# Generated by Django 5.0.11 on 2025-01-27 13:02

from django.db import migrations
from django.contrib.sessions.backends.cache import KEY_PREFIX


def delete_redis_sessions(apps, schema_editor):
    from django.core.cache import caches

    cache = caches["default"]
    # Not a redis cache, skipping
    if not hasattr(cache, "keys"):
        return
    cache.delete_many(cache.keys(f"{KEY_PREFIX}*"))


def delete_old_database_sessions(apps, schema_editor):
    DjangoSession = apps.get_model("sessions", "Session")
    db_alias = schema_editor.connection.alias
    DjangoSession.objects.using(db_alias).all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_core", "0043_session_and_more"),
        ("authentik_providers_rac", "0007_migrate_session"),
        ("authentik_providers_oauth2", "0028_migrate_session"),
    ]

    operations = [
        # migrations.DeleteModel(
        #     name="OldAuthenticatedSession",
        # ),
        # migrations.RunPython(code=delete_redis_sessions),
        # migrations.RunPython(code=delete_old_database_sessions),
    ]
