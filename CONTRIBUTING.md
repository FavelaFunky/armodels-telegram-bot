# 🤝 Вклад в проект ARModels Telegram Bot

Спасибо за интерес к проекту! Мы приветствуем вклад от сообщества. Вот как вы можете помочь:

## 🚀 Быстрый старт

1. **Fork** репозиторий
2. **Clone** ваш fork: `git clone https://github.com/your-username/armodels-bot.git`
3. **Создайте** feature branch: `git checkout -b feature/AmazingFeature`
4. **Установите** зависимости: `make install`
5. **Настройте** проект: `make setup`

## 🛠 Разработка

### Структура проекта

```
armodels-bot/
├── armodels_bot.py      # Основной код бота
├── run.py              # Скрипт запуска с загрузкой .env
├── requirements.txt     # Зависимости Python
├── .env.example         # Пример настроек
├── Makefile           # Команды для разработки
├── .github/           # CI/CD конфигурация
└── docs/              # Документация
```

### Полезные команды

```bash
make help          # Показать все доступные команды
make install       # Установить зависимости
make setup         # Настроить проект (.env файл)
make run           # Запустить бота
make test          # Запустить тесты
make clean         # Очистить кэш
make lint          # Проверить код на ошибки
```

## 📝 Как внести вклад

### 1. Создание Issue

- **🐛 Bug reports**: Описывайте проблему детально
- **💡 Feature requests**: Предлагайте новые возможности
- **❓ Questions**: Задавайте вопросы о проекте

### 2. Работа с кодом

#### Форматирование кода

```bash
make format  # Автоматическое форматирование
make lint    # Проверка на ошибки
```

#### Тестирование

```bash
make test    # Запуск тестов
```

### 3. Pull Request

1. **Обновите** ваш fork с основной веткой:

   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Создайте** feature branch:

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Внесите** изменения и **протестируйте**:

   ```bash
   make test
   make lint
   ```

4. **Зафиксируйте** изменения:

   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

5. **Отправьте** изменения:

   ```bash
   git push origin feature/your-feature-name
   ```

6. **Создайте** Pull Request на GitHub

## 📋 Соглашения

### Commit Messages

Используйте [Conventional Commits](https://www.conventionalcommits.org/):

```bash
feat: add new filter functionality
fix: resolve pagination callback parsing
docs: update README with new features
style: format code with black
refactor: improve error handling
test: add unit tests for parser
```

### Code Style

- **Python**: Следуйте PEP 8
- **Импорты**: Группируйте и сортируйте
- **Документация**: Добавляйте docstrings
- **Обработка ошибок**: Логируйте исключения

### Тестирование

- Добавляйте тесты для новых функций
- Проверяйте edge cases
- Тестируйте на разных версиях Python

## 🎯 Области для вклада

### 🔥 Высокий приоритет

- [ ] Добавление новых фильтров
- [ ] Улучшение производительности парсинга
- [ ] Кэширование данных
- [ ] Добавление unit тестов
- [ ] Docker поддержка

### 📈 Средний приоритет

- [ ] Локализация (многоязычность)
- [ ] Темы оформления
- [ ] Экспорт данных
- [ ] API для внешних интеграций

### 🌱 Низкий приоритет

- [ ] Веб-интерфейс для управления
- [ ] Мобильное приложение
- [ ] Аналитика использования

## 📞 Поддержка

Если у вас есть вопросы:

- 📧 Создайте Issue на GitHub
- 💬 Присоединяйтесь к обсуждениям
- 📖 Читайте документацию

## 📜 Лицензия

Внося вклад в проект, вы соглашаетесь с тем, что ваш код будет распространяться под лицензией MIT.

---

**Спасибо за ваш вклад! 🚀**
