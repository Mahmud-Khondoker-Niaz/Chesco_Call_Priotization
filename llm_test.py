"""
llm_test.py — SCRATCH FILE for UI testing/demoing with mock data only.

This is NOT part of the production code path. It exists so app.py can be
pointed at richer mock scenarios while exploring the UI, without touching
llm_client.py (which is already prepared for the real AI Hub/HAWKI API).

These mocks match the JSON schema defined in system_prompt_text.txt:
- strategic_fit.rating is "HIGH" / "MODERATE" / "LOW" (not a number)
- recommendation.decision is exactly "PURSUE" / "CONSIDER" / "DO NOT PURSUE"
- there is a focus_area block (research_fields, target_application)
- partners_needed has geographic_restrictions (not funding_pct_by_type)
- funding has eigenmittel_required
- recommendation has suggested_lead_team

HOW TO REMOVE THIS LATER (once the real API is ready):
1. Delete this file.
2. In app.py, change the import back to:
     from llm_client import analyze_call, USE_MOCK
3. In llm_client.py, set USE_MOCK = False and fill in the env vars.

HOW TO USE THIS FILE RIGHT NOW:
In app.py, change the import line to:
     from llm_test import analyze_call, USE_MOCK
"""

USE_MOCK = True  # Always True here — this file has no real-API code at all

def analyze_call(call_text: str) -> str:
    """Same signature as llm_client.analyze_call, so app.py doesn't change otherwise."""
    return _mock_llm_response(call_text)


def _mock_llm_response(call_text: str) -> str:
    text_lower = call_text.lower()

    if any(kw in text_lower for kw in ["robotik", "ki-robotikbooster", "hightech agenda"]):
        return _MOCK_KI_ROBOTIKBOOSTER

    if any(kw in text_lower for kw in ["zivile sicherheit", "civil security", "sifo", "feuerwehr", "kritische infrastruktur"]):
        return _MOCK_CIVIL_SECURITY

    if any(kw in text_lower for kw in ["elektrifizierte antriebssysteme", "hybrid-elektrische antriebsarchitekturen", "elektrifizierung von antriebssystemen"]):
        return _MOCK_HYBRID_ELECTRIC

    return _MOCK_GENERIC


# ===== MOCK DATA — REPLACE WITH REAL LLM EXTRACTION WHEN INTEGRATING OPEN WEBUI API =====
# The three funding fields below (total_amount, funding_rate_by_partner_type, eigenmittel_required)
# are hardcoded from the BMFTR "Forschung für die zivile Sicherheit" call text.
# When wiring up the real LLM, remove these hardcoded values and let the LLM extract
# the funding details from the actual call text instead.
# ===== END MOCK DATA =====
_MOCK_CIVIL_SECURITY = """
{
  "summary": "BMFTR funding guideline (published 25 July 2025) under the 'Forschung fuer die zivile Sicherheit' framework, funding demonstration and testing environments that make innovative civil-security solutions visible and evaluable for a broad community of users such as police, fire services, municipalities, critical-infrastructure operators, and private security firms. Projects run 1-2 years, combining scientific design and build-out with practice-near piloting. Submissions are accepted on a rolling basis until 30 June 2027.",
  "what_call_really_wants": "The funder wants concrete, testable demonstrators of civil-security technology that real end users (authorities, emergency services, infrastructure operators) can evaluate in practice, designed to keep running and stay open to third parties after the funded phase ends.",
  "funding": {
    "total_amount": "Up to EUR 55M per project (Grundlagenforschung/basic research); up to EUR 35M (industrielle Forschung/industrial research); up to EUR 25M (experimentelle Entwicklung/experimental development).",
    "funding_rate_by_partner_type": "Grundlagenforschung: up to 100%. Industrielle Forschung: up to 50% (up to 80% with SME/collaboration bonuses). Experimentelle Entwicklung: up to 25% (up to 80% with bonuses). Universities, research institutions, and public authorities: up to 100% in all categories.",
    "eigenmittel_required": "Companies typically must provide a minimum 75% own contribution (funded at <=25% base rate for experimental development; higher rates via SME/collaboration bonuses). Universities, research institutions, and public authorities: up to 100% funded, no Eigenmittel required."
  },
  "consortium_leadership": {
    "can_chesco_lead": "No",
    "rationale": "The call explicitly prefers individual applicants; consortia are only accepted in justified exceptions, so the usual consortium-leadership question is largely moot here."
  },
  "partners_needed": {
    "count": "Typically none (individual project preferred)",
    "types": "N/A under standard track; exceptions require justification",
    "geographic_restrictions": "not specified"
  },
  "deadline_timeline": {
    "deadline": "Rolling, open until 30 June 2027",
    "enough_time": "Comfortable -- the rolling deadline removes time pressure, so timeline is not a limiting factor.",
    "project_duration": "1-2 years"
  },
  "focus_area": {
    "research_fields": ["Other: civil-security demonstrators"],
    "target_application": "other/general"
  },
  "strategic_fit": {
    "rating": "LOW",
    "justification": "The call's domain (civil security, authorities/emergency services as end users) does not align with chesco's hybrid-electric propulsion and aviation focus, research fields, or target applications. No meaningful technical or thematic overlap was identified in the published call text itself."
  },
  "recommendation": {
    "decision": "DO NOT PURSUE",
    "rationale": "Strategic fit is very low despite a workable timeline; pursuing this would not advance chesco's core mission and would consume scarce proposal-writing capacity better spent elsewhere.",
    "suggested_lead_team": "not applicable"
  },
  "open_questions_missing_info": [
    "Exact funding amount/rate per project (check the full Bekanntmachung/FAQ PDF on sifo.de)",
    "Specific topic areas open within the call, if topic-restricted",
    "Conditions under which a consortium exception would be granted"
  ]
}
"""

_MOCK_KI_ROBOTIKBOOSTER = """
{
  "summary": "Flagship measure ('KI-Robotikbooster') of the Hightech Agenda Deutschland, backed by 100 million euro split across a 'Robo-Hubs' funding guideline and a separate multi-purpose-robot challenge run by SPRIND. The Robo-Hubs guideline is a concept competition: research-only consortia of roughly 2-4 partners design a domain-specific 'Robo-Hub' (example domains: production, logistics, agriculture, construction, health/care), each needing one clear application focus. Up to 500,000 euro is available per consortium for a 9-month concept phase, with applications due 31 July 2026.",
  "what_call_really_wants": "BMFTR wants research-institution-led consortia to design domain-specific 'Robo-Hubs': shared, practice-near infrastructure bridging academic robotics research and industrial application, with SMEs as a key intended beneficiary. A credible, broadly-supported plan for one clear application domain is the central evaluation criterion.",
  "funding": {
    "total_amount": "Up to 500,000 euro per consortium for the 9-month concept phase; 100 million euro program-wide.",
    "funding_rate_by_partner_type": "100% for research-institution partners in the concept phase; no direct company funding until a later implementation phase (~30-50% industry/Land co-financing expected then).",
    "eigenmittel_required": "None for the concept phase itself."
  },
  "consortium_leadership": {
    "can_chesco_lead": "Yes",
    "rationale": "The concept-competition phase is exclusively open to universities and non-university research institutions, funded at 100%, so chesco could lead a 2-4 partner research consortium without needing a company co-lead."
  },
  "partners_needed": {
    "count": "Roughly 2-4 partners per consortium",
    "types": "Research institutions only for the concept phase; industry partners should be closely involved in concept development but are not funded until a later phase.",
    "geographic_restrictions": "not specified beyond standard German federal funding eligibility"
  },
  "deadline_timeline": {
    "deadline": "31 July 2026 -- fixed deadline",
    "enough_time": "Tight -- about 5 weeks from today to assemble a 2-4 partner research consortium and submit a German-language formal application.",
    "project_duration": "9 months for the concept phase, targeted start 1 December 2026."
  },
  "focus_area": {
    "research_fields": ["Manufacturing & Assembly"],
    "target_application": "other/general (framed via a production/manufacturing angle)"
  },
  "strategic_fit": {
    "rating": "MODERATE",
    "justification": "Robotics/embodied AI sits outside chesco's hybrid-electric propulsion core, but the call requires each Robo-Hub to have one clear application domain, and 'production' is explicitly listed as an example domain -- overlapping with chesco's own Manufacturing & Assembly research field. A credible framing around AI-based robotics for aviation/hybrid-electric-propulsion manufacturing and assembly is plausible, though not a direct match."
  },
  "recommendation": {
    "decision": "CONSIDER",
    "rationale": "Worth a fast go/no-go check given chesco's direct eligibility to lead and a natural Manufacturing & Assembly angle, but a credible domain framing and a 2-4 partner consortium need to be lined up almost immediately given the 31 July 2026 deadline, and this should be weighed against other capacity commitments.",
    "suggested_lead_team": "Manufacturing & Assembly"
  },
  "open_questions_missing_info": [
    "Can a convincing aviation/hybrid-electric manufacturing-and-assembly framing be written and validated with partners within about 5 weeks?",
    "Are DLR EL, Fraunhofer, or other existing chesco strategic partners available to join a Robo-Hub consortium on this timeline?",
    "Exact terms of the 30-50% co-financing requirement for the later implementation phase"
  ]
}
"""

_MOCK_HYBRID_ELECTRIC = """
{
  "summary": "BMFTR funding guideline under the 7th Luftfahrtforschungsprogramm (LuFo VII-2), supporting R&D projects on electrified propulsion systems for civil aviation. The call targets hybrid-electric drive architectures for aircraft up to 19 seats, battery/fuel-cell integration into existing powertrains, certifiable power electronics and e-motors, and scalable test-bench concepts. Fixed submission deadline of 15 September 2026, project duration 24-36 months, maximum funding 4 million euro per consortium project.",
  "what_call_really_wants": "BMFTR wants concrete, certifiable progress on electrified propulsion architectures for small aircraft, with a credible path to EASA certification and validation via realistic test-bench setups -- not a pure research demonstration. Industrial credibility and a clear route to certification and CO2 reduction are weighted heavily in evaluation.",
  "funding": {
    "total_amount": "Up to 4 million euro per consortium project.",
    "funding_rate_by_partner_type": "Industrial research: companies 50%, SMEs up to 75%, research institutions 100% (requires at least 60% effective consortium collaboration). Experimental development: companies 25%, SMEs up to 50%, research institutions 100%.",
    "eigenmittel_required": "Yes for company partners -- roughly 50% own contribution at the standard industrial-research rate; chesco itself would be funded at 100% as a research institution."
  },
  "consortium_leadership": {
    "can_chesco_lead": "Maybe",
    "rationale": "The call explicitly welcomes a company-led consortium, provided there is a demonstrated close link to an aircraft manufacturer or Tier-1 systems supplier. chesco's hybrid-electric propulsion focus is a direct fit for the topic itself; the open question is whether chesco currently has the OEM/Tier-1 relationship needed to satisfy that specific leadership condition."
  },
  "partners_needed": {
    "count": "Up to 6 partners in the consortium",
    "types": "At least one aircraft manufacturer or Tier-1 systems supplier appears effectively required given the evaluation criteria; likely additional partners for battery/fuel-cell systems and certifiable power electronics.",
    "geographic_restrictions": "Applicants must be based in Germany"
  },
  "deadline_timeline": {
    "deadline": "15 September 2026 -- fixed deadline, not a rolling submission",
    "enough_time": "Tight but workable -- roughly 12 weeks from today. Realistic only if partner outreach, especially toward an OEM/Tier-1 partner, starts immediately.",
    "project_duration": "24-36 months"
  },
  "focus_area": {
    "research_fields": ["Electrical Drive Systems", "Systems Integration", "Thermal Management"],
    "target_application": "aviation"
  },
  "strategic_fit": {
    "rating": "HIGH",
    "justification": "This call sits directly inside chesco's core hybrid-electric propulsion and aviation focus -- battery/fuel-cell integration, certifiable power electronics, and e-motor development for aircraft are squarely within chesco's stated research fields and TRL 1-6 range. One of the closest thematic matches seen so far, far stronger than the Robo-Hubs (MODERATE) or Civil Security (LOW) calls."
  },
  "recommendation": {
    "decision": "PURSUE",
    "rationale": "Near-direct match to chesco's core technology and mission, with a clear EASA-certification angle and a meaningful funding ceiling. The main gating item is the explicit OEM/Tier-1 systems-supplier partner requirement, which should be resolved immediately given the 15 September 2026 deadline.",
    "suggested_lead_team": "Electrical Drive Systems, with Systems Integration support"
  },
  "open_questions_missing_info": [
    "Does chesco have an existing relationship with an aircraft OEM or Tier-1 supplier that satisfies the call's explicit partner requirement?",
    "Exact evaluation weighting between certification readiness and CO2-reduction criteria",
    "Whether chesco's existing hybrid-electric propulsion IP or test data can be leveraged to accelerate the proposal"
  ]
}
"""

_MOCK_GENERIC = """
{
  "summary": "This is a placeholder MOCK response from the AI Call Prioritization Assistant. No real LLM has been called yet — connect the AI Hub/HAWKI endpoint in llm_client.py to get a real analysis of this call text.",
  "what_call_really_wants": "Placeholder text — once connected to a real LLM, this field will explain the funder's underlying intent.",
  "funding": {
    "total_amount": "mock data",
    "funding_rate_by_partner_type": "mock data",
    "eigenmittel_required": "mock data"
  },
  "consortium_leadership": {
    "can_chesco_lead": "mock data",
    "rationale": "This is placeholder text from the mock LLM client."
  },
  "partners_needed": {
    "count": "mock data",
    "types": "mock data",
    "geographic_restrictions": "mock data"
  },
  "deadline_timeline": {
    "deadline": "mock data",
    "enough_time": "mock data",
    "project_duration": "mock data"
  },
  "focus_area": {
    "research_fields": ["mock data"],
    "target_application": "mock data"
  },
  "strategic_fit": {
    "rating": "MODERATE",
    "justification": "No real analysis performed — this is mock data for UI testing."
  },
  "recommendation": {
    "decision": "CONSIDER",
    "rationale": "Placeholder recommendation from mock data.",
    "suggested_lead_team": "mock data"
  },
  "open_questions_missing_info": [
    "This response is mocked — connect a real LLM via llm_client.py for an actual assessment."
  ]
}
"""