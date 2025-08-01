# import os
# import re
# import time
# import requests
# from django.core.files.base import ContentFile
# from django.core.management.base import BaseCommand
# from bs4 import BeautifulSoup
#
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
#
# from catalog.models import QuartzStone, StoneImage
#
#
# class Command(BaseCommand):
#     help = "Парсит кварцевые камни с quartz.makerstone.ru и создаёт модели"
#
#     def handle(self, *args, **options):
#         chrome_options = Options()
#         chrome_options.add_argument("--log-level=3")
#         chrome_options.add_argument("--disable-gcm-initialization")
#         chrome_options.add_argument("--disable-features=GCMDriver")
#         chrome_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
#         chrome_options.add_argument("--ignore-certificate-errors")
#         chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#         chrome_options.add_argument("--disable-gcm")
#         # chrome_options.add_argument("--headless=new")
#
#         # подавляем логи chromedriver
#         service = Service(log_path=os.devnull)
#
#         self.stdout.write("🚀 Запуск браузера...")
#         driver = webdriver.Chrome(service=service, options=chrome_options)
#         wait = WebDriverWait(driver, 15)
#
#         catalog_url = "http://quartz.makerstone.ru/catalog"
#         self.stdout.write("🌐 Открываем каталог...")
#         driver.get(catalog_url)
#         time.sleep(2)
#
#         # Жмём "Загрузить ещё"
#         while True:
#             try:
#                 btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".js-store-load-more-btn")))
#                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
#                 driver.execute_script("arguments[0].click();", btn)
#                 self.stdout.write("🔄 Нажата кнопка 'Загрузить ещё'...")
#                 time.sleep(2)
#             except Exception:
#                 self.stdout.write("✅ Все карточки загружены.")
#                 break
#
#         cards = driver.find_elements(By.CSS_SELECTOR, ".js-store-grid-cont .js-product")
#         urls = [card.find_element(By.TAG_NAME, "a").get_attribute("href") for card in cards]
#         self.stdout.write(f"🔍 Найдено {len(urls)} карточек")
#
#         for idx, url in enumerate(urls, 1):
#             self.stdout.write(f"\n[{idx}/{len(urls)}] 🔧 Обработка: {url}")
#             try:
#                 driver.get(url)
#                 wait.until(EC.presence_of_element_located((By.CLASS_NAME, "scrollbooster-content")))
#                 time.sleep(1.5)
#
#                 soup = BeautifulSoup(driver.page_source, "html.parser")
#
#                 def sel(css, field_name):
#                     el = soup.select_one(css)
#                     if el:
#                         v = el.get_text(strip=True)
#                         self.stdout.write(f"✅ {field_name}: {v}")
#                         return v
#                     self.stdout.write(f"⚠️  {field_name} не найдено")
#                     return ''
#
#                 # Парсим поля
#                 name_stone    = sel('div.t396__elem.name div.tn-atom', "name_stone")
#                 abt_prise     = sel('div.t396__elem.price div.tn-atom', "abt_prise").replace(" ", "").replace("р.", "")
#                 material      = sel('.tn-elem.tabname-2 .tn-atom', "material")
#                 country       = sel('.tn-elem.tabname-5 .tn-atom', "country")
#                 thickness     = re.sub(r'\D', '', sel('.tn-elem.tabname-4 .tn-atom', "thickness"))
#                 article       = sel('.tn-elem.tabname-6 .tn-atom', "article")
#                 about_brand   = sel('div.tn-elem.text div.tn-atom', "about_brand")
#                 scraped_brand = sel('.tn-elem.tabname-1 .tn-atom', "brand_stone")
#                 color         = sel('.tn-elem.tabname-3 .tn-atom', "color")
#                 texture       = sel('.tn-elem.tabname-7 .tn-atom', "texture")
#                 faktura       = sel('.tn-elem.tabname-8 .tn-atom', "faktura")
#
#                 # Ссылка на сертификат
#                 link_serf_el = soup.select_one("div.t1075__row a.t1075__link")
#                 link_serf = link_serf_el["href"] if link_serf_el else ""
#                 self.stdout.write(f"✅ link_serf: {link_serf}")
#
#                 # Определяем бренд по ссылке, если это Caesarstone или Technistone
#                 if link_serf == 'https://drive.google.com/drive/folders/1YgXlFi8KKDzPHz5IheKJlbepOqd1sl3M':
#                     link_serf = 'Caesarstone'
#                 elif link_serf == 'https://technistone.ru/info/certificates/':
#                     link_serf = 'Technistone'
#                 else:
#                     link_serf = 'Not Founded'
#
#                 # Собираем изображения
#                 raw_urls = set()
#                 for tag in soup.find_all(style=True):
#                     for u in re.findall(r'url\(["\']?([^"\'\)]+)', tag['style']):
#                         u = u.strip('"\' ').replace('&quot;', '')
#                         if re.search(r'\.(jpe?g|png|gif|webp|bmp|svg)', u, re.I) and '-/' not in u:
#                             raw_urls.add(u)
#                 res_a_img = list(raw_urls)
#                 self.stdout.write(f"🖼️ Найдено изображений: {len(res_a_img)}")
#
#                 # Создаём или получаем запись камня
#                 stone, created = QuartzStone.objects.get_or_create(
#                     article=article,
#                     defaults=dict(
#                         name_stone=name_stone,
#                         abt_prise=abt_prise,
#                         material=material,
#                         country=country,
#                         thickness=thickness,
#                         about_brand=about_brand,
#                         archive=False,
#                         brand_stone=scraped_brand,
#                         color=color,
#                         texture=texture,
#                         faktura=faktura,
#                         link_serf=link_serf,
#                     )
#                 )
#
#                 # Всегда обновляем бренд и ссылку на сертификат
#                 if not created:
#                     stone.link_serf = link_serf
#                     stone.save(update_fields='link_serf')
#
#                 # Удаляем старые примеры и сохраняем все новые
#                 stone.example_images.all().delete()
#                 for i, img_url in enumerate(res_a_img, 1):
#                     resp = requests.get(img_url)
#                     name = f"{name_stone}_other_{i}.jpg"
#                     StoneImage.objects.create(
#                         stone=stone,
#                         image=ContentFile(resp.content, name=name)
#                     )
#
#                 self.stdout.write(self.style.SUCCESS(
#                     f"{'🆕 Создано' if created else '♻️ Обновлено'}: {name_stone}"
#                 ))
#
#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f"❌ Ошибка при {url}: {e}"))
#
#         driver.quit()
#         self.stdout.write(self.style.SUCCESS("🏁 Парсинг завершён."))
