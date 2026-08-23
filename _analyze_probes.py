import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def summarize_ai(path, label, http_note=None):
    raw = Path(path).read_text(encoding="utf-8")
    print(f"=== {label} ===")
    if http_note:
        print(http_note)
    print("raw_bytes:", Path(path).stat().st_size)
    try:
        data = json.loads(raw)
    except Exception as e:
        print("JSON_ERROR:", e)
        print("RAW:", raw[:2000])
        print()
        return
    qs = data.get("questions") or data.get("tasks") or []
    print("http/body status field:", data.get("status"))
    print("message:", data.get("message"))
    print("detail:", data.get("detail"))
    print("error:", data.get("error"))
    print("questions_length:", len(qs) if isinstance(qs, list) else repr(type(qs)))
    print("top_keys:", list(data.keys()) if isinstance(data, dict) else None)
    if isinstance(qs, list):
        for i in (1, 2):
            print(f"--- q{i+1} ---")
            if i >= len(qs):
                print("MISSING")
                continue
            q = qs[i]
            print("keys:", sorted(q.keys()) if isinstance(q, dict) else type(q))
            if not isinstance(q, dict):
                continue
            print("payload_exists:", "payload" in q)
            gt = q.get("grammar_text")
            print("grammar_text_len:", len(gt) if isinstance(gt, str) else gt)
            print("top-level oge_rus:", q.get("oge_rus"))
            print("top-level kim_type:", q.get("kim_type"))
            print("top-level ui:", q.get("ui"))
            pl = q.get("payload")
            if isinstance(pl, dict):
                print("payload_keys:", sorted(pl.keys()))
                print("payload.oge_rus:", pl.get("oge_rus"))
                print("payload.kim_type:", pl.get("kim_type"))
                print("payload.ui:", pl.get("ui"))
                pgt = pl.get("grammar_text")
                print("payload.grammar_text_len:", len(pgt) if isinstance(pgt, str) else pgt)
            elif pl is not None:
                print("payload_type:", type(pl).__name__, "repr:", repr(pl)[:200])
    print()


summarize_ai("_probe1.json", "PROBE 1", "HTTP_STATUS:200")
summarize_ai("_probe2.json", "PROBE 2", "HTTP_STATUS:422")

# Probe 3
raw = Path("_probe3.json").read_text(encoding="utf-8")
print("=== PROBE 3 ===")
print("HTTP_STATUS:200")
print("raw_bytes:", Path("_probe3.json").stat().st_size)
data = json.loads(raw)
print("top_keys:", list(data.keys()) if isinstance(data, dict) else type(data))
if isinstance(data, dict):
    print("status:", data.get("status"))
    print("message:", data.get("message"))
    print("error:", data.get("error"))
    print("detail:", data.get("detail"))

tasks = None
if isinstance(data, dict):
    for k in ("tasks", "questions", "items", "data"):
        if isinstance(data.get(k), list):
            tasks = data[k]
            print("list_key:", k, "len:", len(tasks))
            break
    if tasks is None:
        for nest in ("result", "variant", "payload", "response"):
            if isinstance(data.get(nest), dict):
                for k in ("tasks", "questions", "items"):
                    if isinstance(data[nest].get(k), list):
                        tasks = data[nest][k]
                        print(f"list_key: {nest}.{k}", "len:", len(tasks))
                        break
            if tasks is not None:
                break


def trunc(obj, n=80):
    if isinstance(obj, str):
        return obj[:n] + ("..." if len(obj) > n else "")
    if isinstance(obj, list):
        return [trunc(x, n) for x in obj]
    if isinstance(obj, dict):
        return {k: trunc(v, n) for k, v in obj.items()}
    return obj

if tasks is None:
    print("RAW_HEAD:", json.dumps(data, ensure_ascii=False)[:4000])
else:
    any_payload = False
    for i in (1, 2):
        print(f"--- task {i+1} full JSON (text truncated 80) ---")
        if i >= len(tasks):
            print("MISSING")
            continue
        print(json.dumps(trunc(tasks[i]), ensure_ascii=False, indent=2))
    for idx, t in enumerate(tasks):
        if isinstance(t, dict) and "payload" in t:
            any_payload = True
            print(f"task[{idx}] has payload key")
    print("any_task_has_payload:", any_payload)
print()

print("=== MAP CHECK ===")
from backend.universal.codes import map_teacher_to_universal
print(repr(map_teacher_to_universal("oge", "Русский язык")))
print(repr(map_teacher_to_universal("OGE", "russian")))
print(repr(map_teacher_to_universal("oge", "russian")))
