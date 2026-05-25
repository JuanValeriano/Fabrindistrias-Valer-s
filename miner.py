import pm4py
import pandas as pd
import os

def descubrir_proceso(df, tipo_grafo="frecuencia"):
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    dataframe_formateado = pm4py.format_dataframe(
        df, 
        case_id='ID_Caso', 
        activity_key='Actividad', 
        timestamp_key='Timestamp'
    )
    
    ruta_imagen = "grafo_proceso.png"
    
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

    df_sorted = df.sort_values(by=['ID_Caso', 'Timestamp'])
    
    case_variants = df_sorted.groupby('ID_Caso')['Actividad'].apply(lambda x: tuple(x.tolist()))
    
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
    df_copy['Timestamp'] = pd.to_datetime(df_copy['Timestamp'])
    df_sorted = df_copy.sort_values(by=['ID_Caso', 'Timestamp'])
    case_times = df_sorted.groupby('ID_Caso')['Timestamp'].agg(Inicio='min', Fin='max').reset_index()
    case_times['Duracion_Horas'] = (case_times['Fin'] - case_times['Inicio']).dt.total_seconds() / 3600.0
    return case_times

def calcular_matriz_traspaso(df):

    df_sorted = df.sort_values(by=['ID_Caso', 'Timestamp'])
    
    df_sorted['Siguiente_Empleado'] = df_sorted.groupby('ID_Caso')['Empleado'].shift(-1)
    
    handovers = df_sorted.dropna(subset=['Siguiente_Empleado'])
    
    matrix_df = handovers.groupby(['Empleado', 'Siguiente_Empleado']).size().reset_index(name='Frecuencia')
    
    pivot_matrix = matrix_df.pivot(index='Empleado', columns='Siguiente_Empleado', values='Frecuencia').fillna(0)
    return pivot_matrix
