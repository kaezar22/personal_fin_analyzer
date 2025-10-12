from dotenv import load_dotenv
import os
import streamlit as st
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

load_dotenv(override=True)
# Configuración de la página
st.set_page_config(
    page_title="🏦 Analizador Financiero IA",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para mejorar la apariencia
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Configuración en la barra lateral
st.sidebar.header("🔧 Configuración")

# API Key hardcoded (no mostrar en interfaz)
google_api_key = os.getenv("GOOGLE_API_KEY")

key_path = os.getenv("key_path")


spreadsheet_id = "185BYhloP_cxaikxb4lK4joFAC0SQCfea35l4Owb3tJs"


# Título principal
st.markdown('<h1 class="main-header">🏦 Analizador Financiero con IA</h1>', unsafe_allow_html=True)

# Funciones para cargar y procesar datos
def clean_column_names(df):
    """Limpiar nombres de columnas duplicadas y vacías"""
    columns = df.columns.tolist()
    new_columns = []
    seen = {}
    
    for col in columns:
        # Si la columna está vacía, asignar un nombre genérico
        if col == '' or col is None or str(col).strip() == '':
            col = 'columna_vacia'
        
        # Si ya existe esta columna, agregar un sufijo
        if col in seen:
            seen[col] += 1
            new_col = f"{col}_{seen[col]}"
        else:
            seen[col] = 0
            new_col = col
        
        new_columns.append(new_col)
    
    df.columns = new_columns
    return df

@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_google_sheets():
    """Load data from Google Sheets using Streamlit Secrets."""
    try:
        # Load credentials directly from Streamlit secrets
        creds_info = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
        creds = Credentials.from_service_account_info(
            creds_info,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets.readonly",
                "https://www.googleapis.com/auth/drive"
            ]
        )

        # Authorize gspread
        gc = gspread.authorize(creds)

        # Spreadsheet ID also stored in secrets
        spreadsheet_id = st.secrets["SPREADSHEET_ID"]
        sh = gc.open_by_key(spreadsheet_id)

        # Load "cashflow2" worksheet
        ws_detalle = sh.worksheet("cashflow2")
        values_detalle = ws_detalle.get_all_values()

        headers_detalle = values_detalle[0]
        data_detalle = values_detalle[1:]
        df_detalle = pd.DataFrame(data_detalle, columns=headers_detalle)

        # Optional: clean column names if you have that function
        if "clean_column_names" in globals():
            df_detalle = clean_column_names(df_detalle)

        return df_detalle, None

    except Exception as e:
        return None, str(e)
        
def dataframes_to_context(df_detalle, max_rows=120):
    """Convertir DataFrames a contexto para el modelo"""
    context = "=== DATOS DISPONIBLES ===\n\n"
    
    # Información sobre hoja "detalle"
    context += f"1. HOJA 'cashflow2':\n"
    context += f"   - {len(df_detalle)} filas y {len(df_detalle.columns)} columnas\n"
    context += f"   - Columnas: {', '.join(df_detalle.columns)}\n"
    context += f"   - Primeras filas:\n"
    context += df_detalle.head(max_rows).to_string(index=False)
    if len(df_detalle) > max_rows:
        context += f"\n   ... y {len(df_detalle) - max_rows} filas más.\n\n"
    else:
        context += "\n\n"
    
    # Información sobre hoja "Cashflow"
  #  context += f"2. HOJA 'CASHFLOW':\n"
  #  context += f"   - {len(df_cashflow)} filas y {len(df_cashflow.columns)} columnas\n"
  #  context += f"   - Columnas: {', '.join(df_cashflow.columns)}\n"
  #  context += f"   - Primeras filas:\n"
  #  context += df_cashflow.head(max_rows).to_string(index=False)
  #  if len(df_cashflow) > max_rows:
   #     context += f"\n   ... y {len(df_cashflow) - max_rows} filas más."
    
        return context

def ask_ai_about_data(api_key, df_detalle, question):
    """Enviar pregunta al modelo Gemini usando solo la hoja 'detalle'"""
    try:
        gemini = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )

        # Convertir DataFrame a texto
        data_context = dataframes_to_context(df_detalle)

        # Nuevo prompt sin referencias a Cashflow
        system_prompt = """Eres un asistente especializado en análisis de datos financieros personales.
Te proporcionaré datos de una hoja llamada 'cashflow2' que contiene mis transacciones, categorías y fechas.

Tu tarea es:
1. Analizar los datos de la hoja 'cashflow2' y responder preguntas sobre gastos, ingresos o patrones.
2. Si el usuario pide un gráfico, al final de tu respuesta incluye una sección con el formato:

---GRAFICO---
TIPO: [bar/line/pie/scatter]
TITULO: [título del gráfico]
DATOS: [descripción clara de qué filtrar y cómo agrupar]
X: [eje X]
Y: [eje Y]
---FIN_GRAFICO---

Responde en español, de forma clara y concisa. Si la información no está disponible, explícalo sin pedir otras hojas.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Aquí están los datos de la hoja 'cashflow2':\n\n{data_context}\n\nPregunta: {question}"}
        ]

        response = gemini.chat.completions.create(
            model="gemini-2.0-flash",
            messages=messages
        )

        answer = response.choices[0].message.content
        return answer, None

    except Exception as e:
        return None, str(e)


def create_chart_from_ai_response(response_text, df_detalle):
    """Crear gráfico basado en la respuesta de la IA"""
    try:
        if "---GRAFICO---" not in response_text:
            return None
        
        # Extraer información del gráfico
        start = response_text.find("---GRAFICO---")
        end = response_text.find("---FIN_GRAFICO---")
        
        if start == -1 or end == -1:
            return None
        
        chart_info = response_text[start:end+len("---FIN_GRAFICO---")]
        
        # Parsear información del gráfico
        chart_data = {}
        for line in chart_info.split('\n'):
            if ':' in line and any(key in line.upper() for key in ['TIPO', 'TITULO', 'DATOS', 'X:', 'Y:']):
                key, value = line.split(':', 1)
                chart_data[key.strip().upper()] = value.strip()
        
        if not chart_data:
            return None
        
        # Determinar qué hoja usar y cómo procesar los datos
        datos_desc = chart_data.get('DATOS', '').lower()
        
        # Seleccionar DataFrame
        if 'cashflow2' in datos_desc:
            df = df_detalle.copy()
            sheet_name = 'cashflow2'
       # elif 'cashflow' in datos_desc:
       #     df = df_cashflow.copy()
       #     sheet_name = 'cashflow'
        else:
            df = df_detalle.copy()  # Default
            sheet_name = 'cashflow2'
        
        # Intentar crear diferentes tipos de gráficos basados en palabras clave
        fig = None
        chart_type = chart_data.get('TIPO', 'bar').lower()
        title = chart_data.get('TITULO', 'Gráfico Financiero')
        
        # Buscar columnas relevantes (esto es básico, se puede mejorar)
        numeric_cols = []
        date_cols = []
        text_cols = []
        
        for col in df.columns:
            sample_values = df[col].dropna().astype(str).str.strip()
            sample_values = sample_values[sample_values != '']
            
            if len(sample_values) > 0:
                # Intentar detectar números
                try:
                    pd.to_numeric(sample_values.iloc[:5], errors='raise')
                    numeric_cols.append(col)
                    continue
                except:
                    pass
                
                # Intentar detectar fechas
                try:
                    pd.to_datetime(sample_values.iloc[:5], errors='raise')
                    date_cols.append(col)
                    continue
                except:
                    pass
                
                text_cols.append(col)
        
        # Crear gráfico simple basado en lo disponible
        if 'transporte' in datos_desc.lower() and len(numeric_cols) > 0:
            # Filtrar por taxi si es posible
            taxi_mask = df.astype(str).apply(lambda x: x.str.lower().str.contains('transporte', na=False)).any(axis=1)
            if taxi_mask.any():
                df_filtered = df[taxi_mask]
                if len(df_filtered) > 0 and len(numeric_cols) > 0:
                    # Convertir primera columna numérica
                    df_filtered[numeric_cols[0]] = pd.to_numeric(df_filtered[numeric_cols[0]], errors='coerce')
                    df_filtered = df_filtered.dropna(subset=[numeric_cols[0]])
                    
                    if len(df_filtered) > 0:
                        if chart_type == 'pie':
                            fig = px.pie(
                                values=df_filtered[numeric_cols[0]].head(10), 
                                names=range(len(df_filtered.head(10))),
                                title=title
                            )
                        else:
                            fig = px.bar(
                                df_filtered.head(10), 
                                y=numeric_cols[0],
                                title=title
                            )
        
        elif len(numeric_cols) > 0:
            # Gráfico general con datos numéricos
            df_chart = df.head(20).copy()
            
            # Limpiar y convertir datos numéricos
            for col in numeric_cols[:2]:  # Máximo 2 columnas numéricas
                df_chart[col] = pd.to_numeric(df_chart[col], errors='coerce')
            
            df_chart = df_chart.dropna(subset=numeric_cols[:1])
            
            if len(df_chart) > 0:
                if chart_type == 'pie' and len(numeric_cols) >= 1:
                    fig = px.pie(
                        values=df_chart[numeric_cols[0]], 
                        names=df_chart.index,
                        title=title
                    )
                elif chart_type == 'line' and len(numeric_cols) >= 1:
                    fig = px.line(
                        df_chart, 
                        y=numeric_cols[0],
                        title=title
                    )
                else:
                    # Bar chart por defecto
                    fig = px.bar(
                        df_chart, 
                        y=numeric_cols[0],
                        title=title
                    )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creando gráfico: {str(e)}")
        return None

# Inicializar el estado de la sesión
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# Botón para cargar datos
if st.sidebar.button("🔄 Cargar/Actualizar Datos", type="primary"):
    with st.spinner("Cargando datos de Google Sheets..."):
        df_detalle, error = load_google_sheets()
        
        if error:
            st.error(f"❌ Error al cargar datos: {error}")
            st.session_state.data_loaded = False
        else:
            st.session_state.df_detalle = df_detalle
            # st.session_state.df_cashflow = df_cashflow
            st.session_state.data_loaded = True
            st.success("✅ Datos cargados exitosamente!")

# Mostrar información de los datos si están cargados
if st.session_state.data_loaded:
    st.sidebar.success("✅ Datos cargados")
    
    # Mostrar métricas básicas
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("cashflow2", f"{len(st.session_state.df_detalle)} filas")
    # with col2:
    #    st.metric("Cashflow", f"{len(st.session_state.df_cashflow)} filas")
    
    # Mostrar vista previa de datos
    with st.expander("📊 Vista previa de datos"):
        tab1, tab2 = st.tabs(["📝 Cashflow2", "💰 Cashflow"])
        
        with tab1:
            st.subheader("Hoja 'Cashflow2'")
            st.write(f"**Columnas disponibles:** {len(st.session_state.df_detalle.columns)}")
            
            # Mostrar primeras columnas que no estén vacías
            df_preview = st.session_state.df_detalle.head(10)
            
            # Filtrar columnas que no sean completamente vacías
            non_empty_cols = []
            for col in df_preview.columns:
                if not df_preview[col].astype(str).str.strip().eq('').all():
                    non_empty_cols.append(col)
            
            if non_empty_cols:
                st.dataframe(df_preview[non_empty_cols[:10]])  # Mostrar máximo 10 columnas
            else:
                st.warning("No se encontraron columnas con datos válidos")
            
#        with tab2:
#            st.subheader("Hoja 'Cashflow'")
#            st.write(f"**Columnas disponibles:** {len(st.session_state.df_cashflow.columns)}")
            
            # Mostrar primeras columnas que no estén vacías
 #           df_preview = st.session_state.df_cashflow.head(10)
            
            # Filtrar columnas que no sean completamente vacías
#            non_empty_cols = []
#            for col in df_preview.columns:
#                if not df_preview[col].astype(str).str.strip().eq('').all():
#                    non_empty_cols.append(col)
            
#            if non_empty_cols:
#                st.dataframe(df_preview[non_empty_cols[:10]])  # Mostrar máximo 10 columnas
#            else:
#                st.warning("No se encontraron columnas con datos válidos")

# Preguntas predefinidas
if st.session_state.data_loaded:
    st.sidebar.markdown("### 💡 Preguntas sugeridas")
    preguntas_sugeridas = [
        "¿Cuánto gasté en transporte en Octubre?"
    ]
    
    for pregunta in preguntas_sugeridas:
        if st.sidebar.button(f"💬 {pregunta}", key=f"btn_{pregunta}"):
            st.session_state.messages.append({"role": "user", "content": pregunta})

# Interfaz de chat principal
if st.session_state.data_loaded:
    st.subheader("💬 Chat con tu Asistente Financiero")
    
    # Mostrar historial de mensajes
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                # Separar texto y gráfico si existe
                response_content = message["content"]
                if "---GRAFICO---" in response_content:
                    text_response = response_content.split("---GRAFICO---")[0].strip()
                    st.markdown(text_response)
                    
                    # Mostrar el gráfico si está en el historial
                    fig = create_chart_from_ai_response(
                        response_content, 
                        st.session_state.df_detalle
#                        st.session_state.df_cashflow
                    )
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.markdown(response_content)
    
    # Input de chat
    if prompt := st.chat_input("Haz una pregunta sobre tus datos financieros..."):
        # Añadir mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generar respuesta
        with st.chat_message("assistant"):
            with st.spinner("Analizando tus datos..."):
                response, error = ask_ai_about_data(
                    google_api_key,
                    st.session_state.df_detalle,
                    prompt
                )
                
                if error:
                    st.error(f"❌ Error al procesar la pregunta: {error}")
                else:
                    # Mostrar la respuesta de texto
                    # Separar la respuesta del gráfico si existe
                    if "---GRAFICO---" in response:
                        text_response = response.split("---GRAFICO---")[0].strip()
                        st.markdown(text_response)
                        
                        # Intentar crear el gráfico
                        with st.spinner("Generando gráfico..."):
                            fig = create_chart_from_ai_response(
                                response, 
                                st.session_state.df_detalle
                               # st.session_state.df_cashflow
                            )
                            
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                                st.success("📊 ¡Gráfico generado exitosamente!")
                            else:
                                st.warning("⚠️ No pude generar el gráfico, pero aquí tienes el análisis de texto.")
                    else:
                        st.markdown(response)
                    
                    st.session_state.messages.append({"role": "assistant", "content": response})

else:
    # Mensaje de bienvenida si no hay datos cargados
    st.info("👆 Configura tus credenciales en la barra lateral y haz clic en 'Cargar Datos' para comenzar.")
    
    st.markdown("""
    ## 🚀 Cómo usar esta aplicación:
    
    1. **Configura las credenciales** en la barra lateral:
       - Ruta del archivo JSON de Google Service Account
       - ID de tu Google Spreadsheet
    
    2. **Carga los datos** haciendo clic en el botón "Cargar Datos"
    
    3. **Haz preguntas** sobre tus finanzas usando lenguaje natural
    
    ## 📊 Funcionalidades:
    
    - ✅ Análisis automático de dos hojas: 'detalle' y 'Cashflow'
    - ✅ Chat inteligente con IA para hacer preguntas
    - ✅ Preguntas sugeridas para empezar rápidamente
    - ✅ Vista previa de los datos cargados
    - ✅ Actualizaciones en tiempo real
    
    ## 💡 Ejemplos de preguntas:
    
    **Preguntas de análisis:**
    - "¿Cuánto gasté en restaurantes este mes?"
    - "¿Cómo está mi flujo de efectivo comparado con el mes pasado?"
    - "¿Cuáles son mis categorías de gasto más grandes?"
    - "¿Hay algún patrón en mis gastos que debería revisar?"
    
    **Preguntas con gráficos:**
    - "Muéstrame mis gastos en taxis en un gráfico"
    - "Crea una gráfica de mis categorías de gastos"
    - "Visualiza mis gastos más grandes en una gráfica"
    - "Haz un gráfico de barras de mis gastos mensuales"
    - "Muestra mi evolución de ingresos en un gráfico de líneas"
    """)

# Botón para limpiar historial de chat
if st.session_state.data_loaded and st.session_state.messages:
    if st.sidebar.button("🗑️ Limpiar Chat"):
        st.session_state.messages = []
        st.rerun()

# Información adicional en el pie de página
st.sidebar.markdown("---")
st.sidebar.markdown("🤖 **Powered by DeepSeek**")
st.sidebar.markdown("📊 **Streamlit App**")
st.sidebar.caption("Actualiza automáticamente cada 5 minutos")



