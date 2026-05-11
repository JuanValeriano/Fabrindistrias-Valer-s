import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
import urllib.parse
import bcrypt

DATABASE_URL = "postgresql://postgres:juanvaleriano@localhost:5432/Valers"
engine = create_engine(DATABASE_URL, echo=False)

# ==========================================
# GESTIÓN DE SEGURIDAD Y USUARIOS
# ==========================================

def inicializar_tablas_sistema():

    with engine.connect() as conn:

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS usuarios (
                usuario VARCHAR(50) PRIMARY KEY,
                password_hash TEXT NOT NULL,
                rol VARCHAR(20) NOT NULL
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS configuracion_sistema (
                clave VARCHAR(50) PRIMARY KEY,
                valor FLOAT NOT NULL
            );
        """))
        conn.commit()

def crear_usuario(nombre_usuario, password_plano, rol):

    bytes_password = password_plano.encode('utf-8')
    sal = bcrypt.gensalt()
    hash_password = bcrypt.hashpw(bytes_password, sal).decode('utf-8')
    
    with engine.connect() as conn:
        query = text("INSERT INTO usuarios (usuario, password_hash, rol) VALUES (:u, :p, :r) ON CONFLICT (usuario) DO NOTHING")
        conn.execute(query, {"u": nombre_usuario, "p": hash_password, "r": rol})
        conn.commit()

def verificar_login(nombre_usuario, password_intento):

    with engine.connect() as conn:
        result = conn.execute(text("SELECT password_hash, rol FROM usuarios WHERE usuario = :u"), {"u": nombre_usuario}).fetchone()
        
        if result:
            hash_guardado = result[0].encode('utf-8')
            if bcrypt.checkpw(password_intento.encode('utf-8'), hash_guardado):
                return True, result[1]
    return False, None


def obtener_usuarios():

    with engine.connect() as conn:
        result = conn.execute(text("SELECT usuario, rol FROM usuarios"))

        return pd.DataFrame(result.fetchall(), columns=["Usuario", "Rol"])

def eliminar_usuario(nombre_usuario):

    with engine.connect() as conn:
        conn.execute(text("DELETE FROM usuarios WHERE usuario = :u"), {"u": nombre_usuario})
        conn.commit()
    return True, f"Usuario '{nombre_usuario}' eliminado exitosamente."

# ==========================================
# GESTIÓN DE METAS (SLA)
# ==========================================

def guardar_meta_tiempo(horas):
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO configuracion_sistema (clave, valor) VALUES ('umbral_horas', :v) ON CONFLICT (clave) DO UPDATE SET valor = :v"), {"v": horas})
        conn.commit()

def obtener_meta_tiempo():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT valor FROM configuracion_sistema WHERE clave = 'umbral_horas'")).fetchone()
        return res[0] if res else 48.0

def guardar_nuevo_analisis(df, nombre_archivo):

    fecha_actual = datetime.now()
    id_ejecucion = fecha_actual.strftime("EXEC_%Y%m%d_%H%M%S")
    nombre_analisis = f"Análisis {fecha_actual.strftime('%d/%m/%Y %H:%M')} - {nombre_archivo}"
    
    df_guardar = df.copy()
    df_guardar['ID_Ejecucion'] = id_ejecucion
    df_guardar['Nombre_Analisis'] = nombre_analisis
    df_guardar['Fecha_Subida'] = fecha_actual
    
    df_guardar.to_sql('registro_eventos_inventario', engine, if_exists='append', index=False)
    
    return id_ejecucion, nombre_analisis

def obtener_lista_analisis():

    query = """
    SELECT DISTINCT "ID_Ejecucion", "Nombre_Analisis", "Fecha_Subida" 
    FROM registro_eventos_inventario 
    ORDER BY "Fecha_Subida" DESC
    """
    try:
        df_historial = pd.read_sql(query, engine)
        return df_historial
    except Exception as e:
        return pd.DataFrame()

def obtener_datos_analisis(id_ejecucion):

    query = f"SELECT * FROM registro_eventos_inventario WHERE \"ID_Ejecucion\" = '{id_ejecucion}'"
    return pd.read_sql(query, engine)


