.PHONY: help install run clean test

help: ## Показать эту справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install: ## Установить зависимости
	@echo "📦 Установка зависимостей..."
	pip install -r requirements.txt

setup: ## Настроить проект (создать .env файл)
	@echo "⚙️  Настройка проекта..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Создан .env файл. Отредактируйте его и добавьте токен бота."; \
	else \
		echo "ℹ️  .env файл уже существует."; \
	fi

run: ## Запустить бота
	@echo "🤖 Запуск бота..."
	python run.py

run-direct: ## Запустить бота напрямую (без .env)
	@echo "🤖 Запуск бота напрямую..."
	python armodels_bot.py

clean: ## Очистить кэш и временные файлы
	@echo "🧹 Очистка..."
	rm -rf __pycache__
	rm -rf *.pyc
	rm -rf .pytest_cache
	rm -rf .coverage

test: ## Запустить тесты
	@echo "🧪 Запуск тестов..."
	python -m pytest

lint: ## Проверить код на ошибки
	@echo "🔍 Проверка кода..."
	python -m flake8 armodels_bot.py || echo "flake8 не установлен, пропускаем проверку"

format: ## Форматировать код
	@echo "💅 Форматирование кода..."
	python -m black armodels_bot.py || echo "black не установлен, пропускаем форматирование"

deps: ## Показать зависимости проекта
	@echo "📋 Зависимости проекта:"
	@cat requirements.txt

env: ## Показать переменные окружения
	@echo "🔐 Переменные окружения:"
	@if [ -f .env ]; then \
		grep -v '^#' .env | grep -v '^$$'; \
	else \
		echo "❌ .env файл не найден. Создайте его с помощью 'make setup'"; \
	fi

status: ## Показать статус проекта
	@echo "📊 Статус проекта:"
	@echo "Python version: $$(python --version)"
	@echo ".env файл: $$(if [ -f .env ]; then echo "✅ существует"; else echo "❌ отсутствует"; fi)"
	@echo "Зависимости: $$(if python -c "import telegram, bs4, requests" 2>/dev/null; then echo "✅ установлены"; else echo "❌ не установлены"; fi)"
	@echo "Токен бота: $$(if [ -n "$$TELEGRAM_BOT_TOKEN" ]; then echo "✅ задан"; else echo "❌ не задан"; fi)"

# По умолчанию показываем справку
.DEFAULT_GOAL := help