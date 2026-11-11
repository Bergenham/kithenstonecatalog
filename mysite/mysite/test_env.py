import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from .env import env_bool, env_list, env_nonnegative_int, load_env, required_env


class EnvTests(SimpleTestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix='catalog-env-test-')
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / '.env'

    def load(self, content, environ=None):
        self.path.write_text(content, encoding='utf-8')
        target = {} if environ is None else environ
        load_env(self.path, target)
        return target

    def test_secrets_preserve_hash_dollar_and_backslashes(self):
        values = self.load(
            "SECRET_KEY='test#secret$with\\slashes'\n"
            "DB_PASSWORD='test%~|@password'\n"
        )
        self.assertEqual(values['SECRET_KEY'], 'test#secret$with\\slashes')
        self.assertEqual(values['DB_PASSWORD'], 'test%~|@password')

    def test_server_environment_takes_priority(self):
        values = self.load('DB_PASSWORD=file-value\n', {'DB_PASSWORD': 'server-value'})
        self.assertEqual(values['DB_PASSWORD'], 'server-value')

    def test_comments_bom_export_and_blank_values(self):
        values = self.load(
            '\ufeff# Config\n\nexport DB_HOST = localhost # note\n'
            "DB_USER='test-user' # note\nEMPTY=\nHASH=abc#123\n"
        )
        self.assertEqual(values, {
            'DB_HOST': 'localhost', 'DB_USER': 'test-user',
            'EMPTY': '', 'HASH': 'abc#123',
        })

    def test_double_quoted_json_escapes(self):
        self.assertEqual(self.load(r'PASSWORD="a\\b\"c"')['PASSWORD'], 'a\\b"c')

    def test_values_are_not_executed_or_interpolated(self):
        values = self.load("VALUE='${SECRET_KEY} $(command)'\n")
        self.assertEqual(values['VALUE'], '${SECRET_KEY} $(command)')

    def test_missing_file_is_allowed_for_environment_only_deployment(self):
        values = {'SECRET_KEY': 'from-environment'}
        load_env(self.path, values)
        self.assertEqual(values, {'SECRET_KEY': 'from-environment'})

    def test_invalid_lines_do_not_expose_values_or_partially_apply_file(self):
        for line in ["INVALID-NAME=private-value", "PASSWORD='private-value",
                     'PASSWORD="private-value', "PASSWORD='private-value' trailing",
                     'PASSWORD=one\nPASSWORD=private-value']:
            with self.subTest(line=line):
                target = {}
                with self.assertRaises(ImproperlyConfigured) as caught:
                    self.load('VALID=ok\n' + line, target)
                self.assertNotIn('private-value', str(caught.exception))
                self.assertEqual(target, {})

    def test_required_secret_has_no_fallback(self):
        for environ in [{}, {'DB_PASSWORD': ''}]:
            with self.subTest(environ=environ), patch.dict(os.environ, environ, clear=True):
                with self.assertRaisesMessage(ImproperlyConfigured, 'DB_PASSWORD'):
                    required_env('DB_PASSWORD')

    def test_required_secret_is_read_from_environment(self):
        with patch.dict(os.environ, {'DB_PASSWORD': 'configured-password'}):
            self.assertEqual(required_env('DB_PASSWORD'), 'configured-password')

    def test_boolean_settings_are_parsed_instead_of_using_string_truthiness(self):
        for value in ['False', 'false', '0', 'off', 'no']:
            with self.subTest(value=value), patch.dict(os.environ, {'DEBUG': value}):
                self.assertFalse(env_bool('DEBUG'))
        for value in ['True', 'true', '1', 'on', 'yes']:
            with self.subTest(value=value), patch.dict(os.environ, {'DEBUG': value}):
                self.assertTrue(env_bool('DEBUG'))
        with patch.dict(os.environ, {'DEBUG': 'typo'}):
            with self.assertRaises(ImproperlyConfigured):
                env_bool('DEBUG')

    def test_domain_lists_ignore_empty_items_and_spaces(self):
        with patch.dict(os.environ, {'ALLOWED_HOSTS': 'example.com, www.example.com,,'}):
            self.assertEqual(env_list('ALLOWED_HOSTS'), ['example.com', 'www.example.com'])

    def test_hsts_duration_cannot_be_negative_or_invalid(self):
        for value in ['-1', 'bad', '1.5']:
            with self.subTest(value=value), patch.dict(os.environ, {'SECURE_HSTS_SECONDS': value}):
                with self.assertRaises(ImproperlyConfigured):
                    env_nonnegative_int('SECURE_HSTS_SECONDS')
        with patch.dict(os.environ, {'SECURE_HSTS_SECONDS': '3600'}):
            self.assertEqual(env_nonnegative_int('SECURE_HSTS_SECONDS'), 3600)
