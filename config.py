"""Central configuration for the Analizador Financiero app."""

# Google Sheets
SHEET_NAME = "cashflow2"

# Column names as they appear in the sheet (order matters for appending rows)
COL_FECHA = "fecha"
COL_CATEGORIA = "categoria"
COL_DETALLE = "detalle"
COL_VALOR = "valor"
COL_MEDIO = "medio"
COL_MES = "mes"
COL_DOW = "dow"
COL_ANO = "año"

SHEET_COLUMNS = [
    COL_FECHA, COL_CATEGORIA, COL_DETALLE, COL_VALOR,
    COL_MEDIO, COL_MES, COL_DOW, COL_ANO,
]

# Spanish month names, keyed by month number (1-12)
MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

# Fallback lists used only if the sheet has no data yet
DEFAULT_CATEGORIAS = [
    "mercado", "eatout", "transporte", "servicios",
    "credito", "ayudas", "ingreso", "otros",
]
DEFAULT_MEDIOS = ["bancolombia", "TC VISA", "efectivo"]

ADD_NEW_OPTION = "+ Otra / nueva..."

# Chart palette (consistent colors across the whole app)
CATEGORY_COLOR_SEQUENCE = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]

# AI assistant (DeepSeek, OpenAI-compatible API)
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
