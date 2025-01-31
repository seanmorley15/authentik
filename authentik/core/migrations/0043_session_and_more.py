# Generated by Django 5.0.11 on 2025-01-27 12:58

import uuid
import pickle
import authentik.core.models
from django.db import migrations, models
import authentik.core.models
import django.db.models.deletion
from django.conf import settings
from django.contrib.sessions.backends.cache import KEY_PREFIX
from django.utils.timezone import now, timedelta
from authentik.lib.migrations import progress_bar
from uuid import uuid4


SESSION_CACHE_ALIAS = "default"


def _migrate_session(
    db_alias, Session, OldAuthenticatedSession, AuthenticatedSession, session_key, **data
):
    old_auth_session = (
        OldAuthenticatedSession.objects.using(db_alias).filter(session_key=session_key).first()
    )
    if old_auth_session:
        AuthenticatedSession.objects.using(db_alias).create(
            session_key=session_key,
            **data,
            user=old_auth_session.user,
            last_ip=old_auth_session.last_ip,
            last_user_agent=old_auth_session.last_user_agent,
            last_used=old_auth_session.last_used,
        )
    else:
        Session.objects.using(db_alias).create(session_key=session_key, **data)


def migrate_redis_sessions(apps, schema_editor):
    from django.core.cache import caches

    Session = apps.get_model("authentik_core", "Session")
    OldAuthenticatedSession = apps.get_model("authentik_core", "OldAuthenticatedSession")
    AuthenticatedSession = apps.get_model("authentik_core", "AuthenticatedSession")
    db_alias = schema_editor.connection.alias
    cache = caches[SESSION_CACHE_ALIAS]

    # Not a redis cache, skipping
    if not hasattr(cache, "keys"):
        return

    print("\nMigrating Redis sessions to database, this might take a couple of minutes...")
    for key, session_data in progress_bar(cache.get_many(cache.keys(f"{KEY_PREFIX}*")).items()):
        _migrate_session(
            db_alias=db_alias,
            Session=Session,
            OldAuthenticatedSession=OldAuthenticatedSession,
            AuthenticatedSession=AuthenticatedSession,
            session_key=key.removeprefix(KEY_PREFIX),
            session_data=pickle.dumps(session_data, pickle.HIGHEST_PROTOCOL),
            expires=now() + timedelta(seconds=cache.ttl(key)),
        )


def migrate_database_sessions(apps, schema_editor):
    DjangoSession = apps.get_model("sessions", "Session")
    Session = apps.get_model("authentik_core", "Session")
    OldAuthenticatedSession = apps.get_model("authentik_core", "OldAuthenticatedSession")
    AuthenticatedSession = apps.get_model("authentik_core", "AuthenticatedSession")
    db_alias = schema_editor.connection.alias

    print("\nMigration database sessions, this might take a couple of minutes...")
    for django_session in progress_bar(DjangoSession.objects.using(db_alias).all()):
        _migrate_session(
            db_alias=db_alias,
            Session=Session,
            OldAuthenticatedSession=OldAuthenticatedSession,
            AuthenticatedSession=AuthenticatedSession,
            session_key=django_session.session_key,
            session_data=django_session.session_data,
            expires=django_session.expire_date,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("sessions", "0001_initial"),
        ("authentik_core", "0042_authenticatedsession_authentik_c_expires_08251d_idx_and_more"),
        ("authentik_providers_oauth2", "0027_accesstoken_authentik_p_expires_9f24a5_idx_and_more"),
        ("authentik_providers_rac", "0006_connectiontoken_authentik_p_expires_91f148_idx_and_more"),
    ]

    operations = [
        # Rename AuthenticatedSession to OldAuthenticatedSession
        migrations.RenameModel(
            old_name="AuthenticatedSession",
            new_name="OldAuthenticatedSession",
        ),
        migrations.RenameIndex(
            model_name="oldauthenticatedsession",
            new_name="authentik_c_expires_cf4f72_idx",
            old_name="authentik_c_expires_08251d_idx",
        ),
        migrations.RenameIndex(
            model_name="oldauthenticatedsession",
            new_name="authentik_c_expirin_c1f17f_idx",
            old_name="authentik_c_expirin_9cd839_idx",
        ),
        migrations.RenameIndex(
            model_name="oldauthenticatedsession",
            new_name="authentik_c_expirin_e04f5d_idx",
            old_name="authentik_c_expirin_195a84_idx",
        ),
        migrations.RenameIndex(
            model_name="oldauthenticatedsession",
            new_name="authentik_c_session_a44819_idx",
            old_name="authentik_c_session_d0f005_idx",
        ),
        migrations.RunSQL(
            "ALTER INDEX authentik_core_authenticatedsession_user_id_5055b6cf RENAME TO authentik_core_oldauthenticatedsession_user_id_5055b6cf",
            "ALTER INDEX authentik_core_oldauthenticatedsession_user_id_5055b6cf RENAME TO authentik_core_authenticatedsession_user_id_5055b6cf",
        ),
        # Create new Session and AuthenticatedSession models
        migrations.CreateModel(
            name="Session",
            fields=[
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "session_key",
                    models.CharField(max_length=40, db_index=True, verbose_name="session key"),
                ),
                ("session_data", models.TextField(verbose_name="session data")),
                ("expires", models.DateTimeField(default=None, null=True)),
                ("expiring", models.BooleanField(default=True)),
            ],
            options={
                "default_permissions": [],
                "verbose_name": "Session",
                "verbose_name_plural": "Sessions",
            },
            managers=[
                ("objects", authentik.core.models.SessionManager()),
            ],
        ),
        migrations.AddIndex(
            model_name="session",
            index=models.Index(fields=["expires"], name="authentik_c_expires_d2f607_idx"),
        ),
        migrations.AddIndex(
            model_name="session",
            index=models.Index(fields=["expiring"], name="authentik_c_expirin_7c2cfb_idx"),
        ),
        migrations.AddIndex(
            model_name="session",
            index=models.Index(
                fields=["expiring", "expires"], name="authentik_c_expirin_1ab2e4_idx"
            ),
        ),
        migrations.CreateModel(
            name="AuthenticatedSession",
            fields=[
                (
                    "session_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="authentik_core.session",
                    ),
                ),
                ("last_ip", models.TextField()),
                ("last_user_agent", models.TextField(blank=True)),
                ("last_used", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                "verbose_name": "Authenticated Session",
                "verbose_name_plural": "Authenticated Sessions",
            },
            bases=("authentik_core.session",),
            managers=[
                ("objects", authentik.core.models.SessionManager()),
            ],
        ),
        migrations.RunPython(migrate_redis_sessions, migrations.RunPython.noop),
        migrations.RunPython(migrate_database_sessions, migrations.RunPython.noop),
    ]
