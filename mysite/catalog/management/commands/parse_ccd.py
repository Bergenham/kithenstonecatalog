# import_acrylic_stones.py  (обновлённый, устойчивый вариант)
import os
import re
import time
import hashlib
import requests
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, StaleElementReferenceException,
    ElementClickInterceptedException, WebDriverException
)

# -------------------- НАСТРАИВАЕМЫЕ КОНСТАНТЫ --------------------
APP_NAME = 'catalog'  # <- имя твоего django-приложения (замени, если нужно)
CHILD_CATALOG_URL = 'https://ssd.su/brands/durasein/'  # <- дочерний каталог
BASE_URL = 'https://ssd.su/'  # <- базовый домен
BRAND_NAME = 'Durasein'  # <- константа brand_stone
LINK_SERF = 'https://ssd.su/upload/iblock/a62/2n2gdb8s43pfs2bqjt7g6wdwdx0vwvcf.zip'
FAKTURA_STR = 'NONE'
ABT_PRIZE = 101.00
MATERIAL = 'Акриловый камень'
ABOUT_BRAND = """Durasein создан для бесстрашных дизайнеров и мечтателей, которые не боятся выходить за рамки привычного.

Откажитесь от устаревших стандартов и дайте волю фантазии — вместе мы превратим ваши идеи в нечто по-настоящему вдохновляющее. """
ARCHIVE = False
DEFAULT_COUNTRY = 'Южная Корея'

# Поведение драйвера
HEADLESS = False        # <- важно: по умолчанию False, чтобы видеть браузер и гарантировать подгрузку lazy-img.
WAIT_SHORT = 4         # небольшой wait
WAIT_MED = 8
WAIT_LONG = 20
DOWNLOAD_TIMEOUT = 30
THICKNESS_FALLBACK = 12  # если не найдено — ставим 1 мм (без ошибок валидатора)
# ----------------------------------------------------------------

# Импорт моделей
ModelsModule = __import__(f"{APP_NAME}.models", fromlist=['AcrylicStone', 'StoneImage'])
AcrylicStone = getattr(ModelsModule, 'AcrylicStone')
StoneImage = getattr(ModelsModule, 'StoneImage')

# Карты для соответствия цветов/текстур/стран
COLOR_MAP = {
    'беж': 'Бежевый', 'бел': 'Белый', 'жёлт': 'Жёлтый', 'желт': 'Жёлтый',
    'коричн': 'Коричневый', 'светло-голуб': 'Светло-голубой', 'сер': 'Серый',
    'тёмно-': 'Темно-коричневый', 'тёмн': 'Темно-серый', 'черн': 'Черный',
    'зел': 'Зеленый', 'красн': 'Красный', 'оранж': 'Оранжевый', 'синий': 'Синий'
}

TEXTURE_MAP = {
    'мрамор': 'Мраморная', 'однотон': 'Однотонная', 'песк': 'Пески',
    'чип': 'Средний чип', 'крупн': 'Крупный чип', 'бел': 'Белый'
}

COUNTRY_MAP = {
    'чех': 'Чехия', 'чеш': 'Чехия',
    'изра': 'Израиль',
    'коре': 'Южная Корея', 'кит': 'Китай', 'китай': 'Китай',
}

def map_value(text, mapping, default):
    if not text:
        return default
    t = text.lower()
    for k, v in mapping.items():
        if k in t:
            return v
    return default

def map_country(text, default):
    return map_value(text, COUNTRY_MAP, default)

def safe_js_click(driver, element):
    """
    Надёжный клик: прокрутка + JS click + ретраи.
    """

    for attempt in range(6):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
            time.sleep(0.3)
            # Попытка через js_click (избегает interception)
            driver.execute_script("arguments[0].click();", element)
            return True
        except (ElementClickInterceptedException, WebDriverException, StaleElementReferenceException) as e:
            # Попробуем скрыть потенциально перекрывающие элементы (cookie, sticky footer) и повторим
            try:
                driver.execute_script("""
                var els = document.querySelectorAll('header, .cookie, .cookie-banner, .fixed-footer, .sticky, .modal, .overlay');
                for(var i=0;i<els.length;i++){ els[i].style.pointerEvents='none'; els[i].style.opacity='0.01'; }
                """)
            except Exception:
                pass
            time.sleep(0.6 + attempt*0.3)
            continue
    return False

def extract_first_available_text(driver, selectors):
    for sel in selectors:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            text = el.text.strip()
            if text:
                return text
        except Exception:
            continue
    return ''

def download_image_bytes(url):
    try:
        r = requests.get(url, timeout=DOWNLOAD_TIMEOUT)
        if r.status_code == 200 and r.content:
            return r.content
    except Exception:
        return None
    return None

def generate_article_from_url(url):
    h = hashlib.md5(url.encode('utf-8')).hexdigest()[:10]
    return f"no-article-{h}"

class Command(BaseCommand):
    help = 'Робастный парсер AcrylicStone (обновлённый, надежный).'

    def handle(self, *args, **options):
        print("=== START: импорт AcrylicStone (robust) ===")
        # Настройка selenium
        chrome_options = webdriver.ChromeOptions()
        if HEADLESS:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # Отключаем image-inlining для стабильности? пока не нужно.
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, WAIT_LONG)

        try:
            print(f"Открываем каталог: {CHILD_CATALOG_URL}")
            driver.get(CHILD_CATALOG_URL)
            time.sleep(1.0)

            # Ждём ключевой контейнер каталога (попробуем несколько вариантов селекторов)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".catalogq__content")), timeout=WAIT_LONG)
            except Exception:
                # пробуем минимальный wait
                time.sleep(2.0)

            # Убедимся, что Lazy-loaded карточки могут подгрузиться: прокручиваем вниз один раз
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(0.7)

            # Нажимаем "Загрузить ещё" пока кнопка видна и количество карточек увеличивается
            prev_count = -1
            stable_no_change = 0
            max_no_change = 5
            while True:
                # Найдём карточки сейчас
                cards = driver.find_elements(By.CSS_SELECTOR, ".catalogq__content .prodcard")
                cur_count = len(cards)
                # Если кнопки нет — выходим
                try:
                    load_btn = driver.find_element(By.CSS_SELECTOR, ".load_more, .catalog__loadmore, .load-more, button.load_more")
                    visible = load_btn.is_displayed()
                except NoSuchElementException:
                    visible = False
                    load_btn = None

                if not visible:
                    print("Кнопка 'Загрузить ещё' отсутствует или не видима — считаем, что загрузка завершена.")
                    break

                print(f"Кнопок: видна. Карточек сейчас: {cur_count}. Пытаюсь кликнуть 'Загрузить ещё'...")
                ok = safe_js_click(driver, load_btn)
                if not ok:
                    print("WARN: не удалось корректно кликнуть (последняя попытка — js click). Попробую ещё немного прокрутить и повторить.")
                    driver.execute_script("window.scrollBy(0, 200);")
                    time.sleep(1.0)
                    try:
                        driver.execute_script("arguments[0].click();", load_btn)
                    except Exception as e:
                        print("WARN: окончательная попытка кликнуть завершилась ошибкой:", e)
                        break

                # ждём увеличения количества карточек либо исчезновения кнопки
                t0 = time.time()
                waited = False
                while time.time() - t0 < WAIT_LONG:
                    time.sleep(0.6)
                    cards = driver.find_elements(By.CSS_SELECTOR, ".catalogq__content .prodcard")
                    new_count = len(cards)
                    if new_count > cur_count:
                        print(f"Подгрузилось карточек: {new_count - cur_count} (всего {new_count})")
                        waited = True
                        break
                    # если кнопка исчезла — выйти
                    try:
                        if not driver.find_element(By.CSS_SELECTOR, ".load_more, .catalog__loadmore, .load-more, button.load_more").is_displayed():
                            waited = True
                            break
                    except Exception:
                        waited = True
                        break
                if not waited:
                    stable_no_change += 1
                    print("WARN: карточек не прибавилось после клика. Попробую повторно.")
                else:
                    stable_no_change = 0

                if stable_no_change >= max_no_change:
                    print("WARN: несколько попыток не увеличивали количество карточек — выхожу из цикла.")
                    break

            # Теперь собираем все ссылки на карточки — берём hrefы внутри карточек
            anchors = driver.find_elements(By.CSS_SELECTOR, ".catalogq__content .prodcard .prodcard__img a[href], .prodcard a[href]")
            link_set = []
            for a in anchors:
                try:
                    href = a.get_attribute("href")
                    if not href:
                        continue
                    if href.startswith('/'):
                        href = BASE_URL.rstrip('/') + href
                    link_set.append(href)
                except Exception:
                    continue
            # Уникализируем и сохраним порядок
            links = list(dict.fromkeys(link_set))
            print(f"Найдено уникальных ссылок на карточки: {len(links)}")

            # Обработка каждой карточки — открываем в новой вкладке
            for idx, link in enumerate(links, start=1):
                print(f"\n[{idx}/{len(links)}] Обработка: {link}")
                try:
                    driver.execute_script("window.open(arguments[0], '_blank');", link)
                    driver.switch_to.window(driver.window_handles[-1])
                    # Даём странице подгрузиться
                    time.sleep(1.0)
                    # Ждём основной блока (если есть)
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")), timeout=WAIT_MED)
                    except Exception:
                        pass

                    # Попытки получить название: h1, .singleprod__title, .product-title, meta og:title
                    name_stone = extract_first_available_text(driver, [
                        "h1", ".singleprod__title", ".product-title", ".product-name", ".page-title"
                    ])
                    if not name_stone:
                        # try meta og:title
                        try:
                            meta = driver.find_element(By.CSS_SELECTOR, "meta[property='og:title']")
                            name_stone = meta.get_attribute("content") or ''
                        except Exception:
                            name_stone = ''

                    # Собираем поля характеристик в attrs: ищем пары .singleprod__hars-item (или tr в таблице)
                    attrs = {}
                    try:
                        items = driver.find_elements(By.CSS_SELECTOR, ".singleprod__hars-list .singleprod__hars-item, .characteristics .item, .hars .item, .product-params tr")
                        for it in items:
                            try:
                                # разные структуры: title/value или two td
                                title = ''
                                value = ''
                                try:
                                    t_el = it.find_element(By.CSS_SELECTOR, ".singleprod__hars-title, .item-title, th")
                                    title = t_el.text.strip().rstrip(':').strip()
                                except Exception:
                                    # fallback: first child
                                    parts = it.text.split('\n')
                                    if len(parts) >= 2:
                                        title = parts[0].strip().rstrip(':')
                                        value = parts[1].strip()
                                if not value:
                                    try:
                                        v_el = it.find_element(By.CSS_SELECTOR, ".singleprod__hars-value, .item-value, td")
                                        value = v_el.text.strip()
                                    except Exception:
                                        if not value:
                                            # last resort: full text minus title
                                            txt = it.text.strip()
                                            if title and txt.startswith(title):
                                                value = txt[len(title):].strip(': ').strip()
                                if title:
                                    attrs[title] = value
                            except Exception:
                                continue
                    except Exception:
                        pass

                    # Иногда артикула нет в attrs — ищем на странице текст 'Артикул' в любом месте
                    article = name_stone.split(" ", 1)[0].strip()


                    # thickness: ищем 'Толщина' в attrs или в тексте
                    thickness_raw = attrs.get('Толщина') or attrs.get('Толщина (мм)') or ''
                    if not thickness_raw:
                        # поиск по всему тексту (например "Толщина: 12 мм")
                        try:
                            body = driver.find_element(By.TAG_NAME, "body").text
                            m = re.search(r'Толщина[:\s]*([\d]{1,4})\s*мм', body, re.IGNORECASE)
                            if m:
                                thickness_raw = m.group(1)
                        except Exception:
                            thickness_raw = ''
                    thickness = THICKNESS_FALLBACK
                    try:
                        if thickness_raw:
                            thickness = int(''.join(ch for ch in thickness_raw if ch.isdigit()))
                            if thickness <= 0:
                                thickness = THICKNESS_FALLBACK
                    except Exception:
                        thickness = THICKNESS_FALLBACK

                    # color / texture
                    color_raw = attrs.get('Цвет') or attrs.get('Color') or ''
                    texture_raw = attrs.get('Коллекция') or attrs.get('Текстура') or ''

                    color = map_value(color_raw, COLOR_MAP, 'Белый')
                    texture = map_value(texture_raw, TEXTURE_MAP, 'Однотонная')

                    # IMPORTANT: в твоём файле блок, который раньше был "Бренд", теперь содержит country.
                    brand_block_candidates = ['Бренд', 'Производитель', 'Бренд/производитель', 'Brand', 'Manufacturer']
                    country_raw = ''
                    for key in brand_block_candidates:
                        if key in attrs:
                            country_raw = attrs.get(key, '')
                            break
                    if not country_raw:
                        for key in ['Страна', 'Страна изготовления', 'Made in']:
                            if key in attrs:
                                country_raw = attrs.get(key, '')
                                break
                    country = map_country(country_raw, DEFAULT_COUNTRY)

                    # Если article всё еще пустой — сгенерируем уникальный
                    if not article:
                        article = generate_article_from_url(link)
                        print(f"WARN: артикул не найден — сгенерирован article: {article}")

                    # Сбор изображений: соберём src, data-src, data-lazy, srcset
                    img_srcs = []
                    try:
                        # Сначала ищем стандартный слайдер
                        imgs = driver.find_elements(By.CSS_SELECTOR, ".swiper-wrapper img, .product-gallery img, .product-images img, .gallery img")
                        for im in imgs:
                            try:
                                # получаем возможные атрибуты
                                for attr in ('src', 'data-src', 'data-lazy', 'data-original'):
                                    src = im.get_attribute(attr)
                                    if src and src.strip():
                                        if src.startswith('//'):
                                            src = 'https:' + src
                                        if src.startswith('/'):
                                            src = BASE_URL.rstrip('/') + src
                                        if src not in img_srcs:
                                            img_srcs.append(src)
                                # srcset: берем первую запись
                                srcset = im.get_attribute('srcset') or ''
                                if srcset:
                                    first = srcset.split(',')[0].strip().split(' ')[0]
                                    if first and first not in img_srcs:
                                        if first.startswith('/'):
                                            first = BASE_URL.rstrip('/') + first
                                        img_srcs.append(first)
                                # Также попробуем data-srcset
                                ds = im.get_attribute('data-srcset') or ''
                                if ds:
                                    first = ds.split(',')[0].strip().split(' ')[0]
                                    if first and first not in img_srcs:
                                        if first.startswith('/'):
                                            first = BASE_URL.rstrip('/') + first
                                        img_srcs.append(first)
                            except StaleElementReferenceException:
                                continue
                    except Exception:
                        pass

                    # Если не нашли картинки в слайдере — попробуем искать мета og:image
                    if not img_srcs:
                        try:
                            meta = driver.find_element(By.CSS_SELECTOR, "meta[property='og:image']")
                            val = meta.get_attribute('content')
                            if val:
                                img_srcs.append(val)
                        except Exception:
                            pass

                    # Если нашли картинки — ждём их загрузки (naturalWidth > 0) и попытаемся скачать
                    downloaded = []
                    if img_srcs:
                        print(f"Найдено candidate изображений: {len(img_srcs)} — пытаюсь дождаться загрузки и скачать...")
                        for i, src in enumerate(img_srcs):
                            # немного подождём, так как lazy-load может ещё работать
                            try:
                                # Скрипт на случай, если картинка ещё не загружена — попытаемся её force-load через создание Image()
                                driver.execute_script("""
                                   var src = arguments[0];
                                   if(!document.querySelector('img[src="'+src+'"]')) {
                                     var img = new Image(); img.src = src;
                                   }
                                """, src)
                            except Exception:
                                pass
                            # wait a bit for server
                            time.sleep(0.6)
                            # Попытки загрузки через requests (с таймаутом)
                            b = download_image_bytes(src)
                            if b:
                                ext = os.path.splitext(src.split('?')[0])[1] or '.jpg'
                                fname = f"{article}_{i+1}{ext}"
                                downloaded.append((fname, b))
                            else:
                                print(f"WARN: не удалось скачать изображение: {src}")
                    else:
                        print("WARN: изображений не найдено в карточке.")

                    # Запись в базу (get_or_create по article). Обновляем поля.
                    with transaction.atomic():
                        try:
                            defaults = {
                                'name_stone': name_stone or f"{BRAND_NAME} {article}",
                                'abt_prise': ABT_PRIZE,
                                'material': MATERIAL,
                                'country': country,
                                'thickness': thickness,
                                'about_brand': ABOUT_BRAND,
                                'archive': ARCHIVE,
                                'brand_stone': BRAND_NAME,
                                'color': color,
                                'texture': texture,
                                'faktura': FAKTURA_STR,
                                'link_serf': LINK_SERF,
                            }
                            instance, created = AcrylicStone.objects.get_or_create(article=article, defaults=defaults)
                            if not created:
                                # обновляем только полезные поля (не портим вручную исправленное)
                                instance.name_stone = name_stone or instance.name_stone
                                instance.abt_prise = ABT_PRIZE
                                instance.material = MATERIAL
                                instance.country = country or instance.country
                                instance.thickness = thickness or instance.thickness
                                instance.about_brand = ABOUT_BRAND
                                instance.archive = ARCHIVE
                                instance.brand_stone = BRAND_NAME
                                instance.color = color
                                instance.texture = texture
                                instance.faktura = FAKTURA_STR
                                instance.link_serf = LINK_SERF
                                instance.save()
                                print(f"UPDATED: {instance.article} (id={instance.pk})")
                            else:
                                print(f"CREATED: {instance.article} (id={instance.pk})")

                            # Сохраняем preview_img = первая картинка, затем StoneImage для всех
                            if downloaded:
                                # preview
                                try:
                                    preview_name, preview_bytes = downloaded[0]
                                    instance.priview_img.delete(save=False)
                                    instance.priview_img.save(preview_name, ContentFile(preview_bytes), save=True)
                                    instance.save()
                                except Exception as e:
                                    print("WARN: не удалось сохранить preview_img:", e)
                                # все примеры
                                saved_count = 0
                                for fname, content in downloaded:
                                    try:
                                        si = StoneImage(stone=instance)
                                        si.image.save(fname, ContentFile(content), save=True)
                                        saved_count += 1
                                    except Exception as e:
                                        print("WARN: не удалось сохранить StoneImage:", e)
                                print(f"Saved {saved_count} StoneImage(s) for {instance.article}")
                            else:
                                print(f"Нет изображений для {article} — пропускаем сохранение файлов.")
                        except IntegrityError as e:
                            print("ERROR: IntegrityError при сохранении:", e)

                    # Закрываем вкладку продукта и возвращаемся к основной
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    time.sleep(0.4)

                except Exception as e:
                    print(f"ERROR: ошибка при обработке {link}: {e}")
                    # закрыть текущую вкладку если открыта и перейти в первую
                    try:
                        if len(driver.window_handles) > 1:
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                    except Exception:
                        pass
                    continue

            print("\n=== FINISHED: обработаны все найденные ссылки ===")
        finally:
            try:
                driver.quit()
            except Exception:
                pass
            print("Selenium driver закрыт.")
