# chesco Call Prioritization Assistant

A Streamlit prototype for chesco's Application Process. Paste in the text of a
funding call (Förderaufruf) and get a structured analysis: summary, funding details,
strategic fit, focus area, and an overall recommendation (PURSUE / CONSIDER / DO NOT
PURSUE).

This is a **decision-support tool** — it does not replace human judgment, it
accelerates the initial assessment so the team can prioritize across multiple calls
faster.

---

## Project Structure

```
chesco_call_prioritizer/
├── app.py                  # Streamlit UI - main entry point
├── llm_client.py            # Handles LLM calls (mock + real API)
├── system_prompt_text.txt   # The system prompt (edit this to refine analysis behavior)
├── requirements.txt          # Python dependencies
├── docs/
│   └── system_prompt.md      # Documented version of the system prompt with notes
└── README.md
```

---

## Setup & Run (Local)

1. **Install Python 3.9+** if not already installed.

2. **Create a virtual environment (recommended):**


   ```bash
  venv\Scripts\activate   # On Windows: venv\Scripts\activate
   ```
  ```bash
  source venv/bin/activate  # On MacOs/Linux
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app:**
   ```bash
   streamlit run app.py
   ```

5. The app will open in your browser (usually `http://localhost:8501`).

---

## Current Status: MOCK MODE

By default, the app runs with `USE_MOCK = True` in `llm_client.py`. This returns a
placeholder response so the UI can be tested and demoed **before** real AI Hub/HAWKI
API access is available.

---

## Connecting the Real LLM (AI Hub / HAWKI)

Once API access details are available from Ankit/Sabith:

1. Open `llm_client.py`
2. Set the following (preferably via environment variables, not hardcoded):
   - `AI_HUB_ENDPOINT` - the API URL (e.g., `https://ai-hub.chesco.de/api/v1/chat/completions`)
   - `AI_HUB_API_KEY` - authentication token/key
   - `MODEL_NAME` - the model identifier to use
3. Set `USE_MOCK = False`
4. Check `_call_real_llm()` - the request/response format assumes an
   OpenAI-compatible chat completions API (common for Open WebUI). Adjust if the
   actual API differs.

### Setting environment variables

**Linux/macOS:**
```bash
export AI_HUB_ENDPOINT="https://ai-hub.chesco.de/api/v1/chat/completions"
export AI_HUB_API_KEY="your-api-key-here"
export AI_HUB_MODEL_NAME="model-name-here"
streamlit run app.py
```

**Windows (PowerShell):**
```powershell
$env:AI_HUB_ENDPOINT="https://ai-hub.chesco.de/api/v1/chat/completions"
$env:AI_HUB_API_KEY="your-api-key-here"
$env:AI_HUB_MODEL_NAME="model-name-here"
streamlit run app.py
```

Alternatively, use [Streamlit secrets](https://docs.streamlit.io/develop/concepts/connections/secrets-management)
(`.streamlit/secrets.toml`) for a more integrated approach — recommended for
deployment.

---

## Editing the System Prompt

The system prompt lives in `system_prompt_text.txt` as plain text — edit it directly
to refine the analysis logic (e.g., adjust the Focus Area taxonomy, add new sections,
change the strategic fit criteria). No code changes needed; the app reloads it on
each analysis.

A documented version with design notes is in `docs/system_prompt.md`.

---

## Testing

Test with the two sample calls used during development:
1. **Civil Security Demonstration Call** (BMFTR) - expected: LOW strategic fit
2. **KI-Robotikbooster** (BMFTR/Hightech Agenda) - expected: MODERATE strategic fit

Paste each call's full text into the app and review the output against the expected
strategic fit ratings to sanity-check the prompt.

---

## Roadmap / Next Steps

- [x] System prompt design
- [x] Streamlit skeleton with mock response
- [ ] Connect real AI Hub/HAWKI API endpoint
- [ ] Test with sample calls, refine prompt
- [ ] Set up GitLab repository
- [ ] Multi-call comparison view (overlap & capacity check across parallel calls)
- [ ] Deploy/integrate into chesco environment (AI Hub infra, AD auth, security review)

---

## Contacts (for integration)

| Item | Contact |
|---|---|
| AI Hub/HAWKI API endpoint, credentials, model name | Ankit / Sabith |
| GitLab repo access | Ankit/Sabith or IT |
| Deployment feasibility on AI Hub infrastructure | Sabith/Ankit |
| Active Directory access control | Mukund |
| Security compliance review | Pradeep |
