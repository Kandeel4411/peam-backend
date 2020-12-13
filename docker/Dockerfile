FROM python:3.8-slim-buster as base

RUN apt-get update

ENV PYTHONFAULTHANDLER 1
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_BINARY psycopg2

# --home DIR                Home directory
# --gid GRP                 Add user to existing group
# --system                  Create a system user
# --uid UID                 User id
# --shell SHELL             Login shell
# --disabled-login          Don't assign a password
# --no-create-home          Don't create home directory
RUN adduser --system \
    --disabled-password \
    --no-create-home \
    --shell /bin/false \
    --uid 3000 \
    newuser



########################################
#  Image for main project dependencies #
########################################
FROM base as dependencies

# psycopg2 building requirements
RUN apt-get install -y --no-install-recommends libpq-dev gcc python3-dev
# Error checking for psycopg2
RUN pg_config --version

RUN python3 -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install -U pip
# Last known working version
RUN pip install poetry

COPY poetry.lock pyproject.toml ./

RUN poetry config virtualenvs.create false \
    && poetry export -f requirements.txt \
    | pip install -r /dev/stdin  \
    && poetry debug


#############################################
# Helper image for development dependencies #
#############################################
FROM dependencies as dev-dependencies
RUN poetry export -f requirements.txt --dev \
    | pip install -r /dev/stdin  \
    && poetry debug




####################
#  Final dev image #
####################
FROM base as dev

# Runtime dependency requirement for psycop2
RUN apt-get install -y --no-install-recommends libpq5
RUN apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*

# copy installed deps from dev-dependencies image
COPY --from=dev-dependencies /opt/venv /opt/venv

# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000
WORKDIR /app
COPY . /app

RUN chmod +x docker/entrypoint.sh
RUN chmod +x docker/.dev/start.sh

RUN chown -R newuser /app
USER newuser

ENTRYPOINT ["./docker/entrypoint.sh"]



#####################
#  Final prod image #
#####################
FROM base as prod

# Runtime dependency requirement for psycop2
RUN apt-get install -y --no-install-recommends libpq5
RUN apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*

# copy installed deps from dependencies image
COPY --from=dependencies /opt/venv /opt/venv

# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000
WORKDIR /app
COPY . /app

RUN chmod +x docker/entrypoint.sh
RUN chmod +x docker/.prod/start.sh

RUN chown -R newuser /app
USER newuser

ENTRYPOINT ["./docker/entrypoint.sh"]
