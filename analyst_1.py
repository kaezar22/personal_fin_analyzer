"""Analizador Financiero - entry point.

Kept as 'analyst_1.py' (instead of renaming to app.py) so the existing
Streamlit Community Cloud deployment keeps working without changing its
"Main file path" setting.
"""
import streamlit as st

from core.sheets import load_data
from core.transform import clean_dataframe
from ui.styles import load_css
from ui.input_tab import render_input_tab
from ui.dashboard_tab import render_dashboard_tab
from ui.chat_tab import render_chat_tab

st.set_page_config(
    page_title="Analizador Financiero",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)
load_css()

st.sidebar.header("Datos")
if st.sidebar.button("Recargar datos"):
    load_data.clear()
    st.rerun()

df_raw, error = load_data()
if error:
    st.error(f"No se pudieron cargar los datos: {error}")
    st.stop()

st.sidebar.success(f"{len(df_raw)} filas cargadas")

df = clean_dataframe(df_raw)

st.markdown('<h1 class="main-header">🏦 Analizador Financiero</h1>', unsafe_allow_html=True)

tab_input, tab_dashboard, tab_chat = st.tabs(["➕ Nuevo movimiento", "📊 Dashboard", "💬 Chat"])

with tab_input:
    render_input_tab(df_raw)

with tab_dashboard:
    render_dashboard_tab(df)

with tab_chat:
    render_chat_tab(df)
