import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from parsers.models_parser import ModelsParser
from parsers.teachers_parser import TeachersParser
from parsers.partners_parser import PartnersParser

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ModelsTelegramBot:
    def __init__(self, token):
        self.application = Application.builder().token(token).build()

        # Инициализация парсеров
        self.models_parser = ModelsParser()
        self.teachers_parser = TeachersParser()
        self.partners_parser = PartnersParser()

        # Кэши для данных
        self.models_cache = []
        self.teachers_cache = []
        self.partners_cache = []

        # Регистрация обработчиков команд
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("models", self.models_command))
        self.application.add_handler(CommandHandler("teachers", self.teachers_command))
        self.application.add_handler(CommandHandler("partners", self.partners_command))
        self.application.add_handler(CallbackQueryHandler(self.model_detail, pattern='^model_'))
        self.application.add_handler(CallbackQueryHandler(self.photo_navigation, pattern='^photo_(prev|next)_'))
        self.application.add_handler(CallbackQueryHandler(self.back_to_models, pattern='^back_to_models$'))
        self.application.add_handler(CallbackQueryHandler(self.back_to_main, pattern='^back_to_main$'))
        self.application.add_handler(CallbackQueryHandler(self.handle_pagination, pattern='^page_'))
        self.application.add_handler(CallbackQueryHandler(self.handle_filter, pattern='^filter_'))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /start"""
        welcome_text = (
            "Добро пожаловать в бот модельного агентства ARModels!\n\n"
            "📋 <b>Доступные команды:</b>\n"
            "• /models — Список всех моделей\n"
            "• /teachers — Список учителей\n"
            "• /partners — Список партнеров\n\n"
            "Выберите нужный раздел для просмотра информации."
        )
        await update.message.reply_text(welcome_text, parse_mode='HTML')

        # Очищаем предыдущие данные
        context.user_data.clear()

    async def models_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /models"""
        # Удаляем предыдущее сообщение, если оно есть
        await self.delete_previous_message(context)

        # Устанавливаем параметры по умолчанию
        context.user_data['current_page'] = 0
        context.user_data['current_filter'] = 'all'

        # Показываем список моделей
        await self.list_models(update, context, page=0, filter_type="all")

    async def teachers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /teachers"""
        # Удаляем предыдущее сообщение, если оно есть
        await self.delete_previous_message(context)

        keyboard = [[InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = await update.message.reply_text(
            "👨‍🏫 <b>Раздел учителей</b>\n\n"
            "Функционал находится в разработке.\n"
            "Скоро здесь будет список всех учителей агентства!",
            parse_mode='HTML',
            reply_markup=reply_markup
        )

        # Сохраняем ID сообщения для последующего удаления
        context.user_data['last_message_id'] = message.message_id

    async def partners_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /partners"""
        # Удаляем предыдущее сообщение, если оно есть
        await self.delete_previous_message(context)

        keyboard = [[InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = await update.message.reply_text(
            "🤝 <b>Раздел партнеров</b>\n\n"
            "Функционал находится в разработке.\n"
            "Скоро здесь будет список всех партнеров агентства!",
            parse_mode='HTML',
            reply_markup=reply_markup
        )

        # Сохраняем ID сообщения для последующего удаления
        context.user_data['last_message_id'] = message.message_id

    async def list_models(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0, filter_type: str = "all"):
        """Обрабатывает команду /models, парсит список моделей и выводит его с пагинацией и фильтрами."""
        try:
            # Сохраняем chat_id для удаления сообщений
            if hasattr(update, 'message') and update.message:
                context.user_data['chat_id'] = update.message.chat_id
            elif hasattr(update, 'callback_query') and update.callback_query:
                context.user_data['chat_id'] = update.callback_query.message.chat_id

            # Сохраняем текущую страницу и фильтр в контексте
            context.user_data['current_page'] = page
            context.user_data['current_filter'] = filter_type

            # Загружаем модели, если они еще не загружены
            if not self.models_cache:
                models = self.models_parser.parse_list()
                self.models_cache = models
            else:
                models = self.models_cache

            if not models:
                message = 'Не удалось загрузить список моделей. Попробуйте позже.'
                sent_message = await self.send_message(update, message)
                if sent_message:
                    context.user_data['last_message_id'] = sent_message.message_id
                return

            # Применяем фильтр
            filtered_models = self.apply_filter(models, filter_type)

            # Настройки пагинации
            models_per_page = 6
            total_pages = (len(filtered_models) + models_per_page - 1) // models_per_page
            start_idx = page * models_per_page
            end_idx = min(start_idx + models_per_page, len(filtered_models))
            current_models = filtered_models[start_idx:end_idx]

            # Создаем сообщение
            filter_name = self.get_filter_name(filter_type)
            message = f"📋 <b>Модели {filter_name}</b>\n\n"
            message += f"Показаны модели {start_idx + 1}-{end_idx} из {len(filtered_models)}\n\n"

            # Создаем клавиатуру
            keyboard = []

            # Добавляем модели текущей страницы
            for idx, model in enumerate(current_models):
                actual_idx = models.index(model)  # Получаем реальный индекс в основном списке
                keyboard.append([InlineKeyboardButton(
                    f"👤 {model['name']}",
                    callback_data=f"model_{actual_idx}"
                )])

            # Добавляем кнопки навигации и фильтров
            nav_row = []

            if page > 0:
                nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"page_{page-1}_filter_{filter_type}"))

            nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="page_counter"))

            if page < total_pages - 1:
                nav_row.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"page_{page+1}_filter_{filter_type}"))

            if nav_row:
                keyboard.append(nav_row)

            # Добавляем кнопки фильтров
            filter_row = []
            filters = [
                ("all", "Все"),
                ("male", "Юноши"),
                ("female", "Девушки"),
                ("first_course", "1 курс"),
                ("second_course", "2 курс"),
                ("third_course", "3 курс"),
                ("fourth_course", "4 курс")
            ]

            for filter_key, filter_label in filters:
                if filter_key != filter_type:
                    filter_row.append(InlineKeyboardButton(
                        filter_label,
                        callback_data=f"filter_{filter_key}_page_0"
                    ))

            if filter_row:
                # Разбиваем фильтры на строки по 3 кнопки
                for i in range(0, len(filter_row), 3):
                    keyboard.append(filter_row[i:i+3])

            # Добавляем кнопку "Вернуться в главное меню" в конце
            keyboard.append([InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            sent_message = await self.send_message(update, message, reply_markup)
            if sent_message:
                context.user_data['last_message_id'] = sent_message.message_id

        except Exception as e:
            logger.error(f"Ошибка при получении списка моделей: {e}")
            await self.send_message(update, 'Произошла ошибка при загрузке списка моделей. Попробуйте позже.')

    def apply_filter(self, models, filter_type):
        """Применяет фильтр к списку моделей"""
        if filter_type == "all":
            return models
        elif filter_type in ["male", "female"]:
            # Фильтруем по полу на основе данных из HTML
            return [model for model in models if model.get('gender') == filter_type]
        elif filter_type.endswith("_course"):
            # Фильтруем по курсу на основе данных из HTML
            return [model for model in models if model.get('course_type') == filter_type]
        return models

    def get_filter_name(self, filter_type):
        """Возвращает читаемое название фильтра"""
        filter_names = {
            "all": "(все модели)",
            "male": "(юноши)",
            "female": "(девушки)",
            "first_course": "(1 курс)",
            "second_course": "(2 курс)",
            "third_course": "(3 курс)",
            "fourth_course": "(4 курс)"
        }
        return filter_names.get(filter_type, "")

    async def send_message(self, update, text, reply_markup=None):
        """Универсальный метод отправки сообщений"""
        if hasattr(update, 'message') and update.message:
            message = await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
            # Сохраняем ID сообщения для последующего удаления
            if hasattr(update, 'message') and hasattr(update.message, '_bot'):
                # Получаем context из update
                context = None
                if hasattr(update, '_bot') and hasattr(update._bot, '_context'):
                    context = update._bot._context
                if context:
                    context.user_data['last_message_id'] = message.message_id
            return message
        elif hasattr(update, 'callback_query') and update.callback_query:
            message = await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
            return message

    async def delete_previous_message(self, context):
        """Удаляет предыдущее сообщение, если оно есть"""
        last_message_id = context.user_data.get('last_message_id')
        if last_message_id:
            try:
                await context.bot.delete_message(
                    chat_id=context.user_data.get('chat_id'),
                    message_id=last_message_id
                )
            except Exception as e:
                # Игнорируем ошибки удаления (сообщение могло быть уже удалено)
                logger.debug(f"Не удалось удалить сообщение {last_message_id}: {e}")
            finally:
                # Очищаем ID в любом случае
                context.user_data.pop('last_message_id', None)

    async def model_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает нажатие на кнопку модели, парсит и показывает детали."""
        query = update.callback_query
        await query.answer()

        model_idx = int(query.data.replace('model_', ''))

        if model_idx < 0 or model_idx >= len(self.models_cache):
            await query.edit_message_text(text='Ошибка: модель не найдена.')
            return

        model_url = self.models_cache[model_idx]['url']

        try:
            model_info = self.models_parser.parse_detail(model_url)

            if not model_info:
                await query.edit_message_text(text='Не удалось загрузить информацию о модели.')
                return

            # Удаляем сообщение со списком моделей
            await query.delete_message()

            # Сохраняем информацию о модели в контексте для навигации по фото
            # (предыдущие параметры страницы и фильтра остаются сохраненными)
            context.user_data['current_model'] = model_info
            context.user_data['current_photo_idx'] = 0
            context.user_data['message_id'] = None  # Сбрасываем ID сообщения

            # Показываем первое фото с кнопками навигации
            await self.show_photo_with_navigation(query, context, model_info, 0)

        except Exception as e:
            logger.error(f"Ошибка при загрузке деталей модели: {e}")
            await query.edit_message_text(text='Не удалось загрузить информацию о модели.')

    async def show_photo_with_navigation(self, query, context: ContextTypes.DEFAULT_TYPE, model_info, photo_idx):
        """Показывает фото с кнопками навигации"""
        from telegram import InputMediaPhoto

        photos = model_info['photos']

        if not photos:
            # Если нет фото, показываем только текст
            message_text = self.format_model_text(model_info)
            await query.edit_message_text(text=message_text, parse_mode='HTML')
            return

        # Форматируем текст сообщения
        message_text = self.format_model_text(model_info)

        # Создаем кнопки навигации
        keyboard = []

        # Кнопка "Назад к списку моделей"
        keyboard.append([InlineKeyboardButton("⬅️ Назад к списку моделей", callback_data="back_to_models")])

        if len(photos) > 1:
            row = []
            if photo_idx > 0:
                row.append(InlineKeyboardButton("⬅️ Предыдущая", callback_data=f"photo_prev_{photo_idx}"))
            row.append(InlineKeyboardButton(f"{photo_idx + 1}/{len(photos)}", callback_data="photo_counter"))
            if photo_idx < len(photos) - 1:
                row.append(InlineKeyboardButton("Следующая ➡️", callback_data=f"photo_next_{photo_idx}"))
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Для первого показа отправляем новое фото
        if not context.user_data.get('message_id'):
            message = await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=photos[photo_idx],
                caption=message_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            context.user_data['message_id'] = message.message_id
        else:
            # Для последующих - редактируем существующее фото
            media = InputMediaPhoto(media=photos[photo_idx], caption=message_text, parse_mode='HTML')
            await context.bot.edit_message_media(
                chat_id=query.message.chat_id,
                message_id=context.user_data['message_id'],
                media=media,
                reply_markup=reply_markup
            )

    async def photo_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает навигацию по фото"""
        query = update.callback_query
        await query.answer()

        model_info = context.user_data.get('current_model')
        if not model_info:
            await query.edit_message_text(text='Информация о модели не найдена. Попробуйте выбрать модель заново.')
            return

        current_idx = context.user_data.get('current_photo_idx', 0)
        photos = model_info['photos']

        if query.data.startswith('photo_prev_'):
            new_idx = max(0, current_idx - 1)
        elif query.data.startswith('photo_next_'):
            new_idx = min(len(photos) - 1, current_idx + 1)
        else:
            return  # Неизвестная команда

        context.user_data['current_photo_idx'] = new_idx

        # Обновляем фото без удаления сообщения
        await self.show_photo_with_navigation(query, context, model_info, new_idx)

    async def back_to_models(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает возврат к списку всех моделей"""
        query = update.callback_query
        await query.answer()

        # Удаляем текущее сообщение с моделью
        await query.delete_message()

        # Восстанавливаем сохраненные параметры страницы и фильтра
        current_page = context.user_data.get('current_page', 0)
        current_filter = context.user_data.get('current_filter', 'all')

        # Очищаем данные о текущей модели, но сохраняем параметры страницы
        context.user_data.pop('current_model', None)
        context.user_data.pop('current_photo_idx', None)
        context.user_data.pop('message_id', None)

        # Показываем список моделей с сохраненными параметрами
        await self.list_models(update, context, page=current_page, filter_type=current_filter)

    async def back_to_main(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает возврат в главное меню"""
        query = update.callback_query
        await query.answer()

        # Удаляем текущее сообщение
        await query.delete_message()

        # Очищаем все данные пользователя
        context.user_data.clear()

        # Показываем главное меню
        welcome_text = (
            "Добро пожаловать в бот модельного агентства ARModels!\n\n"
            "📋 <b>Доступные команды:</b>\n"
            "• /models — Список всех моделей\n"
            "• /teachers — Список учителей\n"
            "• /partners — Список партнеров\n\n"
            "Выберите нужный раздел для просмотра информации."
        )
        message = await query.message.reply_text(welcome_text, parse_mode='HTML')

        # Сохраняем ID сообщения для последующего удаления
        context.user_data['last_message_id'] = message.message_id
        context.user_data['chat_id'] = query.message.chat_id

    async def handle_pagination(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает пагинацию списка моделей"""
        query = update.callback_query
        await query.answer()

        # Парсим callback_data: page_{page_num}_filter_{filter_type}
        data = query.data

        if data.startswith('page_') and '_filter_' in data:
            # Находим позицию "_filter_"
            filter_pos = data.find('_filter_')
            page_str = data[5:filter_pos]  # Берем часть между "page_" и "_filter_"
            filter_type = data[filter_pos + 8:]  # Берем все после "_filter_"

            try:
                page = int(page_str)

                # Удаляем старое сообщение
                await query.delete_message()

                # Показываем новую страницу
                await self.list_models(update, context, page=page, filter_type=filter_type)
            except ValueError:
                await query.edit_message_text(text='Ошибка обработки запроса пагинации.')
        else:
            await query.edit_message_text(text='Ошибка: неизвестный формат запроса пагинации.')

    async def handle_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает применение фильтров"""
        query = update.callback_query
        await query.answer()

        # Парсим callback_data: filter_{filter_type}_page_{page}
        data = query.data

        if data.startswith('filter_') and '_page_' in data:
            # Находим позицию "_page_"
            page_pos = data.find('_page_')
            filter_type = data[7:page_pos]  # Убираем "filter_" в начале
            page_str = data[page_pos + 6:]  # Берем все после "_page_"

            try:
                page = int(page_str)

                # Удаляем старое сообщение
                await query.delete_message()

                # Показываем отфильтрованный список
                await self.list_models(update, context, page=page, filter_type=filter_type)
            except ValueError:
                await query.edit_message_text(text='Ошибка обработки запроса фильтрации.')
        else:
            await query.edit_message_text(text='Ошибка: неизвестный формат запроса фильтрации.')

    def format_model_text(self, model_info):
        """Форматирует текст информации о модели"""
        message_text = f"<b>{model_info['name']}</b>\n\n"

        if model_info['parameters']:
            hobbies_text = None
            for key, value in model_info['parameters'].items():
                if key == 'Увлечения и хобби':
                    # Сохраняем увлечения для отдельного вывода
                    hobbies_text = value
                else:
                    message_text += f"• {key}: {value}\n"

            # Добавляем увлечения и хобби в конце, если они есть
            if hobbies_text:
                message_text += f"\n{hobbies_text}\n"

        message_text += f'\n<a href="{model_info["url"]}">Ссылка на портфолио</a>'
        return message_text

    def run(self):
        """Запускает бота"""
        self.application.run_polling()

if __name__ == '__main__':
    # Токен бота берется из переменной окружения TELEGRAM_BOT_TOKEN
    import os
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

    if not BOT_TOKEN:
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN не найден!")
        print("📝 Создайте .env файл на основе .env.example")
        print("🔗 Получите токен у @BotFather в Telegram")
        exit(1)

    print("🤖 Запуск ARModels Telegram Bot...")
    bot = ModelsTelegramBot(BOT_TOKEN)
    bot.run()