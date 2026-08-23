"""Универсальная PostgreSQL-генерация вариантов КИМ."""

from backend.universal.codes import map_teacher_to_universal
from backend.universal.variant_builder import generate_variant

__all__ = ["generate_variant", "map_teacher_to_universal"]
