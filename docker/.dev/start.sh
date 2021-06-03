#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset


cd src
python manage.py collectstatic --no-input
python manage.py runserver 0.0.0.0:8000
