"""Isolated importer tests: never connect to the configured PostgreSQL database."""

import os

# Test-only defaults allow a fresh checkout to run without a private .env.
# These defaults are never loaded by the ordinary WSGI/ASGI settings.
for name, value in {
    'SECRET_KEY': 'isolated-tests-only-secret-key',
    'DB_NAME': 'unused-test-database',
    'DB_USER': 'unused-test-user',
    'DB_PASSWORD': 'unused-test-password',
    'DEBUG': 'True',
}.items():
    os.environ.setdefault(name, value)

from .settings import *  # noqa: F403

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
