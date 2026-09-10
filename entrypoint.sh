#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput


echo "Seeding database..."
python manage.py seed_db

echo "Starting Gunicorn server..."
exec gunicorn project.wsgi:application --bind 0.0.0.0:8000 --workers 3 --log-level info