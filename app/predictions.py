from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import EuroMillionsDraw, LotoDraw


@dataclass
class Prediction:
    method: str
    main_numbers: List[int]
    extra_numbers: List[int]


def _counter_from_draws(draws: Iterable[Sequence[int]]) -> Counter:
    counter: Counter = Counter()
    for draw in draws:
        counter.update(draw)
    return counter


def _select_top_numbers(counter: Counter, total_numbers: int, picks: int) -> List[int]:
    ordered = [number for number, _ in counter.most_common()]
    remaining = [number for number in range(1, total_numbers + 1) if number not in ordered]
    combined = ordered + remaining
    return sorted(combined[:picks])



def _select_avoiding_recent(recent_draw: Sequence[int], total_numbers: int, picks: int) -> List[int]:
    pool = [number for number in range(1, total_numbers + 1) if number not in recent_draw]
    if len(pool) < picks:
        pool = list(range(1, total_numbers + 1))
    chosen = random.sample(pool, k=picks)
    chosen.sort()
    return chosen


def generate_loto_predictions(session: Session) -> List[Prediction]:
    draws = session.execute(select(LotoDraw).order_by(LotoDraw.draw_date.desc())).scalars().all()
    if not draws:
        return []

    main_draws = [draw.numbers_list() for draw in draws]
    chance_numbers = [draw.chance_number for draw in draws]

    overall_counter = _counter_from_draws(main_draws)
    chance_counter = Counter(chance_numbers)

    predictions = []

    # Method 1: Overall frequency
    predictions.append(
        Prediction(
            method="Fréquence historique",
            main_numbers=_select_top_numbers(overall_counter, 49, 5),
            extra_numbers=_select_top_numbers(chance_counter, 10, 1),
        )
    )

    # Method 2: Recent trend (last 30 draws)
    recent_draws = main_draws[:30]
    recent_chance = chance_numbers[:30]
    recent_counter = _counter_from_draws(recent_draws)
    recent_chance_counter = Counter(recent_chance)
    predictions.append(
        Prediction(
            method="Tendance récente",
            main_numbers=_select_top_numbers(recent_counter, 49, 5),
            extra_numbers=_select_top_numbers(recent_chance_counter, 10, 1),
        )
    )

    # Method 3: Avoid last draw
    last_draw = main_draws[0]
    last_chance = chance_numbers[0]
    predictions.append(
        Prediction(
            method="Évitement du dernier tirage",
            main_numbers=_select_avoiding_recent(last_draw, 49, 5),
            extra_numbers=_select_avoiding_recent([last_chance], 10, 1),
        )
    )

    return predictions


def generate_euromillions_predictions(session: Session) -> List[Prediction]:
    draws = (
        session.execute(select(EuroMillionsDraw).order_by(EuroMillionsDraw.draw_date.desc()))
        .scalars()
        .all()
    )
    if not draws:
        return []

    main_draws = [draw.numbers_list() for draw in draws]
    star_draws = [draw.star_numbers_list() for draw in draws]

    overall_counter = _counter_from_draws(main_draws)
    star_counter = _counter_from_draws(star_draws)

    predictions = []

    predictions.append(
        Prediction(
            method="Fréquence historique",
            main_numbers=_select_top_numbers(overall_counter, 50, 5),
            extra_numbers=_select_top_numbers(star_counter, 12, 2),
        )
    )

    recent_draws = main_draws[:30]
    recent_stars = star_draws[:30]
    recent_counter = _counter_from_draws(recent_draws)
    recent_star_counter = _counter_from_draws(recent_stars)
    predictions.append(
        Prediction(
            method="Tendance récente",
            main_numbers=_select_top_numbers(recent_counter, 50, 5),
            extra_numbers=_select_top_numbers(recent_star_counter, 12, 2),
        )
    )

    last_draw = main_draws[0]
    last_star_draw = star_draws[0]
    predictions.append(
        Prediction(
            method="Évitement du dernier tirage",
            main_numbers=_select_avoiding_recent(last_draw, 50, 5),
            extra_numbers=_select_avoiding_recent(last_star_draw, 12, 2),
        )
    )

    return predictions
