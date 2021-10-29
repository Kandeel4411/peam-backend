#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset


cd src
echo "Applying database migrations..."
python manage.py migrate
echo "Configuring site domain..."
python manage.py setup_site
echo "Running..."
python manage.py runserver 0.0.0.0:8000
