COMPOSE := $(shell which docker-compose)
ifeq ($(COMPOSE),)
	COMPOSE := docker compose
endif

COMPOSE_FILE := "docker-compose.dev.yml"
COMPOSE_CONTAINER_NAME := "peam_backend"

POSTGRES_COMPOSE_VOLUME := "peam-backend_local_postgres_data"
POSTGRES_COMPOSE_SERVICE := "postgres"

# Building and running
.PHONY: detached
detached:
	${COMPOSE} -f ${COMPOSE_FILE} up -d

.PHONY: run
run:
	${COMPOSE} -f ${COMPOSE_FILE} up

.PHONY: build
build:
	${COMPOSE} -f ${COMPOSE_FILE} build

.PHONY: stop
stop:
	${COMPOSE} -f ${COMPOSE_FILE} down

.PHONY: db
db:
	${COMPOSE} -f ${COMPOSE_FILE} up -d ${POSTGRES_COMPOSE_SERVICE}


# Utilities
.PHONY: test
test:
	${COMPOSE} -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} /bin/bash -c "export DJANGO_SETTINGS_MODULE=core.settings.test && \
	pytest src"

.PHONY: format
format:
	${COMPOSE} -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} black .

.PHONY: lint
lint:
	${COMPOSE} -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} flake8 .

.PHONY: migration
migration:
	${COMPOSE} -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} python src/manage.py makemigrations

.PHONY: migrate
migrate:
	${COMPOSE} -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} python src/manage.py migrate

.PHONY: prune
prune: stop
	docker volume rm ${POSTGRES_COMPOSE_VOLUME}


# Ease of usage
.PHONY: shell
shell:
	${COMPOSE} -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} python src/manage.py shell

.PHONY: bash
bash:
	${COMPOSE} -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} /bin/bash

.PHONY: fmtlint
fmtlint:
	${COMPOSE} -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} black . && flake8 .

.PHONY: create-admin-user
create-admin-user:
	${COMPOSE} -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} python src/manage.py create_admin_user \
	--noinput \
	--username admin \
	--password admin \
	--email admin@hotmail.com

.PHONY: create-db
create-db: stop prune db migrate

.PHONY: local-create-db
local-create-db: stop prune db
	echo "Waiting for db..."
	sleep 5
	python src/manage.py makemigrations
	python src/manage.py migrate
	python src/manage.py setup_site
	python src/manage.py create_admin_user \
	--noinput \
	--username admin \
	--password admin \
	--email admin@hotmail.com
