#!/bin/bash
set -e

echo "✅ Starting Django App on Azure..."
echo "📍 Working dir: $(pwd)"

# ✅ Always go to project root (manage.py should be here)
cd /home/site/wwwroot

echo "✅ Python version:"
python --version

echo "✅ Running migrations..."
python -u manage.py migrate --noinput --verbosity 2

echo "✅ Collecting static files..."
python -u manage.py collectstatic --noinput

echo "✅ Starting Gunicorn..."
exec gunicorn demodjango.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 2 \
  --timeout 180 \
  --access-logfile - \
  --error-logfile -
