import html
import json
import math

import streamlit as st
# from llm_client import analyze_call, USE_MOCK
from llm_test import analyze_call, USE_MOCK
from analysis import analyze_funding_call

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="chesco — Call Dashboard",
    page_icon="🛰️",
    layout="wide",
)

# ---------------------------------------------------------
# GLOBAL STYLES — dark dashboard theme
# ---------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: #1A2030;
    --panel: #232A3D;
    --panel-border: #343D54;
    --ink: #EDF1F7;
    --ink-soft: #9AA3B5;
    --accent: #22D3EE;
    --go: #34D399;
    --hold: #FBBF24;
    --rej: #F87171;
}

.stApp { background-color: var(--bg); }
.stApp p, .stApp span, .stApp label, .stCaption { color: var(--ink-soft); }

/* ---- Header ---- */
.dash-header {
    border-bottom: 1px solid var(--panel-border);
    padding-bottom: 18px;
    margin-bottom: 8px;
}
.dash-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: .14em;
    text-transform: uppercase;
    color: var(--accent);
}
.dash-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 32px;
    color: var(--ink);
    margin: 2px 0 4px 0;
}
.dash-sub {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    color: var(--ink-soft);
}
.mock-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--ink-soft);
    border: 1px dashed var(--panel-border);
    border-radius: 4px;
    padding: 4px 10px;
    display: inline-block;
    margin-top: 10px;
}
.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: var(--ink-soft);
}

/* ---- Hero: verdict pill + gauge ---- */
.dash-hero {
    display: flex;
    align-items: center;
    gap: 36px;
    flex-wrap: wrap;
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 16px;
    padding: 28px 32px;
    margin-top: 20px;
}
.verdict-pill {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 15px;
    letter-spacing: .04em;
    text-transform: uppercase;
    padding: 12px 22px;
    border-radius: 999px;
    white-space: nowrap;
    display: inline-block;
}
.pill-go   { background: rgba(52,211,153,0.12); color: var(--go); border: 1px solid rgba(52,211,153,0.45); }
.pill-hold { background: rgba(251,191,36,0.12); color: var(--hold); border: 1px solid rgba(251,191,36,0.45); }
.pill-rej  { background: rgba(248,113,113,0.12); color: var(--rej); border: 1px solid rgba(248,113,113,0.45); }
.hero-text { flex: 1; min-width: 240px; }
.hero-rationale {
    font-family: 'Inter', sans-serif;
    font-size: 14.5px;
    line-height: 1.6;
    color: #C3CAD9;
    margin-top: 14px;
    max-width: 620px;
}
.gauge-wrap { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.gauge-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--ink-soft);
}

/* ---- Key facts (at-a-glance, right after verdict) ---- */
.key-facts {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-top: 20px;
}
.key-fact {
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 12px;
    padding: 16px 20px;
}
.key-fact-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--ink-soft);
    margin-bottom: 6px;
}
.key-fact-value {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    line-height: 1.5;
    color: var(--ink);
}

/* ---- Panel grid ---- */
.dash-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin-top: 20px;
}
.dash-panel {
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 14px;
    padding: 22px 26px;
}
.dash-panel.full { grid-column: 1 / -1; }
.panel-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 15px;
    color: var(--ink);
    margin-bottom: 14px;
}
.panel-body {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    line-height: 1.65;
    color: #C3CAD9;
}
.panel-fields {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 16px 24px;
    margin-bottom: 14px;
}
.panel-field-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    letter-spacing: .07em;
    text-transform: uppercase;
    color: var(--ink-soft);
    margin-bottom: 5px;
}
.panel-field-value {
    font-family: 'Inter', sans-serif;
    font-size: 13.5px;
    line-height: 1.55;
    color: var(--ink);
}
.dash-oq { list-style: none; padding-left: 0; margin: 0; }
.dash-oq li {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: #C3CAD9;
    padding-left: 20px;
    position: relative;
    margin-bottom: 9px;
}
.dash-oq li::before {
    content: "▸";
    position: absolute;
    left: 0;
    color: var(--accent);
}

/* ---- Inputs ---- */
.stTextArea textarea {
    border-radius: 10px;
    border: 1px solid var(--panel-border) !important;
    font-family: 'Inter', sans-serif;
    font-size: 14.5px;
    background: var(--panel) !important;
    color: var(--ink) !important;
    caret-color: var(--accent) !important;
}
.stTextArea textarea::placeholder { color: var(--ink-soft) !important; opacity: 0.7; }
.stButton>button, .stButton>button p, .stButton>button span {
    color: #06141F !important;
}
.stButton>button {
    background: linear-gradient(135deg, var(--accent), #0EA5B7);
    border-radius: 10px;
    height: 2.8em;
    width: 100%;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    letter-spacing: .03em;
    border: none;
}
.stButton>button:hover { filter: brightness(1.08); }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def fmt(value):
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        if not value:
            return "—"
        return html.escape(", ".join(str(v) for v in value))
    return html.escape(str(value))


def fmt_extracted(value):
    """Like fmt(), but for deterministically-extracted fields: None means
    the extractor found nothing in the call text, not just an empty value."""
    if value is None or value == "":
        return "Not stated in call text"
    return html.escape(str(value))


def verdict_class_and_label(decision: str):
    d = (decision or "").lower().strip()
    if "do not pursue" in d or "not pursue" in d or "no-go" in d or "no go" in d or "reject" in d or "decline" in d or "skip" in d or d == "pass":
        return "pill-rej"
    if "consider" in d or "condition" in d or "maybe" in d or "review" in d or "hold" in d or "moderate" in d:
        return "pill-hold"
    if "pursue" in d or "go" in d or "yes" in d or "apply" in d or "submit" in d:
        return "pill-go"
    return "pill-hold"


def fit_rating_color(rating: str):
    r = (rating or "").lower().strip()
    if "high" in r:
        return "#34D399"
    if "low" in r:
        return "#F87171"
    return "#FBBF24"


def _score_color(score: int) -> str:
    if score >= 70:
        return "#34D399"
    if score < 40:
        return "#F87171"
    return "#FBBF24"


def gauge_svg(rating: str, score: int | None = None):
    """Renders a glowing ring gauge.

    Pass score (0-100) to drive from a numeric match_score; otherwise falls
    back to the legacy HIGH/MODERATE/LOW string rating.
    """
    if score is not None:
        color = _score_color(score)
        frac = max(0.03, min(1.0, score / 100))
        label = str(score)
    else:
        color = fit_rating_color(rating)
        r = (rating or "").lower().strip()
        frac = 0.95 if "high" in r else (0.32 if "low" in r else 0.63)
        label = (rating or "—").upper()
    radius = 58
    circumference = 2 * math.pi * radius
    arc = circumference * frac
    return (
        '<svg width="150" height="150" viewBox="0 0 150 150">'
        '<circle cx="75" cy="75" r="' + str(radius) + '" fill="none" stroke="#232C42" stroke-width="13"></circle>'
        '<circle cx="75" cy="75" r="' + str(radius) + '" fill="none" stroke="' + color + '" stroke-width="13" '
        'stroke-linecap="round" stroke-dasharray="' + f"{arc:.1f} {circumference:.1f}" + '" '
        'transform="rotate(-90 75 75)"></circle>'
        '<text x="75" y="82" text-anchor="middle" font-family="Space Grotesk, sans-serif" '
        'font-weight="700" font-size="18" fill="' + color + '">' + html.escape(label) + '</text>'
        '</svg>'
    )


def parse_result(raw_json: str):
    try:
        data = json.loads(raw_json)
    except Exception:
        return None

    return {
        "summary": data.get("summary", "—"),
        "what_call_wants": data.get("what_call_really_wants", "—"),
        "funding": data.get("funding", {}),
        "consortium": data.get("consortium_leadership", {}),
        "partners": data.get("partners_needed", {}),
        "deadline": data.get("deadline_timeline", {}),
        "focus_area": data.get("focus_area", {}),
        "strategic_fit": data.get("strategic_fit", {}),
        "recommendation": data.get("recommendation", {}),
        "open_questions": data.get("open_questions_missing_info", []),
    }


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
mock_badge = (
    '<div class="mock-badge">MOCK MODE — structure final, content placeholder</div>'
    if USE_MOCK else ""
)
st.markdown(
    '<div class="dash-header"><div class="dash-eyebrow">CALL PRIORITIZATION DASHBOARD</div>'
    '<div class="dash-title">chesco</div>'
    '<div class="dash-sub">Paste a funding call below for an instant assessment.</div>'
    + mock_badge + '</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# INPUT
# ---------------------------------------------------------
st.markdown('<p class="section-label" style="margin-top:18px;">Submit call text</p>', unsafe_allow_html=True)

call_text = st.text_area(
    label="Funding call text",
    height=240,
    placeholder="Paste the full text of the funding call here…",
    label_visibility="collapsed",
)

col_btn, col_info = st.columns([1, 4])
with col_btn:
    analyze_clicked = st.button("Analyze call", use_container_width=True)
with col_info:
    if call_text:
        st.caption(f"{len(call_text.split())} words · {len(call_text)} characters")

# ---------------------------------------------------------
# OUTPUT — dashboard: hero gauge/pill + topic-grouped panel grid
# ---------------------------------------------------------
if analyze_clicked:
    if not call_text.strip():
        st.error("Please paste some call text before analyzing.")
    else:
        with st.spinner("Analyzing…"):
            # Strategy-fit analysis drives the hero section
            strategy_error: str | None = None
            strategy_result: dict | None = None
            try:
                strategy_result = analyze_funding_call(call_text)
            except FileNotFoundError as exc:
                strategy_error = f"Strategy document not found: {exc}"
            except Exception as exc:
                strategy_error = f"Strategy analysis failed: {exc}"

            # Detailed panel analysis (mock scenarios / full JSON schema)
            raw = analyze_call(call_text)

        if strategy_error:
            st.error(strategy_error)

        parsed = parse_result(raw)

        if not parsed:
            st.error("Could not parse the detailed analysis response.")
            st.code(raw)
        else:
            if strategy_result:
                parsed["open_questions"] = strategy_result.get("open_questions", [])

            extracted = (strategy_result or {}).get("extracted_details", {})
            ext_funding = extracted.get("funding", {})
            ext_deadline = extracted.get("deadline", {})
            ext_consortium = extracted.get("consortium", {})
            ext_summary = extracted.get("call_summary")
            ext_focus_area = extracted.get("focus_area", {})
            ext_suggested_programs = extracted.get("suggested_funding_programs")

            rec = parsed["recommendation"]
            strat = parsed["strategic_fit"]
            consortium = parsed["consortium"]

            # Hero driven by strategy_result when available, else fall back to detailed schema
            if strategy_result:
                hero_decision = strategy_result.get("recommendation", "—")
                hero_rationale = strategy_result.get("reasoning", "—")
                hero_score = strategy_result.get("match_score")
                gauge_html = gauge_svg("", score=hero_score)
                gauge_label = "Strategy Match"
            else:
                hero_decision = rec.get("decision", "—")
                hero_rationale = rec.get("rationale", "—")
                gauge_html = gauge_svg(strat.get("rating", ""))
                gauge_label = "Strategic Fit"

            v_class = verdict_class_and_label(hero_decision)

            hero_html = (
'<div class="dash-hero">'
f'<div class="verdict-pill {v_class}">{fmt(hero_decision)}</div>'
'<div class="hero-text">'
f'<div class="hero-rationale">{fmt(hero_rationale)}</div>'
'</div>'
'<div class="gauge-wrap">'
f'{gauge_html}'
f'<div class="gauge-label">{gauge_label}</div>'
'</div>'
'</div>'
            )
            st.markdown(hero_html, unsafe_allow_html=True)

            key_facts_html = (
'<div class="key-facts">'
'<div class="key-fact">'
'<div class="key-fact-label">Funding total</div>'
f'<div class="key-fact-value">{fmt_extracted(ext_funding.get("total_amount"))}</div>'
'</div>'
'<div class="key-fact">'
'<div class="key-fact-label">Deadline</div>'
f'<div class="key-fact-value">{fmt_extracted(ext_deadline.get("deadline"))}</div>'
'</div>'
'<div class="key-fact">'
'<div class="key-fact-label">Project duration</div>'
f'<div class="key-fact-value">{fmt_extracted(ext_deadline.get("project_duration"))}</div>'
'</div>'
'<div class="key-fact">'
'<div class="key-fact-label">Partners needed</div>'
f'<div class="key-fact-value">{fmt_extracted(ext_consortium.get("partner_count"))}</div>'
'</div>'
'</div>'
            )
            st.markdown(key_facts_html, unsafe_allow_html=True)

            oq = parsed["open_questions"]
            if oq:
                oq_html = "".join(f"<li>{fmt(q)}</li>" for q in oq)
            else:
                oq_html = "<li>No open questions in this response.</li>"

            grid_html = (
'<div class="dash-grid">'

'<div class="dash-panel full">'
'<div class="panel-title">Call summary</div>'
f'<div class="panel-body">{fmt_extracted(ext_summary)}</div>'
'</div>'

'<div class="dash-panel full">'
'<div class="panel-title">What the call really wants</div>'
f'<div class="panel-body">{fmt(parsed["what_call_wants"])}</div>'
'</div>'

'<div class="dash-panel">'
'<div class="panel-title">Focus area &amp; fit reasoning</div>'
'<div class="panel-fields">'
'<div><div class="panel-field-label">Research fields</div>'
f'<div class="panel-field-value">{fmt_extracted(ext_focus_area.get("research_fields"))}</div></div>'
'<div><div class="panel-field-label">Target application</div>'
f'<div class="panel-field-value">{fmt_extracted(ext_focus_area.get("target_application"))}</div></div>'
'<div><div class="panel-field-label">Suggested lead team</div>'
f'<div class="panel-field-value">{fmt(rec.get("suggested_lead_team"))}</div></div>'
'</div>'
f'<div class="panel-body">{fmt(hero_rationale)}</div>'
'</div>'

'<div class="dash-panel">'
'<div class="panel-title">Funding</div>'
'<div class="panel-fields">'
'<div><div class="panel-field-label">Total amount</div>'
f'<div class="panel-field-value">{fmt_extracted(ext_funding.get("total_amount"))}</div></div>'
'<div><div class="panel-field-label">Eigenmittel required</div>'
f'<div class="panel-field-value">{fmt_extracted(ext_funding.get("eigenmittel_required"))}</div></div>'
'</div>'
'<div class="panel-field-label">Rate by partner type</div>'
f'<div class="panel-field-value">{fmt_extracted(ext_funding.get("funding_rate_by_partner_type"))}</div>'
'<div class="panel-field-label" style="margin-top:12px;">Suggested funding programs</div>'
f'<div class="panel-field-value">{fmt_extracted(ext_suggested_programs)}</div>'
'</div>'

'<div class="dash-panel">'
'<div class="panel-title">Timeline</div>'
'<div class="panel-fields">'
'<div><div class="panel-field-label">Deadline</div>'
f'<div class="panel-field-value">{fmt_extracted(ext_deadline.get("deadline"))}</div></div>'
'<div><div class="panel-field-label">Project duration</div>'
f'<div class="panel-field-value">{fmt_extracted(ext_deadline.get("project_duration"))}</div></div>'
'</div>'
'<div class="panel-field-label">Enough time?</div>'
f'<div class="panel-field-value">{fmt_extracted(ext_deadline.get("enough_time"))}</div>'
'</div>'

'<div class="dash-panel">'
'<div class="panel-title">Consortium &amp; partners</div>'
'<div class="panel-fields">'
'<div><div class="panel-field-label">Can chesco lead?</div>'
f'<div class="panel-field-value">{fmt_extracted(ext_consortium.get("lead_eligibility_signal"))}</div></div>'
'<div><div class="panel-field-label">Partner count</div>'
f'<div class="panel-field-value">{fmt_extracted(ext_consortium.get("partner_count"))}</div></div>'
'<div><div class="panel-field-label">Partner types</div>'
f'<div class="panel-field-value">{fmt_extracted(ext_consortium.get("partner_types"))}</div></div>'
'<div><div class="panel-field-label">Geographic restrictions</div>'
f'<div class="panel-field-value">{fmt_extracted(ext_consortium.get("geographic_restrictions"))}</div></div>'
'</div>'
f'<div class="panel-body">{fmt(consortium.get("rationale"))}</div>'
'</div>'

'<div class="dash-panel full">'
'<div class="panel-title">Open questions</div>'
f'<ul class="dash-oq">{oq_html}</ul>'
'</div>'

'</div>'
            )
            st.markdown(grid_html, unsafe_allow_html=True)