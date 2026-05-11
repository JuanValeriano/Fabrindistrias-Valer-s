import pm4py
import pandas as pd
from pm4py.visualization.dfg import visualizer as dfg_visualizer

def descubrir_proceso(df):
    df_copy = df.copy()
    
    col_map = {col.lower(): col for col in df_copy.columns}
    
    case_id = col_map.get('id_caso', 'ID_Caso')
    activity = col_map.get('actividad', 'Actividad')
    timestamp = col_map.get('timestamp', col_map.get('fecha_hora', 'Timestamp'))

    df_copy[timestamp] = pd.to_datetime(df_copy[timestamp])

    # 1. Formatear el dataframe para PM4Py
    event_log = pm4py.format_dataframe(
        df_copy, 
        case_id=case_id, 
        activity_key=activity, 
        timestamp_key=timestamp
    )

    # 2. Descubrir DFG de RENDIMIENTO (tiempos en segundos)
    performance_dfg, start_activities, end_activities = pm4py.discover_performance_dfg(event_log)

    # 3. Convertir de segundos a minutos
    performance_dfg_minutos = {}
    for arco, valor in performance_dfg.items():
        if isinstance(valor, dict):
            segundos = valor.get('mean', 0)
        elif isinstance(valor, (tuple, list)):
            segundos = valor[0]
        else:
            segundos = valor
        performance_dfg_minutos[arco] = round(segundos / 60, 1)

    # 4. Visualizar con color rojo claro
    ruta_imagen = "grafo_proceso.png"

    parameters = {
        "format": "png",
        "bgcolor": "white",
        "color_map": {arco: "salmon" for arco in performance_dfg_minutos},  # rojo claro
        "node_color": "#FF9999"  # rojo claro para los nodos
    }

    pm4py.save_vis_performance_dfg(
        performance_dfg_minutos,
        start_activities,
        end_activities,
        ruta_imagen,
        parameters=parameters
    )

    return ruta_imagen