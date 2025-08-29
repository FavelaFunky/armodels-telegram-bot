import logging
import requests
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseParser(ABC):
    """Базовый класс для всех парсеров сайта armodels.ru"""

    BASE_URL = 'https://armodels.ru'

    def __init__(self):
        """Инициализация базового парсера с настройками сессии"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_page_content(self, url: str, timeout: int = 10) -> BeautifulSoup:
        """
        Получить содержимое страницы и вернуть BeautifulSoup объект

        Args:
            url: URL страницы для парсинга
            timeout: Таймаут запроса в секундах

        Returns:
            BeautifulSoup объект страницы

        Raises:
            Exception: При ошибке загрузки страницы
        """
        try:
            # Убеждаемся, что URL абсолютный
            if not url.startswith('http'):
                if url.startswith('/'):
                    url = self.BASE_URL + url
                else:
                    url = self.BASE_URL + '/' + url

            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()  # Проверяем статус ответа

            return BeautifulSoup(response.text, 'html.parser')

        except requests.RequestException as e:
            logger.error(f"Ошибка при загрузке страницы {url}: {e}")
            raise Exception(f"Не удалось загрузить страницу: {e}")

    def extract_text(self, element, default: str = 'Не указано') -> str:
        """
        Безопасно извлечь текст из элемента BeautifulSoup

        Args:
            element: Элемент BeautifulSoup или None
            default: Значение по умолчанию

        Returns:
            Извлеченный текст или значение по умолчанию
        """
        return element.get_text(strip=True) if element else default

    def find_element_by_classes(self, soup: BeautifulSoup, classes: list, tag: str = None) -> BeautifulSoup:
        """
        Найти элемент по списку классов

        Args:
            soup: BeautifulSoup объект
            classes: Список классов для поиска
            tag: Тег элемента (опционально)

        Returns:
            Найденный элемент или None
        """
        for class_name in classes:
            element = soup.find(tag, class_=class_name) if tag else soup.find(class_=class_name)
            if element:
                return element
        return None

    @abstractmethod
    def parse_list(self) -> list:
        """
        Абстрактный метод для парсинга списка элементов

        Returns:
            Список спарсенных элементов
        """
        pass

    @abstractmethod
    def parse_detail(self, url: str) -> dict:
        """
        Абстрактный метод для парсинга детальной информации

        Args:
            url: URL элемента для детального парсинга

        Returns:
            Словарь с детальной информацией
        """
        pass