import json
import os
import subprocess
import sys
from pathlib import Path

from django.contrib.staticfiles import finders
from django.template.loader import get_template
from django.test import SimpleTestCase, TransactionTestCase, override_settings


class DeploymentTests(SimpleTestCase):
    def test_legacy_assets_are_available_to_collectstatic(self):
        # collectstatic uses list(), which also handles prefixed asset trees on
        # Windows; FileSystemFinder.find() expects OS separators after a prefix.
        available = set()
        for finder in finders.get_finders():
            for name, storage in finder.list([]):
                prefix = getattr(storage, 'prefix', '')
                asset_name = name.replace('\\', '/')
                available.add('/'.join(filter(None, [prefix, asset_name])))
        for name in [
            'legacy/basic/css/tilda-grid-3.0.min.css',
            'legacy/basic/js/tilda-scripts-3.0.min.js',
            'legacy/catalog/css/tilda-grid-3.0.min.css',
            'legacy/catalog/js/tilda-scripts-3.0.min.js',
            'admin/js/core.js', 'images/logo.png',
        ]:
            with self.subTest(name=name):
                self.assertIn(name, available)

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'], SECURE_SSL_REDIRECT=False)
    def test_public_pages_and_custom_404_work_without_debug(self):
        for path in [
            '/', '/choice', '/calculator', '/partner', '/trend/hopetoun',
            '/production', '/about', '/privacy', '/quartz', '/acryl', '/natural',
            '/porcelain', '/stairs', '/sinks', '/sills', '/dimensions', '/delivery',
            '/installation', '/panels', '/bar', '/fireplace', '/reception', '/selection',
        ]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertNotIn('\ufffd', response.content.decode('utf-8'))
        response = self.client.get('/definitely-not-a-page')
        self.assertEqual(response.status_code, 404)
        self.assertNotIn('\ufffd', response.content.decode('utf-8'))

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'], SECURE_SSL_REDIRECT=False)
    def test_nested_404_has_readable_text_and_root_relative_assets(self):
        response = self.client.get('/catalog/quartz/unknown/nested/path')
        self.assertContains(response, 'Страница не найдена', status_code=404)
        self.assertContains(response, 'href="/catalog/css/tilda-grid-3.0.min.css"', status_code=404)
        self.assertNotContains(response, 'src="js/', status_code=404)
        self.assertNotIn('\ufffd', response.content.decode('utf-8'))

    def test_export_panel_labels_are_readable(self):
        html = get_template('basic_page/export_panel.html').render()
        self.assertIn('Экспорт заявок', html)
        self.assertIn('Экспорт натурального камня', html)
        self.assertNotIn('\ufffd', html)

    def test_production_settings_default_to_secure_cookies_and_redirects(self):
        environment = os.environ.copy()
        environment.update({
            'DJANGO_SETTINGS_MODULE': 'mysite.settings',
            'DEBUG': 'False', 'ALLOWED_HOSTS': 'example.com,www.example.com',
            'TRUST_PROXY_HEADERS': 'True',
        })
        for key in ['SECURE_SSL_REDIRECT', 'SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE']:
            environment.pop(key, None)
        code = (
            'import json; from mysite import settings as s; '
            'print(json.dumps([s.DEBUG,s.ALLOWED_HOSTS,s.SESSION_COOKIE_SECURE,'
            's.CSRF_COOKIE_SECURE,s.SECURE_SSL_REDIRECT,s.SECURE_PROXY_SSL_HEADER]))'
        )
        process = subprocess.run(
            [sys.executable, '-c', code], env=environment, capture_output=True,
            text=True, cwd=Path(__file__).resolve().parent.parent, check=True,
        )
        self.assertEqual(json.loads(process.stdout), [
            False, ['example.com', 'www.example.com'], True, True, True,
            ['HTTP_X_FORWARDED_PROTO', 'https'],
        ])


@override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'], SECURE_SSL_REDIRECT=False)
class CatalogDeploymentTests(TransactionTestCase):
    def test_catalog_pages_details_ajax_and_sitemap_render_without_debug(self):
        from catalog.models import AcrylicStone, CeramicsStone, NaturalStone, QuartzStone

        for model, kind in [
            (QuartzStone, 'quartz'), (AcrylicStone, 'acril'),
            (NaturalStone, 'natural'), (CeramicsStone, 'ceramic'),
        ]:
            stone = model.objects.create(
                name_stone=f'Test {kind}', article=f'DEPLOY-{kind}',
                priview_img='test-preview.jpg',
            )
            with self.subTest(kind=kind):
                self.assertEqual(self.client.get(f'/catalog/{kind}').status_code, 200)
                response = self.client.get(
                    f'/catalog/{kind}', HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn('html', response.json())
                empty = self.client.get(
                    f'/catalog/{kind}?brand=not-an-existing-brand',
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                )
                self.assertIn('Камни не найдены', empty.json()['html'])
                self.assertNotIn('\ufffd', empty.json()['html'])
                self.assertEqual(
                    self.client.get(f'/catalog/{kind}/stone/{stone.article}').status_code, 200,
                )
        self.assertEqual(self.client.get('/sitemap.xml').status_code, 200)
        self.assertEqual(self.client.get('/robots.txt').status_code, 200)
