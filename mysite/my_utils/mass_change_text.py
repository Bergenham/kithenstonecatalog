import os
import re

# Укажите путь к директории с HTML-файлами
directory_path = r"/mysite/basic_page/templates/basic_page/front"

# Словарь замен: оригинальный URL -> новая Django-ссылка
replacements = {
    '<div class="t228__right_buttons_but"><a href="{% url \'basic_page:\' %}"':
        '<div class="t228__right_buttons_but"><a href="{% url \'basic_page:calculator\' %}"',

    '<div class="t228__right_buttons_but"> <a href="{% url \'basic_page:\' %}"':
        '<div class="t228__right_buttons_but"> <a href="{% url \'basic_page:calculator\' %}"',

    "<div class='t228__right_buttons_but'><a href='{% url \"basic_page:\" %}'":
        "<div class='t228__right_buttons_but'><a href='{% url \"basic_page:calculator\" %}'",

    "<div class='t228__right_buttons_but'> <a href='{% url \"basic_page:\" %}'":
        "<div class='t228__right_buttons_but'> <a href='{% url \"basic_page:calculator\" %}'",

    '<div class="t228__right_buttons_but"><a href="{% url \'basic_page:\' %}" target="" class="t-btn t-btn_md "':
        '<div class="t228__right_buttons_but"><a href="{% url \'basic_page:calculator\' %}" target="" class="t-btn t-btn_md "',

    "<div class='t228__right_buttons_but'><a href='{% url \"basic_page:\" %}' target='' class='t-btn t-btn_md '":
        "<div class='t228__right_buttons_but'><a href='{% url \"basic_page:calculator\" %}' target='' class='t-btn t-btn_md '"
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