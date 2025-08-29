import logging
from typing import List, Dict, Optional
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

class MagazinesParser(BaseParser):
    """Парсер для выпусков журнала с сайта armodels.ru"""

    def parse_list(self) -> List[Dict]:
        """
        Парсит список всех выпусков журнала с главной страницы

        Returns:
            Список словарей с информацией о выпусках журнала
        """
        try:
            # Парсим главную страницу
            soup = self.get_page_content('/')

            magazines = []

            # Ищем секцию с журналами (COVERS section)
            covers_section = soup.find('section', class_='big-section bg-seashell')
            if not covers_section:
                # Попробуем найти по частичному совпадению классов
                covers_section = soup.find('section', class_=lambda x: x and 'big-section' in x and 'bg-seashell' in x)
                if not covers_section:
                    logger.warning("Секция с журналами не найдена")
                    return []

            # Ищем swiper-container с журналами
            swiper_container = covers_section.find('div', class_='swiper-container')
            if not swiper_container:
                logger.warning("Swiper container с журналами не найден")
                return []

            # Ищем все слайды с журналами
            magazine_slides = swiper_container.find_all('div', class_='swiper-slide')

            for slide in magazine_slides:
                try:
                    # Ищем изображение обложки
                    img_elem = slide.find('img')
                    cover_image = None
                    if img_elem:
                        cover_image_src = img_elem.get('data-src') or img_elem.get('src')
                        if cover_image_src and not cover_image_src.startswith('http'):
                            cover_image = f"{self.BASE_URL}{cover_image_src}"
                        else:
                            cover_image = cover_image_src

                    # Ищем номер выпуска
                    issue_elem = slide.find('span', class_='text-extra-small')
                    issue_number = issue_elem.get_text(strip=True) if issue_elem else 'Не указан'

                    # Ищем дату выхода (ищем div с классами alt-font и font-weight-500)
                    date_elem = slide.find('div', class_=lambda x: x and 'alt-font' in x and 'font-weight-500' in x and 'text-extra-large' in x)
                    release_date = 'Не указана'
                    if date_elem:
                        date_text = date_elem.get_text()
                        # Очищаем текст от лишних пробелов и переносов строк
                        import re
                        cleaned_date = re.sub(r'\s+', ' ', date_text).strip()
                        # Убираем префикс "Журнал вышел в"
                        if 'Журнал вышел в' in cleaned_date:
                            # Извлекаем часть после префикса
                            date_part = cleaned_date.split('Журнал вышел в')[-1].strip()
                            release_date = date_part
                        else:
                            release_date = cleaned_date

                    # Ищем ссылку на скачивание PDF
                    download_link = slide.find('a', href=True)
                    pdf_url = None
                    if download_link:
                        pdf_href = download_link.get('href')
                        if pdf_href and not pdf_href.startswith('http'):
                            pdf_url = f"{self.BASE_URL}{pdf_href}"
                        else:
                            pdf_url = pdf_href

                    if cover_image or issue_number != 'Не указан':  # Добавляем только если есть хоть какая-то информация
                        magazines.append({
                            'issue_number': issue_number,
                            'release_date': release_date,
                            'cover_image': cover_image,
                            'pdf_url': pdf_url,
                            'title': f"Журнал {issue_number}"
                        })

                except Exception as e:
                    logger.warning(f"Ошибка при парсинге выпуска журнала: {e}")
                    continue

            logger.info(f"Успешно спарсено {len(magazines)} выпусков журнала")
            return magazines

        except Exception as e:
            logger.error(f"Ошибка при парсинге списка выпусков журнала: {e}")
            return []

    def parse_detail(self, url: str) -> Optional[Dict]:
        """
        Парсит детальную информацию о выпуске журнала

        Args:
            url: URL страницы выпуска журнала

        Returns:
            Словарь с детальной информацией о выпуске или None при ошибке
        """
        try:
            soup = self.get_page_content(url)

            # TODO: Реализовать логику парсинга детальной информации о выпуске журнала
            # Пока возвращаем базовую структуру

            result = {
                'title': 'Не реализовано',
                'description': 'Детальная информация о выпуске журнала пока не реализована',
                'content': [],
                'url': url
            }

            logger.info(f"Успешно спарсен выпуск журнала: {result['title']}")
            return result

        except Exception as e:
            logger.error(f"Ошибка при парсинге выпуска журнала {url}: {e}")
            return None