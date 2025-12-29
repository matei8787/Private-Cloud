#!/bin/bash
set -e

python manage.py collectstatic --no-input
python manage.py makemigrations --no-input
python manage.py makemigrations hello --no-input
python manage.py migrate --no-input
python manage.py migrate hello --no-input

exec "$@"