"""Verify the golden dataset against the fixture. Fails loudly on any
untraceable claim, missing product, or structural violation."""
import json, sys, collections, argparse

_ap = argparse.ArgumentParser()
_ap.add_argument("--set", choices=["full", "sample"], default="full", dest="tier")
_A = _ap.parse_args()

FIX = "data/dataset/golden/product-fixture.json"
DATA = ("data/dataset/golden/golden-conversations.jsonl" if _A.tier == "full"
        else "data/dataset/golden/golden-conversations.sample.jsonl")

fx = json.load(open(FIX, encoding="utf-8"))
IDX = {}
for arr in fx["categories"].values():
    for p in arr:
        IDX[p["product_id"]] = p

cases = [json.loads(l) for l in open(DATA, encoding="utf-8") if l.strip()]
errors, warns = [], []

def field_value(p, field):
    if field == "Giá khuyến mãi": return str(p["Giá khuyến mãi"])
    if field == "Giá gốc": return str(p["Giá gốc"])
    if field == "Trạng thái": return p["Trạng thái"]
    if field == "Khuyến mãi": return p["Khuyến mãi"]
    return str(p["raw_specs"].get(field))

ids = set()
for c in cases:
    cid = c["eval_case_id"]
    if cid in ids: errors.append(f"{cid}: duplicate eval_case_id")
    ids.add(cid)
    exp = c["expected"]
    # one tool per turn
    tc = exp.get("tool_call")
    if isinstance(tc, list): errors.append(f"{cid}: tool_call must be single, not list")
    # candidates exist
    for pid in exp.get("candidate_product_ids", []):
        if pid not in IDX: errors.append(f"{cid}: candidate {pid} not in fixture")
    # grounded claims trace
    for g in exp.get("grounded_claims", []):
        pid = g["product_id"]
        if pid not in IDX:
            errors.append(f"{cid}: grounded product {pid} not in fixture"); continue
        actual = field_value(IDX[pid], g["field"])
        if str(g["value"]) != str(actual):
            errors.append(f"{cid}: grounded {pid}.{g['field']} = {g['value']!r} != fixture {actual!r}")
    # no_match must have empty candidate set
    if exp["answer_type"] == "no_match" and exp.get("candidate_product_ids"):
        errors.append(f"{cid}: no_match but candidate set non-empty {exp['candidate_product_ids']}")
    # comparison tool call must have exactly 2 ids
    if tc and tc["name"] == "compare-search":
        pids = tc["args"].get("product_ids", [])
        if len(pids) != 2:
            errors.append(f"{cid}: compare-search needs exactly 2 product_ids, got {pids}")
        for pid in pids:
            if pid not in IDX: errors.append(f"{cid}: compare id {pid} not in fixture")
    # recommendation budget filter sanity
    if tc and tc["name"] == "search_product_dmx_v3" and exp["answer_type"] == "recommendation":
        bud = tc["args"].get("budget_max")
        if bud:
            for pid in exp.get("candidate_product_ids", []):
                if IDX[pid]["Giá khuyến mãi"] > bud:
                    errors.append(f"{cid}: candidate {pid} price {IDX[pid]['Giá khuyến mãi']} > budget {bud}")

# coverage summary
axcnt = collections.Counter(ax for c in cases for ax in c["coverage_axes"])
sev = collections.Counter(c["severity_if_failed"] for c in cases)
caps = collections.Counter(c["capability"] for c in cases)
cats = collections.Counter(c["category"] for c in cases)

print(f"cases={len(cases)}  conversations={len(set(c['conversation_id'] for c in cases))}")
print(f"capability={dict(caps)}")
print(f"category={dict(cats)}")
print(f"severity={dict(sev)}")
print(f"distinct coverage axes={len(axcnt)}")
if warns:
    print("\nWARNINGS:"); [print("  -", w) for w in warns]
if errors:
    print(f"\n{len(errors)} ERRORS:")
    for e in errors[:60]: print("  -", e)
    sys.exit(1)
print("\nALL CHECKS PASSED")
