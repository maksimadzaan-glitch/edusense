"""Сид OGE math pack → PostgreSQL (context_blocks + связанные prototypes 1–5).

Запуск из корня проекта:
  python -m backend.scripts.seed_oge_math_pack
  python -m backend.scripts.seed_oge_math_pack --reset-contexts

Рекомендуемый порядок:
  1) python -m backend.scripts.seed_all_subjects        # слоты 6–25 (+ legacy 1–5)
  2) python -m backend.scripts.seed_oge_math_pack       # context blocks поверх
  3) restart API / generate с UNIVERSAL_VARY=0

Pack sync НЕ удаляет прототипы без context_id (слоты 6–25 из math_oge.json).
При generate для OGE math слоты 1–5 берутся из одного выбранного context_block.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import delete

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.db.pg import init_pg_tables, is_postgres_configured, session_factory
from backend.db.pg_models import ContextBlock, TaskPrototype
from backend.universal.packs.loader import pack_dir, sync_pack_to_pg


def seed(*, pack_id: str = "oge_math", reset_contexts: bool = False) -> dict:
    if not is_postgres_configured():
        raise SystemExit(
            "POSTGRES_URL не задан. Пример:\n"
            "  POSTGRES_URL=postgresql+psycopg://postgres:postgres@localhost:5432/edusense_universal"
        )

    root = pack_dir(pack_id)
    if not root.is_dir():
        raise SystemExit(f"Нет пака: {root}")

    init_pg_tables()
    SessionLocal = session_factory()
    db = SessionLocal()
    try:
        if reset_contexts:
            # Удалить только связанные с context прототипы math/OGE + сами блоки
            db.execute(
                delete(TaskPrototype).where(
                    TaskPrototype.subject_code == "math",
                    TaskPrototype.exam_code == "OGE",
                    TaskPrototype.context_id.isnot(None),
                )
            )
            db.execute(
                delete(ContextBlock).where(
                    ContextBlock.subject_code == "math",
                    ContextBlock.exam_code == "OGE",
                )
            )
            db.commit()
            print("reset: context_blocks + context-linked prototypes (math/OGE) cleared")

        summary = sync_pack_to_pg(db, pack_id=pack_id, root=root)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print("seed_oge_math_pack done:", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed OGE math pack into PostgreSQL")
    parser.add_argument("--pack-id", default="oge_math", help="Имя каталога в packs/")
    parser.add_argument(
        "--reset-contexts",
        action="store_true",
        help="Удалить context_blocks и связанные prototypes math/OGE перед сидом",
    )
    args = parser.parse_args()
    seed(pack_id=str(args.pack_id), reset_contexts=bool(args.reset_contexts))


if __name__ == "__main__":
    main()
