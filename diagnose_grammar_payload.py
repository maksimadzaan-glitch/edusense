import asyncio, json, os
from pathlib import Path
os.chdir(r"C:\Users\rusti\OneDrive\Рабочий стол\ege_tracker")
import sys
sys.path.insert(0, ".")

env = Path(".env")
if env.exists():
    for line in env.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k,v=line.split("=",1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from backend.universal.variant_builder import generate_variant, _task_from_proto, _oge_rus_payload_from_proto, _split_oge_rus_context, _context_description_map, _context_id_of
from backend.db.pg import session_factory, is_postgres_configured
from backend.db.pg_models import TaskPrototype, ContextBlock
from sqlalchemy import select

print("PG configured:", is_postgres_configured())

async def main():
    db = session_factory()()
    try:
        rows = db.execute(select(ContextBlock).where(ContextBlock.context_id=="oge_rus_var_kim")).scalars().all()
        print("context blocks:", len(rows))
        for r in rows:
            desc = r.description_text or ""
            print("desc len", len(desc), "has GRAMMAR mark", "GRAMMAR" in desc.upper() or "Граммат" in desc or "===GRAMMAR" in desc or "grammar" in desc.lower())
            print("desc first 400:", repr(desc[:400]))
            iz, gr, rd = _split_oge_rus_context(desc)
            print("split izlo", bool(iz), "grammar", bool(gr), "reading", bool(rd))
            if gr: print("grammar first 120:", gr[:120])
        
        protos = db.execute(select(TaskPrototype).where(
            TaskPrototype.subject_code=="russian",
            TaskPrototype.exam_code=="OGE",
            TaskPrototype.task_number==2,
            TaskPrototype.context_id=="oge_rus_var_kim",
        )).scalars().all()
        print("protos task2:", len(protos))
        if protos:
            p = protos[0]
            print("figure_params type", type(p.figure_params), "val", str(p.figure_params)[:300] if p.figure_params else None)
            print("oge_rus_payload_from_proto", _oge_rus_payload_from_proto(p))
            ctx_map = _context_description_map(db, subject_code="russian", exam_code="OGE", context_ids={"oge_rus_var_kim"})
            print("ctx_map keys", list(ctx_map.keys()), "lens", {k: len(v or "") for k,v in ctx_map.items()})
            task = _task_from_proto(p, context_desc=ctx_map.get("oge_rus_var_kim"), subject_code="russian", exam_code="OGE")
            print("task payload keys", (task.get("payload") or {}).keys() if task.get("payload") else None)
            print("grammar_text in payload", bool((task.get("payload") or {}).get("grammar_text")))
            if task.get("payload"):
                print("payload:", json.dumps(task["payload"], ensure_ascii=False)[:500])
    finally:
        db.close()

    v = await generate_variant("russian", "OGE", vary=False)
    t2 = next(t for t in v["tasks"] if t["task_number"]==2)
    print("generate task2 keys", t2.keys())
    print("generate task2 has payload", "payload" in t2, t2.get("payload"))
    print("payload count", sum(1 for t in v["tasks"] if t.get("payload")))
    print("grammar count", sum(1 for t in v["tasks"] if (t.get("payload") or {}).get("grammar_text")))

asyncio.run(main())
