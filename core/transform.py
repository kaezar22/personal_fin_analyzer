"""Cleaning, typing and aggregation helpers. Pure pandas, no Streamlit."""
import pandas as pd

from config import COL_FECHA, COL_CATEGORIA, COL_DETALLE, COL_VALOR, COL_MEDIO


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Convert raw string columns from Google Sheets into proper dtypes and
    add 'gasto' / 'ingreso' helper columns (always positive numbers)."""
    df = df.copy()

    if COL_FECHA in df.columns:
        df[COL_FECHA] = pd.to_datetime(df[COL_FECHA], format="%d/%m/%Y", errors="coerce")

    if COL_VALOR in df.columns:
        # Handles both "1234567" and "1.234.567,00" style numbers.
        cleaned = df[COL_VALOR].astype(str).str.strip()
        cleaned = cleaned.str.replace(r"\.(?=\d{3}(?:\D|$))", "", regex=True)
        cleaned = cleaned.str.replace(",", ".", regex=False)
        df[COL_VALOR] = pd.to_numeric(cleaned, errors="coerce")

    for col in (COL_CATEGORIA, COL_DETALLE, COL_MEDIO):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    if COL_FECHA in df.columns and COL_VALOR in df.columns:
        df = df.dropna(subset=[COL_FECHA, COL_VALOR])

    df["gasto"] = df[COL_VALOR].where(df[COL_VALOR] < 0, 0).abs()
    df["ingreso"] = df[COL_VALOR].where(df[COL_VALOR] > 0, 0)

    return df.sort_values(COL_FECHA).reset_index(drop=True)


def unique_sorted(df: pd.DataFrame, col: str):
    if df is None or col not in df.columns:
        return []
    return sorted({str(v).strip() for v in df[col].dropna() if str(v).strip() != ""})


def spend_by_category(df: pd.DataFrame):
    gastos = df[df[COL_VALOR] < 0].copy()
    gastos["gasto_abs"] = gastos[COL_VALOR].abs()
    return (
        gastos.groupby(COL_CATEGORIA)["gasto_abs"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )


def top_detalle(df: pd.DataFrame, n: int = 10):
    gastos = df[df[COL_VALOR] < 0].copy()
    gastos["gasto_abs"] = gastos[COL_VALOR].abs()
    return gastos.nlargest(n, "gasto_abs")[[COL_FECHA, COL_CATEGORIA, COL_DETALLE, "gasto_abs"]]
