import pm4py
import pandas as pd
import os

def descubrir_proceso(df):

    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    dataframe_formateado = pm4py.format_dataframe(
        df, 
        case_id='ID_Caso', 
        activity_key='Actividad', 
        timestamp_key='Timestamp'
    )
    
    dfg, start_activities, end_activities = pm4py.discover_dfg(dataframe_formateado)
    
    ruta_imagen = "grafo_proceso.png"
    
    pm4py.save_vis_performance_dfg(
        dfg, 
        start_activities, 
        end_activities, 
        ruta_imagen
    )
    
    return ruta_imagen