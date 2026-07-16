import json
from html import escape
from urllib.parse import urlparse
from xml.sax.saxutils import escape as xml_escape

from django.conf import settings
from django.urls import reverse
from django.utils.text import Truncator


SITE_NAME = getattr(settings, "SEO_SITE_NAME", "Maker Stone")
SITE_URL = getattr(settings, "SEO_SITE_URL", "https://makerstone.ru").rstrip("/")
SITE_DOMAIN = urlparse(SITE_URL).netloc or "makerstone.ru"
SITE_REGION = getattr(settings, "SEO_REGION", "Москва и Московская область")
SITE_PHONE = getattr(settings, "SEO_PHONE", "+7 985 967-11-88")
DEFAULT_OG_IMAGE = getattr(settings, "SEO_DEFAULT_OG_IMAGE", "/static/images/logo.png")

DEFAULT_DESCRIPTION = getattr(
    settings,
    "SEO_DEFAULT_DESCRIPTION",
    (
        "Maker Stone изготавливает столешницы, подоконники, панели, барные стойки "
        "и другие интерьерные изделия из кварцевого, акрилового, натурального "
        f"камня и керамики в регионе {SITE_REGION}."
    ),
)


STATIC_SEO_PAGES = [
    ("basic_page:main_page", "Главная", 1.0, "weekly"),
    ("basic_page:topstone", "Столешницы из камня", 0.9, "weekly"),
    ("basic_page:quartz", "Кварцевый камень", 0.85, "weekly"),
    ("basic_page:acryl", "Акриловый камень", 0.85, "weekly"),
    ("basic_page:natural", "Натуральный камень", 0.8, "weekly"),
    ("basic_page:porcelain", "Керамика и керамогранит", 0.8, "weekly"),
    ("basic_page:sills", "Подоконники из камня", 0.8, "monthly"),
    ("basic_page:sinks", "Раковины из камня", 0.8, "monthly"),
    ("basic_page:stairs", "Лестницы из камня", 0.8, "monthly"),
    ("basic_page:panels", "Стеновые панели из камня", 0.8, "monthly"),
    ("basic_page:bar", "Барные стойки из камня", 0.8, "monthly"),
    ("basic_page:fireplace", "Камины из камня", 0.75, "monthly"),
    ("basic_page:reception", "Ресепшн из камня", 0.75, "monthly"),
    ("basic_page:productions", "Производство изделий из камня", 0.75, "monthly"),
    ("basic_page:delivery", "Доставка изделий из камня", 0.65, "monthly"),
    ("basic_page:installation", "Монтаж изделий из камня", 0.65, "monthly"),
    ("basic_page:dimensions", "Замер изделий из камня", 0.65, "monthly"),
    ("basic_page:choice", "Выбор камня", 0.65, "monthly"),
    ("basic_page:about", "Контакты Maker Stone", 0.6, "monthly"),
    ("basic_page:politic_conf", "Политика конфиденциальности", 0.2, "yearly"),
    ("catalog:quartz_catalog", "Каталог кварцевого камня", 0.95, "daily"),
    ("catalog:acril_catalog", "Каталог акрилового камня", 0.95, "daily"),
    ("catalog:natural_catalog", "Каталог натурального камня", 0.85, "weekly"),
    ("catalog:ceramic_catalog", "Каталог керамики", 0.85, "weekly"),
]


CATALOG_SEO = {
    "quartz": {
        "title": "Каталог кварцевого камня - цвета, фактуры, бренды | Maker Stone",
        "h1": "Каталог кварцевого камня",
        "description": (
            "Каталог кварцевого камня Maker Stone: Caesarstone, Technistone, PrimaxQuartz, "
            "цвета, текстуры, фактуры и фото слэбов для столешниц, подоконников и панелей."
        ),
        "url_name": "catalog:quartz_catalog",
        "material": "Кварцевый камень",
        "schema_type": "CollectionPage",
    },
    "acryl": {
        "title": "Каталог акрилового камня - Hanex, Durasein, Primax | Maker Stone",
        "h1": "Каталог акрилового камня",
        "description": (
            "Каталог акрилового камня Maker Stone: Hanex, Durasein, Primax, популярные "
            "цвета и текстуры для бесшовных столешниц, раковин и интерьерных изделий."
        ),
        "url_name": "catalog:acril_catalog",
        "material": "Акриловый камень",
        "schema_type": "CollectionPage",
    },
    "natural": {
        "title": "Каталог натурального камня - мрамор, гранит, слэбы | Maker Stone",
        "h1": "Каталог натурального камня",
        "description": (
            "Каталог натурального камня Maker Stone: фото, цвета, текстуры и фактуры "
            "камня для столешниц, подоконников, стеновых панелей и декоративных изделий."
        ),
        "url_name": "catalog:natural_catalog",
        "material": "Натуральный камень",
        "schema_type": "CollectionPage",
    },
    "ceramic": {
        "title": "Каталог керамики и керамогранита для интерьера | Maker Stone",
        "h1": "Каталог керамики",
        "description": (
            "Каталог керамики и керамогранита Maker Stone: фактуры, цвета и фото "
            "материалов для столешниц, панелей, подоконников и других изделий."
        ),
        "url_name": "catalog:ceramic_catalog",
        "material": "Керамический камень",
        "schema_type": "CollectionPage",
    },
}


STONE_DETAIL_SEO = {
    "quartz": {
        "catalog_name": "Каталог кварцевого камня",
        "catalog_url_name": "catalog:quartz_catalog",
        "detail_url_name": "catalog:stone_detail_q",
        "material": "кварцевый камень",
    },
    "acryl": {
        "catalog_name": "Каталог акрилового камня",
        "catalog_url_name": "catalog:acril_catalog",
        "detail_url_name": "catalog:stone_detail_a",
        "material": "акриловый камень",
    },
    "natural": {
        "catalog_name": "Каталог натурального камня",
        "catalog_url_name": "catalog:natural_catalog",
        "detail_url_name": "catalog:stone_detail_n",
        "material": "натуральный камень",
    },
    "ceramic": {
        "catalog_name": "Каталог керамики",
        "catalog_url_name": "catalog:ceramic_catalog",
        "detail_url_name": "catalog:stone_detail_c",
        "material": "керамический камень",
    },
}


def absolute_url(path):
    if not path:
        return SITE_URL
    path = str(path)
    if path.startswith(("http://", "https://")):
        return path
    return f"{SITE_URL}/{path.lstrip('/')}"


def absolute_reverse(url_name, *args, **kwargs):
    return absolute_url(reverse(url_name, args=args, kwargs=kwargs))


def image_url(image_field):
    if image_field and getattr(image_field, "url", None):
        return absolute_url(image_field.url)
    return absolute_url(DEFAULT_OG_IMAGE)


def display_value(obj, field_name):
    value = getattr(obj, field_name, None)
    if value in ("", None):
        return ""
    display_method = getattr(obj, f"get_{field_name}_display", None)
    if callable(display_method):
        return str(display_method())
    return str(value)


def compact_description(text, length=160):
    return Truncator(" ".join(str(text).split())).chars(length)


def json_ld(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def organization_schema():
    return {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": SITE_NAME,
        "url": SITE_URL,
        "logo": absolute_url(DEFAULT_OG_IMAGE),
        "image": absolute_url(DEFAULT_OG_IMAGE),
        "telephone": SITE_PHONE,
        "areaServed": SITE_REGION,
        "sameAs": [
            "https://vk.com/makerstone",
            "https://wa.me/79859671188",
        ],
        "contactPoint": {
            "@type": "ContactPoint",
            "telephone": SITE_PHONE,
            "contactType": "customer service",
            "areaServed": "RU",
            "availableLanguage": "Russian",
        },
    }


def breadcrumb_schema(items):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index,
                "name": name,
                "item": url,
            }
            for index, (name, url) in enumerate(items, start=1)
        ],
    }


def catalog_seo_context(request, catalog_key):
    data = CATALOG_SEO[catalog_key]
    canonical = absolute_reverse(data["url_name"])
    filtered = bool(request.GET)
    robots = "noindex, follow" if filtered else "index, follow"
    title = data["title"]
    description = data["description"]

    schema = [
        organization_schema(),
        breadcrumb_schema([
            ("Главная", SITE_URL),
            (data["h1"], canonical),
        ]),
        {
            "@context": "https://schema.org",
            "@type": data["schema_type"],
            "name": data["h1"],
            "description": description,
            "url": canonical,
            "isPartOf": {
                "@type": "WebSite",
                "name": SITE_NAME,
                "url": SITE_URL,
            },
        },
    ]

    return {
        "seo_title": title,
        "seo_h1": data["h1"],
        "seo_description": description,
        "seo_canonical": canonical,
        "seo_robots": robots,
        "seo_og_url": canonical,
        "seo_og_title": title,
        "seo_og_description": description,
        "seo_og_image": absolute_url(DEFAULT_OG_IMAGE),
        "seo_og_type": "website",
        "seo_site_name": SITE_NAME,
        "seo_json_ld": json_ld(schema),
    }


def stone_seo_context(stone, catalog_key):
    data = STONE_DETAIL_SEO[catalog_key]
    canonical = absolute_reverse(data["detail_url_name"], article_get=stone.article)
    image = image_url(stone.priview_img)
    brand = display_value(stone, "brand_stone")
    color = display_value(stone, "color")
    texture = display_value(stone, "texture")
    faktura = display_value(stone, "faktura")
    country = display_value(stone, "country")
    material = display_value(stone, "material") or data["material"]

    title_parts = [stone.name_stone]
    if brand:
        title_parts.append(brand)
    title = f"{' - '.join(title_parts)} | {material} | {SITE_NAME}"

    details = []
    if brand:
        details.append(f"бренд {brand}")
    if color:
        details.append(f"цвет {color}")
    if texture:
        details.append(f"текстура {texture}")
    if faktura:
        details.append(f"фактура {faktura}")
    if country:
        details.append(f"страна {country}")
    if stone.thickness:
        details.append(f"толщина {stone.thickness} мм")

    detail_sentence = f" {', '.join(details)}." if details else ""
    description = compact_description(
        (
            f"{stone.name_stone}: {data['material']} для столешниц, подоконников и "
            f"интерьерных изделий.{detail_sentence} Фото, характеристики и заявка "
            f"на расчет в {SITE_NAME}."
        )
    )

    product_schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": stone.name_stone,
        "description": description,
        "image": [image],
        "url": canonical,
        "sku": stone.article or str(stone.pk),
        "category": data["material"],
        "material": material,
        "color": color or None,
        "brand": {
            "@type": "Brand",
            "name": brand or SITE_NAME,
        },
    }
    if stone.abt_prise:
        product_schema["offers"] = {
            "@type": "Offer",
            "url": canonical,
            "priceCurrency": "RUB",
            "price": str(stone.abt_prise),
            "availability": "https://schema.org/InStock",
        }

    schema = [
        organization_schema(),
        breadcrumb_schema([
            ("Главная", SITE_URL),
            (data["catalog_name"], absolute_reverse(data["catalog_url_name"])),
            (stone.name_stone, canonical),
        ]),
        {key: value for key, value in product_schema.items() if value is not None},
    ]

    return {
        "seo_title": title,
        "seo_description": description,
        "seo_canonical": canonical,
        "seo_robots": "index, follow",
        "seo_og_url": canonical,
        "seo_og_title": title,
        "seo_og_description": description,
        "seo_og_image": image,
        "seo_og_type": "product",
        "seo_site_name": SITE_NAME,
        "seo_json_ld": json_ld(schema),
    }


def sitemap_url(location, priority="0.5", changefreq="monthly"):
    return (
        "  <url>\n"
        f"    <loc>{xml_escape(location)}</loc>\n"
        f"    <changefreq>{xml_escape(str(changefreq))}</changefreq>\n"
        f"    <priority>{xml_escape(str(priority))}</priority>\n"
        "  </url>"
    )


def html_attr(value):
    return escape(str(value), quote=True)
