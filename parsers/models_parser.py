import logging
from typing import List, Dict, Optional
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

class ModelsParser(BaseParser):
    """Парсер для моделей с сайта armodels.ru"""

    def parse_list(self) -> List[Dict]:
        """
        Парсит список всех моделей с основной страницы

        Returns:
            Список словарей с информацией о моделях
        """
        try:
            soup = self.get_page_content('/public/models')

            models = []
            # Ищем все элементы с моделями
            model_items = soup.find_all('li', class_='grid-item')

            for item in model_items:
                # Ищем ссылку на портфолио
                portfolio_link = item.find('a', href=True, string='Портфолио')
                if not portfolio_link:
                    continue

                # Ищем имя модели (в span с определенными классами)
                name_span = item.find('span', class_=lambda x: x and 'text-white' in x and 'text-large' in x)
                if not name_span:
                    continue

                name = self.extract_text(name_span)
                profile_url = portfolio_link.get('href')

                # Извлекаем курс
                course_span = item.find('span', class_=lambda x: x and 'text-white' in x and 'text-medium' in x)
                course = self.extract_text(course_span)

                # Извлекаем пол из классов
                classes = item.get('class', [])
                gender = 'Не указан'
                if 'male' in classes:
                    gender = 'male'
                elif 'female' in classes:
                    gender = 'female'

                # Определяем курс по классам
                course_type = 'Не указан'
                if 'first_course' in classes:
                    course_type = 'first_course'
                elif 'second_course' in classes:
                    course_type = 'second_course'
                elif 'third_course' in classes:
                    course_type = 'third_course'
                elif 'fourth_course' in classes:
                    course_type = 'fourth_course'

                if profile_url and name:
                    if not profile_url.startswith('http'):
                        if profile_url.startswith('/public'):
                            # Убираем /public из ссылки для более короткого URL
                            profile_url = profile_url.replace('/public', '', 1)
                            profile_url = self.BASE_URL + profile_url
                        elif profile_url.startswith('/'):
                            profile_url = self.BASE_URL + profile_url
                        else:
                            profile_url = self.BASE_URL + '/' + profile_url

                    models.append({
                        'name': name,
                        'url': profile_url,
                        'course': course,
                        'gender': gender,
                        'course_type': course_type
                    })

            logger.info(f"Успешно спарсено {len(models)} моделей")
            return models

        except Exception as e:
            logger.error(f"Ошибка при парсинге списка моделей: {e}")
            return []

    def parse_detail(self, url: str) -> Optional[Dict]:
        """
        Парсит детальную информацию о конкретной модели

        Args:
            url: URL страницы модели

        Returns:
            Словарь с детальной информацией о модели или None при ошибке
        """
        try:
            soup = self.get_page_content(url)

            # Извлечение имени модели
            name_tag = soup.find('h1', class_=lambda x: x and 'title-extra-large-light' in x)
            name = self.extract_text(name_tag)

            # Извлечение параметров модели
            params = {}

            # Курс обучения
            course_tag = soup.find('span', class_=lambda x: x and 'text-extra-medium' in x and 'text-uppercase' in x, string=lambda s: s and ('курс' in s.lower()))
            if course_tag:
                course_text = self.extract_text(course_tag)
                # Убираем слово "курс" из текста
                course_text = course_text.replace(' курс', '').replace('Курс', '').replace('курс', '').strip()
                params['Курс'] = course_text

            # Возраст
            age_container = soup.find('span', class_=lambda x: x and 'font-weight-500' in x and 'text-extra-dark-gray' in x, string=lambda s: s and any(char.isdigit() for char in s))
            if age_container:
                age_text = self.extract_text(age_container)
                if 'лет' in age_text.lower() or any(char.isdigit() for char in age_text):
                    params['Возраст'] = age_text

            # Город
            city_tag = soup.find('span', class_=lambda x: x and 'text-extra-medium' in x and 'text-uppercase' in x, string=lambda s: s and len(s.strip()) > 0)
            if city_tag and self.extract_text(city_tag) not in ['Первый курс', 'Второй курс', 'Третий курс', 'Четвертый курс']:
                params['Город'] = self.extract_text(city_tag)

            # Параметры (рост, цвет волос, цвет глаз, размер обуви)
            param_labels = ['Рост:', 'Цвет волос:', 'Цвет глаз:', 'Размер обуви:']
            for label in param_labels:
                label_tag = soup.find('span', class_=lambda x: x and 'font-weight-500' in x, string=label)
                if label_tag:
                    # Находим родительский контейнер d-flex
                    parent = label_tag.find_parent('div', class_=lambda x: x and 'd-flex' in x)
                    if parent:
                        # Ищем следующий div с классом text-end, который содержит значение
                        value_container = parent.find('div', class_=lambda x: x and 'text-end' in x)
                        if value_container:
                            value_tag = value_container.find('span', class_='text-uppercase')
                            if value_tag:
                                params[label.rstrip(':')] = self.extract_text(value_tag)

            # Параметры тела (ищем в увлечениях)
            hobbies_tag = soup.find('p', class_=lambda x: x and 'text-extra-medium-gray' in x)
            if hobbies_tag:
                hobbies_text = self.extract_text(hobbies_tag)

                # Ищем параметры тела в формате "Параметры: 78/75/86"
                import re
                params_match = re.search(r'Параметры:\s*([\d/]+)', hobbies_text)
                if params_match:
                    params['Параметры'] = params_match.group(1)
                    # Убираем параметры из текста увлечений
                    hobbies_text = re.sub(r'Параметры:\s*[\d/]+\.?\s*', '', hobbies_text).strip()

                # Оставляем только увлечения и хобби
                if hobbies_text and len(hobbies_text) > 10 and 'не указаны' not in hobbies_text.lower():
                    # Форматируем как expandable blockquote без заголовка
                    formatted_hobbies = f"<blockquote expandable>" + '\n'.join(f"{line}" for line in hobbies_text.split('\n') if line.strip()) + "</blockquote>"
                    params['Увлечения и хобби'] = formatted_hobbies

            # Фотографии - берем только из основного слайдера, исключая миниатюры
            photos = []
            # Ищем основной контейнер слайдера
            main_slider = soup.find('div', class_=lambda x: x and 'product-image-slider' in x)
            if main_slider:
                # Берем только изображения из основного слайдера
                img_tags = main_slider.find_all('img', {'data-src': True})
                for img in img_tags:
                    src = img.get('data-src')
                    if src and ('models' in src or 'slides' in src):
                        if not src.startswith('http'):
                            if src.startswith('/storage'):
                                src = self.BASE_URL + src
                            elif src.startswith('/'):
                                src = self.BASE_URL + src
                            else:
                                src = self.BASE_URL + '/' + src
                        photos.append(src)

            result = {
                'name': name,
                'parameters': params,
                'photos': photos,
                'url': url
            }

            logger.info(f"Успешно спарсена модель: {name}")
            return result

        except Exception as e:
            logger.error(f"Ошибка при парсинге модели {url}: {e}")
            return None