import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
import bcrypt
import os

env_path = ".env" if os.path.exists(".env") else "../.env"
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                clave, valor = line.split("=", 1)
                os.environ[clave.strip()] = valor.strip().strip('"').strip("'")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:963852741.@localhost:5432/VALERS"

engine = create_engine(DATABASE_URL, echo=False)

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

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ejecuciones (
                id_ejecucion VARCHAR(50) PRIMARY KEY,
                nombre_analisis VARCHAR(150) NOT NULL,
                fecha_subida TIMESTAMP NOT NULL
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id_proveedor SERIAL PRIMARY KEY,
                nombre VARCHAR(100) UNIQUE NOT NULL
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS materiales (
                id_material SERIAL PRIMARY KEY,
                sku_descripcion VARCHAR(100) UNIQUE NOT NULL,
                categoria VARCHAR(50) NOT NULL,
                unidad_medida VARCHAR(20) NOT NULL
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS empleados (
                id_empleado SERIAL PRIMARY KEY,
                nombre VARCHAR(50) UNIQUE NOT NULL,
                rol VARCHAR(50) NOT NULL,
                turno VARCHAR(50) NOT NULL
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ubicaciones (
                id_ubicacion SERIAL PRIMARY KEY,
                nombre VARCHAR(50) UNIQUE NOT NULL
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS actividades (
                id_actividad SERIAL PRIMARY KEY,
                nombre VARCHAR(50) UNIQUE NOT NULL
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lotes (
                id_caso VARCHAR(50) PRIMARY KEY,
                id_material INT REFERENCES materiales(id_material),
                cantidad INT NOT NULL,
                id_proveedor INT REFERENCES proveedores(id_proveedor),
                costo_lote_soles FLOAT NOT NULL,
                prioridad_produccion VARCHAR(20) NOT NULL,
                id_ejecucion VARCHAR(50) REFERENCES ejecuciones(id_ejecucion) ON DELETE CASCADE
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS eventos (
                id_evento SERIAL PRIMARY KEY,
                id_caso VARCHAR(50) REFERENCES lotes(id_caso) ON DELETE CASCADE,
                id_actividad INT REFERENCES actividades(id_actividad),
                timestamp TIMESTAMP NOT NULL,
                id_empleado INT REFERENCES empleados(id_empleado),
                estado_calidad VARCHAR(50) NOT NULL,
                id_ubicacion INT REFERENCES ubicaciones(id_ubicacion),
                id_ejecucion VARCHAR(50) REFERENCES ejecuciones(id_ejecucion) ON DELETE CASCADE
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS registro_eventos_inventario (
                id_registro SERIAL PRIMARY KEY,
                id_caso VARCHAR(50),
                actividad VARCHAR(50),
                timestamp TIMESTAMP,
                empleado VARCHAR(50),
                rol VARCHAR(50),
                turno VARCHAR(50),
                categoria_material VARCHAR(50),
                sku_descripcion VARCHAR(100),
                unidad_medida VARCHAR(20),
                cantidad INT,
                proveedor VARCHAR(100),
                estado_calidad VARCHAR(50),
                ubicacion_fisica VARCHAR(50),
                costo_lote_soles FLOAT,
                prioridad_produccion VARCHAR(20),
                id_ejecucion VARCHAR(50) REFERENCES ejecuciones(id_ejecucion) ON DELETE CASCADE
            );
        """))
        conn.commit()
    
    ejecutar_migracion_relacional()

def ejecutar_migracion_relacional():
    """
    Comprueba si existe la tabla plana antigua 'registro_eventos_inventario'.
    Si existe y tiene datos, los migra al esquema normalizado de forma automática.
    """
    with engine.connect() as conn:
        old_table_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'registro_eventos_inventario_old'
            );
        """)).fetchone()[0]
        if old_table_exists:
            return

        table_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'registro_eventos_inventario'
            );
        """)).fetchone()[0]
        
        if not table_exists:
            return
            
        try:
            df_cols = pd.read_sql_query("SELECT * FROM registro_eventos_inventario LIMIT 1", engine)
            cols_lower = [c.lower() for c in df_cols.columns]
            if 'nombre_analisis' not in cols_lower and 'fecha_subida' not in cols_lower:
                return
                
            print("Detectada tabla plana antigua 'registro_eventos_inventario'. Iniciando migracion a 3NF...")
            df = pd.read_sql_query("SELECT * FROM registro_eventos_inventario", engine)
            if df.empty:
                conn.execute(text("ALTER TABLE registro_eventos_inventario RENAME TO registro_eventos_inventario_old;"))
                conn.commit()
                return
                
            cols_map = {c: c for c in df.columns}
            for c in df.columns:
                if c.lower() == 'id_caso': cols_map[c] = 'ID_Caso'
                elif c.lower() == 'actividad': cols_map[c] = 'Actividad'
                elif c.lower() == 'timestamp': cols_map[c] = 'Timestamp'
                elif c.lower() == 'fecha_hora': cols_map[c] = 'Timestamp'
                elif c.lower() == 'empleado': cols_map[c] = 'Empleado'
                elif c.lower() == 'rol': cols_map[c] = 'Rol'
                elif c.lower() == 'turno': cols_map[c] = 'Turno'
                elif c.lower() == 'categoria_material': cols_map[c] = 'Categoria_Material'
                elif c.lower() == 'sku_descripcion': cols_map[c] = 'SKU_Descripcion'
                elif c.lower() == 'unidad_medida': cols_map[c] = 'Unidad_Medida'
                elif c.lower() == 'cantidad': cols_map[c] = 'Cantidad'
                elif c.lower() == 'proveedor': cols_map[c] = 'Proveedor'
                elif c.lower() == 'estado_calidad': cols_map[c] = 'Estado_Calidad'
                elif c.lower() == 'ubicacion_fisica': cols_map[c] = 'Ubicacion_Fisica'
                elif c.lower() == 'costo_lote_soles': cols_map[c] = 'Costo_Lote_Soles'
                elif c.lower() == 'prioridad_produccion': cols_map[c] = 'Prioridad_Produccion'
                elif c.lower() == 'id_ejecucion': cols_map[c] = 'ID_Ejecucion'
                elif c.lower() == 'nombre_analisis': cols_map[c] = 'Nombre_Analisis'
                elif c.lower() == 'fecha_subida': cols_map[c] = 'Fecha_Subida'
                
            df = df.rename(columns=cols_map)
            
            ejecs = df[['ID_Ejecucion', 'Nombre_Analisis', 'Fecha_Subida']].drop_duplicates().dropna()
            for _, row in ejecs.iterrows():
                conn.execute(text("""
                    INSERT INTO ejecuciones (id_ejecucion, nombre_analisis, fecha_subida)
                    VALUES (:id, :nom, :fec) ON CONFLICT (id_ejecucion) DO NOTHING
                """), {"id": row['ID_Ejecucion'], "nom": row['Nombre_Analisis'], "fec": row['Fecha_Subida']})
            
            provs = df['Proveedor'].dropna().unique()
            for prov in provs:
                conn.execute(text("INSERT INTO proveedores (nombre) VALUES (:nom) ON CONFLICT (nombre) DO NOTHING"), {"nom": prov})
                
            mats = df[['SKU_Descripcion', 'Categoria_Material', 'Unidad_Medida']].drop_duplicates().dropna()
            for _, row in mats.iterrows():
                conn.execute(text("""
                    INSERT INTO materiales (sku_descripcion, categoria, unidad_medida)
                    VALUES (:sku, :cat, :uni) ON CONFLICT (sku_descripcion) DO NOTHING
                """), {"sku": row['SKU_Descripcion'], "cat": row['Categoria_Material'], "uni": row['Unidad_Medida']})
                
            emps = df[['Empleado', 'Rol', 'Turno']].drop_duplicates().dropna()
            for _, row in emps.iterrows():
                conn.execute(text("""
                    INSERT INTO empleados (nombre, rol, turno)
                    VALUES (:nom, :rol, :tur) ON CONFLICT (nombre) DO NOTHING
                """), {"nom": row['Empleado'], "rol": row['Rol'], "tur": row['Turno']})
                
            locs = df['Ubicacion_Fisica'].dropna().unique()
            for loc in locs:
                conn.execute(text("INSERT INTO ubicaciones (nombre) VALUES (:nom) ON CONFLICT (nombre) DO NOTHING"), {"nom": loc})
                
            acts = df['Actividad'].dropna().unique()
            for act in acts:
                conn.execute(text("INSERT INTO actividades (nombre) VALUES (:nom) ON CONFLICT (nombre) DO NOTHING"), {"nom": act})
                
            conn.commit()
            
            prov_map = {r[1]: r[0] for r in conn.execute(text("SELECT id_provider, nombre FROM proveedores" if 'id_provider' in df.columns else "SELECT id_proveedor, nombre FROM proveedores")).fetchall()}
            mat_map = {r[1]: r[0] for r in conn.execute(text("SELECT id_material, sku_descripcion FROM materiales")).fetchall()}
            emp_map = {r[1]: r[0] for r in conn.execute(text("SELECT id_empleado, nombre FROM empleados")).fetchall()}
            loc_map = {r[1]: r[0] for r in conn.execute(text("SELECT id_ubicacion, nombre FROM ubicaciones")).fetchall()}
            act_map = {r[1]: r[0] for r in conn.execute(text("SELECT id_actividad, nombre FROM actividades")).fetchall()}
            
            lotes_df = df[['ID_Caso', 'SKU_Descripcion', 'Cantidad', 'Proveedor', 'Costo_Lote_Soles', 'Prioridad_Produccion', 'ID_Ejecucion']].drop_duplicates(subset=['ID_Caso']).dropna(subset=['ID_Caso'])
            for _, row in lotes_df.iterrows():
                mat_id = mat_map.get(row['SKU_Descripcion'])
                prov_id = prov_map.get(row['Proveedor'])
                conn.execute(text("""
                    INSERT INTO lotes (id_caso, id_material, cantidad, id_proveedor, costo_lote_soles, prioridad_produccion, id_ejecucion)
                    VALUES (:id, :mat, :cant, :prov, :costo, :prio, :exec) ON CONFLICT (id_caso) DO NOTHING
                """), {
                    "id": row['ID_Caso'], "mat": mat_id, "cant": int(row['Cantidad']), "prov": prov_id,
                    "costo": float(row['Costo_Lote_Soles']), "prio": row['Prioridad_Produccion'], "exec": row['ID_Ejecucion']
                })
                
            eventos_df = df[['ID_Caso', 'Actividad', 'Timestamp', 'Empleado', 'Estado_Calidad', 'Ubicacion_Fisica', 'ID_Ejecucion']].dropna(subset=['ID_Caso', 'Actividad'])
            for _, row in eventos_df.iterrows():
                act_id = act_map.get(row['Actividad'])
                emp_id = emp_map.get(row['Empleado'])
                loc_id = loc_map.get(row['Ubicacion_Fisica'])
                conn.execute(text("""
                    INSERT INTO eventos (id_caso, id_actividad, timestamp, id_empleado, estado_calidad, id_ubicacion, id_ejecucion)
                    VALUES (:caso, :act, :ts, :emp, :cal, :loc, :exec)
                """), {
                    "caso": row['ID_Caso'], "act": act_id, "ts": pd.to_datetime(row['Timestamp']), "emp": emp_id,
                    "cal": row['Estado_Calidad'], "loc": loc_id, "exec": row['ID_Ejecucion']
                })
                
            conn.execute(text("ALTER TABLE registro_eventos_inventario RENAME TO registro_eventos_inventario_old;"))
            conn.commit()
            print("¡Migracion de base de datos a 3NF completada con exito!")
            
        except Exception as e:
            conn.rollback()
            print(f"Error durante la migracion de base de datos: {e}")

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
        return [{"usuario": r[0], "rol": r[1]} for r in result.fetchall()]

def eliminar_usuario(nombre_usuario):
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM usuarios WHERE usuario = :u"), {"u": nombre_usuario})
        conn.commit()
    return True, f"Usuario '{nombre_usuario}' eliminado exitosamente."

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
    
    df_temp = df.copy()
    cols_map = {}
    for c in df_temp.columns:
        c_low = c.lower()
        if c_low == 'id_caso': cols_map[c] = 'id_caso'
        elif c_low == 'actividad': cols_map[c] = 'actividad'
        elif c_low == 'timestamp': cols_map[c] = 'timestamp'
        elif c_low == 'fecha_hora': cols_map[c] = 'timestamp'
        elif c_low == 'empleado': cols_map[c] = 'empleado'
        elif c_low == 'rol': cols_map[c] = 'rol'
        elif c_low == 'turno': cols_map[c] = 'turno'
        elif c_low == 'categoria_material': cols_map[c] = 'categoria_material'
        elif c_low == 'sku_descripcion': cols_map[c] = 'sku_descripcion'
        elif c_low == 'unidad_medida': cols_map[c] = 'unidad_medida'
        elif c_low == 'cantidad': cols_map[c] = 'cantidad'
        elif c_low == 'proveedor': cols_map[c] = 'proveedor'
        elif c_low == 'estado_calidad': cols_map[c] = 'estado_calidad'
        elif c_low == 'ubicacion_fisica': cols_map[c] = 'ubicacion_fisica'
        elif c_low == 'costo_lote_soles': cols_map[c] = 'costo_lote_soles'
        elif c_low == 'prioridad_produccion': cols_map[c] = 'prioridad_produccion'
        
    df_temp = df_temp.rename(columns=cols_map)
    
    target_cols = [
        'id_caso', 'actividad', 'timestamp', 'empleado', 'rol', 'turno',
        'categoria_material', 'sku_descripcion', 'unidad_medida', 'cantidad',
        'proveedor', 'estado_calidad', 'ubicacion_fisica', 'costo_lote_soles',
        'prioridad_produccion'
    ]
    
    for col in target_cols:
        if col not in df_temp.columns:
            df_temp[col] = None
            
    if 'timestamp' in df_temp.columns:
        df_temp['timestamp'] = pd.to_datetime(df_temp['timestamp'], errors='coerce')
        
    if 'cantidad' in df_temp.columns:
        df_temp['cantidad'] = pd.to_numeric(df_temp['cantidad'], errors='coerce')
        
    if 'costo_lote_soles' in df_temp.columns:
        df_temp['costo_lote_soles'] = pd.to_numeric(df_temp['costo_lote_soles'], errors='coerce')
        
    df_temp['id_ejecucion'] = id_ejecucion
    
    df_insert = df_temp[target_cols + ['id_ejecucion']].copy()
    
    for col in df_insert.columns:
        if df_insert[col].dtype == object:
            df_insert[col] = df_insert[col].where(df_insert[col].notna(), None)
            
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            conn.execute(text("INSERT INTO ejecuciones (id_ejecucion, nombre_analisis, fecha_subida) VALUES (:id, :nom, :fec)"),
                         {"id": id_ejecucion, "nom": nombre_analisis, "fec": fecha_actual})
            
            if not df_insert.empty:
                df_insert.to_sql(
                    name='registro_eventos_inventario',
                    con=conn,
                    if_exists='append',
                    index=False,
                    method='multi',
                    chunksize=1000
                )
            trans.commit()
        except Exception as e:
            trans.rollback()
            raise e
            
    return id_ejecucion, nombre_analisis

def obtener_lista_analisis():
    res_list = [{"id_ejecucion": "LIVE", "nombre_analisis": "🟢 Datos en Vivo (ERP)", "fecha_subida": "En vivo"}]
    
    query = """
    SELECT id_ejecucion, nombre_analisis, fecha_subida 
    FROM ejecuciones 
    ORDER BY fecha_subida DESC
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query)).fetchall()
            for r in result:
                res_list.append({
                    "id_ejecucion": r[0], 
                    "nombre_analisis": r[1], 
                    "fecha_subida": r[2].isoformat() if r[2] else None
                })
    except Exception as e:
        print(f"Error al listar ejecuciones: {e}")
        
    return res_list

def obtener_datos_analisis(id_ejecucion):
    if id_ejecucion == "LIVE":
        query = """
        SELECT 
            e.id_caso AS "ID_Caso",
            a.nombre AS "Actividad",
            e.timestamp AS "Timestamp",
            em.nombre AS "Empleado",
            em.rol AS "Rol",
            em.turno AS "Turno",
            m.categoria AS "Categoria_Material",
            m.sku_descripcion AS "SKU_Descripcion",
            m.unidad_medida AS "Unidad_Medida",
            l.cantidad AS "Cantidad",
            p.nombre AS "Proveedor",
            e.estado_calidad AS "Estado_Calidad",
            u.nombre AS "Ubicacion_Fisica",
            l.costo_lote_soles AS "Costo_Lote_Soles",
            l.prioridad_produccion AS "Prioridad_Produccion",
            e.id_ejecucion AS "ID_Ejecucion"
        FROM eventos e
        LEFT JOIN lotes l ON e.id_caso = l.id_caso
        LEFT JOIN actividades a ON e.id_actividad = a.id_actividad
        LEFT JOIN empleados em ON e.id_empleado = em.id_empleado
        LEFT JOIN materiales m ON l.id_material = m.id_material
        LEFT JOIN proveedores p ON l.id_proveedor = p.id_proveedor
        LEFT JOIN ubicaciones u ON e.id_ubicacion = u.id_ubicacion
        WHERE e.id_ejecucion IS NULL
        """
        params = {}
    else:
        query = """
        SELECT 
            id_caso AS "ID_Caso",
            actividad AS "Actividad",
            timestamp AS "Timestamp",
            empleado AS "Empleado",
            rol AS "Rol",
            turno AS "Turno",
            categoria_material AS "Categoria_Material",
            sku_descripcion AS "SKU_Descripcion",
            unidad_medida AS "Unidad_Medida",
            cantidad AS "Cantidad",
            proveedor AS "Proveedor",
            estado_calidad AS "Estado_Calidad",
            ubicacion_fisica AS "Ubicacion_Fisica",
            costo_lote_soles AS "Costo_Lote_Soles",
            prioridad_produccion AS "Prioridad_Produccion",
            id_ejecucion AS "ID_Ejecucion"
        FROM registro_eventos_inventario
        WHERE id_ejecucion = :id
        """
        params = {"id": id_ejecucion}
        
    return pd.read_sql_query(text(query), engine, params=params)
