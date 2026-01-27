#!/bin/bash
set -e

echo "📍 Switching to app root"
cd /home/site/wwwroot

echo "📍 Exporting PYTHONPATH"
export PYTHONPATH=/home/site/wwwroot

echo "✅ Running migrations"
python -u manage.py migrate --noinput

echo "✅ Collecting static files"
python -u manage.py collectstatic --noinput

echo "🚀 Starting Gunicorn"
exec gunicorn demodjango.wsgi:application \
  --chdir /home/site/wwwroot \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 2 \
  --timeout 180 \
  --access-logfile - \
  --error-logfile -
