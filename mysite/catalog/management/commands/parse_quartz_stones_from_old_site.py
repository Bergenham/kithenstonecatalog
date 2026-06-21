import os
import re
import time

import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from catalog.models import QuartzStone, StoneImage

from ._parser_utils import emit, normalize_model_payload


class Command(BaseCommand):
    help = "Парсит кварцевые камни с quartz.makerstone.ru и сохраняет их в БД"

    def handle(self, *args, **options):
        chrome_options = Options()
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--disable-gcm-initialization")
        chrome_options.add_argument("--disable-features=GCMDriver")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-gcm")

        service = Service(log_path=os.devnull)

        emit(self.stdout.write, "INFO", "Запуск браузера")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 15)

        try:
            catalog_url = "http://quartz.makerstone.ru/catalog"
            emit(self.stdout.write, "INFO", f"Открываем каталог {catalog_url}")
            driver.get(catalog_url)
            time.sleep(2)

            while True:
                try:
                    btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".js-store-load-more-btn")))
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    driver.execute_script("arguments[0].click();", btn)
                    emit(self.stdout.write, "INFO", "Нажата кнопка 'Загрузить ещё'")
                    time.sleep(2)
                except Exception:
                    emit(self.stdout.write, "INFO", "Все карточки загружены")
                    break

            cards = driver.find_elements(By.CSS_SELECTOR, ".js-store-grid-cont .js-product")
            urls = [card.find_element(By.TAG_NAME, "a").get_attribute("href") for card in cards]
            emit(self.stdout.write, "INFO", f"Найдено карточек: {len(urls)}")

            for idx, url in enumerate(urls, 1):
                emit(self.stdout.write, "INFO", f"[{idx}/{len(urls)}] Обработка {url}")
                try:
                    driver.get(url)
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "scrollbooster-content")))
                    time.sleep(1.5)

                    soup = BeautifulSoup(driver.page_source, "html.parser")

                    def sel(css, field_name):
                        el = soup.select_one(css)
                        if el:
                            value = el.get_text(strip=True)
                            emit(self.stdout.write, "INFO", f"{field_name}={value!r}")
                            return value
                        emit(self.stdout.write, "WARN", f"{field_name} не найдено")
                        return None

                    name_stone = sel("div.t396__elem.name div.tn-atom", "name_stone")
                    abt_prise = (sel("div.t396__elem.price div.tn-atom", "abt_prise") or "").replace(" ", "").replace("р.", "")
                    material = sel(".tn-elem.tabname-2 .tn-atom", "material")
                    country = sel(".tn-elem.tabname-5 .tn-atom", "country")
                    thickness_raw = sel(".tn-elem.tabname-4 .tn-atom", "thickness")
                    thickness = re.sub(r"\D", "", thickness_raw or "") or None
                    article = sel(".tn-elem.tabname-6 .tn-atom", "article")
                    about_brand = sel("div.tn-elem.text div.tn-atom", "about_brand")
                    scraped_brand = sel(".tn-elem.tabname-1 .tn-atom", "brand_stone")
                    color = sel(".tn-elem.tabname-3 .tn-atom", "color")
                    texture = sel(".tn-elem.tabname-7 .tn-atom", "texture")
                    faktura = sel(".tn-elem.tabname-8 .tn-atom", "faktura")

                    link_serf_el = soup.select_one("div.t1075__row a.t1075__link")
                    raw_link_serf = link_serf_el["href"] if link_serf_el else None
                    emit(self.stdout.write, "INFO", f"link_serf raw={raw_link_serf!r}")

                    if raw_link_serf == "https://drive.google.com/drive/folders/1YgXlFi8KKDzPHz5IheKJlbepOqd1sl3M":
                        link_serf = "Caesarstone"
                    elif raw_link_serf == "https://technistone.ru/info/certificates/":
                        link_serf = "Technistone"
                    elif raw_link_serf == "https://primax.pro/catalog/acryl/certificates/":
                        link_serf = "Primax"
                    else:
                        link_serf = None

                    raw_urls = set()
                    for tag in soup.find_all(style=True):
                        for candidate in re.findall(r'url\(["\']?([^"\'\)]+)', tag["style"]):
                            candidate = candidate.strip('"\' ').replace("&quot;", "")
                            if re.search(r"\.(jpe?g|png|gif|webp|bmp|svg)", candidate, re.I) and "-/" not in candidate:
                                raw_urls.add(candidate)
                    image_urls = list(raw_urls)
                    emit(self.stdout.write, "INFO", f"Найдено изображений: {len(image_urls)}")

                    defaults = normalize_model_payload(
                        QuartzStone,
                        {
                            "name_stone": name_stone,
                            "abt_prise": abt_prise,
                            "material": material,
                            "country": country,
                            "thickness": thickness,
                            "about_brand": about_brand,
                            "archive": False,
                            "brand_stone": scraped_brand,
                            "color": color,
                            "texture": texture,
                            "faktura": faktura,
                            "link_serf": link_serf,
                        },
                        self.stdout.write,
                        choice_aliases={
                            "link_serf": {
                                "Caesarstone": QuartzStone.LinkSerfChoices.CAESARSTONE,
                                "Technistone": QuartzStone.LinkSerfChoices.TECHNISTONE,
                                "Primax": QuartzStone.LinkSerfChoices.PRIMAX,
                            }
                        },
                    )

                    stone, created = QuartzStone.objects.get_or_create(article=article, defaults=defaults)
                    if not created:
                        for field_name, value in defaults.items():
                            setattr(stone, field_name, value)
                        stone.save()
                        emit(self.stdout.write, "INFO", f"Updated stone article={article} id={stone.pk}")
                    else:
                        emit(self.stdout.write, "INFO", f"Created stone article={article} id={stone.pk}")

                    stone.example_images.all().delete()
                    for i, img_url in enumerate(image_urls, 1):
                        try:
                            resp = requests.get(img_url, timeout=30)
                            resp.raise_for_status()
                        except Exception as exc:
                            emit(self.stdout.write, "WARN", f"Не удалось скачать {img_url}: {exc}")
                            continue

                        name = f"{name_stone or article}_other_{i}.jpg"
                        StoneImage.objects.create(
                            stone=stone,
                            image=ContentFile(resp.content, name=name),
                        )

                    self.stdout.write(
                        self.style.SUCCESS(f"{'Создано' if created else 'Обновлено'}: {name_stone or article}")
                    )
                except Exception as exc:
                    self.stdout.write(self.style.ERROR(f"Ошибка при {url}: {exc}"))
        finally:
            driver.quit()
            self.stdout.write(self.style.SUCCESS("Парсинг завершён"))
