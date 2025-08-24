.PHONY: help install test lint type-check run build up down clean logs

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости
	pip install -r requirements.txt

test: ## Запустить тесты
	python -m unittest discover -s . -p "test_*.py" -v

test-coverage: ## Запустить тесты с покрытием
	coverage run -m unittest discover -s . -p "test_*.py" -v
	coverage report
	coverage html

lint: ## Проверить код с flake8
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

type-check: ## Проверить типы с mypy
	mypy . --ignore-missing-imports

run: ## Запустить приложение локально
	streamlit run streamlit_app.py

build: ## Собрать Docker образ
	docker build -t resume-analyzer .

up: ## Запустить с Docker Compose
	docker-compose up -d

down: ## Остановить Docker Compose
	docker-compose down

clean: ## Очистить Docker образы и контейнеры
	docker system prune -f
	docker image prune -f

logs: ## Показать логи Docker Compose
	docker-compose logs -f

format: ## Форматировать код
	black .
	isort .

check-all: lint type-check test ## Запустить все проверки
