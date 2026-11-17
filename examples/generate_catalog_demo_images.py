"""Recreate the small, synthetic image fixtures for examples/catalog_bundle.

These colored swatches are sample assets, not photographs of real products.
Existing images are not overwritten.
"""

from pathlib import Path

from PIL import Image, ImageDraw


def main():
    root = Path(__file__).resolve().parent / 'catalog_bundle' / 'images'
    samples = [
        ('entity_001/preview.jpg', '#f0ece4', 'Quartz preview'),
        ('entity_001/example_01.jpg', '#dfd5c2', 'Quartz example 1'),
        ('entity_001/example_02.png', '#d4d9dc', 'Quartz example 2'),
        ('entity_002/preview.webp', '#a9b0b7', 'Acrylic preview'),
        ('entity_002/example_01.jpg', '#85939e', 'Acrylic example 1'),
    ]
    for relative, color, label in samples:
        path = root / relative
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        image = Image.new('RGB', (320, 200), color)
        ImageDraw.Draw(image).text((20, 85), f'DEMO: {label}', fill='#202020')
        image.save(path)
        print(path)


if __name__ == '__main__':
    main()
