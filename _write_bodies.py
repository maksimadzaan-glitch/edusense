import json
from pathlib import Path
Path('_body1.json').write_text(json.dumps({"exam":"oge","subject":"Русский язык","difficulty":"medium","count":13,"vary":False}, ensure_ascii=False), encoding='utf-8')
Path('_body2.json').write_text(json.dumps({"exam":"OGE","subject":"russian","difficulty":"medium","count":13,"vary":False}, ensure_ascii=False), encoding='utf-8')
Path('_body3.json').write_text(json.dumps({"subject_code":"russian","exam_code":"OGE"}, ensure_ascii=False), encoding='utf-8')
print('ok', Path('_body1.json').read_text(encoding='utf-8'))
print('ok2', Path('_body2.json').read_text(encoding='utf-8'))
print('ok3', Path('_body3.json').read_text(encoding='utf-8'))
