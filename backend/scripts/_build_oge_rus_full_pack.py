"""Собрать pack JSON: kim + новые полные варианты → oge_rus_variants_full.json"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMP = ROOT / "backend/universal/packs/oge_rus/imports"

SKIP = {
    "oge_rus_var_TEMPLATE.json",
    "oge_rus_var_a.json",
    "oge_rus_var_01.json",
    "oge_rus_var_02.json",
    "oge_rus_var_03.json",
    "oge_rus_var_04.json",
    "oge_rus_var_05.json",
    "oge_rus_pool_49.json",
}


def _variant_files() -> list[str]:
    names = [
        p.name
        for p in IMP.glob("oge_rus_var_*.json")
        if p.name not in SKIP
    ]
    # kim оставляем в паке для эталона, но generate его не берёт
    return sorted(names, key=lambda n: (n != "oge_rus_var_kim.json", n))


def main() -> None:
    variants = []
    for name in _variant_files():
        path = IMP / name
        raw = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(raw, dict) and raw.get("variant_id")
        assert isinstance(raw.get("listening_text"), dict)
        assert isinstance(raw.get("grammar_text"), dict)
        assert isinstance(raw.get("reading_text"), dict)
        tasks = raw.get("tasks") or []
        nums = {int(t["task_number"]) for t in tasks if isinstance(t, dict)}
        # tasks JSON has 2..13; slot 1 from listening
        assert nums >= set(range(2, 14)), (name, sorted(nums))
        variants.append(raw)

    pack = {
        "pack_info": {
            "pack_id": "oge_rus",
            "version": "2.1.0",
            "exam_year": 2026,
            "title": "ОГЭ Русский — полные КИМ-варианты",
        },
        "variants": variants,
    }
    out = IMP / "oge_rus_variants_full.json"
    out.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} n={len(variants)} ids={[v['variant_id'] for v in variants]}")


if __name__ == "__main__":
    main()
