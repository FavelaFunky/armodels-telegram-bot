import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from parsers.models_parser import ModelsParser
from parsers.teachers_parser import TeachersParser
from parsers.partners_parser import PartnersParser
from parsers.magazines_parser import MagazinesParser
from parsers.projects_parser import ProjectsParser

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
        self.magazines_parser = MagazinesParser()
        self.projects_parser = ProjectsParser()

        # Кэши для данных
        self.models_cache = []
        self.teachers_cache = []
        self.partners_cache = []
        self.magazines_cache = []
        self.projects_cache = {}

        # Регистрация обработчиков команд
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("models", self.models_command))
        self.application.add_handler(CommandHandler("teachers", self.teachers_command))
        self.application.add_handler(CommandHandler("partners", self.partners_command))
        self.application.add_handler(CommandHandler("magazines", self.magazines_command))
        self.application.add_handler(CommandHandler("projects", self.projects_command))
        self.application.add_handler(CallbackQueryHandler(self.model_detail, pattern='^model_'))
        self.application.add_handler(CallbackQueryHandler(self.teacher_detail, pattern='^teacher_'))
        self.application.add_handler(CallbackQueryHandler(self.partner_detail, pattern='^partner_'))
        self.application.add_handler(CallbackQueryHandler(self.project_detail, pattern='^project_'))
        self.application.add_handler(CallbackQueryHandler(self.project_category, pattern='^category_'))
        self.application.add_handler(CallbackQueryHandler(self.magazine_detail, pattern='^magazine_'))
        self.application.add_handler(CallbackQueryHandler(self.photo_navigation, pattern='^photo_(prev|next)_'))
        self.application.add_handler(CallbackQueryHandler(self.back_to_models, pattern='^back_to_models$'))
        self.application.add_handler(CallbackQueryHandler(self.back_to_teachers, pattern='^back_to_teachers$'))
        self.application.add_handler(CallbackQueryHandler(self.back_to_partners, pattern='^back_to_partners$'))
        self.application.add_handler(CallbackQueryHandler(self.back_to_magazines, pattern='^back_to_magazines$'))
        self.application.add_handler(CallbackQueryHandler(self.back_to_main, pattern='^back_to_main$'))
        self.application.add_handler(CallbackQueryHandler(self.back_to_projects, pattern='^back_to_projects$'))
        self.application.add_handler(CallbackQueryHandler(self.handle_pagination, pattern='^page_'))
        self.application.add_handler(CallbackQueryHandler(self.handle_filter, pattern='^filter_'))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /start"""
        welcome_text = (
            "Добро пожаловать в бот модельного агентства ARModels!\n\n"
            "📋 <b>Доступные команды:</b>\n"
            "• /models — Список всех моделей с фильтрами\n"
            "• /teachers — Список преподавателей\n"
            "• /partners — Список партнеров агентства\n"
            "• /projects — Проекты и мероприятия агентства\n"
            "• /magazines — Архив выпусков глянцевого журнала\n\n"
            "Выберите нужный раздел для просмотра информации.\n"
            "Все данные парсятся с официального сайта armodels.ru"
        )
        await update.message.reply_text(welcome_text, parse_mode='HTML')

        # Очищаем данные, но сохраняем приветственное сообщение
        context.user_data.pop('current_page', None)
        context.user_data.pop('current_filter', None)
        context.user_data.pop('current_model', None)

    async def models_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /models"""
        # Сохраняем ID команды пользователя для последующего удаления
        context.user_data['command_message_id'] = update.message.message_id

        # Устанавливаем параметры по умолчанию
        context.user_data['current_page'] = 0
        context.user_data['current_filter'] = 'all'

        # Показываем список моделей
        await self.list_models(update, context, page=0, filter_type="all")

    async def teachers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /teachers"""
        # Определяем chat_id в зависимости от типа update
        if hasattr(update, 'message') and update.message:
            chat_id = update.message.chat_id
            context.user_data['command_message_id'] = update.message.message_id
        elif hasattr(update, 'callback_query') and update.callback_query:
            chat_id = update.callback_query.message.chat_id
        else:
            return

        # Загружаем учителей, если они еще не загружены
        if not self.teachers_cache:
            teachers = self.teachers_parser.parse_list()
            self.teachers_cache = teachers
        else:
            teachers = self.teachers_cache

        if not teachers:
            keyboard = [[InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=chat_id,
                text="👨‍🏫 <b>Раздел учителей</b>\n\nНе удалось загрузить список учителей. Попробуйте позже.",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            return

        # Создаем сообщение со списком учителей
        message = "👨‍🏫 <b>Наши преподаватели</b>\n\n"
        message += f"Найдено {len(teachers)} преподавателей:\n\n"

        # Создаем клавиатуру
        keyboard = []

        for idx, teacher in enumerate(teachers):
            # Создаем кнопку с именем и специальностью
            button_text = f"👨‍🏫 {teacher['name']}"
            if teacher.get('specialty'):
                button_text += f" ({teacher['specialty']})"

            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"teacher_{idx}"
            )])

        # Добавляем кнопку "Вернуться в главное меню" в конце
        keyboard.append([InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    async def partners_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /partners"""
        # Определяем chat_id в зависимости от типа update
        if hasattr(update, 'message') and update.message:
            chat_id = update.message.chat_id
            context.user_data['command_message_id'] = update.message.message_id
        elif hasattr(update, 'callback_query') and update.callback_query:
            chat_id = update.callback_query.message.chat_id
        else:
            return

        # Загружаем партнеров, если они еще не загружены
        if not self.partners_cache:
            partners = self.partners_parser.parse_list()
            self.partners_cache = partners
        else:
            partners = self.partners_cache

        if not partners:
            keyboard = [[InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=chat_id,
                text="🤝 <b>Раздел партнеров</b>\n\nНе удалось загрузить список партнеров. Попробуйте позже.",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            return

        # Создаем сообщение со списком партнеров
        message = "🤝 <b>Наши партнеры</b>\n\n"
        message += f"Найдено {len(partners)} партнеров:\n\n"

        # Создаем клавиатуру
        keyboard = []

        for idx, partner in enumerate(partners):
            # Создаем кнопку с названием партнера
            button_text = f"🤝 {partner['name']}"

            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"partner_{idx}"
            )])

        # Добавляем кнопку "Вернуться в главное меню" в конце
        keyboard.append([InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    async def list_models(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0, filter_type: str = "all"):
        """Обрабатывает команду /models, парсит список моделей и выводит его с пагинацией и фильтрами."""
        try:
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
                await self.send_message(update, message)
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
            await self.send_message(update, message, reply_markup)

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
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            # Если update не содержит message или callback_query, получаем chat_id из контекста
            chat_id = None
            if hasattr(update, 'effective_chat'):
                chat_id = update.effective_chat.id
            elif hasattr(update, 'callback_query') and update.callback_query:
                chat_id = update.callback_query.message.chat_id

            if chat_id:
                from telegram.ext import ContextTypes
                # Получаем context из параметров (нужно будет передавать context в вызовы)
                # Пока что оставим как есть для обратной совместимости
                pass

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

    async def teacher_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает нажатие на кнопку учителя"""
        query = update.callback_query
        await query.answer()

        teacher_idx = int(query.data.replace('teacher_', ''))

        if teacher_idx < 0 or teacher_idx >= len(self.teachers_cache):
            await query.edit_message_text(text='Ошибка: учитель не найден.')
            return

        teacher = self.teachers_cache[teacher_idx]

        # Удаляем сообщение со списком учителей
        await query.delete_message()

        # Форматируем информацию об учителе
        message_text = f"👨‍🏫 <b>{teacher['name']}</b>\n\n"

        if teacher.get('specialty'):
            message_text += f"🎓 <b>Специальность:</b> {teacher['specialty']}\n\n"

        if teacher.get('photo'):
            # Если есть фото, отправляем его с подписью
            keyboard = [
                [InlineKeyboardButton("⬅️ Назад к списку учителей", callback_data="back_to_teachers")],
                [InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=teacher['photo'],
                caption=message_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        else:
            # Если нет фото, отправляем только текст
            keyboard = [
                [InlineKeyboardButton("⬅️ Назад к списку учителей", callback_data="back_to_teachers")],
                [InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )

    async def partner_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает нажатие на кнопку партнера"""
        query = update.callback_query
        await query.answer()

        partner_idx = int(query.data.replace('partner_', ''))

        if partner_idx < 0 or partner_idx >= len(self.partners_cache):
            await query.edit_message_text(text='Ошибка: партнер не найден.')
            return

        partner = self.partners_cache[partner_idx]

        # Удаляем сообщение со списком партнеров
        await query.delete_message()

        # Форматируем информацию о партнере
        message_text = f"🤝 <b>{partner['name']}</b>\n\n"

        if partner.get('website'):
            message_text += f"🌐 <b>Сайт:</b> {partner['website']}\n\n"

        if partner.get('logo'):
            # Если есть логотип, отправляем его с подписью
            keyboard = [
                [InlineKeyboardButton("⬅️ Назад к списку партнеров", callback_data="back_to_partners")],
                [InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=partner['logo'],
                caption=message_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        else:
            # Если нет логотипа, отправляем только текст
            keyboard = [
                [InlineKeyboardButton("⬅️ Назад к списку партнеров", callback_data="back_to_partners")],
                [InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )

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

        # Кнопка "Вернуться в главное меню" в конце
        keyboard.append([InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")])

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

    async def back_to_teachers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает возврат к списку учителей"""
        query = update.callback_query
        await query.answer()

        # Удаляем текущее сообщение с деталями учителя
        await query.delete_message()

        # Загружаем учителей, если они еще не загружены
        if not self.teachers_cache:
            teachers = self.teachers_parser.parse_list()
            self.teachers_cache = teachers
        else:
            teachers = self.teachers_cache

        if not teachers:
            keyboard = [[InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="👨‍🏫 <b>Раздел учителей</b>\n\nНе удалось загрузить список учителей. Попробуйте позже.",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            return

        # Создаем сообщение со списком учителей
        message = "👨‍🏫 <b>Наши преподаватели</b>\n\n"
        message += f"Найдено {len(teachers)} преподавателей:\n\n"

        # Создаем клавиатуру
        keyboard = []

        for idx, teacher in enumerate(teachers):
            # Создаем кнопку с именем и специальностью
            button_text = f"👨‍🏫 {teacher['name']}"
            if teacher.get('specialty'):
                button_text += f" ({teacher['specialty']})"

            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"teacher_{idx}"
            )])

        # Добавляем кнопку "Вернуться в главное меню" в конце
        keyboard.append([InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    async def back_to_partners(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает возврат к списку партнеров"""
        query = update.callback_query
        await query.answer()

        # Удаляем текущее сообщение с деталями партнера
        await query.delete_message()

        # Загружаем партнеров, если они еще не загружены
        if not self.partners_cache:
            partners = self.partners_parser.parse_list()
            self.partners_cache = partners
        else:
            partners = self.partners_cache

        if not partners:
            keyboard = [[InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="🤝 <b>Раздел партнеров</b>\n\nНе удалось загрузить список партнеров. Попробуйте позже.",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            return

        # Создаем сообщение со списком партнеров
        message = "🤝 <b>Наши партнеры</b>\n\n"
        message += f"Найдено {len(partners)} партнеров:\n\n"

        # Создаем клавиатуру
        keyboard = []

        for idx, partner in enumerate(partners):
            # Создаем кнопку с названием партнера
            button_text = f"🤝 {partner['name']}"

            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"partner_{idx}"
            )])

        # Добавляем кнопку "Вернуться в главное меню" в конце
        keyboard.append([InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    async def back_to_main(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает возврат в главное меню"""
        query = update.callback_query
        await query.answer()

        # Удаляем текущее сообщение (раздел моделей/учителей/партнеров)
        await query.delete_message()

        # Удаляем команду пользователя, если она сохранена
        command_message_id = context.user_data.get('command_message_id')
        chat_id = context.user_data.get('chat_id') or query.message.chat_id

        logger.info(f"back_to_main: command_message_id={command_message_id}, chat_id={chat_id}")

        if command_message_id:
            try:
                await context.bot.delete_message(
                    chat_id=chat_id,
                    message_id=command_message_id
                )
                logger.info(f"Команда пользователя удалена: message_id={command_message_id}")
            except Exception as e:
                logger.error(f"Не удалось удалить команду пользователя: {e}")

        # Очищаем данные
        context.user_data.pop('current_model', None)
        context.user_data.pop('current_photo_idx', None)
        context.user_data.pop('message_id', None)
        context.user_data.pop('current_page', None)
        context.user_data.pop('current_filter', None)
        context.user_data.pop('command_message_id', None)
        context.user_data.pop('chat_id', None)
        context.user_data.pop('projects_list_message_id', None)

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

    async def magazines_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /magazines"""
        # Определяем chat_id в зависимости от типа update
        if hasattr(update, 'message') and update.message:
            chat_id = update.message.chat_id
            context.user_data['command_message_id'] = update.message.message_id
        elif hasattr(update, 'callback_query') and update.callback_query:
            chat_id = update.callback_query.message.chat_id
        else:
            return

        # Загружаем журналы, если они еще не загружены
        if not self.magazines_cache:
            magazines = self.magazines_parser.parse_list()
            self.magazines_cache = magazines
        else:
            magazines = self.magazines_cache

        if not magazines:
            keyboard = [[InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=chat_id,
                text="📖 <b>Архив журнала</b>\n\nНе удалось загрузить список выпусков журнала. Попробуйте позже.",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            return

        # Создаем сообщение со списком журналов
        message = "📖 <b>Глянцевый журнал ARMODELS</b>\n\n"
        message += f"Найдено {len(magazines)} выпусков:\n\n"

        # Создаем клавиатуру
        keyboard = []

        for idx, magazine in enumerate(magazines):
            # Создаем кнопку только с номером выпуска
            button_text = f"📖 {magazine['issue_number']}"

            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"magazine_{idx}"
            )])

        # Добавляем кнопку "Вернуться в главное меню" в конце
        keyboard.append([InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    async def magazine_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает нажатие на кнопку выпуска журнала"""
        query = update.callback_query
        await query.answer()

        magazine_idx = int(query.data.replace('magazine_', ''))

        if magazine_idx < 0 or magazine_idx >= len(self.magazines_cache):
            await query.edit_message_text(text='Ошибка: выпуск журнала не найден.')
            return

        magazine = self.magazines_cache[magazine_idx]

        # Удаляем сообщение со списком журналов
        await query.delete_message()

        # Форматируем информацию о выпуске журнала
        message_text = f"📖 <b>{magazine['issue_number']}</b>\n\n"

        if magazine.get('release_date') and magazine['release_date'] != 'Не указана':
            message_text += f"📅 <b>Дата выхода:</b> в {magazine['release_date']}\n\n"

        message_text += "Воплощение элегантности, стиля и красоты в каждом выпуске!\n\n"

        # Создаем клавиатуру
        keyboard = []

        # Кнопка скачивания PDF, если есть ссылка
        if magazine.get('pdf_url'):
            keyboard.append([InlineKeyboardButton("⬇️ Скачать PDF", url=magazine['pdf_url'])])

        # Кнопки навигации
        keyboard.append([InlineKeyboardButton("⬅️ Назад к списку журналов", callback_data="back_to_magazines")])
        keyboard.append([InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Если есть изображение обложки, отправляем его с подписью
        if magazine.get('cover_image'):
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=magazine['cover_image'],
                caption=message_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        else:
            # Если нет изображения, отправляем только текст
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )

    async def back_to_magazines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает возврат к списку журналов"""
        query = update.callback_query
        await query.answer()

        # Удаляем текущее сообщение с деталями журнала
        await query.delete_message()

        # Загружаем журналы, если они еще не загружены
        if not self.magazines_cache:
            magazines = self.magazines_parser.parse_list()
            self.magazines_cache = magazines
        else:
            magazines = self.magazines_cache

        if not magazines:
            keyboard = [[InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="📖 <b>Архив журнала</b>\n\nНе удалось загрузить список выпусков журнала. Попробуйте позже.",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            return

        # Создаем сообщение со списком журналов
        message = "📖 <b>Глянцевый журнал ARMODELS</b>\n\n"
        message += f"Найдено {len(magazines)} выпусков:\n\n"

        # Создаем клавиатуру
        keyboard = []

        for idx, magazine in enumerate(magazines):
            # Создаем кнопку только с номером выпуска
            button_text = f"📖 {magazine['issue_number']}"

            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"magazine_{idx}"
            )])

        # Добавляем кнопку "Вернуться в главное меню" в конце
        keyboard.append([InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    async def projects_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /projects"""
        try:
            # Получаем доступные категории
            categories = self.projects_parser.get_categories()

            # Создаем клавиатуру с категориями
            keyboard = []

            # Кнопка "Все проекты"
            keyboard.append([InlineKeyboardButton("🎭 Все проекты", callback_data="category_all")])

            # Кнопки для каждой категории
            for category_code, category_name in categories.items():
                emoji = self._get_category_emoji(category_code)
                keyboard.append([InlineKeyboardButton(f"{emoji} {category_name}", callback_data=f"category_{category_code}")])

            # Кнопка "Вернуться в главное меню"
            keyboard.append([InlineKeyboardButton("🏠 Вернуться в главное меню", callback_data="back_to_main")])

            reply_markup = InlineKeyboardMarkup(keyboard)

            message_text = "🎭 <b>Проекты ARMODELS</b>\n\n"
            message_text += "Выберите категорию проектов или просмотрите все проекты:"

            # Определяем chat_id в зависимости от типа update
            if hasattr(update, 'message') and update.message:
                chat_id = update.message.chat_id
                # Сохраняем ID команды и chat_id для удаления команды
                context.user_data['command_message_id'] = update.message.message_id
                context.user_data['chat_id'] = chat_id
                logger.info(f"projects_command: Сохранен command_message_id={update.message.message_id}")
                await update.message.reply_text(
                    message_text,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            elif hasattr(update, 'callback_query') and update.callback_query:
                chat_id = update.callback_query.message.chat_id
                # Сохраняем chat_id для удаления команды (command_message_id уже должен быть сохранен)
                context.user_data['chat_id'] = chat_id
                existing_command_id = context.user_data.get('command_message_id')
                logger.info(f"projects_command (callback): chat_id={chat_id}, existing command_message_id={existing_command_id}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            else:
                return

        except Exception as e:
            logger.error(f"Ошибка при обработке команды /projects: {e}")
            # Определяем chat_id для отправки сообщения об ошибке
            if hasattr(update, 'message') and update.message:
                chat_id = update.message.chat_id
                await update.message.reply_text(
                    "❌ Произошла ошибка при загрузке проектов. Попробуйте позже."
                )
            elif hasattr(update, 'callback_query') and update.callback_query:
                chat_id = update.callback_query.message.chat_id
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Произошла ошибка при загрузке проектов. Попробуйте позже."
                )

    def _get_category_emoji(self, category_code: str) -> str:
        """Возвращает эмодзи для категории проекта"""
        emoji_map = {
            'photo-projects': '📸',
            'konkursi-krasoti': '👑',
            'fashion-shows': '👗',
            'advertising-shoots': '📹',
            'interview': '🎤'
        }

        # Если category_code пустой или None, возвращаем иконку по умолчанию
        if not category_code:
            return '🎭'

        return emoji_map.get(category_code, '🎭')

    async def project_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает выбор категории проектов"""
        query = update.callback_query
        await query.answer()

        # Сохраняем chat_id для удаления команды
        context.user_data['chat_id'] = query.message.chat_id

        category_code = query.data.replace('category_', '')

        try:
            # Определяем категорию для парсинга
            category = None if category_code == 'all' else category_code

            # Получаем проекты
            if category not in self.projects_cache:
                projects = self.projects_parser.parse_list(category)
                self.projects_cache[category] = projects
            else:
                projects = self.projects_cache[category]

            if not projects:
                await query.delete_message()
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="📭 В этой категории пока нет проектов.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад к категориям", callback_data="back_to_projects"),
                        InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")
                    ]])
                )
                return

            # Создаем сообщение со списком проектов
            category_name = "Все проекты" if category_code == 'all' else self.projects_parser.get_categories().get(category_code, category_code)

            # Получаем иконку для категории
            category_emoji = self._get_category_emoji(category_code)

            message_text = f"{category_emoji} <b>{category_name}</b>\n\n"
            message_text += f"Найдено {len(projects)} проектов:\n\n"

            # Создаем клавиатуру
            keyboard = []

            for idx, project in enumerate(projects):
                # Обрезаем название если оно слишком длинное
                title = project['title']
                if len(title) > 30:
                    title = title[:27] + "..."

                # Получаем иконку для проекта
                if category_code == 'all':
                    # Для общего списка используем иконку категории проекта
                    project_category = project.get('category')
                    if not project_category:
                        logger.warning(f"Проект '{title}' не имеет категории, используем по умолчанию")
                        project_category = ''
                    project_emoji = self._get_category_emoji(project_category)
                else:
                    # Для конкретной категории используем иконку этой категории
                    project_emoji = self._get_category_emoji(category_code)

                keyboard.append([InlineKeyboardButton(
                    f"{project_emoji} {title}",
                    callback_data=f"project_{category_code}_{idx}"
                )])

            # Кнопки навигации
            keyboard.append([
                InlineKeyboardButton("🔙 К категориям", callback_data="back_to_projects"),
                InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")
            ])

            reply_markup = InlineKeyboardMarkup(keyboard)

            # Удаляем старое сообщение и отправляем новое
            await query.delete_message()
            message = await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            # Сохраняем ID нового сообщения для возможного удаления
            context.user_data['projects_list_message_id'] = message.message_id

        except Exception as e:
            logger.error(f"Ошибка при обработке категории проектов {category_code}: {e}")
            await query.delete_message()
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ Произошла ошибка при загрузке проектов.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад к категориям", callback_data="back_to_projects"),
                    InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")
                ]])
            )

    async def project_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает просмотр деталей проекта"""
        query = update.callback_query
        await query.answer()

        # Сохраняем chat_id для удаления команды
        context.user_data['chat_id'] = query.message.chat_id

        # Удаляем сообщение со списком проектов, если оно есть
        projects_list_message_id = context.user_data.get('projects_list_message_id')
        if projects_list_message_id:
            try:
                await context.bot.delete_message(
                    chat_id=query.message.chat_id,
                    message_id=projects_list_message_id
                )
            except Exception as e:
                logger.debug(f"Не удалось удалить сообщение со списком проектов: {e}")
            finally:
                context.user_data.pop('projects_list_message_id', None)

        # Парсим callback_data: project_{category}_{index}
        parts = query.data.split('_')
        if len(parts) < 3:
            await query.delete_message()
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ Ошибка в данных проекта."
            )
            return

        category_code = parts[1]
        project_idx = int(parts[2])

        try:
            # Определяем категорию для получения данных
            category = None if category_code == 'all' else category_code

            # Получаем проекты из кэша
            if category not in self.projects_cache:
                projects = self.projects_parser.parse_list(category)
                self.projects_cache[category] = projects
            else:
                projects = self.projects_cache[category]

            if project_idx < 0 or project_idx >= len(projects):
                await query.delete_message()
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="❌ Проект не найден."
                )
                return

            project = projects[project_idx]

            # Получаем иконку для категории проекта
            project_category = project.get('category', '')
            category_emoji = self._get_category_emoji(project_category)

            # Форматируем информацию о проекте
            message_text = f"{category_emoji} <b>{project['title']}</b>\n\n"
            message_text += f"📂 <b>Категория:</b> {project['category_name']}\n\n"

            if project['description']:
                message_text += f"📝 <b>Описание:</b>\n{project['description']}\n\n"

            if project['detail_url']:
                message_text += f"🔗 <a href=\"{project['detail_url']}\">Подробнее на сайте</a>"

            # Кнопки навигации
            category_callback = "category_all" if category_code == 'all' else f"category_{category_code}"
            keyboard = [
                [InlineKeyboardButton("🔙 К списку проектов", callback_data=category_callback)],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Если есть изображение, отправляем его с подписью
            if project.get('image_url'):
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=project['image_url'],
                    caption=message_text,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            else:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=message_text,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )

        except Exception as e:
            logger.error(f"Ошибка при загрузке деталей проекта {project_idx}: {e}")
            category_callback = "category_all" if category_code == 'all' else f"category_{category_code}"
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ Произошла ошибка при загрузке информации о проекте.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data=category_callback),
                    InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")
                ]])
            )

    async def back_to_projects(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает возврат к категориям проектов"""
        query = update.callback_query
        await query.answer()

        # Удаляем текущее сообщение
        await query.delete_message()

        # Сохраняем chat_id для удаления команды
        context.user_data['chat_id'] = query.message.chat_id

        existing_command_id = context.user_data.get('command_message_id')
        logger.info(f"back_to_projects: existing command_message_id={existing_command_id}")

        # Показываем категории проектов
        await self.projects_command(update, context)

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