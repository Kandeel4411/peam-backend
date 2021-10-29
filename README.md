# Peam Backend

![CI](https://github.com/Kandeel4411/peam-backend/workflows/CI/badge.svg?branch=main)
[![Python: 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Generic badge](https://img.shields.io/badge/django-3.1.4-blue.svg)](https://shields.io/)
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
- Run `make run`
- Navigate to [http://localhost:8000/](http://localhost:8000/) to view the API documentation.
- **Optional**: Create a default `admin` user account by running `make create-admin-user` for the django admin panel.

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
  - Clone the following dependency repos for plagiarism detection.

  ```bash
  ## In project root directory... ##

  git -C src/plagiarism/vendor/ clone https://github.com/tree-sitter/tree-sitter-javascript
  git -C src/plagiarism/vendor/ clone https://github.com/tree-sitter/tree-sitter-python
  ```

  - Run the following command to compile the cloned languages

  ```bash
  ## In project root directory... ##
  poetry run python src/manage.py setup_plagiarism
  ```

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

If developing locally, you need to create a `.env.local.dev` file similar to [.env.local.dev.example](.env.local.dev.example) and overriding the default values appropriately.

```bash
## In project root directory... ##

# Run migrate to create db / apply migrations
poetry run python src/manage.py migrate

# Create a new admin user
poetry run python src/manage.py create_admin_user \
    --noinput \
    --username admin \
    --password admin \
    --email admin@hotmail.com

# Setup site domain and display
poetry run python src/manage.py setup_site

# Run local development server
poetry run python src/manage.py runserver

# Run tests
poetry run pytest src

# Run formatting and linting
poetry run black src
# the next line shouldn't output anything to the terminal if it passes
poetry run flake8 src

```

if you want to be able to reload server on any code changes without having to run `make build` every time then you could change the [docker-compose.dev.yml](docker-compose.dev.yml)'s `volume` section to the following instead:

```yaml
  volumes:
    # - .:/app       # Uncomment this line
    ...
```
