"""Run from mysite/: gunicorn --config ../deploy/gunicorn.conf.py mysite.wsgi:application."""

import os

bind = '127.0.0.1:8000'
workers = int(os.getenv('WEB_CONCURRENCY', '2'))
timeout = 60
accesslog = '-'
errorlog = '-'
capture_output = True
forwarded_allow_ips = '127.0.0.1'
