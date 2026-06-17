import pm4py
import pandas as pd
import os

def descubrir_proceso(df, tipo_grafo="frecuencia", id_ejecucion="temp"):
    df = df.copy()
    col_timestamp = 'Timestamp' if 'Timestamp' in df.columns else 'fecha_hora'
    df[col_timestamp] = pd.to_datetime(df[col_timestamp])
    
    case_id_col = 'ID_Caso' if 'ID_Caso' in df.columns else 'id_caso'
    act_col = 'Actividad' if 'Actividad' in df.columns else 'actividad'
    
    dataframe_formateado = pm4py.format_dataframe(
        df, 
        case_id=case_id_col, 
        activity_key=act_col, 
        timestamp_key=col_timestamp
    )
    
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        
    ruta_imagen = os.path.join(static_dir, f"grafo_{id_ejecucion}_{tipo_grafo}.png")
    
    if os.path.exists(ruta_imagen):
        try:
            os.remove(ruta_imagen)
        except Exception:
            pass
            
    if tipo_grafo == "desempeño":
        dfg, start_activities, end_activities = pm4py.discover_performance_dfg(dataframe_formateado)
        pm4py.save_vis_performance_dfg(
            dfg, 
            start_activities, 
            end_activities, 
            ruta_imagen,
            aggregation_measure="mean"
        )
    else:
        dfg, start_activities, end_activities = pm4py.discover_dfg(dataframe_formateado)
        pm4py.save_vis_dfg(
            dfg, 
            start_activities, 
            end_activities, 
            ruta_imagen
        )
    
    return ruta_imagen

def obtener_variantes(df):
    df_sorted = df.copy()
    case_id_col = 'ID_Caso' if 'ID_Caso' in df.columns else 'id_caso'
    act_col = 'Actividad' if 'Actividad' in df.columns else 'actividad'
    timestamp_col = 'Timestamp' if 'Timestamp' in df.columns else 'fecha_hora'
    
    df_sorted[timestamp_col] = pd.to_datetime(df_sorted[timestamp_col])
    df_sorted = df_sorted.sort_values(by=[case_id_col, timestamp_col])
    
    case_variants = df_sorted.groupby(case_id_col)[act_col].apply(lambda x: tuple(x.tolist()))
    variant_counts = case_variants.value_counts().reset_index()
    variant_counts.columns = ['Actividades', 'Cantidad']
    
    total_casos = len(case_variants)
    variant_counts['Porcentaje'] = (variant_counts['Cantidad'] / total_casos) * 100
    variant_counts['Variante_ID'] = [f"Variante {i+1}" for i in range(len(variant_counts))]
    variant_counts = variant_counts[['Variante_ID', 'Actividades', 'Cantidad', 'Porcentaje']]
    
    variant_map = dict(zip(variant_counts['Actividades'], variant_counts['Variante_ID']))
    case_to_variant = {case_id: variant_map[activities] for case_id, activities in case_variants.items()}
    
    return variant_counts, case_to_variant

def calcular_tiempos_ciclo(df):
    df_copy = df.copy()
    case_id_col = 'ID_Caso' if 'ID_Caso' in df.columns else 'id_caso'
    timestamp_col = 'Timestamp' if 'Timestamp' in df.columns else 'fecha_hora'
    
    df_copy[timestamp_col] = pd.to_datetime(df_copy[timestamp_col])
    df_sorted = df_copy.sort_values(by=[case_id_col, timestamp_col])
    case_times = df_sorted.groupby(case_id_col)[timestamp_col].agg(Inicio='min', Fin='max').reset_index()
    case_times['Duracion_Horas'] = (case_times['Fin'] - case_times['Inicio']).dt.total_seconds() / 3600.0
    return case_times

def calcular_matriz_traspaso(df):
    df_sorted = df.copy()
    case_id_col = 'ID_Caso' if 'ID_Caso' in df.columns else 'id_caso'
    emp_col = 'Empleado' if 'Empleado' in df.columns else 'empleado'
    timestamp_col = 'Timestamp' if 'Timestamp' in df.columns else 'fecha_hora'
    
    if emp_col not in df.columns:
        return pd.DataFrame()
        
    df_sorted[timestamp_col] = pd.to_datetime(df_sorted[timestamp_col])
    df_sorted = df_sorted.sort_values(by=[case_id_col, timestamp_col])
    
    df_sorted['Siguiente_Empleado'] = df_sorted.groupby(case_id_col)[emp_col].shift(-1)
    handovers = df_sorted.dropna(subset=['Siguiente_Empleado'])
    
    if handovers.empty:
        return pd.DataFrame()
        
    matrix_df = handovers.groupby([emp_col, 'Siguiente_Empleado']).size().reset_index(name='Frecuencia')
    pivot_matrix = matrix_df.pivot(index=emp_col, columns='Siguiente_Empleado', values='Frecuencia').fillna(0)
    return pivot_matrix
