"""All Google Sheets I/O lives here. No Streamlit UI code in this file."""
import json

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

from config import SHEET_NAME, SHEET_COLUMNS

# Full read/write scopes - required because the Input tab appends rows.
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource(show_spinner=False)
def get_worksheet():
    """Authorize with the service account and return the 'cashflow2' worksheet.
    Cached as a resource (not data) because gspread objects aren't serializable.
    """
    creds_info = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    gc = gspread.authorize(creds)
    spreadsheet_id = st.secrets["SPREADSHEET_ID"]
    sh = gc.open_by_key(spreadsheet_id)
    return sh.worksheet(SHEET_NAME)


def _clean_column_names(columns):
    """De-duplicate / fill blank header names, same as the original app."""
    new_columns, seen = [], {}
    for col in columns:
        if col is None or str(col).strip() == "":
            col = "columna_vacia"
        if col in seen:
            seen[col] += 1
            col = f"{col}_{seen[col]}"
        else:
            seen[col] = 0
        new_columns.append(col)
    return new_columns


@st.cache_data(ttl=300, show_spinner=False)
def load_data():
    """Load the full 'cashflow2' sheet as a DataFrame of raw strings.
    Returns (df, error_message).
    """
    try:
        ws = get_worksheet()
        values = ws.get_all_values()
        if not values:
            return pd.DataFrame(columns=SHEET_COLUMNS), None
        headers = _clean_column_names(values[0])
        df = pd.DataFrame(values[1:], columns=headers)
        return df, None
    except Exception as e:
        return None, str(e)


def append_expense(row: dict):
    """Append one row to the sheet, in the exact column order of SHEET_COLUMNS.
    Clears the data cache so the next load_data() picks it up.
    Returns (success, error_message).
    """
    try:
        ws = get_worksheet()
        ordered_row = [row.get(col, "") for col in SHEET_COLUMNS]
        ws.append_row(ordered_row, value_input_option="USER_ENTERED")
        load_data.clear()
        return True, None
    except Exception as e:
        return False, str(e)
