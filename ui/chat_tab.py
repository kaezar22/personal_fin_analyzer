"""Tab 3 - chat with an AI assistant over the cashflow data, with optional charts."""
import json
import os

import pandas as pd
import plotly.express as px
import streamlit as st
from openai import OpenAI

from config import COL_FECHA, COL_CATEGORIA, COL_DETALLE, COL_VALOR, COL_MEDIO, GEMINI_MODEL

CHART_START = "---CHART_JSON---"
CHART_END = "---END_CHART_JSON---"

SYSTEM_PROMPT = f"""Eres un asistente especializado en análisis de finanzas personales.
Te doy datos de la hoja 'cashflow2' de mi Google Sheet, con movimientos de gasto e ingreso.

Responde siempre en español, de forma clara y concisa.

Si la pregunta se puede ilustrar con un gráfico, agrega al FINAL de tu respuesta un bloque
con este formato EXACTO (JSON válido en una sola línea):

{CHART_START}
{{"chart_type": "bar|line|pie", "title": "string", "group_by": "categoria|detalle|medio|mes", "value_col": "gasto|ingreso|valor", "agg": "sum|mean|count", "top_n": 10, "resample": null, "filters": {{"fecha_desde": "YYYY-MM-DD", "fecha_hasta": "YYYY-MM-DD", "categoria": ["..."], "medio": ["..."]}}}}
{CHART_END}

Usa "resample": "D", "M" o "Y" en vez de "group_by" cuando el usuario pida una evolución en el tiempo.
Omite el bloque de gráfico si no aplica. No inventes categorías que no existen en los datos.
"""


def _build_context(df: pd.DataFrame, max_rows: int = 1500) -> str:
    total_gasto = df["gasto"].sum()
    total_ingreso = df["ingreso"].sum()
    por_categoria = df.groupby(COL_CATEGORIA)["gasto"].sum().sort_values(ascending=False)
    por_mes = df.groupby(df[COL_FECHA].dt.to_period("M"))["gasto"].sum()

    context = "=== RESUMEN ===\n"
    context += f"Rango de fechas: {df[COL_FECHA].min().date()} a {df[COL_FECHA].max().date()}\n"
    context += f"Total gastos: {total_gasto:,.0f}\n"
    context += f"Total ingresos: {total_ingreso:,.0f}\n"
    context += f"Gasto por categoría:\n{por_categoria.to_string()}\n\n"
    context += f"Gasto por mes:\n{por_mes.to_string()}\n\n"
    context += "=== DATOS DETALLADOS (cashflow2) ===\n"
    context += f"Columnas: {', '.join(df.columns)}\n"

    sample = df.tail(max_rows) if len(df) > max_rows else df
    context += sample.to_string(index=False)
    if len(df) > max_rows:
        context += f"\n... y {len(df) - max_rows} filas más antiguas no incluidas."
    return context


def _ask_ai(api_key: str, df: pd.DataFrame, question: str):
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{_build_context(df)}\n\nPregunta: {question}"},
        ]
        response = client.chat.completions.create(model=GEMINI_MODEL, messages=messages)
        return response.choices[0].message.content, None
    except Exception as e:
        return None, str(e)


def _extract_chart_spec(text: str):
    if CHART_START not in text or CHART_END not in text:
        return None
    raw = text.split(CHART_START, 1)[1].split(CHART_END, 1)[0].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _build_chart(df: pd.DataFrame, spec: dict):
    dff = df.copy()
    filters = spec.get("filters") or {}

    if filters.get("fecha_desde"):
        dff = dff[dff[COL_FECHA] >= pd.to_datetime(filters["fecha_desde"], errors="coerce")]
    if filters.get("fecha_hasta"):
        dff = dff[dff[COL_FECHA] <= pd.to_datetime(filters["fecha_hasta"], errors="coerce")]
    if filters.get(COL_CATEGORIA):
        dff = dff[dff[COL_CATEGORIA].isin(filters[COL_CATEGORIA])]
    if filters.get(COL_MEDIO):
        dff = dff[dff[COL_MEDIO].isin(filters[COL_MEDIO])]

    value_col = spec.get("value_col") if spec.get("value_col") in {COL_VALOR, "gasto", "ingreso"} else "gasto"
    agg = spec.get("agg") if spec.get("agg") in {"sum", "mean", "count"} else "sum"
    chart_type = spec.get("chart_type") if spec.get("chart_type") in {"bar", "line", "pie"} else "bar"
    title = spec.get("title") or "Gráfico financiero"
    resample = spec.get("resample")

    if resample in {"D", "M", "Y"}:
        freq_map = {"D": "D", "M": "MS", "Y": "YS"}
        grouped = dff.set_index(COL_FECHA)[value_col].resample(freq_map[resample]).agg(agg).reset_index()
        x, y = COL_FECHA, value_col
    else:
        group_by = spec.get("group_by")
        if group_by not in dff.columns:
            group_by = COL_CATEGORIA
        grouped = dff.groupby(group_by)[value_col].agg(agg).reset_index()
        grouped = grouped.sort_values(value_col, ascending=False)
        top_n = spec.get("top_n")
        if top_n:
            grouped = grouped.head(int(top_n))
        x, y = group_by, value_col

    if grouped.empty:
        return None

    if chart_type == "pie":
        return px.pie(grouped, names=x, values=y, title=title, hole=0.4)
    if chart_type == "line":
        return px.line(grouped, x=x, y=y, title=title, markers=True)
    return px.bar(grouped, x=x, y=y, title=title)


def _render_assistant_message(content: str, df: pd.DataFrame):
    text = content.split(CHART_START)[0].strip() if CHART_START in content else content
    st.markdown(text)
    spec = _extract_chart_spec(content)
    if spec:
        fig = _build_chart(df, spec)
        if fig:
            st.plotly_chart(fig, use_container_width=True)


def render_chat_tab(df: pd.DataFrame):
    st.subheader("Chat con tu asistente financiero")

    api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("Falta GOOGLE_API_KEY en los secrets de Streamlit.")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                _render_assistant_message(message["content"], df)
            else:
                st.write(message["content"])

    prompt = st.chat_input("Haz una pregunta sobre tus finanzas...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analizando tus datos..."):
                answer, error = _ask_ai(api_key, df, prompt)
            if error:
                st.error(f"Error al consultar la IA: {error}")
            else:
                _render_assistant_message(answer, df)
                st.session_state.messages.append({"role": "assistant", "content": answer})

    if st.session_state.messages and st.button("Limpiar conversación"):
        st.session_state.messages = []
        st.rerun()
