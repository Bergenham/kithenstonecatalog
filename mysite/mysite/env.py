"""Load the project's small .env file without executing/interpolating its values."""

import json
import os
import re

from django.core.exceptions import ImproperlyConfigured


def load_env(path, environ=None):
    """Read UTF-8 KEY=value entries; existing environment variables win.

    Single quotes preserve literal characters. Double quotes accept JSON escapes.
    No shell execution, variable expansion, or multiline values are supported.
    Never include the contents of a malformed line in an exception message.
    """
    environ = os.environ if environ is None else environ
    try:
        lines = path.read_text(encoding='utf-8-sig').splitlines()
    except FileNotFoundError:
        return
    except (OSError, UnicodeError):
        raise ImproperlyConfigured('Не удалось прочитать файл .env в UTF-8.') from None

    entries = {}
    for number, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('export '):
            line = line[7:].lstrip()
        key, separator, value = line.partition('=')
        key, value = key.strip(), value.strip()
        try:
            if not separator or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key):
                raise ValueError
            if key in entries:
                raise ValueError
            if value.startswith("'"):
                end = value.index("'", 1)
                parsed, remainder = value[1:end], value[end + 1:].strip()
            elif value.startswith('"'):
                parsed, end = json.JSONDecoder().raw_decode(value)
                remainder = value[end:].strip()
            else:
                parsed = re.split(r'\s+#', value, maxsplit=1)[0].rstrip()
                remainder = ''
            if remainder and not remainder.startswith('#'):
                raise ValueError
        except ValueError:
            raise ImproperlyConfigured(f'Некорректная строка {number} в .env.') from None
        entries[key] = parsed

    for key, value in entries.items():
        environ.setdefault(key, value)


def required_env(name):
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(
            f'Задайте {name} в корневом .env или переменных окружения.'
        )
    return value


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    value = value.strip().lower()
    if value in {'true', '1', 'yes', 'on'}:
        return True
    if value in {'false', '0', 'no', 'off'}:
        return False
    raise ImproperlyConfigured(f'{name}: ожидается true/false или 1/0.')


def env_list(name):
    return [value.strip() for value in os.environ.get(name, '').split(',') if value.strip()]


def env_nonnegative_int(name, default=0):
    try:
        value = int(os.environ.get(name, str(default)))
        if value < 0:
            raise ValueError
    except ValueError:
        raise ImproperlyConfigured(f'{name}: ожидается целое неотрицательное число.') from None
    return value
