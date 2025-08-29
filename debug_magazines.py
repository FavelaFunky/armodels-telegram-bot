#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parsers.magazines_parser import MagazinesParser

def debug_magazines():
    print("Debugging magazines section...")

    try:
        parser = MagazinesParser()
        soup = parser.get_page_content('/')

        print("Looking for magazines section...")

        # Ищем секцию с журналами
        covers_section = soup.find('section', class_='big-section bg-seashell')
        if covers_section:
            print("[OK] Found covers section")

            # Ищем swiper-container
            swiper_container = covers_section.find('div', class_='swiper-container')
            if swiper_container:
                print("[OK] Found swiper container")

                # Ищем все слайды
                magazine_slides = swiper_container.find_all('div', class_='swiper-slide')
                print(f"Found {len(magazine_slides)} slides")

                for i, slide in enumerate(magazine_slides[:3]):
                    print(f"\nSlide {i+1}:")
                    print(f"  Classes: {slide.get('class', [])}")

                    # Ищем изображение
                    img_elem = slide.find('img')
                    if img_elem:
                        print(f"  Image src: {img_elem.get('src')}")
                        print(f"  Image data-src: {img_elem.get('data-src')}")

                    # Ищем номер выпуска
                    issue_elem = slide.find('span', class_='text-extra-small')
                    if issue_elem:
                        print(f"  Issue: {issue_elem.get_text(strip=True)}")

                    # Ищем дату
                    date_elem = slide.find('div', class_='alt-font font-weight-500 text-extra-large')
                    if date_elem:
                        print(f"  Date: {date_elem.get_text(strip=True)}")

                    # Ищем ссылку на PDF
                    download_link = slide.find('a', href=True)
                    if download_link:
                        print(f"  PDF href: {download_link.get('href')}")
            else:
                print("[ERROR] Swiper container not found")
                print("Available divs in covers section:")
                for div in covers_section.find_all('div', class_=True)[:5]:
                    print(f"  {div.get('class')}")
        else:
            print("[ERROR] Covers section not found")
            print("Available sections:")
            for section in soup.find_all('section', class_=True)[:5]:
                print(f"  {section.get('class')}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_magazines()