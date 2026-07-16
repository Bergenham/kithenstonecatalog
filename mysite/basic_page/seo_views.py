from django.http import HttpResponse
from django.urls import NoReverseMatch, reverse

from catalog.models import AcrylicStone, CeramicsStone, NaturalStone, QuartzStone

from .seo import (
    SITE_DOMAIN,
    SITE_URL,
    STATIC_SEO_PAGES,
    absolute_reverse,
    sitemap_url,
)


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /export_panel",
        "Disallow: /PsstFuVvwLjdQvu",
        "Disallow: /t3WNStJaz2N5Cuw",
        "Disallow: /pnCne7xcIVMjG57",
        "Disallow: /Nor2qRjFD3wbKiy",
        "Disallow: /X5KD08OHn25yNLf",
        "Disallow: /tilda/",
        "",
        f"Sitemap: {SITE_URL}/sitemap.xml",
        f"Host: {SITE_DOMAIN}",
        "",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    urls = []
    for url_name, _title, priority, changefreq in STATIC_SEO_PAGES:
        try:
            urls.append(sitemap_url(absolute_reverse(url_name), priority, changefreq))
        except NoReverseMatch:
            continue

    stone_sources = [
        (QuartzStone, "catalog:stone_detail_q", "0.75", "weekly"),
        (AcrylicStone, "catalog:stone_detail_a", "0.75", "weekly"),
        (NaturalStone, "catalog:stone_detail_n", "0.65", "weekly"),
        (CeramicsStone, "catalog:stone_detail_c", "0.65", "weekly"),
    ]
    for model_class, url_name, priority, changefreq in stone_sources:
        for article in model_class.objects.filter(archive=False).values_list("article", flat=True):
            if not article:
                continue
            location = SITE_URL + reverse(url_name, kwargs={"article_get": article})
            urls.append(sitemap_url(location, priority, changefreq))

    payload = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    return HttpResponse(payload, content_type="application/xml; charset=utf-8")
