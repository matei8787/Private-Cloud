#!/bin/bash
set -e

# Wait for services to begin

echo "Waiting for postgres to start"

nc -z "$SQL_HOST" "$SQL_PORT"
PG_UP=$?
nc -z "$REDIS_HOST" "$REDIS_PORT"
REDIS_UP=$?

while [[ $PG_UP -ne 0 && $REDIS_UP -ne 0 ]]; do

    sleep 1

    if [[ $PG_UP -eq 0 ]]; then
        nc -z "$SQL_HOST" "$SQL_PORT"
        PG_UP=$?
    fi

    if [[ $REDIS_UP -eq 0 ]]; then
        nc -z "$REDIS_HOST" "$REDIS_PORT"
        REDIS_UP=$?
    fi

done
echo "Postgres started"

python manage.py collectstatic --no-input
python manage.py makemigrations --no-input
python manage.py makemigrations core --no-input
python manage.py migrate --no-input
python manage.py migrate core --no-input

exec "$@"