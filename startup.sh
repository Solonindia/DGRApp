#!/bin/bash
set -e

cd /home/site/wwwroot
export PYTHONPATH=/home/site/wwwroot

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn \
  --module demodjango.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 2 \
  --timeout 180 \
  --access-logfile - \
  --error-logfile -
