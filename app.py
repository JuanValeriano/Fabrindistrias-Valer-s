import streamlit as st
import database
import pandas as pd
import miner

st.set_page_config(page_title="Minería de Procesos - Valer's", layout="wide", initial_sidebar_state="expanded")

database.inicializar_tablas_sistema()

if "logeado" not in st.session_state:
    st.session_state.logeado = False
    st.session_state.rol = None
    st.session_state.usuario_actual = None

# ==========================================
# PANTALLA DE LOGIN
# ==========================================
if not st.session_state.logeado:
    st.title("🔐 Acceso al Sistema Valer's")
    st.markdown("Por favor, ingresa tus credenciales para acceder al análisis de procesos.")
    
    with st.form("Formulario de Login"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        btn = st.form_submit_button("Entrar")
        
        if btn:
            database.crear_usuario("admin", "valers2024", "admin")
            
            exito, rol = database.verificar_login(u, p)
            if exito:
                st.session_state.logeado = True
                st.session_state.rol = rol
                st.session_state.usuario_actual = u
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")
    st.stop()

# ==========================================
# BARRA LATERAL (SIDEBAR) UNIFICADA Y LIMPIA
# ==========================================
st.sidebar.write(f"👤 Usuario: **{st.session_state.usuario_actual}** | Rol: **{st.session_state.rol.capitalize()}**")
if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
    st.session_state.logeado = False
    st.rerun()

st.sidebar.divider()
st.sidebar.header("🧭 Menú Principal")

if st.session_state.rol == "admin":
    menu = ["📊 Nuevo Análisis", "📜 Historial de Análisis", "⚙️ Panel de Administrador"]
else:
    menu = ["📜 Historial de Análisis"]

opcion = st.sidebar.radio("Navegación", menu, label_visibility="collapsed")
st.sidebar.divider()

df_eventos = None
analisis_cargado = False

# ==========================================
# VISTAS SEGÚN LA OPCIÓN DEL MENÚ
# ==========================================

if opcion == "📊 Nuevo Análisis":
    st.title("📊 Nuevo Análisis de Procesos")
    st.markdown("Sube tu archivo de eventos (Event Log) para generar un nuevo modelo.")
    
    st.sidebar.subheader("📁 Carga de Datos")
    archivo_subido = st.sidebar.file_uploader("Sube tu archivo (CSV o Excel)", type=['xlsx', 'csv'])
    
    if archivo_subido is not None:
        if archivo_subido.name.endswith('.csv'):
            df_temp = pd.read_csv(archivo_subido)
        else:
            df_temp = pd.read_excel(archivo_subido)
            
        st.sidebar.info(f"Archivo detectado: {len(df_temp)} filas.")
        
        if st.sidebar.button("💾 Guardar en BD y Analizar", use_container_width=True):
            with st.spinner("Inyectando datos en PostgreSQL..."):
                id_ejec, nom_analisis = database.guardar_nuevo_analisis(df_temp, archivo_subido.name)
                st.sidebar.success(f"¡Guardado con éxito!")
                df_eventos = database.obtener_datos_analisis(id_ejec)
                analisis_cargado = True
    else:
        st.info("👋 Sube tu archivo CSV en el panel lateral para comenzar.")

elif opcion == "📜 Historial de Análisis":
    st.title("📜 Historial de Análisis")
    st.markdown("Consulta modelos de procesos generados anteriormente.")
    
    st.sidebar.subheader("📥 Cargar Histórico")
    historial = database.obtener_lista_analisis()
    
    if not historial.empty:
        opciones_hist = historial.set_index('ID_Ejecucion')['Nombre_Analisis'].to_dict()
        seleccion_id = st.sidebar.selectbox("Selecciona un análisis:", options=list(opciones_hist.keys()), format_func=lambda x: opciones_hist[x])
        
        if st.sidebar.button("Cargar Análisis", use_container_width=True):
            with st.spinner("Extrayendo registros..."):
                df_eventos = database.obtener_datos_analisis(seleccion_id)
                analisis_cargado = True
    else:
        st.warning("La base de datos de historial está vacía.")

elif opcion == "⚙️ Panel de Administrador":
    st.title("⚙️ Gestión del Sistema")
    st.markdown("Panel exclusivo para el Administrador.")
    
    tab_usuarios, tab_config = st.tabs(["👥 Gestión de Usuarios", "⏳ Configuración de Alertas (SLA)"])
    
    with tab_usuarios:
        col_crear, col_lista = st.columns([1, 1.5])
        
        with col_crear:
            st.subheader("Crear Nuevo Usuario")
            with st.form("form_nuevo_usuario"):
                nuevo_u = st.text_input("Nombre de Usuario")
                nuevo_p = st.text_input("Contraseña temporal", type="password")
                nuevo_r = st.selectbox("Rol", ["usuario", "admin"])
                if st.form_submit_button("Registrar"):
                    if nuevo_u and nuevo_p:
                        database.crear_usuario(nuevo_u, nuevo_p, nuevo_r)
                        st.success(f"Usuario '{nuevo_u}' creado.")
                        st.rerun()
                    else:
                        st.error("Rellena todos los campos.")
                        
        with col_lista:
            st.subheader("Usuarios Registrados")
            df_users = database.obtener_usuarios()
            
            encabezado1, encabezado2, encabezado3 = st.columns([2, 2, 1.5])
            encabezado1.markdown("**👤 Usuario**")
            encabezado2.markdown("**🔑 Rol**")
            encabezado3.markdown("**⚙️ Acción**")
            st.divider()
            
            for index, fila in df_users.iterrows():
                usuario_fila = fila['Usuario']
                rol_fila = fila['Rol']
                
                col1, col2, col3 = st.columns([2, 2, 1.5])
                
                col1.write(usuario_fila)
                col2.write(rol_fila)
                
                if usuario_fila != st.session_state.usuario_actual:
                    if col3.button("🗑️ Eliminar", key=f"btn_eliminar_{usuario_fila}", type="primary", use_container_width=True):
                        exito, msj = database.eliminar_usuario(usuario_fila)
                        if exito:
                            st.success(msj)
                            st.rerun()
                        else:
                            st.error(msj)
                else:
                    col3.markdown("🔒 *Tú (Protegido)*")
                
                st.markdown("<hr style='margin: 0.5em 0px; border-top: 1px solid #333;'>", unsafe_allow_html=True)

    with tab_config:
        st.subheader("Meta Global de Operación")
        st.markdown("Define el tiempo máximo aceptable que debe tardar un caso/lote de principio a fin.")
        meta_actual = database.obtener_meta_tiempo()
        nueva_meta = st.number_input("Meta Máxima de Ciclo (Horas):", value=float(meta_actual), step=1.0)
        if st.button("Guardar Configuración"):
            database.guardar_meta_tiempo(nueva_meta)
            st.success(f"Umbral de tiempo actualizado a {nueva_meta} horas.")

# ==========================================
# RENDERIZADO DEL DASHBOARD (Si hay datos cargados)
# ==========================================
if analisis_cargado and df_eventos is not None:
    st.divider()
    
    columnas_sistema = ['ID_Ejecucion', 'Nombre_Analisis', 'Fecha_Subida']
    df_vista = df_eventos.drop(columns=[col for col in columnas_sistema if col in df_eventos.columns])

    df_vista.columns = df_vista.columns.str.lower()

    if 'timestamp' in df_vista.columns: 
        df_vista['timestamp'] = pd.to_datetime(df_vista['timestamp'])
    elif 'fecha_hora' in df_vista.columns:
        df_vista['fecha_hora'] = pd.to_datetime(df_vista['fecha_hora'])

    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Total de Lotes Procesados", len(df_vista['id_caso'].unique()))
    col2.metric("🔄 Total de Eventos Registrados", len(df_vista))
    
    if 'costo_lote_soles' in df_vista.columns:
        col3.metric("💰 Costo Total", f"S/ {df_vista.drop_duplicates(subset=['id_caso'])['costo_lote_soles'].sum():,.2f}")
    else:
        col3.metric("💰 Costo Total", "S/ 0.00")

    st.divider()
    
    # ==========================================
    # CEREBRO ANALÍTICO: ALERTAS Y CUELLOS DE BOTELLA
    # ==========================================
    st.subheader("🧠 Interpretación Automática del Proceso")
    
    col_tiempo = 'timestamp' if 'timestamp' in df_vista.columns else 'fecha_hora'
    
    if col_tiempo in df_vista.columns and 'id_caso' in df_vista.columns:

        df_vista[col_tiempo] = pd.to_datetime(df_vista[col_tiempo])
        df_ordenado = df_vista.sort_values(by=['id_caso', col_tiempo])
        
        tiempos_ciclo = df_ordenado.groupby('id_caso')[col_tiempo].agg(Inicio='min', Fin='max')
        tiempos_ciclo['Duracion_Horas'] = (tiempos_ciclo['Fin'] - tiempos_ciclo['Inicio']).dt.total_seconds() / 3600
        
        meta_horas = database.obtener_meta_tiempo()
        
        lotes_retrasados = tiempos_ciclo[tiempos_ciclo['Duracion_Horas'] > meta_horas]
        total_lotes = len(tiempos_ciclo)
        num_retrasados = len(lotes_retrasados)
        
        if num_retrasados > 0:
            porcentaje_critico = round((num_retrasados / total_lotes) * 100, 1)
            promedio_retraso = round(lotes_retrasados['Duracion_Horas'].mean(), 1)
            
            st.error(f"🚨 **ALERTA DE DESEMPEÑO:** Se detectaron **{num_retrasados} lotes** que superaron la meta operativa de {meta_horas} horas.")
            
            st.markdown(f"""
            > **💡 Diagnóstico del Sistema:** El **{porcentaje_critico}%** de los procesos analizados rompen la meta de tiempo establecida. 
            El tiempo de ciclo promedio de estos lotes críticos es de **{promedio_retraso} horas**. 
            Te sugerimos observar el **Mapa de Procesos (Grafo)** en la pestaña inferior para identificar qué actividad específica está reteniendo el flujo.
            """)
        else:
            st.success(f"✅ **PROCESO SALUDABLE:** Todos los lotes procesados cumplen con la meta operativa de {meta_horas} horas. No se detectan cuellos de botella críticos a nivel general.")
    else:
        st.warning("No se pudo realizar la interpretación automática. Faltan las columnas de fecha o id_caso.")
        
    st.divider()

    # TABS DEL DASHBOARD
    tab1, tab2, tab3 = st.tabs(["🗺️ Mapa de Procesos Real", "📊 Análisis Estadístico", "📋 Datos Crudos"])

    with tab1:
        st.write("### Descubrimiento del Flujo Real")
        st.dataframe(df_vista.head(10), use_container_width=True)
        
        st.write("#### 🧠 Modelo Generado por IA (PM4Py)")
        with st.spinner('Construyendo grafo...'):
            try:
                ruta_imagen_grafo = miner.descubrir_proceso(df_eventos)
                st.success("¡Grafo generado exitosamente!")
                st.image(ruta_imagen_grafo, use_column_width=True)  # ← CAMBIO AQUÍ
            except Exception as e:
                st.error(f"Error al generar el grafo: {e}")
                st.info("Nota: Asegúrate de tener Graphviz instalado en el PATH de Windows.")

    with tab2:
        st.write("### Indicadores de Eficiencia Operativa")
        
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.write("**Frecuencia de Actividades**")
            if 'actividad' in df_vista.columns:
                df_act = df_vista['actividad'].value_counts().reset_index()
                df_act.columns = ['Actividad', 'Cantidad']
                st.bar_chart(df_act, x='Actividad', y='Cantidad', color="#1f77b4")
            
        with col_graf2:
            if 'empleado' in df_vista.columns:
                st.write("**Carga de Trabajo por Empleado**")
                df_emp = df_vista['empleado'].value_counts().reset_index()
                df_emp.columns = ['Empleado', 'Cantidad']
                st.bar_chart(df_emp, x='Empleado', y='Cantidad', color="#ff7f0e")

        st.divider()

        st.write("**📈 Volumen de Eventos en el Tiempo**")
        col_tiempo = 'timestamp' if 'timestamp' in df_vista.columns else 'fecha_hora'
        
        if col_tiempo in df_vista.columns:
            df_fechas = df_vista.copy()
            df_fechas[col_tiempo] = pd.to_datetime(df_fechas[col_tiempo])
            df_fechas['Solo_Fecha'] = df_fechas[col_tiempo].dt.date
            df_tiempos = df_fechas.groupby('Solo_Fecha').size().reset_index(name='Eventos')
            st.line_chart(df_tiempos, x='Solo_Fecha', y='Eventos', color="#2ca02c")
        else:
            st.warning("No se encontró una columna de tiempo para generar el histograma.")

    with tab3:
        st.write("### Base de Datos Completa")
        st.dataframe(df_vista, use_container_width=True)