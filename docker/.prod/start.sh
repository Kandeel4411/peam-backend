#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset


cd src

echo "Collecting static files..."
python manage.py collectstatic --no-input
echo "Applying database migrations..."
python manage.py migrate
echo "Configuring site domain..."
python manage.py setup_site
echo "Running..."
gunicorn core.wsgi --config gunicorn_config.py
