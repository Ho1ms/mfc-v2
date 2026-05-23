DC := docker compose

.DEFAULT_GOAL := help

help: ## Показать список целей
	@awk 'BEGIN{FS=":.*##"; printf "\nЦели:\n"} /^[a-zA-Z_-]+:.*?##/{printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.env: .env.example ## Создать .env из .env.example, если его ещё нет
	@if [ ! -f .env ]; then cp .env.example .env; echo "→ создан .env из .env.example (подправьте секреты при необходимости)"; fi

init: .env ## Подготовить локальное окружение (.env)

build: .env ## Сборка всех docker-образов
	$(DC) build

up: .env ## Запуск всего стека в фоне
	$(DC) up -d

up-fg: .env ## Запуск всего стека в foreground (логи в консоль)
	$(DC) up

down: ## Остановка стека
	$(DC) down

restart: ## Перезапуск (down + up -d)
	$(DC) down
	$(DC) up -d

logs: ## Логи всех сервисов
	$(DC) logs -f --tail=200

logs-backend: ## Логи только backend
	$(DC) logs -f --tail=200 backend

logs-worker: ## Логи только worker
	$(DC) logs -f --tail=200 worker

logs-bot: ## Логи только bot
	$(DC) logs -f --tail=200 bot

ps: ## Статус контейнеров
	$(DC) ps

migrate: ## Применить миграции БД (Alembic)
	$(DC) exec backend alembic upgrade head

makemigration: ## Сгенерировать новую миграцию (m="название")
	$(DC) exec backend alembic revision --autogenerate -m "$(m)"

downgrade: ## Откатить одну миграцию
	$(DC) exec backend alembic downgrade -1

seed: ## Наполнение БД демо-данными (admin/employee, формы, FAQ)
	$(DC) exec backend python -m app.db.seed

bot: ## Перезапустить только бот
	$(DC) up -d --build bot

test: ## Запуск тестов бэкенда
	$(DC) exec backend pytest -q

lint: ## Линт (ruff)
	$(DC) exec backend ruff check .

fmt: ## Форматирование (ruff format)
	$(DC) exec backend ruff format .

shell: ## Shell в контейнере backend
	$(DC) exec backend bash

psql: ## psql в контейнере db
	$(DC) exec db psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

redis-cli: ## redis-cli в контейнере redis
	$(DC) exec redis redis-cli

clean: ## Удалить контейнеры И ТОМА (БД, файлы) — нужно подтверждение
	@read -p "Это удалит все данные (БД, файлы, redis). Продолжить? [y/N] " ans && [ "$$ans" = "y" ] || (echo "отмена" && exit 1)
	$(DC) down -v

.PHONY: help init build up up-fg down restart logs logs-backend logs-worker logs-bot ps \
        migrate makemigration downgrade seed bot test lint fmt shell psql redis-cli clean
