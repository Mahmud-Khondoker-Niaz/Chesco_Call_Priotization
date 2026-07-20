# LLM Integration Notes

Working notes on the current mock architecture, written before wiring up the real Open WebUI / AI Hub API.

---

## Two separate mock data sources

There are currently **two independent places** where mock LLM output lives. They feed different parts of the UI and need to be replaced independently.

### 1. `analysis.py` → `analyze_funding_call()`

- **Schema:** `{ match_score, reasoning, recommendation }`
- **Drives:** the **hero panel** in `app.py` — verdict pill, ring gauge, and rationale text
- **Mock logic:** `_mock_analysis_response()` keyword-matches the call text and returns one of five canned dicts (AAS/Digital Twin → 90, aerospace → 72, robotics → 45, civil security → 10, generic → 35)
- **Mock/real switch:** respects `USE_MOCK` imported from `llm_client.py`; real path calls `_call_real_llm()` with a combined strategy + call text prompt

### 2. `llm_test.py` → `analyze_call()` (via `_MOCK_*` dicts)

- **Schema:** full detailed JSON — `summary`, `what_call_really_wants`, `funding`, `deadline_timeline`, `consortium_leadership`, `partners_needed`, `focus_area`, `strategic_fit`, `recommendation`, `open_questions_missing_info`
- **Drives:** all **detail panels** in `app.py` — funding, timeline, consortium & partners, focus area, open questions
- **Mock logic:** `_mock_llm_response()` keyword-matches and returns one of four scenario strings (`_MOCK_CIVIL_SECURITY`, `_MOCK_KI_ROBOTIKBOOSTER`, `_MOCK_HYBRID_ELECTRIC`, `_MOCK_GENERIC`)
- **Mock/real switch:** `USE_MOCK = True` is hardcoded in this file; real path would require changing the import in `app.py` back to `from llm_client import analyze_call, USE_MOCK` and setting `USE_MOCK = False` there

---

## Why this matters for real API integration

**Both call sites must be updated** when wiring the real API — not just one. In `app.py`'s button handler, `analyze_funding_call()` and `analyze_call()` are called independently under the same spinner. If only one is replaced, the other half of the UI will keep rendering mock/hardcoded data with no obvious error.

---

## Where the hardcoded mock markers are

| Location | What to replace |
|---|---|
| `llm_test.py`, above `_MOCK_CIVIL_SECURITY` | `# ===== MOCK DATA — REPLACE WITH REAL LLM EXTRACTION =====` block — the three funding fields (`total_amount`, `funding_rate_by_partner_type`, `eigenmittel_required`) are hardcoded from the BMFTR civil-security call text |
| `analysis.py`, `_mock_analysis_response()` | The entire keyword-branch function and its five hardcoded score/reasoning dicts — replace with a real LLM call returning the 3-field schema |
| `llm_test.py`, `_mock_llm_response()` | The keyword-branch function and the four `_MOCK_*` scenario strings — replace with the real `_call_real_llm()` path from `llm_client.py` |

---

## Suggested integration approach

Ideally, merge `analyze_funding_call()` and `analyze_call()` into a **single LLM call** that returns both the 3-field strategy match and the full detailed schema in one response. Making two separate API calls per user submission doubles latency and cost unnecessarily. The simplest path: extend the system prompt in `llm_client.py` to include the strategy document as context and expand the output schema to cover both the hero fields (`match_score`, `reasoning`) and the existing detail fields, then update `app.py` to read everything from that one response.
