import base64
import json
import mimetypes
import os
import re
import time
import unicodedata
from pathlib import Path
from urllib import error, request

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from catalog.models import Stone


PROMPT_TEMPLATE = """Ты анализируешь изображение камня для каталога.
Определи только следующие параметры по изображению: color, texture, faktura.

Доступные варианты для этой модели:
{choice_context}

Правила ответа:
1. Верни только JSON без markdown и без пояснений.
2. Сначала выбирай значения из доступных вариантов выше.
3. Для color: если ни один доступный цвет явно не подходит изображению, верни новый короткий цвет на русском языке.
4. Для texture и faktura: выбирай ближайший доступный вариант, если он не противоречит изображению.
5. Если уверенности нет, выбери наиболее вероятный вариант.
6. Формат строго такой:
{{"color": "значение", "texture": "значение", "faktura": "значение"}}
"""

RETRY_STATUS_CODES = {408, 429, 500, 502, 503, 504}

CHOICE_ALIASES = {
    "мрамор": "мраморная",
    "мраморный": "мраморная",
    "однотонный": "однотонная",
    "однородная": "однотонная",
    "бетонный": "бетон",
    "матовый": "матовая",
    "полированный": "полированная",
    "полировка": "полированная",
    "шелковистый": "шелковистая",
    "перламутр": "жемчужная",
}


CYRILLIC_MAP = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


class VisionClient:
    def __init__(self, api_key, model, timeout, retries=2):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.retries = max(0, retries)

    def classify(self, image_path, prompt):
        image_url = self._build_data_url(image_path)
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": image_url},
                    ],
                }
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            "https://api.openai.com/v1/responses",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        for attempt in range(self.retries + 1):
            try:
                with request.urlopen(req, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                break
            except error.HTTPError as exc:
                details = exc.read().decode("utf-8", errors="replace")
                if exc.code in RETRY_STATUS_CODES and attempt < self.retries:
                    time.sleep(self._retry_delay(attempt))
                    continue
                raise CommandError(f"OpenAI API HTTP {exc.code}: {details}") from exc
            except error.URLError as exc:
                if attempt < self.retries:
                    time.sleep(self._retry_delay(attempt))
                    continue
                raise CommandError(f"OpenAI API connection error: {exc}") from exc

        text = self._extract_text(data)
        if not text:
            raise CommandError(f"OpenAI API returned no text payload: {data}")
        return self._extract_json(text), text

    @staticmethod
    def _retry_delay(attempt):
        return min(2 ** attempt, 8)

    def _build_data_url(self, image_path):
        mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    @staticmethod
    def _extract_text(data):
        output_text = data.get("output_text")
        if output_text:
            return output_text.strip()

        parts = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                text = content.get("text")
                if text:
                    parts.append(text)
        return "\n".join(parts).strip()

    @staticmethod
    def _extract_json(raw_text):
        raw_text = raw_text.strip()
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
            if not match:
                raise CommandError(f"Model did not return valid JSON: {raw_text}")
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError as exc:
                raise CommandError(f"Model returned unparsable JSON: {raw_text}") from exc


class ChoiceUpdater:
    FIELD_TO_CLASS = {
        "color": "ColorChoices",
        "texture": "TextureChoices",
        "faktura": "FakturaChoices",
    }

    def __init__(self, models_path):
        self.models_path = Path(models_path)

    def add_choice(self, model_name, field_name, label):
        class_name = self.FIELD_TO_CLASS[field_name]
        lines = self.models_path.read_text(encoding="utf-8").splitlines()

        model_start = self._find_line(lines, rf"^class {re.escape(model_name)}\(Stone\):\s*$")
        if model_start is None:
            raise CommandError(f"Model {model_name} not found in {self.models_path}")

        class_start = self._find_line(
            lines[model_start + 1:],
            rf"^\s{{4}}class {re.escape(class_name)}\(models\.TextChoices\):\s*$",
        )
        if class_start is None:
            raise CommandError(f"{model_name}.{class_name} not found in {self.models_path}")
        class_start += model_start + 1

        insert_at = class_start + 1
        while insert_at < len(lines):
            line = lines[insert_at]
            if not line.startswith(" " * 8):
                break
            if line.strip():
                insert_at += 1
                continue
            next_line = lines[insert_at + 1] if insert_at + 1 < len(lines) else ""
            if not next_line.startswith(" " * 8):
                break
            insert_at += 1

        constant_name = self._make_constant_name(lines[class_start:insert_at], label)
        new_line = f'        {constant_name} = "{label}", "{label}"'
        lines.insert(insert_at, new_line)
        self.models_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return constant_name

    @staticmethod
    def _find_line(lines, pattern):
        regex = re.compile(pattern)
        for index, line in enumerate(lines):
            if regex.match(line):
                return index
        return None

    def _make_constant_name(self, class_lines, label):
        transliterated = "".join(CYRILLIC_MAP.get(ch, ch) for ch in label.lower())
        normalized = unicodedata.normalize("NFKD", transliterated)
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        normalized = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").upper()
        if not normalized:
            normalized = "VALUE"

        existing_names = set()
        for line in class_lines:
            match = re.match(r"^\s{8}([A-Z0-9_]+)\s*=", line)
            if match:
                existing_names.add(match.group(1))

        candidate = normalized
        suffix = 2
        while candidate in existing_names:
            candidate = f"{normalized}_{suffix}"
            suffix += 1
        return candidate


class Command(BaseCommand):
    help = (
        "Классифицирует color/texture/faktura по изображениям камней через vision API, "
        "сохраняет совпавшие значения в БД и пишет неподдержанные варианты в JSON."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            default=os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini"),
            help="Название vision-модели API.",
        )
        parser.add_argument(
            "--api-key",
            default=os.getenv("OPENAI_API_KEY"),
            help="API key. По умолчанию берётся из OPENAI_API_KEY.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Лимит экземпляров на один запуск.",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=0.0,
            help="Пауза между API-запросами в секундах.",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=120,
            help="HTTP timeout для API.",
        )
        parser.add_argument(
            "--retries",
            type=int,
            default=2,
            help="Количество повторов для временных ошибок API.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Не сохранять изменения в БД и не менять models.py.",
        )
        parser.add_argument(
            "--update-models-choices",
            action="store_true",
            help="Добавлять новые choice-значения в catalog/models.py.",
        )
        parser.add_argument(
            "--report",
            default="stone_ai_unknown_choices.json",
            help="Путь к JSON-отчёту с неизвестными значениями.",
        )

    def handle(self, *args, **options):
        api_key = options["api_key"]
        if not api_key:
            raise CommandError("Не задан OPENAI_API_KEY или --api-key")

        report_path = self._resolve_report_path(options["report"])
        client = VisionClient(api_key, options["model"], options["timeout"], options["retries"])
        updater = ChoiceUpdater(Path(__file__).resolve().parents[2] / "models.py")
        unknown_report = self._load_unknown_report(report_path)

        subclasses = [
            subclass for subclass in self._iter_concrete_subclasses(Stone)
            if not subclass._meta.abstract
        ]
        total_processed = 0
        total_saved = 0
        total_skipped = 0
        total_unknown = 0
        total_errors = 0

        for model_class in subclasses:
            queryset = model_class.objects.all().order_by("pk")
            if options["limit"] is not None:
                queryset = queryset[:options["limit"]]

            self.stdout.write(f"\n[{model_class.__name__}] найдено: {queryset.count()}")

            for stone in queryset:
                pending_fields = self._get_pending_fields(stone)
                if not pending_fields:
                    total_skipped += 1
                    self.stdout.write(f"[SKIP] {model_class.__name__}#{stone.pk}: все поля заполнены")
                    continue

                image_path = self._resolve_image_path(stone)
                if image_path is None:
                    total_skipped += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"[SKIP] {model_class.__name__}#{stone.pk}: изображение не найдено"
                        )
                    )
                    continue

                prompt = self._build_prompt(model_class)
                try:
                    ai_json, raw_text = client.classify(image_path, prompt)
                except CommandError as exc:
                    if "OpenAI API HTTP 401" in str(exc) or "OpenAI API HTTP 403" in str(exc):
                        raise
                    total_errors += 1
                    self._merge_unknown_report(
                        unknown_report,
                        model_class.__name__,
                        stone.pk,
                        {"_error": str(exc)},
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            f"[ERROR] {model_class.__name__}#{stone.pk}: {exc}"
                        )
                    )
                    continue
                total_processed += 1

                unknown_fields = {}
                changed_fields = {}
                for field_name in pending_fields:
                    raw_value = self._normalize_ai_value(ai_json.get(field_name))
                    if not raw_value:
                        continue
                    matched_value = self._match_choice_value(model_class, field_name, raw_value)
                    if matched_value is not None:
                        changed_fields[field_name] = matched_value
                    else:
                        unknown_fields[field_name] = raw_value

                if unknown_fields:
                    total_unknown += 1
                    self._merge_unknown_report(unknown_report, model_class.__name__, stone.pk, unknown_fields)

                    if options["update_models_choices"] and not options["dry_run"]:
                        for field_name, label in unknown_fields.items():
                            constant_name = updater.add_choice(model_class.__name__, field_name, label)
                            self.stdout.write(
                                self.style.WARNING(
                                    f"[CHOICE+] {model_class.__name__}.{field_name}: "
                                    f'{constant_name} = "{label}"'
                                )
                            )
                            changed_fields[field_name] = label

                if changed_fields:
                    for field_name, value in changed_fields.items():
                        setattr(stone, field_name, value)
                    if not options["dry_run"]:
                        stone.save(update_fields=list(changed_fields.keys()))
                    total_saved += 1

                self.stdout.write(
                    f"[AI] {model_class.__name__}#{stone.pk} "
                    f"fields={pending_fields} image={image_path.name} "
                    f"response={json.dumps(ai_json, ensure_ascii=False)}"
                )
                if raw_text.strip() != json.dumps(ai_json, ensure_ascii=False):
                    self.stdout.write(f"      raw={raw_text}")
                if changed_fields:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"      saved={json.dumps(changed_fields, ensure_ascii=False)}"
                        )
                    )
                if unknown_fields:
                    self.stdout.write(
                        self.style.WARNING(
                            f"      unknown={json.dumps(unknown_fields, ensure_ascii=False)}"
                        )
                    )

                if options["sleep"] > 0:
                    time.sleep(options["sleep"])

        if not options["dry_run"]:
            self._write_unknown_report(report_path, unknown_report)
        else:
            self.stdout.write("[DRY RUN] JSON report not written")

        self.stdout.write(
            self.style.SUCCESS(
                "\nГотово: "
                f"api_calls={total_processed}, saved={total_saved}, "
                f"skipped={total_skipped}, unknown={total_unknown}, errors={total_errors}, "
                f"report={report_path}"
            )
        )

    def _build_prompt(self, model_class):
        return PROMPT_TEMPLATE.format(
            choice_context=self._format_choice_context(model_class)
        )

    def _format_choice_context(self, model_class):
        lines = []
        for field_name in ("color", "texture", "faktura"):
            field = model_class._meta.get_field(field_name)
            choices = []
            for value, label in field.flatchoices:
                if value in ("", None):
                    continue
                if str(value) == str(label):
                    choices.append(str(value))
                else:
                    choices.append(f"{value} ({label})")
            lines.append(f"- {field_name}: " + "; ".join(choices))
        return "\n".join(lines)

    def _resolve_report_path(self, report_value):
        path = Path(report_value)
        if not path.is_absolute():
            path = Path(settings.BASE_DIR) / report_value
        return path

    def _load_unknown_report(self, report_path):
        if not report_path.exists():
            return {}
        try:
            return json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"Не удалось прочитать report JSON {report_path}: {exc}") from exc

    def _write_unknown_report(self, report_path, payload):
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _merge_unknown_report(self, report, model_name, stone_id, unknown_fields):
        model_bucket = report.setdefault(model_name, {})
        stone_bucket = model_bucket.setdefault(str(stone_id), {})
        stone_bucket.update(unknown_fields)

    def _resolve_image_path(self, stone):
        candidates = []
        if getattr(stone, "priview_img", None) and stone.priview_img.name:
            candidates.append(Path(settings.MEDIA_ROOT) / stone.priview_img.name)
        first_example = stone.example_images.order_by("pk").first()
        if first_example and first_example.image and first_example.image.name:
            candidates.append(Path(settings.MEDIA_ROOT) / first_example.image.name)

        for path in candidates:
            if path.exists():
                return path
        return None

    def _get_pending_fields(self, stone):
        pending = []
        for field_name in ("color", "texture", "faktura"):
            if hasattr(stone, field_name) and not getattr(stone, field_name):
                pending.append(field_name)
        return pending

    def _normalize_ai_value(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return str(value).strip() or None

    def _match_choice_value(self, model_class, field_name, candidate):
        field = model_class._meta.get_field(field_name)
        choice_map = {}
        for value, label in field.flatchoices:
            if value in ("", None):
                continue
            choice_map[self._normalize_choice_key(value)] = value
            choice_map[self._normalize_choice_key(label)] = value

        for key in self._candidate_choice_keys(candidate):
            matched = choice_map.get(key)
            if matched is not None:
                return matched
        return None

    def _candidate_choice_keys(self, candidate):
        key = self._normalize_choice_key(candidate)
        keys = [key]
        alias = CHOICE_ALIASES.get(key)
        if alias:
            keys.append(self._normalize_choice_key(alias))
        return keys

    @staticmethod
    def _normalize_choice_key(value):
        text = str(value).strip().casefold().replace("ё", "е")
        return re.sub(r"[^0-9a-zа-я]+", "", text)

    def _iter_concrete_subclasses(self, base_class):
        for subclass in base_class.__subclasses__():
            yield subclass
            yield from self._iter_concrete_subclasses(subclass)
