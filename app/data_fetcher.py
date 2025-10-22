from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

import requests
from dateutil import parser
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import EuroMillionsDraw, LotoDraw

LOTTO_URL = "https://media.fdj.fr/static/csv/loto.csv"
EUROMILLIONS_URL = "https://media.fdj.fr/static/csv/euromillions.csv"


class FetchError(RuntimeError):
    """Raised when lottery data cannot be fetched."""


def _download_csv(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def _prepare_reader(csv_content: str) -> Iterable[Dict[str, str]]:
    handle = io.StringIO(csv_content)
    sample = handle.read(4096)
    handle.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
        reader = csv.DictReader(handle, dialect=dialect)
    except csv.Error:
        reader = csv.DictReader(handle, delimiter=';')
    # Normalize keys once here for easier handling downstream
    for row in reader:
        yield {key.strip().lower(): value.strip() for key, value in row.items() if key}


def _extract_numbers(row: Dict[str, str], prefix: str) -> List[int]:
    extracted: List[Tuple[int, int]] = []
    for key, value in row.items():
        if key.startswith(prefix) and value:
            try:
                suffix = int(key.replace(prefix, ""))
                extracted.append((suffix, int(value)))
            except ValueError:
                continue
    extracted.sort(key=lambda item: item[0])
    return [value for _, value in extracted]


def _parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:  # pragma: no cover - defensive
        raise FetchError(f"Valeur numérique invalide: {value}") from exc


def _parse_date(row: Dict[str, str]) -> datetime:
    for key in ("date_de_tirage", "date", "drawdate"):
        if key in row and row[key]:
            try:
                return parser.parse(row[key], dayfirst=True)
            except (ValueError, parser.ParserError) as exc:  # pragma: no cover
                raise FetchError(f"Date invalide: {row[key]}") from exc
    raise FetchError("Champ de date introuvable dans la ligne")


def _parse_draw_number(row: Dict[str, str]) -> Optional[int]:
    for key in ("numero_de_tirage", "num_tirage", "drawnumber"):
        if key in row:
            return _parse_int(row[key])
    return None


def update_loto_draws(session: Session) -> int:
    """Download the latest Loto draws and merge them into the database."""
    csv_content = _download_csv(LOTTO_URL)
    reader = _prepare_reader(csv_content)

    inserted = 0
    for row in reader:
        draw_date = _parse_date(row).date()
        draw_number = _parse_draw_number(row)
        numbers = _extract_numbers(row, "boule_")
        chance_number = _parse_int(row.get("numero_chance"))
        if len(numbers) < 5 or chance_number is None:
            # Skip malformed entries
            continue

        numbers = sorted(set(numbers))
        # Some datasets may include duplicates; ensure exactly 5 numbers
        if len(numbers) != 5:
            continue

        stmt = select(LotoDraw).where(
            LotoDraw.draw_date == draw_date,
            LotoDraw.draw_number == draw_number,
        )
        existing = session.execute(stmt).scalar_one_or_none()
        if existing:
            continue

        draw = LotoDraw(
            draw_date=draw_date,
            draw_number=draw_number,
            main_numbers=",".join(str(num) for num in numbers),
            chance_number=chance_number,
        )
        session.add(draw)
        inserted += 1

    if inserted:
        session.commit()
    return inserted


def update_euromillions_draws(session: Session) -> int:
    """Download the latest EuroMillions draws and merge them into the database."""
    csv_content = _download_csv(EUROMILLIONS_URL)
    reader = _prepare_reader(csv_content)

    inserted = 0
    for row in reader:
        draw_date = _parse_date(row).date()
        draw_number = _parse_draw_number(row)
        numbers = _extract_numbers(row, "boule_")
        stars = _extract_numbers(row, "etoile_")
        if len(numbers) < 5 or len(stars) < 2:
            continue

        numbers = sorted(set(numbers))
        stars = sorted(set(stars))
        if len(numbers) != 5 or len(stars) != 2:
            continue

        stmt = select(EuroMillionsDraw).where(
            EuroMillionsDraw.draw_date == draw_date,
            EuroMillionsDraw.draw_number == draw_number,
        )
        existing = session.execute(stmt).scalar_one_or_none()
        if existing:
            continue

        draw = EuroMillionsDraw(
            draw_date=draw_date,
            draw_number=draw_number,
            main_numbers=",".join(str(num) for num in numbers),
            star_numbers=",".join(str(num) for num in stars),
        )
        session.add(draw)
        inserted += 1

    if inserted:
        session.commit()
    return inserted


def update_all_draws(session: Session) -> Dict[str, int]:
    """Update both Loto and EuroMillions draws, returning inserted counts."""
    results = {
        "loto": update_loto_draws(session),
        "euromillions": update_euromillions_draws(session),
    }
    return results
