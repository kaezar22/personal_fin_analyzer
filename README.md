# Analizador Financiero

Streamlit app with 3 tabs backed by the "cashflow2" sheet in the "reflauta" Google Sheet:

1. **Nuevo movimiento** - form to append a row (expense or income) straight to the sheet.
2. **Dashboard** - KPIs and charts (spend over time by category, % by category, spend by payment method, top expenses).
3. **Chat** - ask questions about your data; the assistant can attach a chart to its answer.

## Setup

`requirements.txt` has the dependencies. Streamlit secrets needed (`.streamlit/secrets.toml` locally, or the Cloud app's Secrets panel):

```toml
DEEPSEEK_API_KEY = "..."
SPREADSHEET_ID = "185BYhloP_cxaikxb4lK4joFAC0SQCfea35l4Owb3tJs"
GOOGLE_CREDENTIALS = '''{ ...service account json... }'''
```

**Important:** the service account email inside `GOOGLE_CREDENTIALS` must have **Editor** access on the "reflauta" Google Sheet itself (Share button inside the sheet, not the GCP IAM role) - the Input tab needs write access, not just read.

Run locally with:

```bash
streamlit run analyst_1.py
```
