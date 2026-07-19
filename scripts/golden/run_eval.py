"""Runnable evaluation harness for the DMX sales-advisor golden set.

Scores every rubric dimension (dmx-sales-advisor-rubric-v1) that has a
deterministic or heuristic signal, per turn, replaying each conversation through
a pluggable BOT RUNNER. Dimensions only count on the turns they apply to.

Runners:
  --runner mock    oracle (correct-by-construction) -> ~100%, gate PASS
  --runner noisy   deterministically perturbs turns  -> failures caught, gate FAIL
  --runner http    POSTs {session_id,message,history} to --url; expects prediction schema

Prediction schema a real bot adapter returns per turn:
  { "intent": str, "answer_type": str,
    "tool_call": {"name": str, "args": {...}} | None,
    "product_ids": [int, ...],
    "explanation_text": str }
"""
import json, re, argparse, collections, sys

FIX = "data/dataset/golden/product-fixture.json"
DATA = "data/dataset/golden/golden-conversations.jsonl"

fx = json.load(open(FIX, encoding="utf-8"))
FIDX = {p["product_id"]: p for arr in fx["categories"].values() for p in arr}

def norm(s): return re.sub(r"\s+", " ", str(s).strip().lower())
def digits(s): return re.sub(r"\D", "", str(s))
def mentions(text, token):
    t = str(token)
    return (t in digits(text)) if t.isdigit() else (norm(t) in norm(text))
def has_axis(case, sub):
    return any(sub in a for a in case.get("coverage_axes", []))

def number_runs(text):
    """digit-strings from a possibly formatted text ('5.190.000' -> '5190000')."""
    return {re.sub(r"\D", "", m) for m in re.findall(r"\d[\d.,]*", str(text))}

def allowed_numbers(product_ids):
    """all numeric tokens that legitimately appear in the referenced products."""
    s = set()
    for pid in product_ids:
        p = FIDX.get(pid)
        if not p:
            continue
        for v in (p["Giá khuyến mãi"], p["Giá gốc"], p["Khuyến mãi"], p["Thông tin sản phẩm"]):
            s |= number_runs(v)
        for v in p["raw_specs"].values():
            s |= number_runs(v)
    return s

DISCLOSE_KW = ("chưa được công bố", "không được công bố", "chưa công bố", "không công bố",
               "không có dữ liệu", "chưa có thông tin", "không có thông tin", "not published")
VERDICT_KW = ("đáng", "nên chọn", "phù hợp", "tiết kiệm", "worth")
REFUSE_KW = ("không thể", "xin lỗi", "không hỗ trợ", "cannot", "can't")

# ------------------------------------------------------------------ RUNNERS
def mock_runner(history, message, case, noisy=False):
    exp = case["expected"]
    tc = exp.get("tool_call")
    at = exp["answer_type"]
    english = message.strip().isascii()
    if tc and tc["name"] == "compare-search":
        pids = list(tc["args"].get("product_ids", []))
    elif at == "recommendation":
        pids = list(exp.get("candidate_product_ids", []))[:3]
    else:
        pids = []
    # correct-by-construction explanation / reply text
    ex = exp.get("explanation")
    if at == "guardrail_block":
        etext = "Xin lỗi, mình không thể hỗ trợ yêu cầu này ạ."
    elif at == "clarification":
        etext = "Could you share a bit more so I can help?" if english else "Anh/chị cho em xin thêm thông tin ạ?"
    elif at == "no_match":
        etext = "Hiện chưa có sản phẩm phù hợp trong tầm này, anh/chị tăng ngân sách giúp em nhé."
    elif ex:
        facts = " ; ".join(str(m) for m in ex["must_mention"])
        if english:
            etext = f"Recommended for your need. Facts: {facts}. Trade-off noted. Worth it if you prioritize performance."
        else:
            etext = f"Gợi ý phù hợp nhu cầu. Thông số: {facts} . Đánh đổi: trả thêm để có thông số tốt hơn."
            if ex.get("verdict_required"):
                etext += f" Đáng tiền hơn nếu ưu tiên {ex['worth_paying_more'].get('differentiator_field')}; cần tiết kiệm thì chọn máy rẻ hơn."
    else:
        etext = ""
    if has_axis(case, "disclose-missing"):
        etext += " Một số thông số sản phẩm chưa được công bố."
    pred = {"intent": exp["intent"], "answer_type": at, "tool_call": tc,
            "product_ids": pids, "explanation_text": etext}
    if noisy:
        h = sum(ord(c) for c in case["eval_case_id"]) % 4
        if h == 0 and (ex or at == "comparison"):
            pred["explanation_text"] = pred["explanation_text"][:12]     # drop grounded facts / verdict
        elif h == 1 and at == "recommendation":
            pred["product_ids"] = pred["product_ids"] + [999999999]      # fabricate product
        elif h == 2 and at == "guardrail_block":
            pred["answer_type"] = "text"; pred["tool_call"] = None        # miss guardrail
        elif h == 3 and at == "clarification":
            pred["answer_type"] = "recommendation"                        # over-answer instead of ask
        if h == 1 and (ex or at == "comparison"):
            pred["explanation_text"] += " Giá chỉ còn 123456789đ."         # fabricated price -> numeric_grounding catches it
    return pred

def adapt_agent(resp):
    """Map a live E02 agent response (backend/app/agent: intent/text/flags/
    presented_ids) into the harness prediction schema."""
    pids = []
    for x in resp.get("presented_ids", []) or []:
        dg = re.sub(r"\D", "", str(x))
        if dg:
            pids.append(int(dg))
    return {"intent": resp.get("intent"), "answer_type": None, "tool_call": None,
            "product_ids": pids, "explanation_text": resp.get("text", "") or "",
            "flags": resp.get("flags", []) or []}

def http_runner(url, api="harness"):
    import urllib.request
    def run(history, message, case):
        payload = {"session_id": case["conversation_id"], "message": message}
        if api == "harness":
            payload["history"] = history          # agent API takes only session_id+message
        req = urllib.request.Request(url, json.dumps(payload).encode(),
                                     {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
        return adapt_agent(resp) if api == "agent" else resp
    return run

def mock_agent(case, noisy=False):
    """Offline agent-shaped oracle: lets `--api agent` be tested without a server."""
    exp = case["expected"]
    tc = exp.get("tool_call")
    if tc and tc["name"] == "compare-search":
        pids = list(tc["args"].get("product_ids", []))
    elif exp["answer_type"] == "recommendation":
        pids = list(exp.get("candidate_product_ids", []))[:3]
    else:
        pids = []
    ex = exp.get("explanation")
    txt = ""
    if ex:
        txt = "Gợi ý phù hợp. " + " ; ".join(str(m) for m in ex["must_mention"])
        if ex.get("verdict_required"):
            txt += " Đáng tiền hơn nếu ưu tiên hiệu năng; cần tiết kiệm thì chọn máy rẻ hơn."
    elif exp["answer_type"] == "clarification":
        txt = "Anh/chị cho em xin thêm thông tin ạ?"
    flags = ["guardrail_block"] if exp["answer_type"] == "guardrail_block" else []
    pred = {"intent": exp.get("agent_intent"), "product_ids": pids,
            "explanation_text": txt, "flags": flags}
    if noisy:
        h = sum(ord(c) for c in case["eval_case_id"]) % 3
        if h == 0:
            pred["intent"] = "new_search" if pred["intent"] != "new_search" else "unsupported"
        elif h == 1 and exp["answer_type"] == "recommendation":
            pred["product_ids"] = pred["product_ids"] + [999999999]
        elif h == 2 and exp["answer_type"] == "guardrail_block":
            pred["flags"] = []
    return pred

# ------------------------------------------------------------------ LLM JUDGE
def _product_facts(pids):
    out = []
    for pid in pids:
        p = FIDX.get(pid)
        if p:
            out.append(f"- {p['tên sản phẩm']} | giá {p['Giá khuyến mãi']} | {p['Thông tin sản phẩm'][:220]}")
    return "\n".join(out) or "(none)"

def judge_stub(case, pred):
    """Offline stand-in for the LLM judge: coherence proxy = grounded facts +
    enough length + a verdict for comparisons. Lets --judge run without a key."""
    exp = case["expected"]; ex = exp["explanation"]; txt = pred.get("explanation_text", "") or ""
    facts = all(mentions(txt, m) for m in ex["must_mention"])
    coherent = len(txt.strip()) >= 40
    verdict = (not ex.get("verdict_required")) or any(k in norm(txt) for k in VERDICT_KW)
    ok = facts and coherent and verdict
    return {"score": 5 if ok else 2, "pass": ok, "reason": "stub"}

def judge_llm(case, pred):
    """Grade explanation quality with an LLM via OpenRouter (fails CLOSED)."""
    import os, urllib.request
    key = os.environ.get("OPENROUTER_API_KEY")
    model = os.environ.get("JUDGE_LLM_MODEL", "deepseek/deepseek-v4-flash")
    if not key:
        return {"score": 0, "pass": False, "reason": "no OPENROUTER_API_KEY (fail-closed)"}
    exp = case["expected"]
    pids = (pred.get("product_ids") or
            (exp["tool_call"]["args"].get("product_ids") if exp.get("tool_call") else []) or [])
    sys_p = ("Bạn là giám khảo nghiêm khắc chấm phần giải thích tư vấn/so sánh sản phẩm. "
             "Trả về JSON {\"score\":1-5,\"pass\":bool,\"reason\":str}. "
             "pass=true chỉ khi: mọi con số/thông tin nêu ra khớp dữ liệu sản phẩm (không bịa), "
             "điểm bán chính bám nhu cầu khách, nêu rõ đánh đổi, và (nếu so sánh) có phán quyết nên chọn cái nào. "
             "score>=4 mới pass.")
    usr = (f"Nhu cầu khách: {case['input']['message']}\n"
           f"Dữ liệu sản phẩm:\n{_product_facts(pids)}\n"
           f"Câu trả lời của bot:\n{pred.get('explanation_text','')}\n"
           "Chấm điểm.")
    body = json.dumps({"model": model, "temperature": 0,
                       "messages": [{"role": "system", "content": sys_p},
                                    {"role": "user", "content": usr}]}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body,
                                 {"Content-Type": "application/json",
                                  "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            content = json.loads(r.read())["choices"][0]["message"]["content"]
        m = re.search(r"\{.*\}", content, re.S)
        obj = json.loads(m.group(0))
        return {"score": obj.get("score", 0), "pass": bool(obj.get("pass", False)),
                "reason": str(obj.get("reason", ""))[:160]}
    except Exception as e:
        return {"score": 0, "pass": False, "reason": f"judge error (fail-closed): {e}"}

# ------------------------------------------------------------------ SCORING
# dim -> (is_P0, kind) ; kind: auto=deterministic, proxy=heuristic offline
DIMS_META = {
    "intent_correct": (0, "auto"), "answer_type_correct": (0, "auto"),
    "tool_correct": (1, "auto"), "one_tool_per_turn": (1, "auto"),
    "grounding_no_fabrication": (1, "auto"), "numeric_grounding": (1, "auto"),
    "explanation_quality_judged": (1, "judge"), "comparison_quality_judged": (1, "judge"),
    "filter_correct": (0, "auto"),
    "no_match_handled": (1, "auto"), "clarify_decision": (0, "proxy"),
    "comparison_quality": (1, "proxy"), "explanation_grounded": (1, "proxy"),
    "disclose_missing": (1, "proxy"), "policy_refusal": (1, "auto"),
    "language_mirroring": (0, "proxy"), "robustness": (0, "proxy"),
    "multi_turn_state": (0, "auto"),
    "comparison_has_verdict": (0, "proxy"),   # live-agent mode
}

def score_agent(case, pred, id_universe):
    """Score against the LIVE agent, which exposes intent/text/flags/presented_ids
    but not tool_call/answer_type and uses its own ranking over the full catalog.
    Only dimensions verifiable without pinning the agent's exact picks are scored;
    product-specific dims (filter, must-mention grounding, numeric) are skipped and
    require a fixture-pinned agent or an oracle."""
    exp = case["expected"]; at = exp["answer_type"]; d = {}
    d["intent_correct"] = pred.get("intent") == exp.get("agent_intent")
    pids = pred.get("product_ids", [])
    d["grounding_no_fabrication"] = all(p in id_universe for p in pids)   # real xlsx ids
    flags = pred.get("flags") or []
    if at == "no_match":
        d["no_match_handled"] = len(pids) == 0
    if at == "guardrail_block":
        d["policy_refusal"] = (pred.get("intent") == "unsupported"
                               or any(("guard" in f.lower() or "block" in f.lower()) for f in flags))
    if at == "clarification":
        txt = pred.get("explanation_text", "") or ""
        d["clarify_decision"] = txt.count("?") <= 1 and len(pids) == 0
    if has_axis(case, "robustness"):
        d["robustness"] = d["intent_correct"]
    if has_axis(case, "language-mirroring"):
        want = "en" if case["input"]["message"].strip().isascii() else "vi"
        got = "en" if (pred.get("explanation_text", "") or " ").strip().isascii() else "vi"
        d["language_mirroring"] = want == got
    if at == "comparison":
        d["comparison_has_verdict"] = any(k in norm(pred.get("explanation_text", "")) for k in VERDICT_KW)
    return d

def score_turn(case, pred, history=None):
    exp = case["expected"]; at = exp["answer_type"]; d = {}
    ok_intent = pred.get("intent") == exp["intent"]
    ok_at = pred.get("answer_type") == at
    d["intent_correct"] = ok_intent
    d["answer_type_correct"] = ok_at
    # tool
    et, pt = exp.get("tool_call"), pred.get("tool_call")
    if et is None:
        d["tool_correct"] = pt is None
    else:
        ok = bool(pt) and pt.get("name") == et["name"]
        if ok and et["name"] == "compare-search":
            ok = set(pt.get("args", {}).get("product_ids", [])) == set(et["args"]["product_ids"])
        d["tool_correct"] = ok
    d["one_tool_per_turn"] = pt is None or isinstance(pt, dict)   # never a list of calls
    # grounding
    pids = pred.get("product_ids", [])
    d["grounding_no_fabrication"] = all(pid in FIDX for pid in pids)
    # numeric grounding: any price-like number (>=6 digits) in the reply must
    # belong to a referenced product, the user's own message, or the history.
    txt = pred.get("explanation_text", "") or ""
    if pids or exp.get("explanation"):
        ref = set(pids)
        if at == "recommendation":
            ref |= set(exp.get("candidate_product_ids", []))
        allowed = allowed_numbers(ref)
        allowed |= number_runs(case["input"]["message"])
        for h in (history or []):
            allowed |= number_runs(h.get("content", ""))
        bad = [n for n in number_runs(txt) if len(n) >= 6 and n not in allowed]
        d["numeric_grounding"] = (len(bad) == 0)
    if at == "recommendation" and exp.get("candidate_product_ids"):
        d["filter_correct"] = set(pids).issubset(set(exp["candidate_product_ids"]))
    if at == "no_match":
        d["no_match_handled"] = (at == pred.get("answer_type")) and len(pids) == 0
    # clarification behavior
    if at == "clarification":
        txt = pred.get("explanation_text", "") or ""
        d["clarify_decision"] = ok_at and txt.count("?") <= 1
    # comparison quality (grounded facts + verdict)
    if at == "comparison" and exp.get("explanation"):
        txt = pred.get("explanation_text", "") or ""
        facts = all(mentions(txt, m) for m in exp["explanation"]["must_mention"])
        verdict = any(k in norm(txt) for k in VERDICT_KW)
        d["comparison_quality"] = facts and verdict
    # explanation grounding for recommendation
    if at == "recommendation" and exp.get("explanation"):
        txt = pred.get("explanation_text", "") or ""
        d["explanation_grounded"] = all(mentions(txt, m) for m in exp["explanation"]["must_mention"])
    # disclose missing
    if has_axis(case, "disclose-missing"):
        txt = pred.get("explanation_text", "") or ""
        d["disclose_missing"] = any(k in norm(txt) for k in DISCLOSE_KW)
    # policy refusal
    if at == "guardrail_block":
        d["policy_refusal"] = pred.get("answer_type") == "guardrail_block" and pred.get("tool_call") is None
    # language mirroring
    if has_axis(case, "language-mirroring"):
        want = "en" if case["input"]["message"].strip().isascii() else "vi"
        got = "en" if (pred.get("explanation_text", "") or " ").strip().isascii() else "vi"
        d["language_mirroring"] = want == got
    # robustness
    if has_axis(case, "robustness"):
        d["robustness"] = ok_intent and ok_at
    # multi-turn state
    if exp["intent"] in ("change_constraints", "more_recommendations"):
        cand = set(exp.get("candidate_product_ids", []))
        d["multi_turn_state"] = (not cand) or set(pids).issubset(cand)
    return d

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runner", choices=["mock", "noisy", "http"], default="mock")
    ap.add_argument("--judge", choices=["none", "stub", "llm"], default="none")
    ap.add_argument("--set", choices=["full", "sample"], default="full", dest="tier")
    ap.add_argument("--api", choices=["harness", "agent"], default="harness",
                    help="'agent' = live E02 API (/api/v1/agent/respond) response shape")
    ap.add_argument("--url"); ap.add_argument("--out")
    a = ap.parse_args()
    judge_fn = {"none": None, "stub": judge_stub, "llm": judge_llm}[a.judge]
    data_path = (DATA if a.tier == "full"
                 else DATA.replace(".jsonl", ".sample.jsonl"))
    cases = [json.loads(l) for l in open(data_path, encoding="utf-8") if l.strip()]
    convs = collections.defaultdict(list)
    for c in cases: convs[c["conversation_id"]].append(c)
    for cid in convs: convs[cid].sort(key=lambda c: c["turn_index"])
    if a.runner == "http":
        if not a.url: sys.exit("--url required for http runner")
        runner = http_runner(a.url, api=a.api)
    elif a.api == "agent":
        runner = lambda h, m, c: mock_agent(c, noisy=(a.runner == "noisy"))
    else:
        runner = lambda h, m, c: mock_runner(h, m, c, noisy=(a.runner == "noisy"))

    id_universe = None
    skipped = 0
    if a.api == "agent":
        try:
            id_universe = set(json.load(open("data/dataset/golden/all-product-ids.json")))
        except FileNotFoundError:
            sys.exit("run build_fixture.py first (need all-product-ids.json for agent mode)")

    per = collections.defaultdict(lambda: [0, 0]); results = []; case_pass = 0
    for cid, turns in convs.items():
        hist = []
        for c in turns:
            if a.api == "agent" and not c.get("agent_scope", True):
                skipped += 1                     # out of the advisory agent's scope
                continue
            msg = c["input"]["message"]
            pred = runner(hist, msg, c)
            if a.api == "agent":
                dims = score_agent(c, pred, id_universe)
            else:
                dims = score_turn(c, pred, history=hist)
                if judge_fn and c["expected"].get("explanation"):
                    v = judge_fn(c, pred)
                    key = ("comparison_quality_judged" if c["expected"]["answer_type"] == "comparison"
                           else "explanation_quality_judged")
                    dims[key] = bool(v["pass"])
            for k, ok in dims.items():
                per[k][1] += 1; per[k][0] += int(bool(ok))
            allok = all(dims.values()); case_pass += int(allok)
            results.append({"id": c["eval_case_id"], "pass": allok,
                            "failed": [k for k, ok in dims.items() if not ok]})
            hist += [{"role": "user", "content": msg},
                     {"role": "assistant", "content": pred.get("explanation_text", "")}]

    scored = len(cases) - skipped
    print(f"\nRUNNER = {a.runner}   API = {a.api}   set = {a.tier}   conversations = {len(convs)}")
    if a.api == "agent":
        print(f"scored = {scored} in-scope cases  (skipped {skipped} out-of-agent-scope: order/payment/delivery/greeting)")
    denom = scored or 1
    print(f"case-level pass (all applicable dims) = {case_pass}/{scored} = {case_pass/denom:.1%}\n")
    print(f"{'dimension':<24}{'kind':>6}{'pass':>7}{'appl':>6}{'rate':>8}  P0")
    gate_ok = True
    for k in sorted(per, key=lambda x: (not DIMS_META.get(x, (0, ''))[0], x)):
        p, t = per[k]; rate = p / t if t else 1.0
        p0, kind = DIMS_META.get(k, (0, "?"))
        if p0 and rate < 1.0: gate_ok = False
        print(f"{k:<24}{kind:>6}{p:>7}{t:>6}{rate:>8.1%}  {'P0' if p0 else ''}")
    print(f"\nRELEASE GATE (all P0 dims == 100%): {'PASS' if gate_ok else 'FAIL'}")
    if a.out:
        json.dump({"runner": a.runner, "api": a.api, "set": a.tier,
                   "scored": scored, "skipped": skipped, "case_pass": case_pass,
                   "per_dim": {k: {"pass": v[0], "applicable": v[1]} for k, v in per.items()},
                   "gate_pass": gate_ok, "results": results},
                  open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"wrote {a.out}")
    sys.exit(0 if gate_ok else 1)

if __name__ == "__main__":
    main()
