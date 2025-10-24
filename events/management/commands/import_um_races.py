import csv
import random
import re
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, Optional, Tuple

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from events.models import Event, EventCategory


@dataclass
class EventRecord:
    """Aggregated information for a single event coming from the CSV dataset."""

    year: int
    base_name: str
    country_code: Optional[str]
    country: str
    original_name: str
    date_label: str
    original_start_date: date
    original_end_date: Optional[date]
    finishers: int = 0
    distance_labels: set[str] = field(default_factory=set)
    rows: int = 0
    generated_start_date: Optional[date] = None
    generated_end_date: Optional[date] = None
    registration_open_date: Optional[date] = None
    registration_close_date: Optional[date] = None

    def add_distance(self, distance: Optional[str]) -> None:
        if distance:
            self.distance_labels.add(distance.strip())

    def increase_finishers(self, value: Optional[int]) -> None:
        if value is None:
            return
        self.finishers = max(self.finishers, value)

    @property
    def title(self) -> str:
        return f"{self.base_name} {self.year}"

    @property
    def city(self) -> str:
        return self.base_name

    @property
    def venue(self) -> str:
        return self.base_name

    def build_description(self) -> str:
        def _format_distance_labels(labels: list[str]) -> str:
            if not labels:
                return ""
            if len(labels) == 1:
                return labels[0]
            if len(labels) == 2:
                return " and ".join(labels)
            return ", ".join(labels[:-1]) + f", and {labels[-1]}"

        location_bits = []
        if self.base_name:
            location_bits.append(self.base_name)
        if self.country and self.country != "Unknown":
            location_bits.append(self.country)
        location_text = ", ".join(location_bits) if location_bits else "this destination"

        lines: list[str] = []
        lines.append(f"{self.original_name} welcomes endurance athletes to {location_text}.")

        if self.generated_start_date:
            start_text = self.generated_start_date.strftime("%B %d, %Y")
            if self.generated_end_date and self.generated_end_date != self.generated_start_date:
                end_text = self.generated_end_date.strftime("%B %d, %Y")
                lines.append(
                    f"The {self.year} edition runs from {start_text} to {end_text}, delivering multi-day racing energy."
                )
            else:
                lines.append(
                    f"The {self.year} edition takes place on {start_text}, perfect for a focused race weekend."
                )
        else:
            lines.append(f"The {self.year} edition promises a refreshed course experience.")

        sorted_distances = sorted(self.distance_labels, key=lambda value: (len(value), value.lower()))
        if sorted_distances:
            lines.append(
                f"Choose from {_format_distance_labels(sorted_distances)} challenges crafted for both seasoned ultra runners and ambitious newcomers."
            )
        else:
            lines.append("Look forward to a curated set of race categories tailored for diverse running goals.")

        if self.finishers:
            lines.append(
                f"Historical results highlight {self.finishers} recorded finishers, underscoring supportive crews and dependable race logistics."
            )
        else:
            lines.append("Historic records highlight a tight-knit community of trail athletes backing every stride.")

        if self.registration_open_date and self.registration_close_date:
            open_text = self.registration_open_date.strftime("%B %d, %Y")
            close_text = self.registration_close_date.strftime("%B %d, %Y")
            lines.append(
                f"Registration opens {open_text} and remains available until {close_text}, giving you ample time to plan travel and training."
            )

        lines.append(
            "Expect attentive aid support, scenic sections worthy of a run-cation, and camaraderie that turns every kilometer into a shared adventure."
        )

        return "\n\n".join(lines)


COUNTRY_OVERRIDES = {
    "ARG": "Argentina",
    "AUS": "Australia",
    "AUT": "Austria",
    "BEL": "Belgium",
    "BRA": "Brazil",
    "CAN": "Canada",
    "CHE": "Switzerland",
    "CHI": "Chile",
    "CHN": "China",
    "CZE": "Czech Republic",
    "DEU": "Germany",
    "DNK": "Denmark",
    "ESP": "Spain",
    "EST": "Estonia",
    "FIN": "Finland",
    "FRA": "France",
    "GBR": "United Kingdom",
    "HUN": "Hungary",
    "IRL": "Ireland",
    "ITA": "Italy",
    "JPN": "Japan",
    "MEX": "Mexico",
    "NED": "Netherlands",
    "NOR": "Norway",
    "NZL": "New Zealand",
    "POL": "Poland",
    "PRT": "Portugal",
    "ROU": "Romania",
    "SWE": "Sweden",
    "USA": "United States",
}


def normalize_country(code: Optional[str]) -> str:
    if not code:
        return "Unknown"
    normalized = code.strip().upper()
    return COUNTRY_OVERRIDES.get(normalized, normalized)


def parse_year(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def split_event_name(raw_name: str) -> Tuple[str, Optional[str]]:
    name = raw_name.strip()
    if name.endswith(")") and "(" in name:
        prefix, _, suffix = name.rpartition("(")
        country_candidate = suffix.rstrip(")")
        country_candidate = country_candidate.strip()
        if len(country_candidate) in {2, 3} and country_candidate.isalpha():
            return prefix.strip(), country_candidate.upper()
    return name, None


def parse_event_dates(label: str, fallback_year: int) -> Tuple[Optional[date], Optional[date]]:
    """
    Parse event dates that are expressed in several shorthand formats:
    - 06.01.2018
    - 05.-06.01.2018
    - 23.-25.03.2018
    - 23.03.-08.04.2018
    - 28.12.-02.01.2019
    """

    if not label:
        return None, None

    cleaned = label.strip().replace("\u2013", "-").replace("\u2014", "-")
    cleaned = cleaned.replace(" ", "")
    cleaned = cleaned.replace("/", ".")

    parts = cleaned.split("-")
    if len(parts) == 1:
        single = _parse_date_fragment(parts[0], fallback_year=fallback_year)
        return single, single

    start_fragment = parts[0]
    end_fragment = parts[-1]

    end_date = _parse_date_fragment(end_fragment, fallback_year=fallback_year)
    start_date = _parse_date_fragment(
        start_fragment,
        fallback_year=end_date.year if end_date else fallback_year,
        inherit_month=end_date.month if end_date else None,
    )

    if start_date and end_date and start_date > end_date:
        # Handle cases crossing the year boundary (e.g., 28.12.-02.01.2019).
        adjusted_year = start_date.year - 1
        try:
            start_date = start_date.replace(year=adjusted_year)
        except ValueError:
            pass

    if start_date and not end_date:
        return start_date, start_date
    if end_date and not start_date:
        return end_date, end_date

    return start_date, end_date


def _parse_date_fragment(
    fragment: str,
    *,
    fallback_year: int,
    inherit_month: Optional[int] = None,
) -> Optional[date]:
    if not fragment:
        return None

    token = fragment.strip(".")
    if not token:
        return None

    bits = [part for part in token.split(".") if part]

    if len(bits) == 3:
        day_txt, month_txt, year_txt = bits
    elif len(bits) == 2:
        day_txt, month_txt = bits
        year_txt = str(fallback_year)
    elif len(bits) == 1:
        day_txt = bits[0]
        month_txt = str(inherit_month if inherit_month else 1)
        year_txt = str(fallback_year)
    else:
        return None

    try:
        day = int(day_txt)
        month = int(month_txt)
        year = int(year_txt)
        return datetime(year, month, day).date()
    except ValueError:
        return None


DISTANCE_RE = re.compile(r"(?P<value>\d+(?:\.\d+)?)(?P<unit>km|mi|h)$", re.IGNORECASE)


def parse_distance_km(label: str) -> Optional[Decimal]:
    if not label:
        return None
    text = label.strip().lower()
    match = DISTANCE_RE.match(text)
    if not match:
        if "h" in text:
            return Decimal("0")
        return None

    value = Decimal(match.group("value"))
    unit = match.group("unit").lower()

    if unit == "km":
        return value
    if unit == "mi":
        return (value * Decimal("1.60934")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    # Hour-based events get a nominal zero distance, but we still keep the label.
    return Decimal("0")


def quantize_distance(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class Command(BaseCommand):
    help = "Import events from the Two Centuries of UM Races CSV dataset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            type=str,
            default="TWO_CENTURIES_OF_UM_RACES.csv",
            help="Path to the CSV dataset (default: project root TWO_CENTURIES_OF_UM_RACES.csv).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Limit the number of unique events to import.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview the events without creating database records.",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv"])
        if not csv_path.is_absolute():
            csv_path = Path(settings.BASE_DIR) / csv_path
        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")

        limit = options.get("limit")
        dry_run = options.get("dry_run", False)

        aggregated_events: OrderedDict[Tuple, EventRecord] = OrderedDict()

        self.stdout.write(f"Reading data from {csv_path}...")

        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                record = self._extract_event_record(row)
                if record is None:
                    continue

                key = (
                    record.year,
                    record.base_name.lower(),
                    record.country_code or "",
                    record.original_start_date,
                    record.original_end_date,
                )

                existing = aggregated_events.get(key)
                if existing is None:
                    if limit and len(aggregated_events) >= limit:
                        continue
                    aggregated_events[key] = record
                    existing = record
                else:
                    existing.increase_finishers(record.finishers)

                existing.add_distance(row.get("Event distance/length"))
                existing.rows += 1

        if not aggregated_events:
            self.stdout.write(self.style.WARNING("No events could be parsed from the dataset."))
            return

        self.stdout.write(f"Prepared {len(aggregated_events)} unique events.")

        created = 0
        updated = 0
        dry_run_messages = []
        category_cache: dict[str, EventCategory] = {}

        for record in aggregated_events.values():
            (
                generated_start,
                generated_end,
                registration_open,
                registration_deadline,
            ) = self._generate_schedule(record)

            record.generated_start_date = generated_start
            record.generated_end_date = generated_end
            record.registration_open_date = registration_open
            record.registration_close_date = registration_deadline

            if dry_run:
                end_label = (
                    generated_end.isoformat() if generated_end else generated_start.isoformat()
                )
                dry_run_messages.append(
                    f"[DRY RUN] Would upsert event: {record.title} "
                    f"({generated_start.isoformat()} - {end_label}) "
                    f"[registration {registration_open.isoformat()} -> {registration_deadline.isoformat()}]"
                )
                continue

            event_data = {
                "description": record.build_description(),
                "city": record.city,
                "country": record.country,
                "venue": record.venue,
                "start_date": generated_start,
                "end_date": generated_end,
                "registration_open_date": registration_open,
                "registration_deadline": registration_deadline,
                "status": self._determine_status(generated_start, generated_end),
                "popularity_score": max(record.finishers, 0),
                "participant_limit": max(record.finishers, 0),
                "registered_count": max(record.finishers, 0),
                "featured": False,
                "banner_image": "",
            }

            with transaction.atomic():
                events_qs = Event.objects.filter(title=record.title).order_by("created_at", "id")
                if events_qs.exists():
                    event = events_qs.first()
                    created_flag = False
                else:
                    event = Event(title=record.title)
                    created_flag = True

                for field, value in event_data.items():
                    setattr(event, field, value)

                if created_flag:
                    event.save()
                    created += 1
                else:
                    event.save(update_fields=list(event_data.keys()))
                    updated += 1

                categories = self._get_categories_for_record(record, category_cache)
                event.categories.set(categories)

                duplicates_qs = events_qs.exclude(pk=event.pk)
                duplicates = list(duplicates_qs)
                for duplicate in duplicates:
                    for field, value in event_data.items():
                        setattr(duplicate, field, value)
                    duplicate.save(update_fields=list(event_data.keys()))
                    duplicate.categories.set(categories)
                if duplicates:
                    updated += len(duplicates)

        if dry_run:
            for message in dry_run_messages:
                self.stdout.write(message)
            self.stdout.write(self.style.WARNING("Dry run completed. No database changes were made."))
            return

        self.stdout.write(self.style.SUCCESS(f"Created {created} events."))
        if updated:
            self.stdout.write(self.style.SUCCESS(f"Updated {updated} events."))

    def _extract_event_record(self, row: dict) -> Optional[EventRecord]:
        year = parse_year(row.get("Year of event"))
        raw_name = (row.get("Event name") or "").strip()
        date_label = (row.get("Event dates") or "").strip()

        if not year or not raw_name or not date_label:
            return None

        base_name, country_code = split_event_name(raw_name)
        country = normalize_country(country_code)

        original_start, original_end = parse_event_dates(date_label, fallback_year=year)
        if original_start is None:
            return None

        finishers = parse_int(row.get("Event number of finishers")) or 0

        return EventRecord(
            year=year,
            base_name=base_name,
            country_code=country_code,
            country=country,
            original_name=raw_name,
            date_label=date_label,
            original_start_date=original_start,
            original_end_date=original_end,
            finishers=finishers,
        )

    def _generate_schedule(
        self,
        record: EventRecord,
    ) -> Tuple[date, Optional[date], date, date]:
        seed_value = f"{record.year}-{record.base_name.lower()}-{record.country_code or ''}"
        rng = random.Random(seed_value)
        today = date.today()

        phase = rng.random()

        if phase < 0.45:
            start_offset = rng.randint(35, 180)
            generated_start = today + timedelta(days=start_offset)
            duration_days = rng.randint(0, 2)
            generated_end = generated_start + timedelta(days=duration_days) if duration_days else None
            registration_deadline = generated_start - timedelta(days=rng.randint(7, 20))
            if registration_deadline <= today:
                registration_deadline = today + timedelta(days=rng.randint(5, 20))
                if registration_deadline >= generated_start:
                    registration_deadline = generated_start - timedelta(days=5)
            registration_open = registration_deadline - timedelta(days=rng.randint(30, 120))
        elif phase < 0.6:
            start_back = rng.randint(0, 1)
            generated_start = today - timedelta(days=start_back)
            duration_days = rng.randint(1, 3)
            generated_end = generated_start + timedelta(days=duration_days)
            registration_deadline = generated_start - timedelta(days=rng.randint(2, 6))
            registration_open = registration_deadline - timedelta(days=rng.randint(30, 90))
        else:
            start_back = rng.randint(40, 320)
            generated_start = today - timedelta(days=start_back)
            duration_days = rng.randint(0, 2)
            generated_end = generated_start + timedelta(days=duration_days) if duration_days else None
            registration_deadline = generated_start - timedelta(days=rng.randint(5, 20))
            registration_open = registration_deadline - timedelta(days=rng.randint(30, 160))

        return generated_start, generated_end, registration_open, registration_deadline

    def _determine_status(self, start_date: date, end_date: Optional[date]) -> str:
        today = date.today()
        event_end = end_date or start_date
        if start_date > today:
            return Event.Status.UPCOMING
        if event_end >= today:
            return Event.Status.ONGOING
        return Event.Status.COMPLETED

    def _get_categories_for_record(
        self,
        record: EventRecord,
        cache: dict[str, EventCategory],
    ) -> Iterable[EventCategory]:
        categories = []
        for label in sorted(record.distance_labels):
            cached = cache.get(label)
            if cached:
                categories.append(cached)
                continue

            distance_km = parse_distance_km(label)
            distance_value = quantize_distance(distance_km) if distance_km is not None else Decimal("0")

            name_slug = slugify(label)[:100]
            if not name_slug:
                name_slug = slugify(label.replace(":", "-"))[:100]
            if not name_slug:
                name_slug = f"distance-{abs(hash(label))}"

            category, created = EventCategory.objects.get_or_create(
                display_name=label,
                defaults={
                    "name": name_slug[:100],
                    "distance_km": distance_value,
                },
            )

            if not created and distance_km is not None and category.distance_km == Decimal("0"):
                category.distance_km = distance_value
                category.save(update_fields=["distance_km"])

            cache[label] = category
            categories.append(category)

        return categories
