import logging
from typing import List, Dict, Optional
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

class ProjectsParser(BaseParser):
    """Парсер для проектов с сайта armodels.ru"""

    # Категории проектов
    CATEGORIES = {
        'photo-projects': 'Фотопроекты',
        'konkursi-krasoti': 'Конкурсы красоты',
        'fashion-shows': 'Модные показы',
        'advertising-shoots': 'Рекламные съёмки',
        'interview': 'Интервью'
    }

    def parse_list(self, category: Optional[str] = None) -> List[Dict]:
        """
        Парсит список всех проектов или проекты определенной категории

        Args:
            category: Категория проектов (photo-projects, fashion-shows, etc.)
                     Если None - парсит все проекты

        Returns:
            Список словарей с информацией о проектах
        """
        try:
            # Парсим главную страницу проектов
            soup = self.get_page_content('/projects')

            projects = []

            # Ищем контейнер с проектами
            projects_container = soup.find('ul', class_=lambda x: x and 'blog-grid' in x and 'grid' in x)
            if not projects_container:
                logger.warning("Контейнер с проектами не найден")
                return []

            # Ищем все элементы проектов
            project_items = projects_container.find_all('li', class_=lambda x: x and 'grid-item' in x)
            logger.info(f"Найдено {len(project_items)} элементов проектов")

            for item in project_items:
                try:
                    # Определяем категорию проекта
                    item_classes = item.get('class', [])
                    project_category = None
                    for class_name in item_classes:
                        if class_name in self.CATEGORIES:
                            project_category = class_name
                            break

                    # Если указана конкретная категория, пропускаем другие
                    if category and project_category != category:
                        continue

                    # Извлекаем данные проекта
                    project_data = self._extract_project_data(item, project_category)
                    if project_data:
                        projects.append(project_data)

                except Exception as e:
                    logger.warning(f"Ошибка при парсинге проекта: {e}")
                    continue

            logger.info(f"Успешно спарсено {len(projects)} проектов")
            return projects

        except Exception as e:
            logger.error(f"Ошибка при парсинге списка проектов: {e}")
            return []

    def _extract_project_data(self, item, category: Optional[str]) -> Optional[Dict]:
        """Извлекает данные одного проекта"""
        try:
            # Извлекаем изображение
            img_elem = item.find('img')
            image_url = None
            if img_elem:
                image_src = img_elem.get('data-src') or img_elem.get('src')
                if image_src and not image_src.startswith('http'):
                    image_url = f"{self.BASE_URL}{image_src}"
                else:
                    image_url = image_src

            # Извлекаем название проекта
            title_elem = item.find('a', class_=lambda x: x and 'text-extra-medium' in x and 'text-extra-dark-gray' in x)
            if not title_elem:
                # Альтернативный поиск
                title_elem = item.find('a', href=True)
                if title_elem and 'Подробнее' not in title_elem.get_text():
                    title = title_elem.get_text(strip=True)
                else:
                    return None
            else:
                title = title_elem.get_text(strip=True)

            # Извлекаем описание
            desc_elem = item.find('p', class_='cuttedText')
            description = desc_elem.get_text(strip=True) if desc_elem else ''

            # Извлекаем ссылку на подробности
            detail_link = item.find('a', href=True)
            detail_url = None
            if detail_link:
                href = detail_link.get('href')
                if href and not href.startswith('http'):
                    detail_url = f"{self.BASE_URL}{href}"
                else:
                    detail_url = href

            # Определяем категорию
            category_name = self.CATEGORIES.get(category, 'Проект') if category else 'Проект'

            return {
                'title': title,
                'description': description,
                'image_url': image_url,
                'detail_url': detail_url,
                'category': category,
                'category_name': category_name
            }

        except Exception as e:
            logger.warning(f"Ошибка при извлечении данных проекта: {e}")
            return None

    def parse_detail(self, url: str) -> Optional[Dict]:
        """
        Парсит детальную информацию о проекте

        Args:
            url: URL страницы проекта

        Returns:
            Словарь с детальной информацией о проекте или None при ошибке
        """
        try:
            soup = self.get_page_content(url)

            # TODO: Реализовать детальный парсинг страницы проекта
            # Пока возвращаем базовую структуру

            result = {
                'title': 'Не реализовано',
                'description': 'Детальная информация о проекте пока не реализована',
                'content': [],
                'url': url
            }

            logger.info(f"Успешно спарсен проект: {result['title']}")
            return result

        except Exception as e:
            logger.error(f"Ошибка при парсинге проекта {url}: {e}")
            return None

    def get_categories(self) -> Dict[str, str]:
        """
        Возвращает словарь доступных категорий проектов

        Returns:
            Словарь {код_категории: название_категории}
        """
        return self.CATEGORIES.copy()