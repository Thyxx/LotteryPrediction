from __future__ import annotations

from datetime import date, datetime
from typing import List

from sqlalchemy import Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class LotoDraw(TimestampMixin, Base):
    __tablename__ = "loto_draws"
    __table_args__ = (UniqueConstraint("draw_date", "draw_number", name="uq_loto_draw"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draw_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    draw_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    main_numbers: Mapped[str] = mapped_column(String(64), nullable=False)
    chance_number: Mapped[int] = mapped_column(Integer, nullable=False)

    def numbers_list(self) -> List[int]:
        return [int(value) for value in self.main_numbers.split(",") if value]


class EuroMillionsDraw(TimestampMixin, Base):
    __tablename__ = "euromillions_draws"
    __table_args__ = (
        UniqueConstraint("draw_date", "draw_number", name="uq_euromillions_draw"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draw_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    draw_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    main_numbers: Mapped[str] = mapped_column(String(64), nullable=False)
    star_numbers: Mapped[str] = mapped_column(String(32), nullable=False)

    def numbers_list(self) -> List[int]:
        return [int(value) for value in self.main_numbers.split(",") if value]

    def star_numbers_list(self) -> List[int]:
        return [int(value) for value in self.star_numbers.split(",") if value]
