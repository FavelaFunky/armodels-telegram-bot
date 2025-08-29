import logging
from typing import List, Dict, Optional
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

class TeachersParser(BaseParser):
    """Парсер для учителей с сайта armodels.ru"""

    def parse_list(self) -> List[Dict]:
        """
        Парсит список всех учителей с главной страницы

        Returns:
            Список словарей с информацией об учителях
        """
        try:
            # Парсим главную страницу
            soup = self.get_page_content('/')

            teachers = []

            # Ищем секцию с учителями
            teacher_section = soup.find('section', class_='padding-6-rem-top')
            if not teacher_section:
                logger.warning("Секция с учителями не найдена")
                return []

            # Ищем swiper-wrapper с учителями
            swiper_wrapper = teacher_section.find('div', id='swiper-wrapper-teacher')
            if not swiper_wrapper:
                logger.warning("Swiper wrapper с учителями не найден")
                return []

            # Ищем все слайды с учителями
            teacher_slides = swiper_wrapper.find_all('div', class_='swiper-slide')

            for slide in teacher_slides:
                try:
                    # Ищем имя учителя
                    name_elem = slide.find('span', class_='team-title')
                    if not name_elem:
                        continue

                    # Очищаем имя от лишних пробелов и переносов строк
                    name_text = name_elem.get_text()
                    # Убираем лишние пробелы и переносы строк
                    import re
                    name = re.sub(r'\s+', ' ', name_text).strip()

                    # Ищем специальность
                    specialty_elem = slide.find('span', class_='team-sub-title')
                    if specialty_elem:
                        specialty_text = specialty_elem.get_text()
                        specialty = re.sub(r'\s+', ' ', specialty_text).strip()
                    else:
                        specialty = 'Преподаватель'

                    # Ищем фото
                    img_elem = slide.find('img')
                    photo = None
                    if img_elem:
                        photo_src = img_elem.get('data-src') or img_elem.get('src')
                        if photo_src and not photo_src.startswith('http'):
                            photo = f"{self.BASE_URL}{photo_src}"
                        else:
                            photo = photo_src

                    if name:  # Добавляем только если есть имя
                        teachers.append({
                            'name': name,
                            'specialty': specialty,
                            'photo': photo
                        })

                except Exception as e:
                    logger.warning(f"Ошибка при парсинге учителя: {e}")
                    continue

            logger.info(f"Успешно спарсено {len(teachers)} учителей")
            return teachers

        except Exception as e:
            logger.error(f"Ошибка при парсинге списка учителей: {e}")
            return []

    def parse_detail(self, url: str) -> Optional[Dict]:
        """
        Парсит детальную информацию об учителе

        Args:
            url: URL страницы учителя

        Returns:
            Словарь с детальной информацией об учителе или None при ошибке
        """
        try:
            soup = self.get_page_content(url)

            # TODO: Реализовать логику парсинга детальной информации об учителе
            # Пока возвращаем базовую структуру

            result = {
                'name': 'Не реализовано',
                'parameters': {},
                'photos': [],
                'url': url
            }

            logger.info(f"Успешно спарсен учитель: {result['name']}")
            return result

        except Exception as e:
            logger.error(f"Ошибка при парсинге учителя {url}: {e}")
            return None