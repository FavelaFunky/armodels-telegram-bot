#!/usr/bin/env python3
"""
Скрипт для запуска ARModels Telegram Bot
Загружает настройки из .env файла
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Проверяем наличие токена
token = os.getenv('TELEGRAM_BOT_TOKEN')
if not token:
    print("Ошибка: TELEGRAM_BOT_TOKEN не найден в .env файле")
    print("Создайте .env файл на основе .env.example и добавьте ваш токен")
    sys.exit(1)

# Импортируем и запускаем бота
try:
    from armodels_bot import ModelsTelegramBot

    print("Запуск ARModels Telegram Bot...")
    print(f"Токен бота: {token[:10]}...")

    bot = ModelsTelegramBot(token)
    bot.run()

except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Установите зависимости: pip install -r requirements.txt")
    print("Также установите python-dotenv: pip install python-dotenv")
    sys.exit(1)

except KeyboardInterrupt:
    print("\nБот остановлен пользователем")

except Exception as e:
    print(f"Ошибка запуска бота: {e}")
    sys.exit(1)