import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine

# Conexión a PostgreSQL (No olvides poner tu contraseña real)
DATABASE_URL = "postgresql://postgres:juanvaleriano@localhost:5432/Valers"
engine = create_engine(DATABASE_URL, echo=False)

def guardar_nuevo_analisis(df, nombre_archivo):
    """
    Recibe el DataFrame subido, le agrega identificadores únicos de la sesión actual
    y lo inyecta masivamente en PostgreSQL.
    """
    # Generar un ID único basado en la fecha y hora exacta
    fecha_actual = datetime.now()
    id_ejecucion = fecha_actual.strftime("EXEC_%Y%m%d_%H%M%S")
    nombre_analisis = f"Análisis {fecha_actual.strftime('%d/%m/%Y %H:%M')} - {nombre_archivo}"
    
    # Añadimos las columnas de historial al DataFrame
    df_guardar = df.copy()
    df_guardar['ID_Ejecucion'] = id_ejecucion
    df_guardar['Nombre_Analisis'] = nombre_analisis
    df_guardar['Fecha_Subida'] = fecha_actual
    
    # Guardar en PostgreSQL masivamente. 
    # 'if_exists="append"' crea la tabla si no existe, o añade las filas si ya existe.
    df_guardar.to_sql('registro_eventos_inventario', engine, if_exists='replace', index=False)
    
    return id_ejecucion, nombre_analisis

def obtener_lista_analisis():
    """
    Consulta a la base de datos para obtener los análisis guardados históricamente.
    """
    # Agrupamos por ID de ejecución para mostrar el historial en la interfaz
    query = """
    SELECT DISTINCT "ID_Ejecucion", "Nombre_Analisis", "Fecha_Subida" 
    FROM registro_eventos_inventario 
    ORDER BY "Fecha_Subida" DESC
    """
    try:
        df_historial = pd.read_sql(query, engine)
        return df_historial
    except Exception as e:
        # Si la tabla no existe aún, devolvemos un DataFrame vacío
        return pd.DataFrame()

def obtener_datos_analisis(id_ejecucion):
    """
    Extrae todos los eventos de un análisis histórico específico.
    """
    query = f"SELECT * FROM registro_eventos_inventario WHERE \"ID_Ejecucion\" = '{id_ejecucion}'"
    return pd.read_sql(query, engine)