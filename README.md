# Peam Backend

![CI](https://github.com/Kandeel4411/peam-backend/workflows/CI/badge.svg?branch=main)
[![Python: 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Generic badge](https://img.shields.io/badge/django-3.2-blue.svg)](https://shields.io/)
[![Code-style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

Backend repository for the Peam app.

## Getting Started

- Clone the repo or click [here](https://github.com/Kandeel4411/Vscodescript/archive/master.zip) to download the zip file then extract it locally.

- Install Docker and ensure it is running.
  - [Docker Desktop for Mac and Windows](https://www.docker.com/products/docker-desktop)
  - [Docker Engine for Linux](https://docs.docker.com/install/linux/docker-ce/ubuntu/)
  - Additional step for Linux: install [docker compose](https://docs.docker.com/compose/install/#install-compose) as well.

- [Install Make](http://gnuwin32.sourceforge.net/packages/make.htm) if you're on Windows. OSX already has it installed. Linux will tell you how to install it (i.e., `sudo apt-get install make`)
- Run `make build`
- Run `make create-db`
- Run `make run`
- Navigate to [http://localhost:8000/](http://localhost:8000/) to view the API documentation.

## Development

- [Install Poetry](https://github.com/python-poetry/poetry) for managing dependencies or just use python's `pip`.
  - Poetry provides a custom installer that can be ran via

    ```bash
    curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
    ```

    Alternatively, poetry can be installed via pip/pip3 with `pip install --user poetry` or `pip3 install --user poetry`

    **Note:**
    if using an existing local virtual environment, to disable poetry's default `venv` creation run

      ```bash
      poetry config virtualenvs.create false
      ```

- Run `poetry install` to install dependencies locally. if you are encountering an error with psycopg2 during poetry installation, ensure postgreqsql is installed (macOS: `brew install postgresql`)

- Incase of any code changes, make sure to run the following commands to check linting and tests before committing

  ```bash
  ## In project root directory... ##

  # Rebuild docker image
  make build
  # Check tests
  make test
  # Format & check linting
  make fmtlint
  ```

  To view all available make commands. check [here](Makefile)

## Notes

If developing locally, you need to create a `.env.dev` file similar to [.env.dev.example](.env.dev.example) and overriding the default values appropriately.

```bash
## In project root directory... ##

# Run migrate to create db / apply migrations
poetry run python src/manage.py migrate

# Run local development server
poetry run python src/manage.py runserver

# Run tests
poetry run pytest src

# Run formatting and linting
poetry run black src
# the next line shouldn't output anything to the terminal if it passes
poetry run flake8 src

```

if you want to be able to reload server on any code changes without having to run `make build` everytime then you could change the [Makefile](Makefile)'s `COMPOSE_FILE` variable to the following instead:

```bash
COMPOSE_FILE := "docker-compose.dev.yml"
```
