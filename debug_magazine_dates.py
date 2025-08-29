#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parsers.magazines_parser import MagazinesParser

def debug_magazine_dates():
    print("Debugging magazine dates...")

    try:
        parser = MagazinesParser()
        soup = parser.get_page_content('/')

        # Ищем секцию с журналами
        covers_section = soup.find('section', class_=lambda x: x and 'big-section' in x and 'bg-seashell' in x)
        if covers_section:
            print("[OK] Found covers section")

            swiper_container = covers_section.find('div', class_='swiper-container')
            if swiper_container:
                print("[OK] Found swiper container")

                magazine_slides = swiper_container.find_all('div', class_='swiper-slide')
                print(f"Found {len(magazine_slides)} slides")

                for i, slide in enumerate(magazine_slides[:2]):
                    print(f"\n=== Slide {i+1} ===")

                    # Ищем все div с текстом
                    text_divs = slide.find_all('div')
                    for j, div in enumerate(text_divs):
                        if div.get_text(strip=True):
                            print(f"Div {j}: classes={div.get('class')} text='{div.get_text(strip=True)[:50]}...'")

                    # Ищем все span элементы
                    spans = slide.find_all('span')
                    for j, span in enumerate(spans):
                        if span.get_text(strip=True):
                            print(f"Span {j}: classes={span.get('class')} text='{span.get_text(strip=True)}'")

                    # Конкретно ищем div с датой
                    date_div = slide.find('div', class_=lambda x: x and 'alt-font' in x and 'font-weight-500' in x and 'text-extra-large' in x)
                    if date_div:
                        raw_text = date_div.get_text()
                        print(f"Found date div raw text: '{raw_text}'")

                        # Извлекаем только дату (вторую часть после br)
                        import re
                        cleaned = re.sub(r'\s+', ' ', raw_text).strip()
                        print(f"Cleaned text: '{cleaned}'")

                        # Ищем паттерн "Журнал вышел в [месяц год]"
                        if 'Журнал вышел в' in cleaned:
                            date_part = cleaned.split('Журнал вышел в')[-1].strip()
                            print(f"Extracted date: '{date_part}'")
                        else:
                            print("Date pattern not found")

                        # Посмотрим на внутреннее содержимое
                        print("Children analysis:")
                        for child in date_div.children:
                            if hasattr(child, 'name') and child.name:
                                if child.name == 'br':
                                    print("  Found <br> tag")
                                elif hasattr(child, 'get_text'):
                                    print(f"  Child {child.name}: '{child.get_text()}'")
                            elif hasattr(child, 'strip'):
                                text_content = child.strip()
                                if text_content:
                                    print(f"  Text: '{text_content}'")
                    else:
                        print("Date div not found")

        else:
            print("[ERROR] Covers section not found")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_magazine_dates()