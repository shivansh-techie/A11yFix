# A11yFix

A web accessibility auditor built as a minor project. Paste in a URL, it runs axe-core inside a real browser and shows you every WCAG 2.1 violation, then suggests a corrected HTML snippet for each one.

**Stack:** FastAPI + Playwright + axe-core + Streamlit + SQLite. AI fixes via Claude (optional — works without an API key too).

---

## How it works

1. You submit a URL through the Streamlit dashboard
2. FastAPI queues a background task
3. Playwright launches headless Chromium and navigates to the page
4. axe-core JS is injected and run in-browser → returns violations JSON
5. Each violation gets scored by severity (critical/serious/moderate/minor)
6. Fix suggestions come from a pre-written rule dictionary first; if a rule isn't covered and `ANTHROPIC_API_KEY` is set, it asks Claude instead
7. Everything gets saved to SQLite so you can view history

The scanner uses `wait_until="load"` not `networkidle` — networkidle would time out on most modern sites that have background polling or websockets.

---

## Setup

Python 3.11+ recommended.

```bash
git clone <this-repo>
cd a11yfix
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# edit .env if you want AI fixes (ANTHROPIC_API_KEY is optional)
```

Start locally:

```bash
bash start.sh
```

- API: http://localhost:8000  
- Dashboard: http://localhost:8501

---

## Test URLs (for demo / viva)

These all have known accessibility problems:

| URL | What's broken |
|---|---|
| `https://dequeuniversity.com/demo/mars/` | Intentionally broken demo — loads of violations |
| `https://www.w3schools.com` | Missing alt text, contrast issues |
| `https://govuk-elements.herokuapp.com` | Form label association failures |

---

## Deploy to Hugging Face Spaces

1. Push this repo to GitHub
2. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
3. Set **Space SDK** → **Docker**
4. Connect your GitHub repo
5. In the Space's **Settings → Variables**, add:
   - `ANTHROPIC_API_KEY` (optional — leave blank to use the rule dictionary only)
   - `PORT` = `7860` (HF Spaces expects port 7860)
6. Also update `supervisord.conf` — change the Streamlit port line to use `${PORT:-7860}`

The Space will build from the Dockerfile automatically. Public URL will be `https://huggingface.co/spaces/yourname/a11yfix`.

---

## Project structure

```
a11yfix/
├── app/
│   ├── main.py        FastAPI — scan endpoints, PDF export
│   ├── scanner.py     Playwright + axe-core injection
│   ├── ai_fix.py      rule dictionary → Claude fallback
│   ├── rule_fixes.py  pre-written fixes for ~40 common violations
│   ├── scoring.py     0-100 score from violation severities
│   ├── models.py      SQLModel ORM (Scan, Violation tables)
│   └── database.py    SQLite engine setup
├── frontend/
│   └── app.py         Streamlit dashboard
├── templates/
│   └── report.html    PDF export template (WeasyPrint)
├── Dockerfile
├── supervisord.conf   runs both processes in one container
└── start.sh           local dev launcher
```
