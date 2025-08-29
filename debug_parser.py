#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parsers.partners_parser import PartnersParser

def debug_partners():
    print("=== Отладка парсера партнеров ===")
    try:
        parser = PartnersParser()
        soup = parser.get_page_content('/')

        print(f"Страница загружена, длина: {len(str(soup))}")

        # Ищем все секции
        sections = soup.find_all('section')
        print(f"Найдено секций: {len(sections)}")

        # Ищем секцию с партнерами
        partners_section = None
        for i, section in enumerate(sections):
            # Ищем заголовок с "партнёры"
            header = section.find('span', string=lambda x: x and 'партнёры' in x.lower() if x else False)
            if header:
                print(f"Найдена секция партнеров (индекс {i})")
                partners_section = section
                break

        if not partners_section:
            print("Секция партнеров не найдена")
            return

        # Ищем swiper-wrapper
        swiper_wrapper = partners_section.find('div', id='swiper-wrapper-partners')
        if not swiper_wrapper:
            print("Swiper wrapper не найден")
            # Попробуем найти все div с swiper-wrapper
            all_wrappers = partners_section.find_all('div', class_='swiper-wrapper')
            print(f"Найдено swiper-wrapper элементов: {len(all_wrappers)}")
            for i, wrapper in enumerate(all_wrappers):
                print(f"Wrapper {i}: id={wrapper.get('id')}, classes={wrapper.get('class')}")
            return

        # Ищем слайды
        slides = swiper_wrapper.find_all('div', class_='swiper-slide')
        print(f"Найдено слайдов: {len(slides)}")

        for i, slide in enumerate(slides[:3]):  # Первые 3 слайда
            img = slide.find('img')
            if img:
                name = img.get('alt', 'Без названия')
                logo = img.get('data-src') or img.get('src')
                print(f"Слайд {i+1}: {name} -> {logo}")

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_partners()