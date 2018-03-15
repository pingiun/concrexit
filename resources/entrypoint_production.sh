#!/bin/bash

set -e

>&2 echo "Creating Sphinx documentation"
sphinx-build -b html /usr/src/app/docs/ /concrexit/docs/

until psql -h "$DJANGO_POSTGRES_HOST" -U "postgres" -c '\l' $POSTGRES_DB; do
    >&2 echo "PostgreSQL is unavailable: Sleeping"
    sleep 5
done
>&2 echo "PostgreSQL is up"

chown -R www-data:www-data /concrexit/

cd /usr/src/app/website/
>&2 echo "Running site with uwsgi"
uwsgi --chdir /usr/src/app/website \
    --socket :8000 \
    --socket-timeout 1800 \
    --uid 33 \
    --gid 33 \
    --threads 5 \
    --processes 5 \
    --module thaliawebsite.wsgi:application \
    --harakiri 1800 \
    --master \
    --max-requests 5000 \
    --vacuum \
    --limit-post 0 \
    --post-buffering 16384 \
    --thunder-lock \
    --logto '/concrexit/log/uwsgi.log'
