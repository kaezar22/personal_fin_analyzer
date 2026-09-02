"""Tab 2 - dashboard with KPIs and charts."""
import pandas as pd
import plotly.express as px
import streamlit as st

from config import (
    COL_FECHA, COL_CATEGORIA, COL_DETALLE, COL_VALOR, COL_MEDIO,
    CATEGORY_COLOR_SEQUENCE,
)
from core.transform import spend_by_category, top_detalle, unique_sorted

PERIOD_LABELS = {"Diario": "D", "Mensual": "M", "Anual": "Y"}
FREQ_MAP = {"D": "D", "M": "MS", "Y": "YS"}


def render_dashboard_tab(df):
    st.subheader("Dashboard financiero")

    if df.empty:
        st.info("Todavía no hay datos para mostrar.")
        return

    fcol1, fcol2, fcol3 = st.columns([1.3, 1, 1.3])
    with fcol1:
        min_date, max_date = df[COL_FECHA].min().date(), df[COL_FECHA].max().date()
        date_range = st.date_input(
            "Rango de fechas", value=(min_date, max_date),
            min_value=min_date, max_value=max_date,
        )
    with fcol2:
        periodo_label = st.radio("Ver por", list(PERIOD_LABELS.keys()), horizontal=True, index=1)
    with fcol3:
        todas_categorias = unique_sorted(df, COL_CATEGORIA)
        categorias_sel = st.multiselect("Categorías", todas_categorias, default=todas_categorias)

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
    else:
        start, end = min_date, max_date

    mask = (df[COL_FECHA].dt.date >= start) & (df[COL_FECHA].dt.date <= end)
    if categorias_sel:
        mask &= df[COL_CATEGORIA].isin(categorias_sel)
    dff = df[mask]

    if dff.empty:
        st.warning("No hay movimientos en ese rango/categorías.")
        return

    total_gasto = dff["gasto"].sum()
    total_ingreso = dff["ingreso"].sum()
    balance = total_ingreso - total_gasto
    n_dias = max((end - start).days + 1, 1)
    promedio_diario = total_gasto / n_dias

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total gastos", f"${total_gasto:,.0f}")
    k2.metric("Total ingresos", f"${total_ingreso:,.0f}")
    k3.metric("Balance neto", f"${balance:,.0f}")
    k4.metric("Gasto diario prom.", f"${promedio_diario:,.0f}")

    st.divider()

    periodo = PERIOD_LABELS[periodo_label]
    gastos_df = dff[dff[COL_VALOR] < 0].copy()
    gastos_df["gasto_abs"] = gastos_df[COL_VALOR].abs()

    time_cat = (
        gastos_df.set_index(COL_FECHA)
        .groupby([pd.Grouper(freq=FREQ_MAP[periodo]), COL_CATEGORIA])["gasto_abs"]
        .sum()
        .reset_index()
    )
    fig_time = px.bar(
        time_cat, x=COL_FECHA, y="gasto_abs", color=COL_CATEGORIA,
        title=f"Gastos por período ({periodo_label.lower()}), por categoría",
        labels={"gasto_abs": "Gasto", COL_FECHA: "Fecha"},
        color_discrete_sequence=CATEGORY_COLOR_SEQUENCE,
    )
    fig_time.update_layout(legend_title_text="Categoría", margin=dict(t=50))
    st.plotly_chart(fig_time, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        cat_totals = spend_by_category(dff)
        fig_pie = px.pie(
            cat_totals, names=COL_CATEGORIA, values="gasto_abs",
            title="% de gasto por categoría", hole=0.4,
            color_discrete_sequence=CATEGORY_COLOR_SEQUENCE,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        medio_totals = (
            gastos_df.groupby(COL_MEDIO)["gasto_abs"]
            .sum().sort_values(ascending=False).reset_index()
        )
        fig_medio = px.bar(
            medio_totals, x="gasto_abs", y=COL_MEDIO, orientation="h",
            title="Gasto por medio de pago",
            labels={"gasto_abs": "Gasto", COL_MEDIO: "Medio"},
            color_discrete_sequence=CATEGORY_COLOR_SEQUENCE,
        )
        st.plotly_chart(fig_medio, use_container_width=True)

    st.subheader("Mayores gastos individuales")
    top10 = top_detalle(dff, n=10)
    fig_top = px.bar(
        top10.sort_values("gasto_abs"), x="gasto_abs", y=COL_DETALLE, orientation="h",
        title="Top 10 gastos", labels={"gasto_abs": "Gasto", COL_DETALLE: "Detalle"},
        color_discrete_sequence=["#d62728"],
    )
    st.plotly_chart(fig_top, use_container_width=True)
