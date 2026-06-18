from django.core.management.base import BaseCommand
from django.db import transaction
from catalog.models import AcrylicStone, StoneImage


class Command(BaseCommand):
    help = (
        "Удаляет последние 10 изображений StoneImage "
        "для каждого AcrylicStone."
    )

    @transaction.atomic
    def handle(self, *args, **options):

        total_deleted = 0

        acrylic_stones = AcrylicStone.objects.all()

        self.stdout.write(
            self.style.SUCCESS(
                f"Найдено акриловых камней: {acrylic_stones.count()}"
            )
        )

        for stone in acrylic_stones:

            images = (
                StoneImage.objects
                .filter(stone=stone)
                .order_by("id")
            )

            images_count = images.count()

            if images_count <= 10:
                self.stdout.write(
                    self.style.WARNING(
                        f"[SKIP] {stone.name_stone} "
                        f"(изображений: {images_count})"
                    )
                )
                continue

            bad_images = images.order_by("-id")[:10]

            self.stdout.write(
                f"\n[{stone.name_stone}] "
                f"Удаляем последние 10 изображений "
                f"из {images_count}"
            )

            for image_obj in bad_images:

                image_name = image_obj.image.name

                try:
                    # удаление файла из media
                    image_obj.image.delete(save=False)

                    # удаление записи из БД
                    image_obj.delete()

                    total_deleted += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ {image_name}"
                        )
                    )

                except Exception as exc:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ✗ Ошибка удаления {image_name}: {exc}"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nГотово. Удалено изображений: {total_deleted}"
            )
        )