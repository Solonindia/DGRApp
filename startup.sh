#!/bin/bash
set -e

echo "✅ Running migrations..."
python manage.py migrate --noinput

echo "✅ Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Starting Gunicorn..."
exec gunicorn demodjango.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 2 \
  --timeout 180 \
  --access-logfile - \
  --error-logfile -
