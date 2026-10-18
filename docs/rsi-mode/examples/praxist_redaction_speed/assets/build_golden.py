from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "workspace" / "redaction.py"
OUT = ROOT / "sealed_tests" / "golden.json"

spec = importlib.util.spec_from_file_location("baseline_redaction", MODULE_PATH)
if spec is None or spec.loader is None:
    raise SystemExit(f"cannot load {MODULE_PATH}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

TEXT_INPUTS = [
    ("bearer", "Authorization: Bearer abcdefghijklmnop123456"),
    ("openai", "token=sk-abc1234567890XYZ"),
    ("github", "ghp_abcdefghijklmnopqrstuvwxyz0123456789"),
    ("named", "api_key=supersecretvalue"),
    ("password", "password: hunter2xyz"),
    ("mixed", "Bearer abcdefghijklmnop123456 and sk-abc1234567890XYZ and ghp_abcdefghijklmnopqrstuvwxyz0123456789"),
    ("clean", "the quick brown fox jumps over the lazy dog"),
    ("empty", ""),
    ("unicode", "配置：模型名称 = 万格智能；没有密钥。"),
    ("false_positive", "Bearer short and sk-short"),
    ("cross_line_bearer", "Bearer \nabcdefghijklmnop123456"),
    ("cross_line_named", "api\nkey=supersecretvalue"),
    ("cross_line_password", "password:\nhunter2xyz"),
    ("duplicate_bearer", "Bearer abcdefghijklmnop123456\n\nBearer abcdefghijklmnop123456"),
    ("duplicate_named", "api_key=supersecretvalue\n\napi_key=supersecretvalue"),
    ("unicode_length_change", "İİİ api_key=supersecretvalue İİİ"),
]

JSON_INPUTS = [
    ("nested_secret", {"api_key": "supersecretvalue", "nested": {"password": "hunter2xyz", "safe": "hello"}, "items": [{"secret": "anothervalue"}, "plain"]}),
    ("json_clean", {"name": "demo", "values": [1, 2, 3], "nested": {"ok": True}}),
    ("json_mixed", {"auth_token": "abcdefghijklmnop", "note": "Bearer abcdefghijklmnop123456", "list": ["sk-abc1234567890XYZ"]}),
]


def stable_hits(hits):
    return sorted(str(x) for x in hits)


cases = []
for name, text in TEXT_INPUTS:
    redacted, hits = module.redact_text(text)
    cases.append({
        "name": f"text_{name}",
        "kind": "text",
        "input": text,
        "expected": redacted,
        "hits": stable_hits(hits),
    })

for name, value in JSON_INPUTS:
    redacted, hits = module.redact_json(value)
    cases.append({
        "name": f"json_{name}",
        "kind": "json",
        "input": value,
        "expected": redacted,
        "hits": stable_hits(hits),
    })
    cases.append({
        "name": f"dumps_{name}",
        "kind": "dumps",
        "input": value,
        "expected": module.dumps_redacted(value, sort_keys=True),
    })

for name, text in TEXT_INPUTS[:7]:
    cases.append({
        "name": f"scan_{name}",
        "kind": "scan",
        "input": text,
        "expected": stable_hits(module.scan_text(text)),
    })

payload = {
    "schema_version": 1,
    "generated_from": "workspace/redaction.py",
    "note": "Golden outputs are frozen from the pristine PRAXIST redaction module. The candidate must match them exactly on these cases.",
    "cases": cases,
}
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote {OUT} with {len(cases)} cases")
