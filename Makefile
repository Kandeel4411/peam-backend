DOCKER_COMPOSE := "docker-compose.dev.yml"
CONTAINER_NAME := "peam_backend"

# Building and running
.PHONY: detached
detached:
	docker-compose -f ${DOCKER_COMPOSE} up -d

.PHONY: run
run:
	docker-compose -f ${DOCKER_COMPOSE} up

.PHONY: build
build:
	docker-compose -f ${DOCKER_COMPOSE} build

.PHONY: stop
stop:
	docker-compose -f ${DOCKER_COMPOSE} down

.PHONY: db
db:
	docker-compose -f ${DOCKER_COMPOSE} up -d postgres


# Utilities
.PHONY: test
test:
	docker-compose -f ${DOCKER_COMPOSE} run ${CONTAINER_NAME} /bin/bash -c "export DJANGO_SETTINGS_MODULE=core.settings.test && \
	python src/manage.py test"

.PHONY: lint
lint:
	docker-compose -f ${DOCKER_COMPOSE} run ${CONTAINER_NAME} flake8 .

.PHONY: migration
migration:
	docker-compose -f ${DOCKER_COMPOSE} run ${CONTAINER_NAME} python src/manage.py makemigrations

.PHONY: migrate
migrate:
	docker-compose -f ${DOCKER_COMPOSE} run ${CONTAINER_NAME} python src/manage.py migrate


# Ease of usage
.PHONY: shell
shell:
	docker-compose -f ${DOCKER_COMPOSE} run ${CONTAINER_NAME} python src/manage.py shell

.PHONY: bash
bash:
	docker-compose -f ${DOCKER_COMPOSE} run ${CONTAINER_NAME} /bin/bash
