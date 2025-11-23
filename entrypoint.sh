#!/bin/sh
# Ждём немного, чтобы база точно была доступна
sleep 5

echo "=== Running migrations ==="
python manage.py migrate --noinput

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Copying collected static files to volume ==="
cp -r /app/collected_static/. /backend_static/static/

echo "=== Starting Gunicorn ==="
exec gunicorn --bind 0.0.0.0:8080 pr_service.wsgi
