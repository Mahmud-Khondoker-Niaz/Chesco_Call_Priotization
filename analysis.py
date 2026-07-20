"""
analysis.py — Evaluates a funding call against the chesco strategy document.

Scoring is fully deterministic: it matches the funding call text against
structured strategy elements (target sectors, technologies, focus areas)
extracted by strategy_loader.load_strategy_structure(), using a capped
additive weighting scheme. No LLM call is involved.
"""

import json
import re
from datetime import date

from strategy_loader import load_strategy_structure, load_strategy_tables

_SECTOR_WEIGHT = 45
_SECTOR_CAP = 90
_TECHNOLOGY_WEIGHT = 12
_TECHNOLOGY_CAP = 40
_FOCUS_AREA_WEIGHT = 6
_FOCUS_AREA_CAP = 20

_PURSUE_THRESHOLD = 70
_CONSIDER_THRESHOLD = 35


def _term_present(text_lower: str, term: str) -> bool:
    """
    True if `term` appears in `text_lower` as a whole token, not merely as a
    substring of a longer word (e.g. "AR" must not match inside "Partner",
    "produktion" must not match inside "Produktionsprozess").
    """
    pattern = r"(?<!\w)" + re.escape(term.lower()) + r"(?!\w)"
    return re.search(pattern, text_lower, flags=re.UNICODE) is not None


def analyze_funding_call(funding_call_text: str) -> dict:
    """
    Evaluates a funding call against the chesco strategy.

    Returns a dict with keys: match_score (int), reasoning (str),
    recommendation (str), open_questions (list[str]), plus
    matched_sectors/matched_technologies/matched_focus_areas for
    transparency into how the score was derived.
    """
    structure = load_strategy_structure()
    tables = load_strategy_tables()
    result = score_funding_call(funding_call_text, structure)
    result["open_questions"] = generate_open_questions(funding_call_text, result)

    deadline_info = extract_deadline_info(funding_call_text)
    result["extracted_details"] = {
        "funding": extract_funding_info(funding_call_text),
        "deadline": {**deadline_info, "enough_time": derive_enough_time(deadline_info)},
        "consortium": extract_consortium_info(funding_call_text),
        "call_summary": extract_call_summary(funding_call_text),
        "focus_area": {
            "target_application": derive_target_application(result["matched_sectors"]),
            "research_fields": derive_research_fields_finer(
                result["matched_technologies"],
                result["matched_focus_areas"],
                result["matched_sectors"],
                tables["capability_maturity"],
            ),
        },
        "suggested_funding_programs": suggest_funding_programs(
            funding_call_text, tables["funder_program_topic"]
        ),
    }
    return result


def score_funding_call(funding_call_text: str, structure: dict) -> dict:
    """
    Capped-additive scoring over structured strategy elements:
    - target-sector match: high weight (the strongest fit signal — does the
      call target one of chesco's priority sectors at all)
    - named technology match: medium weight (does the call mention chesco's
      specific core technologies, e.g. Digital Twin, AAS)
    - focus-area match: low weight (generic overlap with chesco's broader
      positioning themes, e.g. data sovereignty)
    Each category is capped before summing so no single category can
    dominate the score on its own, and the total is capped at 100.
    """
    text_lower = funding_call_text.lower()

    matched_sectors = [
        sector["name"] for sector in structure["target_sectors"]
        if any(_term_present(text_lower, term) for term in [sector["name"], *sector["synonyms"]])
    ]
    matched_technologies = [
        term for term in structure["technologies"] if _term_present(text_lower, term)
    ]
    matched_focus_areas = [
        term for term in structure["focus_areas"] if _term_present(text_lower, term)
    ]

    score = 0
    score += min(len(matched_sectors) * _SECTOR_WEIGHT, _SECTOR_CAP)
    score += min(len(matched_technologies) * _TECHNOLOGY_WEIGHT, _TECHNOLOGY_CAP)
    score += min(len(matched_focus_areas) * _FOCUS_AREA_WEIGHT, _FOCUS_AREA_CAP)
    score = min(score, 100)

    if score >= _PURSUE_THRESHOLD:
        recommendation = "pursue"
    elif score >= _CONSIDER_THRESHOLD:
        recommendation = "consider"
    else:
        recommendation = "skip"

    return {
        "match_score": score,
        "reasoning": _build_reasoning(matched_sectors, matched_technologies, matched_focus_areas),
        "recommendation": recommendation,
        "matched_sectors": matched_sectors,
        "matched_technologies": matched_technologies,
        "matched_focus_areas": matched_focus_areas,
    }


_OPEN_QUESTION_CHECKS = [
    (
        lambda text_lower, result: not re.search(r"€|\beur\b|\d+\s*(?:%|prozent)|mio\.", text_lower),
        "Funding amount/rate not clearly stated in the call text — check the full Bekanntmachung.",
    ),
    (
        lambda text_lower, result: not (
            re.search(r"\d{1,2}\.\s*\w+\s*20\d{2}", text_lower)
            or _term_present(text_lower, "frist")
            or _term_present(text_lower, "deadline")
        ),
        "Submission deadline not clearly stated in the call text.",
    ),
    (
        lambda text_lower, result: not any(
            _term_present(text_lower, term) for term in ["Konsortium", "Partner", "Verbundprojekt"]
        ),
        "Consortium/partner requirements not specified in the call text.",
    ),
    (
        lambda text_lower, result: len(result["matched_sectors"]) == 0,
        "No matching chesco priority sector identified in this call — confirm strategic fit manually.",
    ),
    (
        lambda text_lower, result: len(result["matched_sectors"]) > 1,
        "Call spans multiple chesco priority sectors — clarify which framing to lead with.",
    ),
]


def generate_open_questions(funding_call_text: str, score_result: dict) -> list[str]:
    """
    Deterministically flags open questions based on what's actually present
    or absent in the call text and the computed score result — e.g. only
    flags "funding amount" as open if no amount/rate pattern is found in the
    text, rather than returning a fixed canned list regardless of content.
    """
    text_lower = funding_call_text.lower()
    return [
        question for check, question in _OPEN_QUESTION_CHECKS
        if check(text_lower, score_result)
    ]


def _build_reasoning(matched_sectors, matched_technologies, matched_focus_areas) -> str:
    parts = []
    if matched_sectors:
        parts.append(f"Matches chesco priority sector(s): {', '.join(matched_sectors)}.")
    if matched_technologies:
        parts.append(f"References core chesco technologies: {', '.join(matched_technologies)}.")
    if matched_focus_areas:
        parts.append(f"Aligns with chesco focus area(s): {', '.join(matched_focus_areas)}.")
    if not parts:
        parts.append("No overlap detected with chesco's priority sectors, technologies, or focus areas.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Detail-panel extraction — deterministic, regex/pattern-based, no LLM call.
# Every field returns None when not explicitly stated in the call text;
# nothing here is inferred or invented.
# ---------------------------------------------------------------------------

def _clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def _first_matching_line(call_text: str, *patterns: str) -> str | None:
    """First line in call_text matching ANY of the given regex patterns, or None."""
    for line in call_text.split("\n"):
        if any(re.search(p, line, flags=re.IGNORECASE | re.UNICODE) for p in patterns):
            cleaned = _clean_line(line)
            if cleaned:
                return cleaned
    return None


def _first_line_matching_term(call_text: str, terms: list[str]) -> str | None:
    """
    First line containing any of `terms` as a whole token (word-boundary safe via
    _term_present) -- e.g. "Unternehmen" must not match inside the compound word
    "Luftfahrtunternehmen", or "Frist" inside "befristet".
    """
    for line in call_text.split("\n"):
        line_lower = line.lower()
        if any(_term_present(line_lower, term) for term in terms):
            cleaned = _clean_line(line)
            if cleaned:
                return cleaned
    return None


def _first_line_term_and_regex(call_text: str, terms: list[str], value_pattern: str) -> str | None:
    """First line containing a boundary-safe term from `terms` AND matching `value_pattern`."""
    for line in call_text.split("\n"):
        line_lower = line.lower()
        if any(_term_present(line_lower, term) for term in terms) and re.search(
            value_pattern, line, flags=re.IGNORECASE | re.UNICODE
        ):
            cleaned = _clean_line(line)
            if cleaned:
                return cleaned
    return None


def _all_lines_matching_regex(
    call_text: str, value_pattern: str, exclude_terms: list[str] | None = None, max_results: int = 5
) -> list[str]:
    """All lines matching `value_pattern`, skipping lines containing a boundary-safe exclude term."""
    results = []
    for line in call_text.split("\n"):
        if not re.search(value_pattern, line, flags=re.IGNORECASE | re.UNICODE):
            continue
        if exclude_terms and any(_term_present(line.lower(), term) for term in exclude_terms):
            continue
        cleaned = _clean_line(line)
        if cleaned and cleaned not in results:
            results.append(cleaned)
        if len(results) >= max_results:
            break
    return results


def _all_lines_two_term_sets(
    call_text: str, terms_a: list[str], terms_b: list[str], max_results: int = 5
) -> list[str]:
    """All lines containing at least one boundary-safe term from EACH of terms_a and terms_b."""
    results = []
    for line in call_text.split("\n"):
        line_lower = line.lower()
        if any(_term_present(line_lower, t) for t in terms_a) and any(_term_present(line_lower, t) for t in terms_b):
            cleaned = _clean_line(line)
            if cleaned and cleaned not in results:
                results.append(cleaned)
            if len(results) >= max_results:
                break
    return results


_MONEY_PATTERN = r"\d[\d.,]*\s*(?:Mio\.?|Millionen|Mrd\.?|Milliarden|Tsd\.?|Tausend)?\s*(?:Euro|EUR|€)"
_RATE_PATTERN = r"\d{1,3}\s*(?:%|Prozent)"
_FUNDING_CONTEXT_TERMS = [
    "gefördert", "Förderquote", "Forschungseinrichtung", "Unternehmen", "KMU",
    "funding rate", "co-financing", "Fördersatz",
]
_EIGENMITTEL_TERMS = [
    "Eigenmittel", "Eigenanteil", "Eigenbeteiligung", "Kofinanzierung",
    "own contribution", "co-financing requirement",
]
# Publication/disclosure boilerplate that mentions a Euro amount but isn't the
# funding ceiling itself (e.g. "Beihilfen über 100 000 Euro werden veröffentlicht").
_DISCLOSURE_TERMS = ["Transparenzdatenbank", "veröffentlicht", "Offenlegung", "Bekanntgabe"]


def extract_funding_info(call_text: str) -> dict:
    """
    Extracts funding amount(s) / rate-by-partner-type / co-funding requirement.
    total_amount collects ALL non-disclosure money-shaped lines (joined) rather
    than just the first, since real calls often state multiple category-tiered
    ceilings (e.g. separate amounts for Grundlagenforschung/industrielle
    Forschung/experimentelle Entwicklung) with no single "Fördersumme:" line.
    If funding_rate_by_partner_type and eigenmittel_required matched the exact
    same line, keep it only under eigenmittel_required (the more specific
    framing) rather than showing identical text under both labels.
    """
    total_amount_lines = _all_lines_matching_regex(call_text, _MONEY_PATTERN, _DISCLOSURE_TERMS)
    total_amount = "; ".join(total_amount_lines) if total_amount_lines else None

    funding_rate_by_partner_type = _first_line_term_and_regex(call_text, _FUNDING_CONTEXT_TERMS, _RATE_PATTERN)

    eigenmittel_required = _first_line_matching_term(call_text, _EIGENMITTEL_TERMS)

    if funding_rate_by_partner_type is not None and funding_rate_by_partner_type == eigenmittel_required:
        funding_rate_by_partner_type = None

    return {
        "total_amount": total_amount,
        "funding_rate_by_partner_type": funding_rate_by_partner_type,
        "eigenmittel_required": eigenmittel_required,
    }


_DEADLINE_KEYWORD_TERMS = ["Einreichungsfrist", "Bewerbungsschluss", "Abgabefrist", "Deadline", "Frist"]
_DATE_PATTERN = r"\d{1,2}\.\s*\w+\s*20\d{2}"
_ROLLING_TERMS = [
    "rolling", "laufend", "fortlaufend", "bis auf Weiteres", "jederzeit", "ganzjährig",
    "ohne feste Stichtage", "ohne Ausschlussfrist", "keine Ausschlussfrist", "kontinuierlich eingereicht",
]
_DURATION_KEYWORD_TERMS = [
    "Laufzeit", "Projektdauer", "project duration", "Zeitraum", "Förderzeitraum", "Projektzeitraum",
]
_NUMBER_WORD = r"\d+|ein|eine|zwei|drei|vier|fünf|sechs|sieben|acht|neun|zehn"
_DURATION_VALUE_PATTERN = (
    rf"(?:{_NUMBER_WORD})\s*(?:[-–]|bis(?:\s+(?:maximal|zu))?)\s*(?:{_NUMBER_WORD})\s*(?:Monate\w*|Jahre\w*|months|years)"
    rf"|(?:{_NUMBER_WORD})\s*(?:Monate\w*|Jahre\w*|months|years)"
)


def extract_deadline_info(call_text: str) -> dict:
    """
    Extracts submission deadline and project duration. A date only counts as
    the deadline if it co-occurs with a deadline keyword on the same line --
    otherwise a publication date like "Vom 11. Juli 2025" gets mistaken for
    the submission deadline. A rolling/no-fixed-date submission window is
    recognized independently via _ROLLING_TERMS. Duration only counts if a
    duration keyword co-occurs with an actual number (digit OR spelled-out
    German small number, e.g. "ein bis maximal zwei Jahren") + Monate/Jahre on
    the same line, so an unrelated clause (e.g. a post-project sustainability
    obligation) mentioning a duration elsewhere isn't mistaken for the
    project's runtime.
    """
    deadline = (
        _first_line_term_and_regex(call_text, _DEADLINE_KEYWORD_TERMS, _DATE_PATTERN)
        or _first_line_matching_term(call_text, _ROLLING_TERMS)
    )
    project_duration = _first_line_term_and_regex(call_text, _DURATION_KEYWORD_TERMS, _DURATION_VALUE_PATTERN)
    return {
        "deadline": deadline,
        "project_duration": project_duration,
    }


_PARTNER_COUNT_PATTERN = r"\d+\s*[-–]\s*\d+\s*Partner\w*|\bmind\.\s*\d+\s*Partner\w*|\d+\s*Partner\w*|Konsortium:\s*\d+"
_LEAD_KEYWORD_PATTERN = r"Konsortialführung|federführend|kann.{0,15}leiten|can lead|lead the consortium|company-led|research institution.{0,20}\blead\b"
_GEO_TERMS = ["Deutschland", "deutsche", "deutschen", "deutscher", "deutsches", "German"]
_GEO_RESTRICTION_CONTEXT_TERMS = [
    "Antragsberechtigt", "Antragsberechtigte", "Antragsberechtigten",
    "Sitz", "Niederlassung", "ansässig",
    "Bewerbungsberechtigt", "eligible", "must be based",
    "dürfen nur", "beschränkt auf",
]
_PARTNER_TYPE_TERMS = [
    "Forschungseinrichtung", "Forschungseinrichtungen", "Hochschule", "Hochschulen",
    "Universität", "Universitäten", "Unternehmen", "KMU", "Tier-1", "Systemlieferant",
    "Systemlieferanten", "Industriepartner", "research institution", "research institutions",
    "company", "companies", "SME", "SMEs",
]


def extract_consortium_info(call_text: str) -> dict:
    """
    Extracts partner-count requirement, lead-eligibility signals, geographic
    restrictions, and named partner types. geographic_restrictions requires a
    country term AND an eligibility/restriction-context term (Sitz,
    Niederlassung, "dürfen nur", etc.) on the same line -- a bare mention of
    "Deutschland" in scene-setting prose (e.g. "Zivile Sicherheit ist eine
    Grundvoraussetzung ... in Deutschland") is not a restriction. Collects ALL
    matching lines since a call can state both a usage-location restriction
    and a separate applicant-Sitz requirement.
    """
    geo_lines = _all_lines_two_term_sets(call_text, _GEO_TERMS, _GEO_RESTRICTION_CONTEXT_TERMS)
    return {
        "partner_count": _first_matching_line(call_text, _PARTNER_COUNT_PATTERN),
        "lead_eligibility_signal": _first_matching_line(call_text, _LEAD_KEYWORD_PATTERN),
        "geographic_restrictions": "; ".join(geo_lines) if geo_lines else None,
        "partner_types": _first_line_matching_term(call_text, _PARTNER_TYPE_TERMS),
    }


_SUMMARY_ABBREVIATIONS = ["Mio", "Mrd", "Tsd", "bzw", "Nr", "Str", "Dr", "Prof", "ca", "etc"]
_SENTENCE_SPLIT_PATTERN = re.compile(
    "".join(rf"(?<!\b{a}\.)" for a in _SUMMARY_ABBREVIATIONS)
    # Don't split after a period preceded by 1-2 digits -- covers any date
    # ordinal ("Vom 11. Juli 2025", "25.07.2025") or list numbering, not just
    # the specific words above.
    + r"(?<!\d\.)(?<!\d\d\.)"
    + r"(?<=[.!?])\s+(?=[A-ZÄÖÜ„\"])"
)
_FUNDING_BODY_PATTERN = re.compile(
    r"\b(BMWK|BMFTR|BMBF|BMWi|BMWE|SPRIND|EASA|Europäische Kommission|European Commission|"
    r"Horizon Europe|LuFo|ZIM|Manufacturing-X|Bekanntmachung|Förderaufruf|Foerderaufruf)\b",
    re.IGNORECASE,
)


def extract_call_summary(call_text: str, max_sentences: int = 3) -> str | None:
    """
    Extractive summary (not generated prose): the first sentence of the call
    text, plus any additional sentence(s) -- up to max_sentences total, in
    original order -- that name a funding body/framework.
    """
    text = call_text.strip()
    if not text:
        return None

    paragraph = " ".join(line.strip() for line in text.split("\n") if line.strip())
    sentences = [s.strip() for s in _SENTENCE_SPLIT_PATTERN.split(paragraph) if s.strip()]
    if not sentences:
        return None

    selected = [sentences[0]]
    for sentence in sentences[1:]:
        if len(selected) >= max_sentences:
            break
        if sentence not in selected and _FUNDING_BODY_PATTERN.search(sentence):
            selected.append(sentence)

    return " ".join(selected)


def derive_target_application(matched_sectors: list[str]) -> str:
    """Primary matched chesco priority sector, or 'other/general' if none matched."""
    return matched_sectors[0] if matched_sectors else "other/general"


def derive_research_fields(matched_sectors: list[str]) -> str | None:
    """
    Coarse-grained proxy for chesco's internal research-field taxonomy,
    derived from matched_sectors (the doc's actual priority sectors) --
    NOT the finer competency-level taxonomy (e.g. "Electrical Drive
    Systems") implied by the old static mock, which doesn't correspond to
    anything in the real strategy document. Returns None if no sector matched.
    """
    return ", ".join(matched_sectors) if matched_sectors else None


def _normalize_capability_text(text: str) -> str:
    """Lowercases and turns hyphens/slashes/ampersands into spaces so e.g.
    'Digital-Thread-Architektur' and 'Digital Thread' compare as equal tokens."""
    text = text.lower()
    text = re.sub(r"[-/&]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def derive_research_fields_finer(
    matched_technologies: list[str],
    matched_focus_areas: list[str],
    matched_sectors: list[str],
    capability_rows: list[dict],
) -> str | None:
    """
    Finer-grained research_fields using the strategy doc's real
    capability/maturity table: for each capability_maturity row, checks
    whether any already-matched technology/focus-area term (or, via
    strategy_loader's _CAPABILITY_SYNONYMS bridge, a German/English
    synonym of the row's own Fähigkeit name) appears in that Fähigkeit
    name. On a hit, surfaces "{Fähigkeit} ({Reifegrad})". Falls back to
    the coarse matched_sectors-based version if nothing in the capability
    table matches -- this table doesn't cover every chesco capability
    (e.g. "MBSE", "Simulation" aren't tracked technology/focus terms), so
    the fallback keeps the field non-empty rather than going silent.
    """
    candidates = list(dict.fromkeys(matched_technologies + matched_focus_areas))
    hits = []
    seen = set()

    for row in capability_rows:
        fahigkeit = row.get("Fähigkeit", "")
        reifegrad = row.get("Reifegrad", "")
        if not fahigkeit or fahigkeit in seen:
            continue

        names_to_check = [fahigkeit] + row.get("synonyms", [])
        matched = any(
            _term_present(_normalize_capability_text(name), _normalize_capability_text(term))
            for name in names_to_check
            for term in candidates
        )
        if matched:
            hits.append(f"{fahigkeit} ({reifegrad})" if reifegrad else fahigkeit)
            seen.add(fahigkeit)

    if hits:
        return ", ".join(hits)
    return derive_research_fields(matched_sectors)


def suggest_funding_programs(call_text: str, funder_program_rows: list[dict]) -> str | None:
    """
    Additive cross-reference against the strategy doc's funder/program/topic
    directory: for each row, splits "Themen" on commas and checks each topic
    against the raw call text. Returns a formatted string of
    "Programm (Fördergeber) — matched topics" per hit (deduped by
    funder+program), or None if nothing matched. This is exact-string topic
    matching, not semantic -- a call can be clearly relevant to a program
    without using its exact Themen wording (e.g. a civil-security call that
    says "kritische Infrastrukturen" instead of the literal "KRITIS" won't
    surface the Sifo program), so treat this as a lead to verify, not a
    definitive recommendation.
    """
    text_lower = call_text.lower()
    suggestions = []
    seen = set()

    for row in funder_program_rows:
        funder = row.get("Fördergeber", "")
        program = row.get("Programm", "")
        themen = row.get("Themen", "")
        if not themen:
            continue

        topics = [t.strip() for t in themen.split(",") if t.strip()]
        matched_topics = [t for t in topics if _term_present(text_lower, t)]
        if not matched_topics:
            continue

        key = (funder, program)
        if key in seen:
            continue
        seen.add(key)
        suggestions.append(f"{program} ({funder}) — {', '.join(matched_topics)}")

    return "; ".join(suggestions) if suggestions else None


_GERMAN_MONTHS = {
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5, "juni": 6,
    "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}
_GERMAN_DATE_PATTERN = re.compile(r"(\d{1,2})\.\s*(\w+)\s*(20\d{2})")
_COMFORTABLE_DAYS_THRESHOLD = 60


def _parse_german_date(text: str):
    """Parses a 'DD. Month YYYY' German date out of text, or None if not found/unparseable."""
    match = _GERMAN_DATE_PATTERN.search(text)
    if not match:
        return None
    day, month_name, year = match.groups()
    month = _GERMAN_MONTHS.get(month_name.lower())
    if not month:
        return None
    try:
        return date(int(year), month, int(day))
    except ValueError:
        return None


def derive_enough_time(deadline_info: dict) -> str:
    """
    Rule-based classification of whether the stated deadline leaves
    comfortable time: rolling/ongoing deadlines are always comfortable;
    a fixed date is comfortable if more than _COMFORTABLE_DAYS_THRESHOLD
    days out, else tight. Returns "Not stated in call text" if no deadline
    was extracted at all.
    """
    deadline_text = deadline_info.get("deadline")
    if not deadline_text:
        return "Not stated in call text"

    if any(_term_present(deadline_text.lower(), term) for term in _ROLLING_TERMS):
        return "Comfortable — rolling/ongoing submission, no fixed deadline pressure."

    parsed_date = _parse_german_date(deadline_text)
    if parsed_date is None:
        return "Not stated in call text"

    days_remaining = (parsed_date - date.today()).days
    if days_remaining < 0:
        return "Deadline appears to have already passed — verify the date."
    if days_remaining > _COMFORTABLE_DAYS_THRESHOLD:
        return f"Comfortable — {days_remaining} days until the deadline."
    return f"Tight — only {days_remaining} days until the deadline."


# ---------------------------------------------------------------------------
# Quick end-to-end smoke test — run with: python analysis.py
# ---------------------------------------------------------------------------

_SAMPLE_FUNDING_CALL = """
Bekanntmachung: Förderaufruf „Digital Thread für Luft- und Raumfahrtzertifizierung"

Das Bundesministerium für Wirtschaft und Klimaschutz (BMWK) fördert im Rahmen des
Luftfahrtforschungsprogramms VI Verbundprojekte, die den Einsatz von Asset Administration
Shell (AAS) und Digital-Thread-Technologien zur Beschleunigung von EASA-
Zertifizierungsprozessen bei Drohnen und kleinen Flugzeugkategorien demonstrieren.

Ziel ist es, lückenlose Rückverfolgbarkeit von Anforderungen, Konstruktionsentscheidungen
und Testergebnissen über den gesamten Produktlebenszyklus herzustellen und in einem
realen Produktionsprozess bei einem deutschen Luftfahrtunternehmen zu erproben.

Fördersumme: bis zu 3 Mio. Euro pro Verbundprojekt
Laufzeit: 24–36 Monate
Konsortium: 2–5 Partner (mind. ein KMU aus der Luft- und Raumfahrtbranche)
Einreichungsfrist: 15. Oktober 2026

Forschungseinrichtungen werden zu 100 % gefördert. Unternehmen erhalten 50 % (KMU bis 75 %).
"""

if __name__ == "__main__":
    print("Running analysis on sample funding call...\n")
    result = analyze_funding_call(_SAMPLE_FUNDING_CALL)
    print(json.dumps(result, indent=2, ensure_ascii=False))
