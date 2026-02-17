#!/usr/bin/env bash
# Render build script for Room Booking Django application
set -o errexit  # Exit on error

echo "==> Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Running database migrations..."
python manage.py migrate --noinput

echo "==> Build complete!"
