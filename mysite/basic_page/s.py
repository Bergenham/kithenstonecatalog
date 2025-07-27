import os
import re

# Укажите путь к директории с HTML-файлами
directory_path = r"C:\Users\Bergenham\Documents\kithenstonecatalog-main\mysite\basic_page\templates\basic_page\front"

# Словарь замен: оригинальный URL -> новая Django-ссылка
replacements = {
    "https://makerstone.ru/": "{% url 'basic_page:main_page' %}",
    "https://makerstone.ru/main": "{% url 'basic_page:main_page_2' %}",
    "https://makerstone.ru/main_page": "{% url 'basic_page:main_page_2' %}",
    "https://makerstone.ru/topstone": "{% url 'basic_page:topstone' %}",
    "https://makerstone.ru/production": "{% url 'basic_page:productions' %}",
    "https://makerstone.ru/delivery": "{% url 'basic_page:delivery' %}",
    "https://makerstone.ru/installation": "{% url 'basic_page:installation' %}",
    "https://makerstone.ru/stairs": "{% url 'basic_page:stairs' %}",
    "https://makerstone.ru/sinks": "{% url 'basic_page:sinks' %}",
    "https://makerstone.ru/sills": "{% url 'basic_page:sills' %}",
    "https://makerstone.ru/dimensions": "{% url 'basic_page:dimensions' %}",
    "https://makerstone.ru/privacy": "{% url 'basic_page:politic_conf' %}",
    "https://makerstone.ru/panels": "{% url 'basic_page:panels' %}",
    "https://makerstone.ru/bar": "{% url 'basic_page:bar' %}",
    "https://makerstone.ru/fireplace": "{% url 'basic_page:fireplace' %}",
    "https://makerstone.ru/quartz": "{% url 'basic_page:quartz' %}",
    "https://makerstone.ru/acryl": "{% url 'basic_page:acryl' %}",
    "https://makerstone.ru/natural": "{% url 'basic_page:natural' %}",
    "https://makerstone.ru/porcelain": "{% url 'basic_page:porcelain' %}",
    "https://makerstone.ru/reception": "{% url 'basic_page:reception' %}",
    "https://makerstone.ru/selection": "{% url 'basic_page:selection' %}",
    "https://makerstone.ru/otheracrylstone": "{% url 'basic_page:otheracrylstone' %}",
    "https://makerstone.ru/other": "{% url 'basic_page:other' %}",
    "https://makerstone.ru/choice": "{% url 'basic_page:choice' %}",
    "https://makerstone.ru/trend/hopetoun": "{% url 'basic_page:media' %}",
    "https://makerstone.ru/about": "{% url 'basic_page:about' %}",
    "https://makerstone.ru/partner": "{% url 'basic_page:partner' %}",
    "https://makerstone.ru/calculator": "{% url 'basic_page:calculator' %}",
    "https://makerstone.ru/zamer": "{% url 'basic_page:zamer' %}",
}

# Компилируем регулярное выражение для поиска всех URL
pattern = re.compile("|".join(re.escape(url) for url in replacements.keys()))

# Обрабатываем все HTML-файлы в указанной директории
for filename in os.listdir(directory_path):
    if filename.lower().endswith('.html') and filename != "404.html" :
        filepath = os.path.join(directory_path, filename)

        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()

        # Заменяем все вхождения URL
        new_content = pattern.sub(lambda match: replacements[match.group(0)], content)

        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(new_content)

        print(f"Обработан: {filename}")

print("Все файлы успешно обновлены!")