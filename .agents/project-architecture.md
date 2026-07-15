# Архитектура проекта Kitchen Stone Catalog

Документ для ИИ-агентов, которые будут поддерживать этот репозиторий. Цель: быстро понять устройство проекта, основные точки входа и места, где легко сломать поведение.

## Кратко

Это Django-проект каталога камня и сайта услуг по столешницам. Проект состоит из:

- Django-конфигурации в `mysite/mysite/`.
- Приложения каталога `mysite/catalog/`.
- Приложения статических/маркетинговых страниц и заявок `mysite/basic_page/`.
- Большого набора экспортированных Tilda HTML/CSS/JS/assets в шаблонах.
- Management-команд для импорта камней, изображений и классификации параметров.

Зависимости описаны в `pyproject.toml`: Python `^3.13`, Django `^5.1.7`, Pillow, psycopg2-binary, openpyxl.

## Запуск и окружение

Корень Django-проекта: `mysite/`.

Типичный запуск локально:

```powershell
cd mysite
python manage.py runserver
```

База данных в `mysite/mysite/settings.py` настроена на PostgreSQL:

- DB name: `stone_maker_db`
- user: `user_db`
- host: `localhost`
- port: `5432`

Важно: в `settings.py` сейчас хранятся `SECRET_KEY` и пароль БД прямо в коде, `DEBUG=True`, `ALLOWED_HOSTS=[]`. Для production это нужно выносить в переменные окружения.

## Главные приложения

### `catalog`

Отвечает за каталог камней:

- модели камней и изображений;
- публичные страницы каталогов;
- детальные страницы камня;
- AJAX-подгрузку карточек;
- админку камней;
- команды импорта и нормализации данных.

Ключевые файлы:

- `mysite/catalog/models.py`
- `mysite/catalog/views.py`
- `mysite/catalog/urls.py`
- `mysite/catalog/admin.py`
- `mysite/catalog/management/commands/`
- `mysite/catalog/templates/fronttemp/`

### `basic_page`

Отвечает за основные страницы сайта, формы заявок и экспорт в Excel:

- Tilda-страницы из `basic_page/templates/basic_page/front/`;
- формы заявок;
- модель заявки `UserBidModel`;
- Excel-экспорт заявок и камней;
- панель экспорта.

Ключевые файлы:

- `mysite/basic_page/models.py`
- `mysite/basic_page/views.py`
- `mysite/basic_page/urls.py`
- `mysite/basic_page/admin.py`
- `mysite/basic_page/utils/table_export.py`
- `mysite/basic_page/templates/basic_page/`

## URL-маршрутизация

Главный URLConf: `mysite/mysite/urls.py`.

Основные подключения:

- `/admin/` -> Django admin.
- `/catalog/` -> `catalog.urls`.
- `/` -> `basic_page.urls`.

Дополнительно в `mysite/mysite/urls.py` вручную проброшены static-like маршруты для CSS/JS/images из Tilda-экспортов:

- `/css/`, `/js/`, `/images/` -> assets `basic_page`.
- `/trend/css/`, `/trend/js/`, `/trend/images/` -> assets `basic_page` для trend-страницы.
- `/catalog/css/`, `/catalog/js/`, `/catalog/images/` -> assets `catalog/templates/fronttemp`.

Это нестандартная для Django схема, но она нужна текущим HTML-шаблонам, которые ссылаются на такие пути.

## Публичные страницы

`basic_page.urls` содержит маршруты для большинства страниц сайта:

- `/`, `/main`, `/main_page` -> главная.
- `/topstone`, `/production`, `/delivery`, `/installation`.
- `/stairs`, `/sinks`, `/sills`, `/dimensions`.
- `/quartz`, `/acryl`, `/natural`, `/porcelain`.
- `/panels`, `/bar`, `/fireplace`, `/reception`.
- `/selection`, `/otheracrylstone`, `/other`.
- `/about`, `/calculator`, `/zamer` -> используют view `contacts`.
- `/partner` -> `SendUsPageTemplate`.
- `/choice`, `/trend/hopetoun` -> `choice_stone`.

Большинство views в `basic_page/views.py` являются простыми `TemplateView`, которые рендерят конкретные файлы `page*.html` из Tilda-экспорта.

## Каталог камней

`catalog.urls`:

- `/catalog/quartz` -> `QuartzCatalog`.
- `/catalog/acril` -> `AcrilCatalog`.
- `/catalog/natural` -> `NaturalCatalog`.
- `/catalog/ceramic` -> `CeramicCatalog`.
- `/catalog/quartz/stone/<article>` -> детальная страница кварца.
- `/catalog/acril/stone/<article>` -> детальная страница акрила.
- `/catalog/natural/stone/<article>` -> детальная страница натурального камня.
- `/catalog/ceramic/stone/<article>` -> детальная страница керамики.

Внимание: `stone_detail_c` рендерит `fronttemp/ceramic/about_ceramic.html`, а в дереве шаблонов есть файл `about_ceraimic.html` с опечаткой. Если шаблон `about_ceramic.html` отсутствует в рабочей копии, детальная страница керамики будет падать с `TemplateDoesNotExist`.

Каталоги наследуются от `ListView`, но переопределяют `get()`:

- фильтруют по GET-параметрам `brand`, `color`, `texture`, `faktura`;
- исключают архивные записи через `archive=False`;
- берут порцию `PAGE_SIZE = 20` по `offset`;
- при AJAX-запросе возвращают JSON с HTML-фрагментом сетки;
- при обычном GET рендерят полный шаблон каталога.

Фрагменты сеток:

- `fronttemp/quartz/_stones_grid_Q.html`
- `fronttemp/acril/_stones_grid_A.html`
- `fronttemp/natural/_stones_grid_N.html`
- `fronttemp/ceramic/_stones_grid_C.html`

Внимание: в `QuartzCatalog` путь фрагмента сейчас указан как `'fronttemp/quartz/_stones_grid_Q.html '` с пробелом в конце. Это потенциальная ошибка.

## Модель данных

Базовая модель: `catalog.models.Stone`.

Основные поля:

- `name_stone` - название камня.
- `abt_prise` - примерная цена.
- `priview_img` - превью-изображение. Название поля содержит опечатку, но оно уже используется в коде и миграциях.
- `material` - тип материала.
- `country` - страна.
- `thickness` - толщина.
- `article` - артикул, `unique=True`, может быть `NULL`.
- `about_brand` - описание бренда.
- `archive` - скрытие из публичного каталога.

Наследники `Stone` используют Django multi-table inheritance:

- `QuartzStone`
- `AcrylicStone`
- `NaturalStone`
- `CeramicsStone`

У каждого наследника есть поля:

- `brand_stone`
- `color`
- `texture`
- `faktura`
- `link_serf`

Связанные изображения:

- `StoneImage.stone` -> `ForeignKey(Stone, related_name='example_images')`.
- `StoneImage.image` -> примеры изображений в `stones/examples/`.

Путь для `priview_img` строится функцией `get_upload_path()` по `instance.material`. Если `material` пустой или не совпал с ожидаемыми choice-значениями, файл уйдет в `stones/other/previews/`.

## Заявки пользователей

Модель: `basic_page.models.UserBidModel`.

Поля:

- `full_name`
- `phone`
- `email`
- `is_active`
- `AWtPP` - согласие с политикой, название означает `Agree With The Privacy Policy`.
- `created_at`

Заявки создаются из:

- `basic_page.views.choice_stone`
- `basic_page.views.contacts`
- detail views в `catalog.views` при POST на карточке камня.

Detail views каталога возвращают `JsonResponse` со статусом `success/error`.

## Админка

`catalog/admin.py`:

- общий `StoneAdminBase` для всех типов камня;
- inline `StoneImageInline` с preview изображений;
- отдельные admin-классы для Quartz/Acrylic/Natural/Ceramics;
- `StoneImageAdmin`.

`basic_page/admin.py`:

- `UserBidAdmin` с фильтрами, поиском, `date_hierarchy`;
- action `make_inactive`;
- форматированный вывод телефона и согласия.

## Excel-экспорт

Реализация: `basic_page/utils/table_export.py`.

Функции:

- `export_stones(request, model, filename, title)` - выгрузка камней выбранной модели.
- `export_userbids(request)` - формирует workbook с заявками.

Внимание: в `basic_page.views.export_userbids_view` функция вызывается как `export_userbids()` без аргументов, но в `table_export.py` сейчас объявлена как `export_userbids(request)`. Это выглядит как runtime-ошибка `TypeError` при попытке выгрузить заявки.

Маршруты экспорта в `basic_page.urls`:

- `/PsstFuVvwLjdQvu` -> ceramics.
- `/t3WNStJaz2N5Cuw` -> natural.
- `/pnCne7xcIVMjG57` -> acrylic.
- `/Nor2qRjFD3wbKiy` -> quartz.
- `/X5KD08OHn25yNLf` -> user bids.
- `/export_panel` -> HTML-панель экспорта.

Большинство export views защищены `@staff_member_required`, но `export_userbids_view` сейчас не защищен декоратором. Это риск утечки персональных данных.

## Импорт и management-команды

Каталог команд: `mysite/catalog/management/commands/`.

Общие утилиты:

- `_parser_utils.py` - нормализация пустых значений, int/decimal, choice-полей, логирование преобразований.
- `_flat_brand_parser.py` - базовый класс `FlatBrandImportCommand` для импорта плоской папки изображений бренда.

`FlatBrandImportCommand`:

- группирует изображения по артикулу;
- ищет preview по stem с `zoom`;
- создает или обновляет объект камня по `article`;
- заменяет preview;
- удаляет старые `StoneImage`;
- создает новые примеры изображений;
- поддерживает `--source-dir`, `--dry-run`, `--test-mode`.

Команды на базе `FlatBrandImportCommand`:

- `parse_caesarstone_quartz`
- `parse_avant_quartz`
- `parse_avarus_quartz`
- `parse_noblle_quartz`
- `parse_grandex_acrylic`
- `parse_formax_acrylic`
- `parse_neomarm_acrylic`
- `parse_techgres_ceramics`

Другие импортные/служебные команды:

- `parse_primax_xml`
- `parse_wsp_quartz_folders`
- `parse_etnaquartz_main_collection`
- `parse_quartz_stones_from_old_site`
- `parse_ccd`
- `classify_stone_params`
- `remove_bad_acrylic_images`
- `ult`, `d`, `__`

Перед запуском импортов проверяй код конкретной команды: многие source paths захардкожены на локальные папки вида `D:\Project.com\САЙТ\...`.

## Шаблоны и assets

Основные шаблоны:

- `mysite/basic_page/templates/basic_page/front/` - Tilda-export HTML страниц.
- `mysite/basic_page/templates/basic_page/front/css|js|images/` - assets Tilda для основных страниц.
- `mysite/catalog/templates/fronttemp/` - шаблоны каталога и assets.
- `mysite/catalog/templates/fronttemp/quartz|acril|natural|ceramic/` - страницы каталогов и карточек.

При правках шаблонов учитывай:

- это импортированный HTML, там много автогенерированных классов и ссылок;
- часть путей к assets зависит от ручных `static()` маршрутов в `mysite/mysite/urls.py`;
- лучше делать точечные изменения, не форматировать весь HTML.

## 404

Есть два механизма:

- `catalog.views.custom_404_view`.
- `catalog.middleware.Custom404Middleware`, подключен последним в `MIDDLEWARE`.

Middleware заменяет любой response со статусом 404 на `fronttemp/404.html`.

В `catalog/urls.py` указан `handler404 = 'myapp.views.custom_404_view'`, но `myapp` в проекте нет. Кроме того, Django ожидает `handler404` в root URLConf, то есть в `mysite/mysite/urls.py`; переменная в подключаемом `catalog.urls` обычно не используется как глобальный handler.

## Кодировка

В выводе PowerShell часть русских строк может выглядеть как mojibake (`Рџ...`). В самих файлах встречается русскоязычный текст. Перед массовыми изменениями русских строк проверяй реальную кодировку файла и не делай механическую перекодировку всего проекта без отдельной задачи.

## Известные риски и технический долг

- Секреты и пароль БД лежат в `settings.py`.
- `DEBUG=True`.
- `ALLOWED_HOSTS=[]`.
- `export_userbids_view` не защищен `@staff_member_required`.
- `export_userbids_view` вызывает `export_userbids()` без `request`, хотя helper объявлен с параметром `request`.
- В `catalog/urls.py` `handler404` ссылается на несуществующий `myapp`.
- В `QuartzCatalog` возможна ошибка из-за пробела в имени шаблона `_stones_grid_Q.html `.
- `stone_detail_c` ссылается на `fronttemp/ceramic/about_ceramic.html`, а существующий шаблон называется `about_ceraimic.html`.
- Много повторяющегося кода в catalog detail views и catalog ListView-классах.
- Поле `priview_img` написано с опечаткой, но его нельзя просто переименовать без миграции и правки всех ссылок.
- `UserBidModel.AWtPP` имеет неочевидное имя, но уже используется в админке и экспорте.
- Импортные команды местами завязаны на абсолютные локальные Windows-пути.

## Рекомендации для будущих ИИ-агентов

- Перед изменением архитектуры каталога проверь модели, миграции, admin, templates и management-команды: они связаны через имена полей.
- Не переименовывай `priview_img`, `AcrilCatalog`, `AWtPP` и другие опечатанные идентификаторы без отдельного плана миграции.
- Для новых типов камня придется обновлять модель, admin, URLs, views, шаблоны каталога, импорт и экспорт.
- Для небольших UI-правок в Tilda HTML меняй только нужный фрагмент.
- Для импорта сначала запускай management-команды с `--dry-run` и при возможности `--test-mode`.
- После правок Django-кода минимум проверяй `python manage.py check` из папки `mysite`.
