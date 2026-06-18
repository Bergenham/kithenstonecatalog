import os
from collections import defaultdict


def find_duplicate_images(folder_path):
    # Словарь для группировки файлов по размеру
    size_dict = defaultdict(list)

    # Поддерживаемые расширения изображений
    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}

    # Проход по всем файлам в папке
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Проверка, что это файл и с правильным расширением
        if os.path.isfile(file_path):
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in valid_extensions:
                file_size = os.path.getsize(file_path)
                size_dict[file_size].append(filename)

    # Фильтрация дубликатов
    duplicates = {size: files for size, files in size_dict.items() if len(files) > 1}

    # Вывод результатов
    if duplicates:
        print("Найдены дубликаты по размеру файла:")
        for size, files in duplicates.items():
            print(f"\nРазмер: {size} байт")
            print("Файлы:", ", ".join(files))
    else:
        print("Дубликатов не найдено.")


if __name__ == "__main__":
    folder = input("Введите путь к папке с изображениями: ")
    find_duplicate_images(folder)