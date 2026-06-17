import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
import bcrypt

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

def inicializar_y_sembrar_catalogos():
    """
    Se asegura de que existan las tablas y si los catálogos maestros están vacíos,
    los siembra con valores predeterminados extraídos del conjunto de datos original
    para permitir operar de forma inmediata en el ERP.
    """
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS usuarios (
                usuario VARCHAR(50) PRIMARY KEY,
                password_hash TEXT NOT NULL,
                rol VARCHAR(20) NOT NULL
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
        conn.commit()

        acts = ["Recepción en Puerta", "Inspección de Calidad", "Registro en ERP", "Ubicación en Estante", "Despacho a Planta", "Devolución a Proveedor"]
        for act in acts:
            conn.execute(text("INSERT INTO actividades (nombre) VALUES (:nom) ON CONFLICT (nombre) DO NOTHING"), {"nom": act})

        provs = ["Curtiduría Trujillo SAC", "Herrajes Moda SAC", "Química Alemana SA", "Sintéticos y Textiles EIRL", "Suelas El Porvenir"]
        for prov in provs:
            conn.execute(text("INSERT INTO proveedores (nombre) VALUES (:nom) ON CONFLICT (nombre) DO NOTHING"), {"nom": prov})

        locs = ["Zona de Descarga", "Zona de Cuarentena (QA)", "Estantes A (Cueros)", "Estantes B (Suelas)", "Estantes C (Químicos)", "Estantes D (Generales)", "Zona de Despacho"]
        for loc in locs:
            conn.execute(text("INSERT INTO ubicaciones (nombre) VALUES (:nom) ON CONFLICT (nombre) DO NOTHING"), {"nom": loc})

        emps = [
            ("Luis Gomez", "Aux. Recepción", "Mañana (08:00-16:00)"),
            ("Juan Perez", "Aux. Recepción", "Tarde (16:00-00:00)"),
            ("Maria Rojas", "Inspector QA", "Mañana (08:00-16:00)"),
            ("Ana Torres", "Inspector QA", "Tarde (16:00-00:00)"),
            ("Rosa Silva", "Digitadora ERP", "Tarde (16:00-00:00)"),
            ("Miguel Paz", "Montacarguista", "Tarde (16:00-00:00)"),
            ("Carlos Ruiz", "Almacenero", "Mañana (08:00-16:00)")
        ]
        for name, role, shift in emps:
            conn.execute(text("""
                INSERT INTO empleados (nombre, rol, turno)
                VALUES (:nom, :rol, :tur) ON CONFLICT (nombre) DO NOTHING
            """), {"nom": name, "rol": role, "tur": shift})

        mats = [
            ("Hebilla Dorada 15mm", "Avíos/Herrajes", "Unidades"),
            ("Taco Aguja 9cm", "Suelas/Plantas", "Pares"),
            ("Caja Cartón Dama Standard", "Cajas", "Unidades"),
            ("Forro Sintético Beige", "Sintéticos", "Metros"),
            ("Pegamento PU (Poliuretano)", "Químicos/Pegamentos", "Galones"),
            ("Cuero Napa Negro", "Cueros", "Decímetros"),
            ("Cuero Charol Rojo", "Cueros", "Decímetros"),
            ("Planta Caucho T37", "Suelas/Plantas", "Pares")
        ]
        for sku, cat, uni in mats:
            conn.execute(text("""
                INSERT INTO materiales (sku_descripcion, categoria, unidad_medida)
                VALUES (:sku, :cat, :uni) ON CONFLICT (sku_descripcion) DO NOTHING
            """), {"sku": sku, "cat": cat, "uni": uni})

        conn.commit()

def verificar_login(nombre_usuario, password_intento):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT password_hash, rol FROM usuarios WHERE usuario = :u"), {"u": nombre_usuario}).fetchone()
        if result:
            hash_guardado = result[0].encode('utf-8')
            if bcrypt.checkpw(password_intento.encode('utf-8'), hash_guardado):
                return True, result[1]
    return False, None

def obtener_catalogos():
    with engine.connect() as conn:
        provs = [{"id": r[0], "nombre": r[1]} for r in conn.execute(text("SELECT id_proveedor, nombre FROM proveedores ORDER BY nombre")).fetchall()]
        mats = [{"id": r[0], "sku_descripcion": r[1], "categoria": r[2], "unidad_medida": r[3]} for r in conn.execute(text("SELECT id_material, sku_descripcion, categoria, unidad_medida FROM materiales ORDER BY sku_descripcion")).fetchall()]
        emps = [{"id": r[0], "nombre": r[1], "rol": r[2], "turno": r[3]} for r in conn.execute(text("SELECT id_empleado, nombre, rol, turno FROM empleados ORDER BY nombre")).fetchall()]
        locs = [{"id": r[0], "nombre": r[1]} for r in conn.execute(text("SELECT id_ubicacion, nombre FROM ubicaciones ORDER BY nombre")).fetchall()]
        acts = [{"id": r[0], "nombre": r[1]} for r in conn.execute(text("SELECT id_actividad, nombre FROM actividades ORDER BY nombre")).fetchall()]
        
        return {
            "proveedores": provs,
            "materiales": mats,
            "empleados": emps,
            "ubicaciones": locs,
            "actividades": acts
        }

def crear_lote(id_caso, id_material, cantidad, id_proveedor, costo_lote_soles, prioridad_produccion):
    with engine.connect() as conn:
        existing = conn.execute(text("SELECT id_caso FROM lotes WHERE id_caso = :id"), {"id": id_caso}).fetchone()
        if existing:
            return False, f"El lote con código '{id_caso}' ya existe."
            
        conn.execute(text("""
            INSERT INTO lotes (id_caso, id_material, cantidad, id_proveedor, costo_lote_soles, prioridad_produccion, id_ejecucion)
            VALUES (:id, :mat, :cant, :prov, :costo, :prio, NULL)
        """), {
            "id": id_caso, "mat": id_material, "cant": cantidad, "prov": id_proveedor,
            "costo": costo_lote_soles, "prio": prioridad_produccion
        })
        conn.commit()
    return True, f"Lote '{id_caso}' registrado correctamente."

def listar_lotes():
    query = """
    SELECT l.id_caso, l.cantidad, l.costo_lote_soles, l.prioridad_produccion,
           m.sku_descripcion, m.categoria, m.unidad_medida,
           p.nombre AS proveedor
    FROM lotes l
    JOIN materiales m ON l.id_material = m.id_material
    JOIN proveedores p ON l.id_proveedor = p.id_proveedor
    WHERE l.id_ejecucion IS NULL
    ORDER BY l.id_caso DESC
    """
    with engine.connect() as conn:
        result = conn.execute(text(query)).fetchall()
        return [{
            "id_caso": r[0], "cantidad": r[1], "costo_lote_soles": r[2], "prioridad_produccion": r[3],
            "sku_descripcion": r[4], "categoria": r[5], "unidad_medida": r[6], "proveedor": r[7]
        } for r in result]

def obtener_trazabilidad(id_caso):
    query = """
    SELECT e.id_evento, e.timestamp, e.estado_calidad,
           a.nombre AS actividad,
           em.nombre AS empleado, em.rol, em.turno,
           u.nombre AS ubicacion
    FROM eventos e
    JOIN actividades a ON e.id_actividad = a.id_actividad
    JOIN empleados em ON e.id_empleado = em.id_empleado
    LEFT JOIN ubicaciones u ON e.id_ubicacion = u.id_ubicacion
    WHERE e.id_caso = :id
    ORDER BY e.timestamp ASC
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"id": id_caso}).fetchall()
        return [{
            "id_evento": r[0], "timestamp": r[1].strftime('%d/%m/%Y %H:%M:%S'), "estado_calidad": r[2],
            "actividad": r[3], "empleado": r[4], "rol": r[5], "turno": r[6], "ubicacion": r[7] or 'N/A'
        } for r in result]

def validar_siguiente_evento(id_caso, id_actividad_propuesta):
    """
    Algoritmo de validación de secuencia lógica operativa:
    - Retorna (True, "") si el evento propuesto cumple la secuencia lógica.
    - Retorna (False, mensaje_error) si viola el flujo de trabajo.
    """
    with engine.connect() as conn:
        prop_act_name = conn.execute(text("SELECT nombre FROM actividades WHERE id_actividad = :id"), {"id": id_actividad_propuesta}).fetchone()
        if not prop_act_name:
            return False, "Actividad propuesta no válida."
        prop_act_name = prop_act_name[0]
        
        query = """
            SELECT a.nombre, e.estado_calidad 
            FROM eventos e
            JOIN actividades a ON e.id_actividad = a.id_actividad
            WHERE e.id_caso = :id
            ORDER BY e.timestamp DESC, e.id_evento DESC
        """
        registered = conn.execute(text(query), {"id": id_caso}).fetchall()
        
        if not registered:
            if prop_act_name == "Recepción en Puerta":
                return True, ""
            return False, "Secuencia incorrecta. El primer evento obligatorio debe ser 'Recepción en Puerta'."
            
        last_act = registered[0][0]
        
        if last_act == "Recepción en Puerta":
            if prop_act_name == "Inspección de Calidad":
                return True, ""
            return False, "Secuencia incorrecta. Después de 'Recepción en Puerta' debe registrarse 'Inspección de Calidad'."
            
        if last_act == "Inspección de Calidad":
            if prop_act_name == "Registro en ERP":
                return True, ""
            return False, "Secuencia incorrecta. Después de 'Inspección de Calidad' debe registrarse 'Registro en ERP'."
            
        if last_act == "Registro en ERP":
            qa_event = next((ev for ev in registered if ev[0] == "Inspección de Calidad"), None)
            qa_status = qa_event[1] if qa_event else "Aprobado"
            
            if qa_status == "Aprobado":
                if prop_act_name == "Ubicación en Estante":
                    return True, ""
                return False, "Secuencia incorrecta. Como el control de calidad fue 'Aprobado', la siguiente actividad debe ser 'Ubicación en Estante'."
            else:
                if prop_act_name == "Devolución a Proveedor":
                    return True, ""
                return False, "Secuencia incorrecta. Como el control de calidad fue 'Rechazado', la siguiente actividad debe ser 'Devolución a Proveedor'."
                
        if last_act == "Ubicación en Estante":
            if prop_act_name == "Despacho a Planta":
                return True, ""
            return False, "Secuencia incorrecta. Después de 'Ubicación en Estante' debe registrarse 'Despacho a Planta'."
            
        if last_act in ["Despacho a Planta", "Devolución a Proveedor"]:
            return False, f"El lote ya ha finalizado su ciclo operativo (Último evento: '{last_act}'). No se pueden registrar más eventos."
            
        return False, "Flujo operativo desconocido."

def registrar_evento(id_caso, id_actividad, timestamp_str, id_empleado, estado_calidad, id_ubicacion):

    valida, msg = validar_siguiente_evento(id_caso, id_actividad)
    if not valida:
        return False, msg
        
    ts = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M") if "T" in timestamp_str else datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO eventos (id_caso, id_actividad, timestamp, id_empleado, estado_calidad, id_ubicacion, id_ejecucion)
            VALUES (:caso, :act, :ts, :emp, :cal, :loc, NULL)
        """), {
            "caso": id_caso, "act": id_actividad, "ts": ts, "emp": id_empleado,
            "cal": estado_calidad, "loc": id_ubicacion
        })
        conn.commit()
    return True, "Evento registrado con éxito en el lote."

def simular_inyectar_datos(cantidad_eventos_aprox=1000):
    import random
    from datetime import timedelta
    
    with engine.connect() as conn:
        materiales = conn.execute(text("SELECT id_material, sku_descripcion, categoria FROM materiales")).fetchall()
        proveedores = conn.execute(text("SELECT id_proveedor, nombre FROM proveedores")).fetchall()
        empleados = conn.execute(text("SELECT id_empleado, nombre, rol FROM empleados")).fetchall()
        ubicaciones = conn.execute(text("SELECT id_ubicacion, nombre FROM ubicaciones")).fetchall()
        actividades = conn.execute(text("SELECT id_actividad, nombre FROM actividades")).fetchall()
        
        if not materiales or not proveedores or not empleados or not ubicaciones or not actividades:
            return False, "Los catálogos de base de datos están vacíos. Asegúrate de sembrarlos primero."
            
        act_map = {r[1]: r[0] for r in actividades}
        loc_map = {r[1]: r[0] for r in ubicaciones}
        
        emp_by_role = {}
        for r in empleados:
            role = r[2]
            if role not in emp_by_role:
                emp_by_role[role] = []
            emp_by_role[role].append(r[0])
            
        all_emp_ids = [r[0] for r in empleados]
        def get_random_emp(role_name):
            ids = emp_by_role.get(role_name, [])
            if not ids:
                return random.choice(all_emp_ids)
            return random.choice(ids)
            
        existing_sims = conn.execute(text("SELECT id_caso FROM lotes WHERE id_caso LIKE 'SIM-%'")).fetchall()
        sim_nums = []
        for r in existing_sims:
            try:
                sim_nums.append(int(r[0].split('-')[1]))
            except Exception:
                pass
        start_counter = max(sim_nums) + 1 if sim_nums else 1000
        
        lote_dicts = []
        event_dicts = []
        
        num_cases = int(cantidad_eventos_aprox / 5.5)
        current_time = datetime.now()
        
        for i in range(num_cases):
            case_num = start_counter + i
            id_caso = f"SIM-{case_num}"
            
            mat = random.choice(materiales)
            prov = random.choice(proveedores)
            
            priorities = ["Normal", "Alta", "Urgente"]
            prio = random.choices(priorities, weights=[0.6, 0.3, 0.1])[0]
            qty = random.randint(100, 2500)
            cost = round(qty * random.uniform(1.5, 6.0), 2)
            
            lote_dicts.append({
                "id_caso": id_caso,
                "id_material": mat[0],
                "cantidad": qty,
                "id_proveedor": prov[0],
                "costo_lote_soles": cost,
                "prioridad_produccion": prio
            })
            
            qa_status = random.choices(["Aprobado", "Rechazado"], weights=[0.8, 0.2])[0]
            base_days = random.randint(10, 90)
            ts = current_time - timedelta(days=base_days) + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
            
            event_dicts.append({
                "id_caso": id_caso,
                "id_actividad": act_map.get("Recepción en Puerta"),
                "timestamp": ts,
                "id_empleado": get_random_emp("Aux. Recepción"),
                "estado_calidad": "Aprobado",
                "id_ubicacion": loc_map.get("Zona de Descarga")
            })
            
            ts += timedelta(hours=random.randint(2, 24), minutes=random.randint(0, 59))
            event_dicts.append({
                "id_caso": id_caso,
                "id_actividad": act_map.get("Inspección de Calidad"),
                "timestamp": ts,
                "id_empleado": get_random_emp("Inspector QA"),
                "estado_calidad": qa_status,
                "id_ubicacion": loc_map.get("Zona de Cuarentena (QA)")
            })
            
            ts += timedelta(hours=random.randint(1, 12), minutes=random.randint(0, 59))
            event_dicts.append({
                "id_caso": id_caso,
                "id_actividad": act_map.get("Registro en ERP"),
                "timestamp": ts,
                "id_empleado": get_random_emp("Digitadora ERP"),
                "estado_calidad": qa_status,
                "id_ubicacion": loc_map.get("Zona de Cuarentena (QA)")
            })
            
            ts += timedelta(hours=random.randint(4, 36), minutes=random.randint(0, 59))
            if qa_status == "Aprobado":
                cat = mat[2].lower()
                if "cuero" in cat:
                    loc_name = "Estantes A (Cueros)"
                elif "suela" in cat:
                    loc_name = "Estantes B (Suelas)"
                elif "químico" in cat or "quimico" in cat:
                    loc_name = "Estantes C (Químicos)"
                else:
                    loc_name = "Estantes D (Generales)"
                    
                event_dicts.append({
                    "id_caso": id_caso,
                    "id_actividad": act_map.get("Ubicación en Estante"),
                    "timestamp": ts,
                    "id_empleado": get_random_emp("Montacarguista"),
                    "estado_calidad": "Aprobado",
                    "id_ubicacion": loc_map.get(loc_name)
                })
                
                ts += timedelta(hours=random.randint(12, 72), minutes=random.randint(0, 59))
                event_dicts.append({
                    "id_caso": id_caso,
                    "id_actividad": act_map.get("Despacho a Planta"),
                    "timestamp": ts,
                    "id_empleado": get_random_emp("Almacenero"),
                    "estado_calidad": "Aprobado",
                    "id_ubicacion": loc_map.get("Zona de Despacho")
                })
            else:
                event_dicts.append({
                    "id_caso": id_caso,
                    "id_actividad": act_map.get("Devolución a Proveedor"),
                    "timestamp": ts,
                    "id_empleado": get_random_emp("Almacenero"),
                    "estado_calidad": "Rechazado",
                    "id_ubicacion": loc_map.get("Zona de Descarga")
                })
                
        conn.execute(text("""
            INSERT INTO lotes (id_caso, id_material, cantidad, id_proveedor, costo_lote_soles, prioridad_produccion, id_ejecucion)
            VALUES (:id_caso, :id_material, :cantidad, :id_proveedor, :costo_lote_soles, :prioridad_produccion, NULL)
        """), lote_dicts)
        
        conn.execute(text("""
            INSERT INTO eventos (id_caso, id_actividad, timestamp, id_empleado, estado_calidad, id_ubicacion, id_ejecucion)
            VALUES (:id_caso, :id_actividad, :timestamp, :id_empleado, :estado_calidad, :id_ubicacion, NULL)
        """), event_dicts)
        
        conn.commit()
        
    return True, f"Se han inyectado {len(lote_dicts)} lotes y {len(event_dicts)} eventos de simulación correctamente."
