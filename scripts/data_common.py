"""Shared deterministic helpers for the TANIM data foundation."""

import calendar
import csv
import gzip
import hashlib
import io
import json
import math
import re
import unicodedata
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "data" / "dataset_config.json"
DEFAULT_CROPS = ROOT / "data" / "registry" / "crops.csv"
DEFAULT_CROP_SCOPE = ROOT / "data" / "registry" / "crop_scope_inventory.csv"
DEFAULT_GEOGRAPHIES = ROOT / "data" / "registry" / "geographies.csv"
DEFAULT_SCENARIOS = ROOT / "data" / "seeds" / "demo_scenarios.json"
GENERATED_ROOT = ROOT / "data" / "generated"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with open_csv_text(path) as file:
        return list(csv.DictReader(file))


def open_csv_text(path: Path) -> Any:
    if path.suffix == ".gz":
        return gzip.open(path, mode="rt", encoding="utf-8-sig", newline="")
    return path.open(encoding="utf-8-sig", newline="")


def write_csv_rows(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    if path.suffix == ".gz":
        raw_file = path.open("wb")
        compressed_file = gzip.GzipFile(filename="", mode="wb", fileobj=raw_file, mtime=0)
        file = io.TextIOWrapper(compressed_file, encoding="utf-8", newline="")
    else:
        raw_file = path.open("w", encoding="utf-8", newline="")
        file = raw_file
    try:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            count += 1
    finally:
        file.close()
        if path.suffix == ".gz":
            raw_file.close()
    return count


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(content, encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    text_suffixes = {".csv", ".json"}
    if path.suffix.lower() in text_suffixes:
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
        return digest.hexdigest()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_int(seed: int, *parts: object) -> int:
    """Return a stable digest value without Python's randomized hash()."""
    value = "\x1f".join([str(seed), *(str(part) for part in parts)])
    return int.from_bytes(hashlib.sha256(value.encode("utf-8")).digest()[:8], "big")


def is_finite_number(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def classify_snapshot_ratio(ratio: float | None, thresholds: dict[str, float]) -> str:
    """Label synthetic snapshot context using the documented prototype thresholds.

    This helper labels demo snapshots only. It is not the Phase 3 production engine.
    """
    if ratio is None:
        return "no_data"
    if not math.isfinite(ratio) or ratio < 0:
        raise ValueError("snapshot ratio must be a finite non-negative number")
    if ratio < float(thresholds["low_below"]):
        return "low"
    if ratio <= float(thresholds["high_above"]):
        return "moderate"
    return "high"


def normalize_label(value: str) -> str:
    folded = unicodedata.normalize("NFKC", value).casefold().strip()
    return re.sub(r"[^\w]+", " ", folded, flags=re.UNICODE).strip()


def parse_active(value: str, label: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"{label} must be 'true' or 'false', got {value!r}")
    return normalized == "true"


def quarter_periods(config: dict[str, Any]) -> list[tuple[str, str]]:
    periods: list[tuple[str, str]] = []
    future_planning = config["periods"]["future_planning"]
    starts = future_planning["quarter_starts"]
    horizon_start = date.fromisoformat(future_planning["start"])
    horizon_end = date.fromisoformat(future_planning["end"])
    if horizon_start.day != 1 or horizon_start.month not in {1, 4, 7, 10}:
        raise ValueError("future planning start must be the first day of a calendar quarter")
    if horizon_end < horizon_start:
        raise ValueError("future planning end must not be before its start")
    for start_value in starts:
        start = date.fromisoformat(start_value)
        if start.day != 1 or start.month not in {1, 4, 7, 10}:
            raise ValueError(
                f"future planning period must start on a calendar quarter: {start_value}"
            )
        end_month = start.month + 2
        end = date(start.year, end_month, calendar.monthrange(start.year, end_month)[1])
        if start < horizon_start or end > horizon_end:
            raise ValueError(
                f"future planning period is outside its configured horizon: {start_value}"
            )
        periods.append((start.isoformat(), end.isoformat()))
    if periods != sorted(periods) or len(periods) != len(set(periods)):
        raise ValueError("future planning quarter starts must be unique and chronological")
    expected: list[tuple[str, str]] = []
    cursor = horizon_start
    while cursor <= horizon_end:
        end_month = cursor.month + 2
        end = date(cursor.year, end_month, calendar.monthrange(cursor.year, end_month)[1])
        expected.append((cursor.isoformat(), end.isoformat()))
        cursor = date(
            cursor.year + (1 if cursor.month == 10 else 0),
            (cursor.month + 3 - 1) % 12 + 1,
            1,
        )
    if periods != expected:
        raise ValueError(
            "future planning quarter starts must completely cover the configured horizon"
        )
    return periods


def current_supply_period(config: dict[str, Any]) -> tuple[str, str]:
    current = config["periods"]["current_supply"]
    start = date.fromisoformat(current["start"])
    end = date.fromisoformat(current["end"])
    if end < start:
        raise ValueError("current supply period end must not be before its start")
    return start.isoformat(), end.isoformat()


def supply_periods(config: dict[str, Any]) -> list[tuple[str, str, str]]:
    current = current_supply_period(config)
    future = quarter_periods(config)
    if current in set(future):
        raise ValueError("current supply period must be outside the future planning horizon")
    return [(current[0], current[1], "current_supply")] + [
        (start, end, "future_planning") for start, end in future
    ]


def supported_future_period(config: dict[str, Any], start: str, end: str) -> bool:
    return (start, end) in set(quarter_periods(config))


def price_months(config: dict[str, Any]) -> list[str]:
    start_text = config["periods"]["price_start_month"]
    try:
        year_text, month_text = start_text.split("-")
        year, month = int(year_text), int(month_text)
    except (ValueError, AttributeError) as error:
        raise ValueError(f"invalid price start month: {start_text!r}") from error
    if not 1 <= month <= 12:
        raise ValueError(f"invalid price start month: {start_text!r}")
    count = int(config["periods"]["price_month_count"])
    if count < 1:
        raise ValueError("price_month_count must be positive")
    result = []
    for offset in range(count):
        absolute_month = year * 12 + (month - 1) + offset
        result.append(f"{absolute_month // 12:04d}-{absolute_month % 12 + 1:02d}-01")
    return result
