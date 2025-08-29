import logging
from typing import List, Dict, Optional
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

class PartnersParser(BaseParser):
    """Парсер для партнеров с сайта armodels.ru"""

    def parse_list(self) -> List[Dict]:
        """
        Парсит список всех партнеров с главной страницы

        Returns:
            Список словарей с информацией о партнерах
        """
        try:
            # Парсим главную страницу
            soup = self.get_page_content('/')

            partners = []

            # Ищем секцию с партнерами по заголовку
            partners_section = None
            for section in soup.find_all('section'):
                if section.find('span', string=lambda x: x and 'партнёры' in x.lower()):
                    partners_section = section
                    break

            if not partners_section:
                logger.warning("Секция с партнерами не найдена")
                return []

            # Ищем swiper-wrapper с партнерами
            swiper_wrapper = partners_section.find('div', id='swiper-wrapper-partners')
            if not swiper_wrapper:
                logger.warning("Swiper wrapper с партнерами не найден")
                return []

            # Ищем все слайды с партнерами
            partner_slides = swiper_wrapper.find_all('div', class_='swiper-slide')

            for slide in partner_slides:
                try:
                    # Ищем изображение партнера
                    img_elem = slide.find('img')
                    if not img_elem:
                        continue

                    # Получаем название из alt атрибута
                    name = img_elem.get('alt', '').strip()

                    # Получаем URL логотипа
                    logo_src = img_elem.get('data-src') or img_elem.get('src')
                    logo = None
                    if logo_src:
                        if not logo_src.startswith('http'):
                            logo = f"{self.BASE_URL}{logo_src}"
                        else:
                            logo = logo_src

                    # Ищем ссылку на партнера
                    link_elem = slide.find('a')
                    website = None
                    if link_elem:
                        href = link_elem.get('href')
                        if href and not href.startswith('javascript'):
                            website = href if href.startswith('http') else f"{self.BASE_URL}{href}"

                    if name or logo:  # Добавляем если есть хотя бы название или логотип
                        partners.append({
                            'name': name or 'Без названия',
                            'logo': logo,
                            'website': website
                        })

                except Exception as e:
                    logger.warning(f"Ошибка при парсинге партнера: {e}")
                    continue

            logger.info(f"Успешно спарсено {len(partners)} партнеров")
            return partners

        except Exception as e:
            logger.error(f"Ошибка при парсинге списка партнеров: {e}")
            return []

    def parse_detail(self, url: str) -> Optional[Dict]:
        """
        Парсит детальную информацию о партнере

        Args:
            url: URL страницы партнера

        Returns:
            Словарь с детальной информацией о партнере или None при ошибке
        """
        try:
            soup = self.get_page_content(url)

            # TODO: Реализовать логику парсинга детальной информации о партнере
            # Пока возвращаем базовую структуру

            result = {
                'name': 'Не реализовано',
                'parameters': {},
                'photos': [],
                'url': url
            }

            logger.info(f"Успешно спарсен партнер: {result['name']}")
            return result

        except Exception as e:
            logger.error(f"Ошибка при парсинге партнера {url}: {e}")
            return None