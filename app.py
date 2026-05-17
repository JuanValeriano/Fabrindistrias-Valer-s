import streamlit as st
import database
import pandas as pd
import miner
import google.generativeai as genai
import os

if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                clave, valor = line.split("=", 1)
                os.environ[clave.strip()] = valor.strip().strip('"').strip("'")

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
    menu = ["📊 Nuevo Análisis", "📜 Historial de Análisis", "⚙️ Panel de Administrador", "👤 Mi Perfil"]
else:
    menu = ["📜 Historial de Análisis", "👤 Mi Perfil"]

opcion = st.sidebar.radio("Navegación", menu, label_visibility="collapsed")

if 'opcion_anterior' not in st.session_state:
    st.session_state.opcion_anterior = opcion
if st.session_state.opcion_anterior != opcion:
    st.session_state.df_eventos = None
    st.session_state.analisis_cargado = False
    st.session_state.opcion_anterior = opcion
    if 'filtros_aplicados' in st.session_state:
        del st.session_state.filtros_aplicados

st.sidebar.divider()

if 'df_eventos' not in st.session_state:
    st.session_state.df_eventos = None
if 'analisis_cargado' not in st.session_state:
    st.session_state.analisis_cargado = False

df_eventos = st.session_state.df_eventos
analisis_cargado = st.session_state.analisis_cargado

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
                st.session_state.df_eventos = database.obtener_datos_analisis(id_ejec)
                st.session_state.analisis_cargado = True
                df_eventos = st.session_state.df_eventos
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
                st.session_state.df_eventos = database.obtener_datos_analisis(seleccion_id)
                st.session_state.analisis_cargado = True
                df_eventos = st.session_state.df_eventos
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


elif opcion == "👤 Mi Perfil":
    st.title("👤 Mi Perfil de Usuario")
    st.write(f"**Usuario Logeado:** {st.session_state.usuario_actual}")
    st.write(f"**Nivel de Acceso:** {st.session_state.rol.capitalize()}")
    st.divider()
    
    st.subheader("🔑 Cambiar Contraseña")
    st.markdown("Por seguridad, necesitas ingresar tu contraseña actual para establecer una nueva.")
    
    with st.form("form_cambiar_pass"):
        pass_actual = st.text_input("Contraseña Actual", type="password")
        pass_nueva = st.text_input("Nueva Contraseña", type="password")
        pass_confirmar = st.text_input("Confirmar Nueva Contraseña", type="password")
        
        if st.form_submit_button("Actualizar Contraseña", type="primary"):
            if not pass_actual or not pass_nueva or not pass_confirmar:
                st.error("Por favor, rellena todos los campos.")
            elif pass_nueva != pass_confirmar:
                st.error("Las contraseñas nuevas no coinciden. Inténtalo de nuevo.")
            else:
                exito, msj = database.cambiar_contrasena(st.session_state.usuario_actual, pass_actual, pass_nueva)
                if exito:
                    st.success(msj)
                else:
                    st.error(msj)

# ==========================================
# RENDERIZADO DEL DASHBOARD (Si hay datos cargados)
# ==========================================
if analisis_cargado and df_eventos is not None:
    st.divider()
        
    df_vista = df_eventos.copy()
        
    columnas_sistema = ['ID_Ejecucion', 'Nombre_Analisis', 'Fecha_Subida']
    df_vista = df_vista.drop(columns=[col for col in columnas_sistema if col in df_vista.columns])

    df_vista.columns = df_vista.columns.str.lower()
        
    col_tiempo = 'timestamp' if 'timestamp' in df_vista.columns else 'fecha_hora'
    if col_tiempo in df_vista.columns: 
        df_vista[col_tiempo] = pd.to_datetime(df_vista[col_tiempo])
        fecha_min = df_vista[col_tiempo].min().date()
        fecha_max = df_vista[col_tiempo].max().date()
    else:
        import datetime
        fecha_min = datetime.date(2000, 1, 1)
        fecha_max = datetime.date.today()

    lista_empleados = df_vista['empleado'].dropna().unique().tolist() if 'empleado' in df_vista.columns else []

    if 'filtros_aplicados' not in st.session_state:
        st.session_state.f_inicio_val = fecha_min
        st.session_state.f_fin_val = fecha_max
        st.session_state.emps_val = lista_empleados
        st.session_state.filtros_aplicados = True

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Filtros de Búsqueda")
        
    st.sidebar.markdown("**📅 Rango de Fechas**")
    col1, col2, col3, col4 = st.sidebar.columns([1, 4, 1, 4])
    with col1: st.markdown("<p style='margin-top:8px; font-size:14px;'>de</p>", unsafe_allow_html=True)
    with col2: f_inicio = st.date_input("inicio", value=fecha_min, min_value=fecha_min, max_value=fecha_max, label_visibility="collapsed")
    with col3: st.markdown("<p style='margin-top:8px; font-size:14px; text-align:center;'>a</p>", unsafe_allow_html=True)
    with col4: f_fin = st.date_input("fin", value=fecha_max, min_value=fecha_min, max_value=fecha_max, label_visibility="collapsed")
        
    st.sidebar.divider()
        
    st.sidebar.markdown("**👤 Tamaño de la pantalla / Empleado**")
    buscador = st.sidebar.text_input("Buscar...", placeholder="Buscar...", label_visibility="collapsed")
        
    emps_seleccionados_ui = []
    with st.sidebar.container(height=250):
        for emp in lista_empleados:
            if buscador.lower() in str(emp).lower():
                is_checked = emp in st.session_state.emps_val
                if st.checkbox(str(emp), value=is_checked, key=f"chk_{emp}"):
                    emps_seleccionados_ui.append(emp)
                        
    st.sidebar.divider()
        
    if st.sidebar.button("Aplicar Filtros 🚀", type="primary", use_container_width=True):

        st.session_state.f_inicio_val = f_inicio
        st.session_state.f_fin_val = f_fin
        st.session_state.emps_val = emps_seleccionados_ui


    mask_fechas = (df_vista[col_tiempo].dt.date >= st.session_state.f_inicio_val) & (df_vista[col_tiempo].dt.date <= st.session_state.f_fin_val)
    df_vista = df_vista.loc[mask_fechas]
        
    if 'empleado' in df_vista.columns:
        df_vista = df_vista[df_vista['empleado'].isin(st.session_state.emps_val)]

    df_eventos_filtrado = df_eventos.copy()
    col_tiempo_orig = 'Timestamp' if 'Timestamp' in df_eventos_filtrado.columns else 'fecha_hora'
    if col_tiempo_orig in df_eventos_filtrado.columns:
        df_eventos_filtrado[col_tiempo_orig] = pd.to_datetime(df_eventos_filtrado[col_tiempo_orig])
        mask_ev = (df_eventos_filtrado[col_tiempo_orig].dt.date >= st.session_state.f_inicio_val) & (df_eventos_filtrado[col_tiempo_orig].dt.date <= st.session_state.f_fin_val)
        df_eventos_filtrado = df_eventos_filtrado.loc[mask_ev]
            
    col_emp_orig = 'Empleado' if 'Empleado' in df_eventos_filtrado.columns else 'empleado'
    if col_emp_orig in df_eventos_filtrado.columns:
        df_eventos_filtrado = df_eventos_filtrado[df_eventos_filtrado[col_emp_orig].isin(st.session_state.emps_val)]

    if df_vista.empty:
        st.warning("⚠️ No hay datos para mostrar con los filtros aplicados. Intenta cambiar las fechas o marcar más personas.")
        st.stop()

    col1, col2, col3 = st.columns(3)
    if 'id_caso' in df_vista.columns:
        col1.metric("📦 Total de Lotes Procesados", len(df_vista['id_caso'].unique()))
    else:
        col1.metric("📦 Total de Lotes Procesados", 0)
        
    col2.metric("🔄 Total de Eventos Registrados", len(df_vista))
    
    if 'costo_lote_soles' in df_vista.columns and 'id_caso' in df_vista.columns:
        col3.metric("💰 Costo Total", f"S/ {df_vista.drop_duplicates(subset=['id_caso'])['costo_lote_soles'].sum():,.2f}")
    else:
        col3.metric("💰 Costo Total", "S/ 0.00")

    st.divider()
    
    # ==========================================
    # CEREBRO ANALÍTICO:
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
        
        porcentaje_critico = 0.0
        promedio_retraso = 0.0
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

        st.divider()
        st.subheader("🤖 Análisis Avanzado con Inteligencia Artificial (Gemini)")
        st.markdown("Obtén un resumen ejecutivo y recomendaciones basadas en los KPIs descubiertos.")
        
        if st.button("Generar Insights con Gemini 🧠", type="secondary"):
            api_key_env = os.environ.get("GEMINI_API_KEY")
            if not api_key_env:
                st.error("❌ Error: La API Key de Gemini no está configurada en las variables de entorno o en el archivo `.env`.")
            else:
                with st.spinner("Analizando la salud del proceso y buscando oportunidades de mejora..."):
                    try:
                        genai.configure(api_key=api_key_env)
                        model = genai.GenerativeModel('gemini-3-flash-preview')
                        
                        contexto_negocio = ""
                        if 'actividad' in df_vista.columns:
                            top_acts = df_vista['actividad'].value_counts().head(3).index.tolist()
                            contexto_negocio += f"- Actividades más frecuentes en el flujo: {', '.join(map(str, top_acts))}\n"
                        if 'empleado' in df_vista.columns:
                            top_emps = df_vista['empleado'].value_counts().head(3).index.tolist()
                            contexto_negocio += f"- Operarios con mayor volumen de transacciones: {', '.join(map(str, top_emps))}\n"
                        if 'proveedor' in df_vista.columns:
                            top_provs = df_vista['proveedor'].value_counts().head(3).index.tolist()
                            contexto_negocio += f"- Principales proveedores de los materiales: {', '.join(map(str, top_provs))}\n"
                        if 'sku_descripcion' in df_vista.columns:
                            top_skus = df_vista['sku_descripcion'].value_counts().head(3).index.tolist()
                            contexto_negocio += f"- Materiales/SKU más procesados: {', '.join(map(str, top_skus))}\n"
                        if 'estado_calidad' in df_vista.columns:
                            dist_qa = df_vista['estado_calidad'].value_counts(normalize=True).mul(100).round(1).to_dict()
                            qa_str = ", ".join([f"{k}: {v}%" for k, v in dist_qa.items()])
                            contexto_negocio += f"- Distribución de estados de calidad en QA: {qa_str}\n"

                        prompt = f"""
                        Eres un experto consultor estratégico en Minería de Procesos (Process Mining) y mejora continua (Lean/Six Sigma, Kaizen). 
                        A continuación te presento los KPIs operativos reales y el contexto transaccional del proceso de inventario y distribución de mi empresa:
                        
                        **Métricas de Rendimiento y SLAs:**
                        - Total de Lotes Procesados analizados: {total_lotes}
                        - Meta Operativa de Ciclo por Lote (SLA máximo tolerado): {meta_horas} horas
                        - Lotes Retrasados que rompieron el SLA: {num_retrasados}
                        - Porcentaje de lotes en estado crítico: {porcentaje_critico}%
                        - Tiempo de ciclo promedio de los lotes retrasados: {promedio_retraso} horas
                        
                        **Contexto Transaccional del Proceso:**
                        {contexto_negocio if contexto_negocio else '- No hay metadatos transaccionales adicionales.'}
                        
                        En base a estos datos y contexto, por favor elabora un reporte de auditoría operacional:
                        1. Una **interpretación ejecutiva** clara y profesional de la salud actual del proceso.
                        2. Tres **hipótesis de negocio concretas** sobre qué podría estar causando la variabilidad o cuellos de botella (ej. relacionando los operarios con mayor carga, el tipo de material, el estado de calidad de los proveedores o retrasos en la actividad de registro o ubicación).
                        3. **Recomendaciones estratégicas** accionables y priorizadas de mejora continua para acelerar el ciclo.
                        
                        Escribe el reporte en un tono profesional, analítico y corporativo. Usa listas y negritas para facilitar la lectura. No uses más de 300 palabras.
                        """
                        response = model.generate_content(prompt)
                        st.info(response.text)
                    except Exception as e:
                        st.error(f"Error al conectar con la API de Gemini. Revisa que tu clave sea correcta. Detalles: {e}")

    else:
        st.warning("No se pudo realizar la interpretación automática. Faltan las columnas de fecha o id_caso.")
        
    st.divider()

    tab1, tab2, tab3 = st.tabs(["🗺️ Mapa de Procesos Real", "📊 Análisis Estadístico", "📋 Datos Crudos"])

    with tab1:
        st.write("### Descubrimiento del Flujo Real")
        st.dataframe(df_vista.head(10), use_container_width=True)
        
        st.write("#### 🧠 Modelo Generado por IA (PM4Py)")
        with st.spinner('Construyendo grafo...'):
            try:
                ruta_imagen_grafo = miner.descubrir_proceso(df_eventos_filtrado)
                st.success("¡Grafo generado exitosamente!")
                st.image(ruta_imagen_grafo, use_container_width=True)
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

        st.divider()
        st.subheader("🤖 Interpretación Inteligente de Gráficos (Gemini)")
        st.markdown("Genera un análisis explicativo detallado de los patrones estadísticos, la carga de trabajo de los operarios y el volumen temporal.")
        
        if st.button("Interpretar Tendencias Estadísticas con Gemini 🧠", key="btn_interpret_stats", type="primary", use_container_width=True):
            api_key_env = os.environ.get("GEMINI_API_KEY")
            if not api_key_env:
                st.error("❌ Error: La API Key de Gemini no está configurada en las variables de entorno o en el archivo `.env`.")
            else:
                with st.spinner("Analizando la distribución de actividades, carga y temporalidad..."):
                    try:
                        genai.configure(api_key=api_key_env)
                        model = genai.GenerativeModel('gemini-3-flash-preview')
                        
                        act_context = ""
                        if 'actividad' in df_vista.columns:
                            df_act_counts = df_vista['actividad'].value_counts()
                            act_context = "\n".join([f"- {act}: {count} veces" for act, count in df_act_counts.items()])
                        
                        emp_context = ""
                        if 'empleado' in df_vista.columns:
                            df_emp_counts = df_vista['empleado'].value_counts()
                            emp_context = "\n".join([f"- {emp}: {count} eventos" for emp, count in df_emp_counts.items()])
                        
                        temp_context = ""
                        if col_tiempo in df_vista.columns:
                            df_fechas = df_vista.copy()
                            df_fechas[col_tiempo] = pd.to_datetime(df_fechas[col_tiempo])
                            df_fechas['Solo_Fecha'] = df_fechas[col_tiempo].dt.date
                            df_tiempos_group = df_fechas.groupby('Solo_Fecha').size()
                            
                            total_dias = len(df_tiempos_group)
                            avg_eventos = round(df_tiempos_group.mean(), 1)
                            dia_pico = df_tiempos_group.idxmax()
                            max_eventos = df_tiempos_group.max()
                            
                            temp_context = f"""- Período analizado: {df_fechas['Solo_Fecha'].min()} a {df_fechas['Solo_Fecha'].max()} ({total_dias} días)
- Promedio de eventos por día: {avg_eventos}
- Día con mayor volumen de trabajo: {dia_pico} ({max_eventos} eventos)"""

                        prompt = f"""
                        Eres un analista de datos experto en optimización de operaciones y minería de procesos corporativa.
                        A continuación te presento los resultados de las métricas estadísticas, volumen temporal y distribución de cargas de trabajo de nuestra operación para que los interpretes con ojo clínico:
                        
                        **1. FRECUENCIA DE ACTIVIDADES (Flujo del Proceso):**
                        {act_context if act_context else '- Sin datos de actividades.'}
                        
                        **2. CARGA DE TRABAJO POR EMPLEADO (Recursos de Personal):**
                        {emp_context if emp_context else '- Sin datos de empleados.'}
                        
                        **3. VOLUMEN DE EVENTOS EN EL TIEMPO (Tendencia Temporal):**
                        {temp_context if temp_context else '- Sin datos de fechas.'}
                        
                        Por favor, redacta un informe ejecutivo de interpretación operacional que contenga:
                        1. **Análisis de Pareto / Cuellos de botella en Actividades:** Explica qué actividades absorben el mayor volumen operativo de la organización y si denotan ineficiencias o flujos estándar.
                        2. **Diagnóstico de Distribución de Recursos:** Evalúa si la distribución de carga de trabajo entre operarios es sana o si denota monopolización, dependencias críticas de una persona o cuellos de botella por sobrecarga de recursos.
                        3. **Análisis de Capacidad Temporal y Picos:** Interpreta los promedios y el día pico de trabajo para sugerir ajustes organizativos en períodos de alta demanda.
                        
                        Mantén un tono profesional, pragmático y de consultoría estratégica. Usa viñetas y negritas para mejorar la legibilidad. No superes las 300 palabras.
                        """
                        response = model.generate_content(prompt)
                        st.info(response.text)
                    except Exception as e:
                        st.error(f"Error al generar interpretación de gráficos. Detalles: {e}")

    with tab3:
        st.write("### Base de Datos Completa")
        st.dataframe(df_vista, use_container_width=True)