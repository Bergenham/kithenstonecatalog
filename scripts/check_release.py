"""Check a candidate checkout without its ignored .env, media or virtualenv.

Run with the Python environment that has the project's locked dependencies.
Includes tracked edits and untracked/non-ignored files, without changing Git.
"""

import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parent.parent


def run(*args, cwd, env):
    subprocess.run([sys.executable, *args], cwd=cwd, env=env, check=True)


def main():
    result = subprocess.run(
        ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
        cwd=ROOT, capture_output=True, check=True,
    )
    names = sorted(set(result.stdout.decode('utf-8').split('\0')) - {''})
    with TemporaryDirectory(prefix='stonecatalog-release-') as temporary:
        checkout = Path(temporary) / 'checkout'
        count = 0
        for name in names:
            source = ROOT / name
            if not source.is_file():
                continue  # A tracked file intentionally deleted in this worktree.
            parts = Path(name).parts
            if ('.git' in parts or '.venv' in parts or '__pycache__' in parts
                    or 'media' in parts or 'staticfiles' in parts
                    or (source.name.startswith('.env') and source.name != '.env.example')
                    or source.suffix in {'.pyc', '.dump', '.backup', '.sqlite3', '.key', '.pem'}):
                raise SystemExit(f'Private/generated file would enter the candidate checkout: {name}')
            destination = checkout / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            count += 1
        print(f'Candidate checkout: {count} files, without .env/media/.venv.', flush=True)
        project = checkout / 'mysite'
        environment = os.environ.copy()
        # Prevent caller-specific paths/secrets from masking missing clone files.
        for key in ['DJANGO_SETTINGS_MODULE', 'PYTHONPATH', 'MEDIA_ROOT', 'STATIC_ROOT',
                    'SECRET_KEY', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DEBUG']:
            environment.pop(key, None)
        run('manage.py', 'test', '--settings=mysite.import_test_settings',
            cwd=project, env=environment)
        run('manage.py', 'makemigrations', '--check', '--dry-run',
            '--settings=mysite.import_test_settings', cwd=project, env=environment)

        static_root = Path(temporary) / 'staticfiles'
        environment['STATIC_ROOT'] = str(static_root)
        run('manage.py', 'collectstatic', '--noinput', '--verbosity=0',
            '--settings=mysite.import_test_settings', cwd=project, env=environment)
        for name in [
            'legacy/basic/css/tilda-grid-3.0.min.css',
            'legacy/basic/js/tilda-scripts-3.0.min.js',
            'legacy/catalog/css/tilda-grid-3.0.min.css',
            'legacy/catalog/js/tilda-scripts-3.0.min.js',
            'admin/css/base.css', 'images/logo.png',
        ]:
            if not (static_root / name).is_file():
                raise SystemExit(f'Missing collected asset: {name}')
        if any(p.suffix in {'.py', '.html'} or p.name.startswith('.env')
               for p in static_root.rglob('*') if p.is_file()):
            raise SystemExit('Source/templates/private files found in collected static.')
        print('collectstatic: admin and legacy Tilda assets present; no source/templates.', flush=True)

        environment.update({
            'SECRET_KEY': secrets.token_urlsafe(64),
            'DB_NAME': 'release-check-unused', 'DB_USER': 'release-check-unused',
            'DB_PASSWORD': secrets.token_urlsafe(32), 'DEBUG': 'False',
            'ALLOWED_HOSTS': 'example.com,www.example.com',
            'CSRF_TRUSTED_ORIGINS': 'https://example.com,https://www.example.com',
            'TRUST_PROXY_HEADERS': 'True', 'SECURE_HSTS_SECONDS': '3600',
            'SECURE_SSL_REDIRECT': 'True', 'SESSION_COOKIE_SECURE': 'True',
            'CSRF_COOKIE_SECURE': 'True',
        })
        # Equivalent to check --deploy, without opening PostgreSQL. Keep HSTS
        # includeSubDomains/preload disabled: they need a domain-owner decision.
        # Accept only their two documented warnings; all other warnings fail.
        environment['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'
        deployment_checks = '''
import django
from django.core import checks
django.setup()
issues = checks.run_checks(include_deployment_checks=True)
expected = {'security.W005', 'security.W021'}
unexpected = [issue for issue in issues if issue.level >= checks.WARNING and issue.id not in expected]
for issue in issues:
    print(f'{issue.id}: {issue.msg}')
if unexpected:
    raise SystemExit(1)
print('Deployment checks passed; only documented HSTS subdomain/preload warnings are allowed.')
'''
        run('-c', deployment_checks, cwd=project, env=environment)
        print('Candidate checkout checks passed. No working database/media were used.', flush=True)


if __name__ == '__main__':
    main()
