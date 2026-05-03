import streamlit as st
import pandas as pd
import database
import miner
import os
# Ajusta esta ruta a donde se instaló Graphviz en tu PC
os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin'

import pm4py
# ... el resto de tu código de minería de procesos
st.set_page_config(page_title="Minería de Procesos - Valer's", layout="wide")
st.title("🏭 Fabrindustrias Valer's - Análisis de Inventario")
st.markdown("Sistema de Minería de Procesos con trazabilidad histórica en PostgreSQL.")
st.divider()

# ==========================================
# PANEL LATERAL: MODO DE OPERACIÓN
# ==========================================
st.sidebar.header("⚙️ Modo de Operación")
modo = st.sidebar.radio(
    "¿Qué deseas hacer?", 
    ["🆕 Nuevo Análisis (Subir CSV/Excel)", "📜 Ver Historial de Análisis"]
)

st.sidebar.divider()

# Variables de estado
df_eventos = None
analisis_cargado = False

# --- MODO 1: NUEVO ANÁLISIS ---
if modo == "🆕 Nuevo Análisis (Subir CSV/Excel)":
    st.sidebar.subheader("📁 Carga de Datos")
    archivo_subido = st.sidebar.file_uploader("Sube tu archivo para analizar y guardar", type=['xlsx', 'csv'])
    
    if archivo_subido is not None:
        # 1. Leer archivo
        if archivo_subido.name.endswith('.csv'):
            df_temp = pd.read_csv(archivo_subido)
        else:
            df_temp = pd.read_excel(archivo_subido)
            
        st.sidebar.info(f"Archivo detectado: {len(df_temp)} filas. Listo para guardar.")
        
        # 2. Botón de Guardar en BD
        if st.sidebar.button("💾 Guardar en PostgreSQL y Analizar", use_container_width=True):
            with st.spinner("Inyectando datos en la Base de Datos..."):
                id_ejec, nom_analisis = database.guardar_nuevo_analisis(df_temp, archivo_subido.name)
                st.sidebar.success(f"¡Guardado con éxito!\nID: {id_ejec}")
                
                # 3. Extraemos de la BD para asegurar que estamos leyendo lo guardado
                df_eventos = database.obtener_datos_analisis(id_ejec)
                analisis_cargado = True

# --- MODO 2: HISTORIAL ---
else:
    st.sidebar.subheader("📜 Análisis Anteriores")
    historial = database.obtener_lista_analisis()
    
    if not historial.empty:
        # Creamos un diccionario para el selector (Muestra el nombre, pero usa el ID)
        opciones = historial.set_index('ID_Ejecucion')['Nombre_Analisis'].to_dict()
        
        seleccion_id = st.sidebar.selectbox(
            "Selecciona un análisis histórico:", 
            options=list(opciones.keys()), 
            format_func=lambda x: opciones[x]
        )
        
        if st.sidebar.button("📥 Cargar Análisis desde BD", use_container_width=True):
            with st.spinner("Extrayendo registros históricos..."):
                df_eventos = database.obtener_datos_analisis(seleccion_id)
                analisis_cargado = True
                st.sidebar.success("¡Datos históricos cargados!")
    else:
        st.sidebar.warning("La base de datos está vacía. Ve a 'Nuevo Análisis' para subir tu primer archivo.")


# ==========================================
# DASHBOARD PRINCIPAL (Solo se muestra si hay datos cargados)
# ==========================================
if analisis_cargado and df_eventos is not None:
    
    # Asegurarnos del formato de fecha (PM4Py lo exige)
    if 'Timestamp' in df_eventos.columns:
        df_eventos['Timestamp'] = pd.to_datetime(df_eventos['Timestamp'])

    # Filtros visuales (Quitamos las columnas de sistema para la vista)
    columnas_sistema = ['ID_Ejecucion', 'Nombre_Analisis', 'Fecha_Subida']
    df_vista = df_eventos.drop(columns=[col for col in columnas_sistema if col in df_eventos.columns])

    # KPIs PRINCIPALES
    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Total de Lotes (Casos)", len(df_vista['ID_Caso'].unique()))
    col2.metric("🔄 Total de Eventos Registrados", len(df_vista))
    if 'Costo_Lote_Soles' in df_vista.columns:
        col3.metric("💰 Costo Aprox. Inventario", f"S/ {df_vista.drop_duplicates(subset=['ID_Caso'])['Costo_Lote_Soles'].sum():,.2f}")

    st.divider()

    # PESTAÑAS DEL DASHBOARD (TABS)
    tab1, tab2, tab3 = st.tabs(["🗺️ Mapa de Procesos (PM4Py)", "📊 Análisis Estadístico", "📋 Datos Crudos"])

    with tab1:
        st.write("### Descubrimiento del Flujo Real")
        st.write("Vista previa de los datos a analizar:")
        st.dataframe(df_vista.head(10), use_container_width=True)
        
        st.divider()
        st.write("#### 🧠 Modelo Generado por IA")
        # ¡ELIMINAMOS EL BOTÓN! Ahora el grafo se genera de forma automática y directa.
        with st.spinner('Construyendo modelo de IA y detectando cuellos de botella...'):
            try:
                # Le pasamos a miner.py los datos exactos que requiere
                ruta_imagen_grafo = miner.descubrir_proceso(df_eventos)
                st.success("¡Grafo generado exitosamente!")
                st.image(ruta_imagen_grafo, use_column_width=True)
            except Exception as e:
                st.error(f"Error en PM4Py al generar el grafo: {e}")

    with tab2:
        st.write("### Indicadores de Eficiencia Operativa")
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.write("**Frecuencia de Actividades**")
            # Método seguro para gráficos de barras
            df_act = df_vista['Actividad'].value_counts().reset_index()
            df_act.columns = ['Actividad', 'Cantidad']
            st.bar_chart(df_act, x='Actividad', y='Cantidad', color="#1f77b4")
            
        with col_graf2:
            if 'Empleado' in df_vista.columns:
                st.write("**Carga de Trabajo por Empleado**")
                df_emp = df_vista['Empleado'].value_counts().reset_index()
                df_emp.columns = ['Empleado', 'Cantidad']
                st.bar_chart(df_emp, x='Empleado', y='Cantidad', color="#ff7f0e")

        st.divider()
        st.write("**Volumen de Eventos en el Tiempo (Histograma de Carga)**")
        # Método a prueba de balas para el gráfico de líneas (Histograma temporal)
        df_fechas = df_vista.copy()
        # Extraemos solo la fecha (sin la hora) para agrupar correctamente
        df_fechas['Fecha_Corta'] = df_fechas['Timestamp'].dt.date 
        df_tiempo = df_fechas.groupby('Fecha_Corta').size().reset_index(name='Cantidad de Eventos')
        
        st.line_chart(df_tiempo, x='Fecha_Corta', y='Cantidad de Eventos', color="#2ca02c")

    with tab3:
        st.write("### Base de Datos Extraída de PostgreSQL")
        st.dataframe(df_eventos, use_container_width=True)

elif not analisis_cargado and modo == "🆕 Nuevo Análisis (Subir CSV/Excel)":
    st.info("👋 Sube tu archivo CSV en el panel lateral y presiona 'Guardar en BD y Analizar'.")