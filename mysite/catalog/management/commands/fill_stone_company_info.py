import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import AcrylicStone, CeramicsStone, QuartzStone


DEFAULT_SOURCE_PATH = Path(r"D:\Documents\OBS\NOTE\das 1.md")
URL_RE = re.compile(r"https?://[^\]\s]+")
INFO_LINE_RE = re.compile(r"^\s*-\s*([^:]+?)\s*:\s*\[(.*?)\]\s*$")

MODEL_CLASSES = (QuartzStone, AcrylicStone, CeramicsStone)
MODEL_BRAND_ALIASES = {
    QuartzStone: {
        "primax": "primaxquartz",
    },
}


@dataclass(frozen=True)
class CompanyInfo:
    company: str
    country: str
    certificate_url: str


def normalize_key(value):
    return re.sub(r"[^0-9a-z]+", "", str(value).casefold())


def is_blank(value):
    return value is None or str(value).strip() == ""


class CompanyInfoSource:
    def __init__(self, source_path):
        self.source_path = Path(source_path)
        self.by_key = self._load()

    def _load(self):
        if not self.source_path.exists():
            raise CommandError(f"Source file not found: {self.source_path}")
        if not self.source_path.is_file():
            raise CommandError(f"Source path is not a file: {self.source_path}")

        raw_text = self.source_path.read_text(encoding="utf-8-sig")
        first_section = raw_text.split("____", 1)[0]
        result = {}

        for line_number, line in enumerate(first_section.splitlines(), start=1):
            if not line.strip():
                continue

            match = INFO_LINE_RE.match(line)
            if not match:
                continue

            company = match.group(1).strip()
            payload = match.group(2).strip()
            if ";" not in payload:
                raise CommandError(
                    f"Cannot parse country in {self.source_path}:{line_number}: {line}"
                )

            country = payload.split(";", 1)[0].strip()
            url_match = URL_RE.search(payload)
            if not url_match:
                raise CommandError(
                    f"Cannot parse certificate URL in {self.source_path}:{line_number}: {line}"
                )

            info = CompanyInfo(
                company=company,
                country=country,
                certificate_url=url_match.group(0).rstrip(".,;"),
            )
            result[normalize_key(company)] = info

        if not result:
            raise CommandError(f"No company info found in source file: {self.source_path}")
        return result

    def get(self, company):
        key = normalize_key(company)
        return self.by_key.get(key) or self.by_key.get(self._source_alias(key))

    @staticmethod
    def _source_alias(key):
        aliases = {
            "primaxquartz": "primax",
        }
        return aliases.get(key, key)

    def known_keys(self):
        return set(self.by_key)


class Command(BaseCommand):
    help = (
        "Fill empty brand_stone, country and link_serf for quartz, acrylic and "
        "ceramics stones from a markdown company info file."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            default=str(DEFAULT_SOURCE_PATH),
            help="Markdown file with company info.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show planned updates without saving them.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Process only first N rows per model.",
        )
        parser.add_argument(
            "--company",
            action="append",
            default=[],
            help="Limit processing to one company. Can be passed several times.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Rewrite existing field values. By default existing values are not touched.",
        )

    def handle(self, *args, **options):
        source = CompanyInfoSource(options["source"])
        company_filter = {normalize_key(value) for value in options["company"]}
        dry_run = options["dry_run"]
        overwrite = options["overwrite"]

        total_stats = Counter()
        updates_by_company = defaultdict(Counter)

        for model_class in MODEL_CLASSES:
            model_stats = self._process_model(
                model_class=model_class,
                source=source,
                company_filter=company_filter,
                dry_run=dry_run,
                overwrite=overwrite,
                limit=options["limit"],
                updates_by_company=updates_by_company,
            )
            total_stats.update(model_stats)

        self.stdout.write("")
        for company_key in sorted(updates_by_company):
            stats = updates_by_company[company_key]
            self.stdout.write(
                f"[COMPANY] {company_key}: updated={stats['updated']} "
                f"unchanged={stats['unchanged']} skipped={stats['skipped']}"
            )

        prefix = "DRY RUN finished" if dry_run else "Finished"
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}: scanned={total_stats['scanned']}, "
                f"updated={total_stats['updated']}, unchanged={total_stats['unchanged']}, "
                f"skipped={total_stats['skipped']}, errors={total_stats['errors']}"
            )
        )

    def _process_model(
        self,
        *,
        model_class,
        source,
        company_filter,
        dry_run,
        overwrite,
        limit,
        updates_by_company,
    ):
        stats = Counter()
        queryset = model_class.objects.all().order_by("pk")
        if limit is not None:
            queryset = queryset[:limit]

        self.stdout.write(f"\n[{model_class.__name__}] rows={queryset.count()}")

        brand_lookup = self._choice_lookup(model_class, "brand_stone")

        for stone in queryset:
            stats["scanned"] += 1
            company_token = self._resolve_company_token(stone, source.known_keys(), brand_lookup)
            if not company_token:
                stats["skipped"] += 1
                updates_by_company["unknown"]["skipped"] += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"[SKIP] {model_class.__name__}#{stone.pk}: "
                        f"cannot detect company from article={stone.article!r}"
                    )
                )
                continue

            info = source.get(company_token)
            if info is None:
                stats["skipped"] += 1
                company_key = normalize_key(company_token)
                updates_by_company[company_key]["skipped"] += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"[SKIP] {model_class.__name__}#{stone.pk}: "
                        f"no source info for company={company_token!r}"
                    )
                )
                continue

            info_company_key = normalize_key(info.company)
            if company_filter and info_company_key not in company_filter:
                stats["skipped"] += 1
                updates_by_company[info_company_key]["skipped"] += 1
                continue

            changes = self._build_changes(
                stone=stone,
                model_class=model_class,
                info=info,
                brand_lookup=brand_lookup,
                overwrite=overwrite,
            )
            if not changes:
                stats["unchanged"] += 1
                updates_by_company[normalize_key(info.company)]["unchanged"] += 1
                continue

            stats["updated"] += 1
            updates_by_company[normalize_key(info.company)]["updated"] += 1
            self._write_update_line(model_class, stone, info, changes, dry_run)

            if not dry_run:
                with transaction.atomic():
                    for field_name, value in changes.items():
                        setattr(stone, field_name, value)
                    stone.save(update_fields=sorted(changes))

        return stats

    def _build_changes(self, *, stone, model_class, info, brand_lookup, overwrite):
        changes = {}

        brand_value = self._brand_value_for_info(model_class, info, brand_lookup)
        if brand_value is None and (overwrite or is_blank(stone.brand_stone)):
            self.stdout.write(
                self.style.WARNING(
                    f"[WARN] {model_class.__name__}#{stone.pk}: "
                    f"company={info.company!r} is not in brand_stone choices"
                )
            )
        elif self._should_fill(stone.brand_stone, overwrite):
            changes["brand_stone"] = brand_value

        if self._should_fill(stone.country, overwrite):
            changes["country"] = info.country

        if self._should_fill(stone.link_serf, overwrite):
            changes["link_serf"] = info.certificate_url

        return changes

    @staticmethod
    def _should_fill(current_value, overwrite):
        return overwrite or is_blank(current_value)

    @staticmethod
    def _brand_value_for_info(model_class, info, brand_lookup):
        company_key = normalize_key(info.company)
        alias_key = MODEL_BRAND_ALIASES.get(model_class, {}).get(company_key, company_key)
        return brand_lookup.get(alias_key) or brand_lookup.get(company_key)

    def _resolve_company_token(self, stone, source_keys, brand_lookup):
        if not is_blank(stone.brand_stone):
            return str(stone.brand_stone).strip()

        article = str(stone.article or "").strip()
        if not article:
            return None

        candidates = self._article_company_candidates(article)
        known_keys = set(source_keys) | set(brand_lookup)
        for candidate in candidates:
            if normalize_key(candidate) in known_keys:
                return candidate
        return candidates[0] if candidates else None

    @staticmethod
    def _article_company_candidates(article):
        parts = [part.strip() for part in article.split("_") if part.strip()]
        if not parts:
            return []

        candidates = []
        for start in range(len(parts) - 1, -1, -1):
            candidate = "_".join(parts[start:])
            candidates.append(candidate)
            compact_candidate = "".join(parts[start:])
            if compact_candidate != candidate:
                candidates.append(compact_candidate)

        return candidates

    @staticmethod
    def _choice_lookup(model_class, field_name):
        field = model_class._meta.get_field(field_name)
        result = {}
        for value, label in field.flatchoices:
            if value in ("", None):
                continue
            result[normalize_key(value)] = value
            result[normalize_key(label)] = value
        return result

    def _write_update_line(self, model_class, stone, info, changes, dry_run):
        action = "WOULD UPDATE" if dry_run else "UPDATE"
        changes_text = ", ".join(f"{field}={value!r}" for field, value in changes.items())
        self.stdout.write(
            f"[{action}] {model_class.__name__}#{stone.pk} "
            f"article={stone.article!r} company={info.company}: {changes_text}"
        )
