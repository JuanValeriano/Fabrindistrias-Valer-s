from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import os
import io
import google.generativeai as genai

from BACKEND import database_api
from BACKEND import miner_api
from BACKEND import report_generator

app = FastAPI(title="VALERS - Process Mining API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    database_api.inicializar_tablas_sistema()
    database_api.crear_usuario("admin", "valers2024", "admin")

class LoginRequest(BaseModel):
    usuario: str
    password: str

class ChangePasswordRequest(BaseModel):
    usuario: str
    pass_actual: str
    pass_nueva: str

class CreateUserRequest(BaseModel):
    usuario: str
    password: str
    rol: str

class SLAConfigRequest(BaseModel):
    meta_horas: float

class FilterRequest(BaseModel):
    f_inicio: Optional[str] = None
    f_fin: Optional[str] = None
    var_seleccionada: Optional[str] = "Todas"
    emps_seleccionados: Optional[List[str]] = None

class GeminiInsightsRequest(BaseModel):
    total_lotes: int
    meta_horas: float
    num_retrasados: int
    porcentaje_critico: float
    promedio_retraso: float
    contexto_negocio: str

class GeminiTrendsRequest(BaseModel):
    act_context: str
    emp_context: str
    temp_context: str

class ExportRequest(BaseModel):
    format: str
    filters: FilterRequest
    insights: Optional[str] = None


@app.post("/api/auth/login")
def login(req: LoginRequest):
    exito, rol = database_api.verificar_login(req.usuario, req.password)
    if exito:
        return {"success": True, "usuario": req.usuario, "rol": rol}
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

@app.post("/api/auth/change-password")
def change_password(req: ChangePasswordRequest):
    exito, mensaje = database_api.cambiar_contrasena(req.usuario, req.pass_actual, req.pass_nueva)
    if exito:
        return {"success": True, "message": mensaje}
    raise HTTPException(status_code=400, detail=mensaje)

@app.get("/api/users")
def get_users():
    return database_api.obtener_usuarios()

@app.post("/api/users")
def create_user(req: CreateUserRequest):
    if not req.usuario or not req.password or not req.rol:
        raise HTTPException(status_code=400, detail="Faltan datos obligatorios")
    database_api.crear_usuario(req.usuario, req.password, req.rol)
    return {"success": True, "message": f"Usuario '{req.usuario}' registrado."}

@app.delete("/api/users/{usuario}")
def delete_user(usuario: str):
    exito, mensaje = database_api.eliminar_usuario(usuario)
    if exito:
        return {"success": True, "message": mensaje}
    raise HTTPException(status_code=400, detail=mensaje)


@app.get("/api/config/meta")
def get_meta():
    meta = database_api.obtener_meta_tiempo()
    return {"meta_horas": meta}

@app.post("/api/config/meta")
def update_meta(req: SLAConfigRequest):
    database_api.guardar_meta_tiempo(req.meta_horas)
    return {"success": True, "message": f"Umbral de tiempo actualizado a {req.meta_horas} horas."}


@app.post("/api/analysis/upload")
async def upload_analysis(file: UploadFile = File(...)):
    filename = file.filename
    try:
        contents = await file.read()
        import io
        if filename.endswith('.csv'):
            try:
                df = pd.read_csv(io.BytesIO(contents), encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(contents), encoding='latin-1')
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Formato de archivo no soportado (solo CSV o Excel).")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer el archivo: {e}")
        
    try:
        id_ejec, nom_analisis = database_api.guardar_nuevo_analisis(df, filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al guardar los datos en la base de datos: {e}")
        
    return {"success": True, "id_ejecucion": id_ejec, "nombre_analisis": nom_analisis}


@app.get("/api/analysis/history")
def get_history():
    return database_api.obtener_lista_analisis()

@app.post("/api/analysis/query/{id_ejecucion}")
def query_analysis(id_ejecucion: str, filters: FilterRequest):
    df = database_api.obtener_datos_analisis(id_ejecucion)
    if df.empty:
        if id_ejecucion == "LIVE":
            today_str = pd.Timestamp.now().strftime("%Y-%m-%d")
            return {
                "empty": True,
                "metadata": {
                    "fecha_min": today_str,
                    "fecha_max": today_str,
                    "empleados": [],
                    "variantes": []
                }
            }
        raise HTTPException(status_code=404, detail="No se encontraron datos para la ejecución especificada.")
        
    df_temp_cols = df.copy()
    df_temp_cols.columns = df_temp_cols.columns.str.lower()
    lista_empleados = df_temp_cols['empleado'].dropna().unique().tolist() if 'empleado' in df_temp_cols.columns else []
    
    variant_counts, case_to_variant = miner_api.obtener_variantes(df)
    lista_variantes = []
    for _, r in variant_counts.iterrows():
        lista_variantes.append({
            "id": r['Variante_ID'],
            "actividades": list(r['Actividades']),
            "cantidad": int(r['Cantidad']),
            "porcentaje": round(float(r['Porcentaje']), 2)
        })
        
    col_tiempo_orig = 'Timestamp' if 'Timestamp' in df.columns else 'fecha_hora'
    df[col_tiempo_orig] = pd.to_datetime(df[col_tiempo_orig])
    fecha_min = df[col_tiempo_orig].min().strftime("%Y-%m-%d")
    fecha_max = df[col_tiempo_orig].max().strftime("%Y-%m-%d")
    
    df_filtrado = df.copy()
    df_filtrado['Variante_ID'] = df_filtrado['ID_Caso'].map(case_to_variant)
    
    if filters.var_seleccionada and filters.var_seleccionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Variante_ID'] == filters.var_seleccionada]
        
    if filters.f_inicio:
        inicio_dt = pd.to_datetime(filters.f_inicio).date()
        df_filtrado = df_filtrado[df_filtrado[col_tiempo_orig].dt.date >= inicio_dt]
        
    if filters.f_fin:
        fin_dt = pd.to_datetime(filters.f_fin).date()
        df_filtrado = df_filtrado[df_filtrado[col_tiempo_orig].dt.date <= fin_dt]
        
    col_emp_orig = 'Empleado' if 'Empleado' in df_filtrado.columns else 'empleado'
    if filters.emps_seleccionados is not None and col_emp_orig in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado[col_emp_orig].isin(filters.emps_seleccionados)]
        
    if df_filtrado.empty:
        return {
            "empty": True,
            "metadata": {
                "fecha_min": fecha_min,
                "fecha_max": fecha_max,
                "empleados": lista_empleados,
                "variantes": lista_variantes
            }
        }
        
    df_vista = df_filtrado.copy()
    columnas_sistema = ['ID_Ejecucion', 'Nombre_Analisis', 'Fecha_Subida', 'Variante_ID']
    df_vista = df_vista.drop(columns=[col for col in columnas_sistema if col in df_vista.columns])
    df_vista.columns = df_vista.columns.str.lower()
    
    total_lotes = len(df_vista['id_caso'].unique()) if 'id_caso' in df_vista.columns else 0
    total_eventos = len(df_vista)
    
    costo_total = 0.0
    if 'costo_lote_soles' in df_vista.columns and 'id_caso' in df_vista.columns:
        costo_total = float(df_vista.drop_duplicates(subset=['id_caso'])['costo_lote_soles'].sum())
        
    col_tiempo = 'timestamp' if 'timestamp' in df_vista.columns else 'fecha_hora'
    num_retrasados = 0
    porcentaje_critico = 0.0
    promedio_retraso = 0.0
    meta_horas = database_api.obtener_meta_tiempo()
    
    if col_tiempo in df_vista.columns and 'id_caso' in df_vista.columns:
        df_vista[col_tiempo] = pd.to_datetime(df_vista[col_tiempo])
        df_ordenado = df_vista.sort_values(by=['id_caso', col_tiempo])
        
        tiempos_ciclo = df_ordenado.groupby('id_caso')[col_tiempo].agg(Inicio='min', Fin='max')
        tiempos_ciclo['Duracion_Horas'] = (tiempos_ciclo['Fin'] - tiempos_ciclo['Inicio']).dt.total_seconds() / 3600
        
        lotes_retrasados = tiempos_ciclo[tiempos_ciclo['Duracion_Horas'] > meta_horas]
        total_lotes_ciclo = len(tiempos_ciclo)
        num_retrasados = len(lotes_retrasados)
        
        if num_retrasados > 0:
            porcentaje_critico = round((num_retrasados / total_lotes_ciclo) * 100, 1)
            promedio_retraso = round(lotes_retrasados['Duracion_Horas'].mean(), 1)
            
    ciclo_stats = {}
    slowest_cases = []
    histograma = {"categorias": [], "cantidades": []}
    sla_cumplimiento = 100.0
    
    case_durations = miner_api.calcular_tiempos_ciclo(df_filtrado)
    if not case_durations.empty:
        avg_dur = float(case_durations['Duracion_Horas'].mean())
        med_dur = float(case_durations['Duracion_Horas'].median())
        min_dur = float(case_durations['Duracion_Horas'].min())
        max_dur = float(case_durations['Duracion_Horas'].max())
        
        ciclo_stats = {
            "promedio": round(avg_dur, 2),
            "mediana": round(med_dur, 2),
            "minima": round(min_dur, 2),
            "maxima": round(max_dur, 2)
        }
        
        casos_retrasados = case_durations[case_durations['Duracion_Horas'] > meta_horas]
        sla_cumplimiento = float(((len(case_durations) - len(casos_retrasados)) / len(case_durations)) * 100)
        
        import numpy as np
        counts, bins = np.histogram(case_durations['Duracion_Horas'], bins=10)
        histograma = {
            "categorias": [f"{bins[i]:.1f}-{bins[i+1]:.1f}" for i in range(len(counts))],
            "cantidades": [int(c) for c in counts]
        }
        
        slow_cases_df = case_durations.sort_values(by='Duracion_Horas', ascending=False).head(10).copy()
        slow_cases_df['SLA_Status'] = slow_cases_df['Duracion_Horas'].apply(
            lambda x: f"{(x - meta_horas):.2f} hrs de retraso" if x > meta_horas else "Cumple SLA"
        )
        for _, r in slow_cases_df.iterrows():
            slowest_cases.append({
                "id_caso": str(r['ID_Caso']),
                "inicio": r['Inicio'].strftime('%d/%m/%Y %H:%M'),
                "fin": r['Fin'].strftime('%d/%m/%Y %H:%M'),
                "duracion": f"{r['Duracion_Horas']:.2f} hrs",
                "status": r['SLA_Status']
            })
            
    vars_filtradas, _ = miner_api.obtener_variantes(df_filtrado)
    lista_vars_filtradas = []
    for _, r in vars_filtradas.iterrows():
        lista_vars_filtradas.append({
            "id": r['Variante_ID'],
            "actividades": " ➡️ ".join(r['Actividades']),
            "casos": int(r['Cantidad']),
            "cobertura": round(float(r['Porcentaje']), 2)
        })
        
    matriz_traspaso_df = miner_api.calcular_matriz_traspaso(df_filtrado)
    matriz_traspaso = {}
    if not matriz_traspaso_df.empty:
        matriz_traspaso = {
            "index": list(matriz_traspaso_df.index),
            "columns": list(matriz_traspaso_df.columns),
            "values": matriz_traspaso_df.values.tolist()
        }
        
    for col in df_vista.columns:
        if pd.api.types.is_datetime64_any_dtype(df_vista[col]):
            df_vista[col] = df_vista[col].dt.strftime('%Y-%m-%d %H:%M:%S')
    datos_crudos = df_vista.to_dict(orient='records')
    
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

    act_counts_dict = {}
    if 'actividad' in df_vista.columns:
        act_counts_dict = df_vista['actividad'].value_counts().to_dict()
        
    emp_counts_dict = {}
    if 'empleado' in df_vista.columns:
        emp_counts_dict = df_vista['empleado'].value_counts().to_dict()
        
    picos_trabajo_str = ""
    if col_tiempo in df_vista.columns:
        df_fechas = df_vista.copy()
        df_fechas[col_tiempo] = pd.to_datetime(df_fechas[col_tiempo])
        df_fechas['Solo_Fecha'] = df_fechas[col_tiempo].dt.date
        df_tiempos_group = df_fechas.groupby('Solo_Fecha').size()
        if not df_tiempos_group.empty:
            total_dias = len(df_tiempos_group)
            avg_eventos = round(df_tiempos_group.mean(), 1)
            dia_pico = df_tiempos_group.idxmax().strftime("%Y-%m-%d")
            max_eventos = df_tiempos_group.max()
            picos_trabajo_str = f"- Período analizado: {df_fechas['Solo_Fecha'].min().strftime('%Y-%m-%d')} a {df_fechas['Solo_Fecha'].max().strftime('%Y-%m-%d')} ({total_dias} días)\n- Promedio de eventos por día: {avg_eventos}\n- Día con mayor volumen de trabajo: {dia_pico} ({max_eventos} eventos)"

    return {
        "empty": False,
        "metadata": {
            "fecha_min": fecha_min,
            "fecha_max": fecha_max,
            "empleados": lista_empleados,
            "variantes": lista_variantes
        },
        "kpis": {
            "total_lotes": total_lotes,
            "total_eventos": total_eventos,
            "costo_total": costo_total
        },
        "sla_alert": {
            "meta_horas": meta_horas,
            "num_retrasados": num_retrasados,
            "porcentaje_critico": porcentaje_critico,
            "promedio_retraso": promedio_retraso
        },
        "ciclo_stats": ciclo_stats,
        "sla_cumplimiento": round(sla_cumplimiento, 2),
        "histograma": histograma,
        "slowest_cases": slowest_cases,
        "variantes_filtradas": lista_vars_filtradas,
        "matriz_traspaso": matriz_traspaso,
        "datos_crudos": datos_crudos,
        "contexto_negocio": contexto_negocio,
        "act_counts": act_counts_dict,
        "emp_counts": emp_counts_dict,
        "picos_trabajo": picos_trabajo_str
    }

@app.get("/api/analysis/graph/{id_ejecucion}")
def get_graph(
    id_ejecucion: str,
    tipo_grafo: str = "frecuencia",
    f_inicio: Optional[str] = None,
    f_fin: Optional[str] = None,
    var_seleccionada: Optional[str] = "Todas",
    emps_seleccionados: Optional[List[str]] = Query(None)
):
    df = database_api.obtener_datos_analisis(id_ejecucion)
    if df.empty:
        raise HTTPException(status_code=404, detail="No se encontraron datos.")
        
    _, case_to_variant = miner_api.obtener_variantes(df)
    
    col_tiempo_orig = 'Timestamp' if 'Timestamp' in df.columns else 'fecha_hora'
    df[col_tiempo_orig] = pd.to_datetime(df[col_tiempo_orig])
    
    df_filtrado = df.copy()
    df_filtrado['Variante_ID'] = df_filtrado['ID_Caso'].map(case_to_variant)
    
    if var_seleccionada and var_seleccionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Variante_ID'] == var_seleccionada]
        
    if f_inicio:
        inicio_dt = pd.to_datetime(f_inicio).date()
        df_filtrado = df_filtrado[df_filtrado[col_tiempo_orig].dt.date >= inicio_dt]
        
    if f_fin:
        fin_dt = pd.to_datetime(f_fin).date()
        df_filtrado = df_filtrado[df_filtrado[col_tiempo_orig].dt.date <= fin_dt]
        
    col_emp_orig = 'Empleado' if 'Empleado' in df_filtrado.columns else 'empleado'
    if emps_seleccionados is not None and col_emp_orig in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado[col_emp_orig].isin(emps_seleccionados)]
        
    if df_filtrado.empty:
        raise HTTPException(status_code=400, detail="No hay datos para los filtros aplicados para generar el grafo.")
        
    ruta_imagen = miner_api.descubrir_proceso(df_filtrado, tipo_grafo, id_ejecucion)
    return FileResponse(ruta_imagen, media_type="image/png")


@app.post("/api/analysis/gemini/insights")
def get_gemini_insights(req: GeminiInsightsRequest):
    api_key_env = os.environ.get("GEMINI_API_KEY")
    if not api_key_env:
        raise HTTPException(status_code=500, detail="API Key de Gemini no configurada.")
        
    try:
        genai.configure(api_key=api_key_env)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        prompt = f"""
        Actúa como un asesor de negocios cercano, amigable y muy claro, explicando la salud del proceso de inventario y distribución de la empresa de una manera simple y comprensible para alguien que no conoce términos técnicos. Evita usar palabras complejas como 'SLA', 'Kaizen', 'Six Sigma', 'Minería de Procesos', 'cuellos de botella' o 'variabilidad' sin explicarlas antes de forma muy sencilla.
        
        Aquí tienes la información real de la operación de forma simple:
        - Total de lotes o pedidos analizados: {req.total_lotes}
        - Tiempo máximo que debería tomar cada lote (meta del negocio): {req.meta_horas} horas
        - Cantidad de lotes que tardaron más de lo debido (retrasados): {req.num_retrasados}
        - Porcentaje de lotes que se retrasaron: {req.porcentaje_critico}%
        - Tiempo promedio que tardaron los lotes con demoras: {req.promedio_retraso} horas
        
        **Detalles del proceso observados:**
        {req.contexto_negocio if req.contexto_negocio else '- No hay detalles adicionales disponibles.'}
        
        Por favor, redacta un informe sencillo y amigable respondiendo a lo siguiente:
        1. **¿Qué está pasando con los tiempos? (Explicación de los resultados)**: Explica de manera sencilla y clara qué significan estos números sobre el rendimiento actual, de forma que cualquier persona pueda entenderlo.
        2. **¿Por qué está pasando esto? (Causas de las demoras)**: Explica detalladamente y en lenguaje común por qué ocurren estos retrasos basándote en las actividades más frecuentes, el equipo/empleados involucrados o el tipo de materiales/proveedores. Conéctalos de forma lógica para explicar el porqué real del problema.
        3. **¿Cómo podemos solucionarlo de forma sencilla? (Recomendaciones prácticas)**: Sugiere tres acciones muy sencillas, directas y fáciles de entender que el equipo pueda aplicar para evitar estos retrasos en el día a día.
        
        Recuerda explicar siempre el "porqué" de las cosas de forma directa y sencilla. Usa un tono amigable, instructivo y alentador. Usa negritas y viñetas para que sea muy fácil y rápido de leer. Escribe un máximo de 300 palabras.
        """
        response = model.generate_content(prompt)
        return {"insights": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al llamar a la API de Gemini: {e}")

@app.post("/api/analysis/gemini/trends")
def get_gemini_trends(req: GeminiTrendsRequest):
    api_key_env = os.environ.get("GEMINI_API_KEY")
    if not api_key_env:
        raise HTTPException(status_code=500, detail="API Key de Gemini no configurada.")
        
    try:
        genai.configure(api_key=api_key_env)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        prompt = f"""
        Actúa como un asesor amigable y didáctico que ayuda a entender los datos del negocio sin usar tecnicismos. Explica de manera sencilla y clara el "porqué" de lo que se ve en las gráficas estadísticas de la empresa, pensando en un usuario sin conocimientos técnicos.
        
        Aquí están los datos analizados:
        
        **1. Las tareas que más se repiten en el día a día (Frecuencia de Actividades):**
        {req.act_context if req.act_context else '- No hay datos de actividades.'}
        
        **2. La cantidad de tareas que tiene asignada cada persona en el equipo (Carga de Trabajo por Empleado):**
        {req.emp_context if req.emp_context else '- No hay datos de empleados.'}
        
        **3. Cómo varía el volumen de trabajo en el tiempo (Tendencia Temporal):**
        {req.temp_context if req.temp_context else '- No hay datos de fechas.'}
        
        Por favor, redacta una explicación sencilla y clara que responda a:
        1. **¿Cuáles son las tareas más repetitivas y por qué?:** Explica qué actividades consumen más tiempo en la operación y qué razones sencillas de negocio explican que se repitan tanto en el flujo diario.
        2. **¿Cómo está repartido el trabajo y qué problemas puede causar?:** Analiza si hay personas con demasiadas tareas asignadas en comparación con los demás. Explica el porqué esto puede sobrecargar a los empleados y causar demoras o atascos.
        3. **¿Qué significan los picos de trabajo?:** Explica de manera simple por qué hay días con mucho más movimiento que otros y cómo se puede organizar mejor el equipo para enfrentar esos momentos sin saturarse.
        
        Evita tecnicismos como 'Análisis de Pareto', 'capacidad temporal', 'monopolización de recursos', etc. Explica siempre el "porqué" detrás de cada patrón de forma amigable y comprensible. Usa negritas y viñetas para facilitar la lectura. Escribe un máximo de 300 palabras.
        """
        response = model.generate_content(prompt)
        return {"trends": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al llamar a la API de Gemini: {e}")

@app.post("/api/analysis/export/{id_ejecucion}")
def export_analysis(id_ejecucion: str, req: ExportRequest):
    df = database_api.obtener_datos_analisis(id_ejecucion)
    if df.empty:
        raise HTTPException(status_code=404, detail="No se encontraron datos para la ejecución especificada.")
        
    filters = req.filters
    df_temp_cols = df.copy()
    df_temp_cols.columns = df_temp_cols.columns.str.lower()
    
    variant_counts, case_to_variant = miner_api.obtener_variantes(df)
    lista_variantes = []
    for _, r in variant_counts.iterrows():
        lista_variantes.append({
            "id": r['Variante_ID'],
            "actividades": list(r['Actividades']),
            "cantidad": int(r['Cantidad']),
            "porcentaje": round(float(r['Porcentaje']), 2)
        })
        
    col_tiempo_orig = 'Timestamp' if 'Timestamp' in df.columns else 'fecha_hora'
    df[col_tiempo_orig] = pd.to_datetime(df[col_tiempo_orig])
    
    df_filtrado = df.copy()
    df_filtrado['Variante_ID'] = df_filtrado['ID_Caso'].map(case_to_variant)
    
    if filters.var_seleccionada and filters.var_seleccionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Variante_ID'] == filters.var_seleccionada]
        
    if filters.f_inicio:
        inicio_dt = pd.to_datetime(filters.f_inicio).date()
        df_filtrado = df_filtrado[df_filtrado[col_tiempo_orig].dt.date >= inicio_dt]
        
    if filters.f_fin:
        fin_dt = pd.to_datetime(filters.f_fin).date()
        df_filtrado = df_filtrado[df_filtrado[col_tiempo_orig].dt.date <= fin_dt]
        
    col_emp_orig = 'Empleado' if 'Empleado' in df_filtrado.columns else 'empleado'
    if filters.emps_seleccionados is not None and col_emp_orig in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado[col_emp_orig].isin(filters.emps_seleccionados)]
        
    if df_filtrado.empty:
        raise HTTPException(status_code=400, detail="No hay datos para exportar con los filtros seleccionados.")
        
    nombre_analisis = "Datos en Vivo (ERP)" if id_ejecucion == "LIVE" else ""
    if id_ejecucion != "LIVE":
        history = database_api.obtener_lista_analisis()
        for h in history:
            if h.get('id_ejecucion') == id_ejecucion:
                nombre_analisis = h.get('nombre_analisis')
                break
                
    metadata = {
        "nombre_analisis": nombre_analisis or id_ejecucion,
        "f_inicio": filters.f_inicio,
        "f_fin": filters.f_fin,
        "var_seleccionada": filters.var_seleccionada,
        "emps_seleccionados": filters.emps_seleccionados
    }
    
    df_vista = df_filtrado.copy()
    columnas_sistema = ['ID_Ejecucion', 'Nombre_Analisis', 'Fecha_Subida', 'Variante_ID']
    df_vista = df_vista.drop(columns=[col for col in columnas_sistema if col in df_vista.columns])
    df_vista.columns = df_vista.columns.str.lower()
    
    total_lotes = len(df_vista['id_caso'].unique()) if 'id_caso' in df_vista.columns else 0
    total_eventos = len(df_vista)
    costo_total = 0.0
    if 'costo_lote_soles' in df_vista.columns and 'id_caso' in df_vista.columns:
        costo_total = float(df_vista.drop_duplicates(subset=['id_caso'])['costo_lote_soles'].sum())
        
    kpis = {
        "total_lotes": total_lotes,
        "total_eventos": total_eventos,
        "costo_total": costo_total
    }
    
    col_tiempo = 'timestamp' if 'timestamp' in df_vista.columns else 'fecha_hora'
    num_retrasados = 0
    porcentaje_critico = 0.0
    promedio_retraso = 0.0
    meta_horas = database_api.obtener_meta_tiempo()
    
    if col_tiempo in df_vista.columns and 'id_caso' in df_vista.columns:
        df_vista[col_tiempo] = pd.to_datetime(df_vista[col_tiempo])
        df_ordenado = df_vista.sort_values(by=['id_caso', col_tiempo])
        tiempos_ciclo = df_ordenado.groupby('id_caso')[col_tiempo].agg(Inicio='min', Fin='max')
        tiempos_ciclo['Duracion_Horas'] = (tiempos_ciclo['Fin'] - tiempos_ciclo['Inicio']).dt.total_seconds() / 3600
        lotes_retrasados = tiempos_ciclo[tiempos_ciclo['Duracion_Horas'] > meta_horas]
        total_lotes_ciclo = len(tiempos_ciclo)
        num_retrasados = len(lotes_retrasados)
        if num_retrasados > 0:
            porcentaje_critico = round((num_retrasados / total_lotes_ciclo) * 100, 1)
            promedio_retraso = round(lotes_retrasados['Duracion_Horas'].mean(), 1)
            
    alert = {
        "meta_horas": meta_horas,
        "num_retrasados": num_retrasados,
        "porcentaje_critico": porcentaje_critico,
        "promedio_retraso": promedio_retraso
    }
    
    ciclo_stats = {}
    slowest_cases = []
    sla_cumplimiento = 100.0
    
    case_durations = miner_api.calcular_tiempos_ciclo(df_filtrado)
    if not case_durations.empty:
        avg_dur = float(case_durations['Duracion_Horas'].mean())
        med_dur = float(case_durations['Duracion_Horas'].median())
        min_dur = float(case_durations['Duracion_Horas'].min())
        max_dur = float(case_durations['Duracion_Horas'].max())
        
        ciclo_stats = {
            "promedio": round(avg_dur, 2),
            "mediana": round(med_dur, 2),
            "minima": round(min_dur, 2),
            "maxima": round(max_dur, 2)
        }
        
        casos_retrasados = case_durations[case_durations['Duracion_Horas'] > meta_horas]
        sla_cumplimiento = float(((len(case_durations) - len(casos_retrasados)) / len(case_durations)) * 100)
        
        slow_cases_df = case_durations.sort_values(by='Duracion_Horas', ascending=False).head(10).copy()
        slow_cases_df['SLA_Status'] = slow_cases_df['Duracion_Horas'].apply(
            lambda x: f"{(x - meta_horas):.2f} hrs de retraso" if x > meta_horas else "Cumple SLA"
        )
        for _, r in slow_cases_df.iterrows():
            slowest_cases.append({
                "id_caso": str(r['ID_Caso']),
                "inicio": r['Inicio'].strftime('%d/%m/%Y %H:%M'),
                "fin": r['Fin'].strftime('%d/%m/%Y %H:%M'),
                "duracion": f"{r['Duracion_Horas']:.2f} hrs",
                "status": r['SLA_Status']
            })
            
    matriz_traspaso_df = miner_api.calcular_matriz_traspaso(df_filtrado)
    matriz_traspaso = {}
    if not matriz_traspaso_df.empty:
        matriz_traspaso = {
            "index": list(matriz_traspaso_df.index),
            "columns": list(matriz_traspaso_df.columns),
            "values": matriz_traspaso_df.values.tolist()
        }
        
    chart_paths = {}
    try:
        chart_paths = report_generator.generar_graficos_matplotlib(df_filtrado, id_ejecucion, meta_horas)
        ruta_grafo = miner_api.descubrir_proceso(df_filtrado, "frecuencia", id_ejecucion)
        
        if req.format == "docx":
            file_bytes = report_generator.generar_reporte_docx(
                metadata, kpis, alert, req.insights, ruta_grafo,
                ciclo_stats, sla_cumplimiento, lista_variantes, matriz_traspaso, slowest_cases,
                chart_paths
            )
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"Reporte_{id_ejecucion}.docx"
        else:
            file_bytes = report_generator.generar_reporte_pdf(
                metadata, kpis, alert, req.insights, ruta_grafo,
                ciclo_stats, sla_cumplimiento, lista_variantes, matriz_traspaso, slowest_cases,
                chart_paths
            )
            media_type = "application/pdf"
            filename = f"Reporte_{id_ejecucion}.pdf"
    finally:
        for p_img in chart_paths.values():
            if p_img and os.path.exists(p_img):
                try:
                    os.remove(p_img)
                except Exception:
                    pass
        
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
