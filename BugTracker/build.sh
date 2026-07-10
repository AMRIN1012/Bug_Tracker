#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate

# Seed the database with all 7 role-based demo users
# Uses get_or_create + always sets password → safe to re-run on every deploy
python manage.py seed_data
