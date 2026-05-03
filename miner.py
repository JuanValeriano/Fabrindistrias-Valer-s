import pm4py
import pandas as pd
import os

def descubrir_proceso(df):
    """
    Recibe un DataFrame de Pandas desde el CSV cargado y descubre el 
    modelo de procesos usando un Directly-Follows Graph (DFG).
    """
    # 1. Asegurar que la fecha sea tipo Datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # 2. Formatear el DataFrame al estándar de PM4Py
    # Ajustamos a las columnas exactas de tu archivo CSV generado
    dataframe_formateado = pm4py.format_dataframe(
        df, 
        case_id='ID_Caso', 
        activity_key='Actividad', 
        timestamp_key='Timestamp'
    )
    
    # 3. Descubrir el DFG (Directly-Follows Graph)
    dfg, start_activities, end_activities = pm4py.discover_dfg(dataframe_formateado)
    
    # 4. Generar la visualización del Grafo (Anotado con tiempos)
    ruta_imagen = "grafo_proceso.png"
    
    # Grafo de rendimiento (Performance = Tiempos de cuello de botella)
    pm4py.save_vis_performance_dfg(
        dfg, 
        start_activities, 
        end_activities, 
        ruta_imagen
    )
    
    return ruta_imagen