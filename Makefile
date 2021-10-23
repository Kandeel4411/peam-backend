COMPOSE_FILE := "docker-compose.dev.yml"
COMPOSE_CONTAINER_NAME := "peam_backend"

POSTGRES_COMPOSE_VOLUME := "peam-backend_local_postgres_data"
POSTGRES_COMPOSE_SERVICE := "postgres"

# Building and running
.PHONY: detached
detached:
	docker-compose -f ${COMPOSE_FILE} up -d

.PHONY: run
run:
	docker-compose -f ${COMPOSE_FILE} up

.PHONY: build
build:
	docker-compose -f ${COMPOSE_FILE} build

.PHONY: stop
stop:
	docker-compose -f ${COMPOSE_FILE} down

.PHONY: db
db:
	docker-compose -f ${COMPOSE_FILE} up -d ${POSTGRES_COMPOSE_SERVICE}


# Utilities
.PHONY: test
test:
	docker-compose -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} /bin/bash -c "export DJANGO_SETTINGS_MODULE=core.settings.test && \
	pytest src"

.PHONY: format
format:
	docker-compose -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} black .

.PHONY: lint
lint:
	docker-compose -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} flake8 .

.PHONY: migration
migration:
	docker-compose -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} python src/manage.py makemigrations

.PHONY: migrate
migrate:
	docker-compose -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} python src/manage.py migrate

.PHONY: prune
prune: stop
	docker volume rm ${POSTGRES_COMPOSE_VOLUME}


# Ease of usage
.PHONY: shell
shell:
	docker-compose -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} python src/manage.py shell

.PHONY: bash
bash:
	docker-compose -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} /bin/bash

.PHONY: fmtlint
fmtlint:
	docker-compose -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} black . && flake8 .

.PHONY: create-admin-user
create-admin-user:
	docker-compose -f ${COMPOSE_FILE} run ${COMPOSE_CONTAINER_NAME} python src/manage.py create_admin_user \
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
