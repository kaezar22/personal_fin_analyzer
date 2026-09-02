"""Tab 1 - register a new expense/income row into the sheet."""
from datetime import date

import streamlit as st

from config import (
    COL_FECHA, COL_CATEGORIA, COL_DETALLE, COL_VALOR, COL_MEDIO,
    COL_MES, COL_DOW, COL_ANO, MESES_ES, DEFAULT_CATEGORIAS,
    DEFAULT_MEDIOS, ADD_NEW_OPTION,
)
from core.sheets import append_expense
from core.transform import unique_sorted


def _select_or_new(label, options, key):
    """Selectbox that offers '+ new' as its last choice; picking it reveals
    a text_input so the value can still be typed freely."""
    choices = list(options) + [ADD_NEW_OPTION]
    choice = st.selectbox(label, choices, key=f"{key}_select")
    if choice == ADD_NEW_OPTION:
        return st.text_input(f"Nuevo valor para '{label}'", key=f"{key}_new").strip()
    return choice


def render_input_tab(df_raw):
    st.subheader("Registrar movimiento")

    categorias = unique_sorted(df_raw, COL_CATEGORIA) or DEFAULT_CATEGORIAS
    medios = unique_sorted(df_raw, COL_MEDIO) or DEFAULT_MEDIOS
    detalles = unique_sorted(df_raw, COL_DETALLE)

    with st.form("nuevo_movimiento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", value=date.today())
            tipo = st.radio("Tipo", ["Gasto", "Ingreso"], horizontal=True)
            categoria = _select_or_new("Categoría", categorias, "categoria")
        with col2:
            detalle = _select_or_new("Detalle", detalles, "detalle")
            medio = _select_or_new("Medio de pago", medios, "medio")
            monto = st.number_input("Valor", min_value=0.0, step=1000.0, format="%.0f")

        submitted = st.form_submit_button(
            "Guardar movimiento", type="primary", use_container_width=True
        )

    if submitted:
        if not categoria or not detalle or monto <= 0:
            st.error("Completa categoría, detalle y un valor mayor a 0 antes de guardar.")
            return

        valor = monto if tipo == "Ingreso" else -monto
        row = {
            COL_FECHA: fecha.strftime("%d/%m/%Y"),
            COL_CATEGORIA: categoria,
            COL_DETALLE: detalle,
            COL_VALOR: valor,
            COL_MEDIO: medio,
            COL_MES: MESES_ES[fecha.month],
            COL_DOW: fecha.strftime("%A"),
            COL_ANO: fecha.year,
        }
        ok, error = append_expense(row)
        if ok:
            st.success(f"Movimiento guardado: {categoria} / {detalle} - {valor:,.0f}")
            st.rerun()
        else:
            st.error(f"No se pudo guardar en Google Sheets: {error}")
