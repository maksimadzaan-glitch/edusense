"""Уникальные коды вида EDU-XXXX."""

from __future__ import annotations

import random
import string

from sqlalchemy.orm import Session


def generate_edu_code(db: Session, model, field_name: str = "code", attempts: int = 40) -> str:
    column = getattr(model, field_name)
    for _ in range(attempts):
        code = "EDU-" + "".join(random.choices(string.digits, k=4))
        exists = db.query(model).filter(column == code).first()
        if not exists:
            return code
    raise RuntimeError("Не удалось сгенерировать уникальный код EDU-XXXX")
