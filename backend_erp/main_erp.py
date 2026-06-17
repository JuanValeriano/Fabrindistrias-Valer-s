from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

from backend_erp import database_erp

app = FastAPI(title="VALERS - ERP System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    database_erp.inicializar_y_sembrar_catalogos()

class LoginRequest(BaseModel):
    usuario: str
    password: str

class LoteCreateRequest(BaseModel):
    id_caso: str
    id_material: int
    cantidad: int
    id_proveedor: int
    costo_lote_soles: float
    prioridad_produccion: str

class EventoCreateRequest(BaseModel):
    id_caso: str
    id_actividad: int
    timestamp: str
    id_empleado: int
    estado_calidad: str
    id_ubicacion: Optional[int] = None


@app.post("/api/erp/auth/login")
def login(req: LoginRequest):
    exito, rol = database_erp.verificar_login(req.usuario, req.password)
    if exito:
        return {"success": True, "usuario": req.usuario, "rol": rol}
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")


@app.get("/api/erp/catalogos")
def get_catalogos():
    return database_erp.obtener_catalogos()


@app.post("/api/erp/lotes")
def create_lote(req: LoteCreateRequest):
    if not req.id_caso or req.cantidad <= 0 or req.costo_lote_soles < 0:
        raise HTTPException(status_code=400, detail="Datos del lote inválidos.")
        
    exito, mensaje = database_erp.crear_lote(
        id_caso=req.id_caso.strip(),
        id_material=req.id_material,
        cantidad=req.cantidad,
        id_proveedor=req.id_proveedor,
        costo_lote_soles=req.costo_lote_soles,
        prioridad_produccion=req.prioridad_produccion
    )
    if not exito:
        raise HTTPException(status_code=400, detail=mensaje)
    return {"success": True, "message": mensaje}

@app.get("/api/erp/lotes")
def get_lotes():
    return database_erp.listar_lotes()

@app.get("/api/erp/lotes/{id_caso}/trazabilidad")
def get_trazabilidad(id_caso: str):
    return database_erp.obtener_trazabilidad(id_caso)


@app.post("/api/erp/eventos")
def create_evento(req: EventoCreateRequest):
    exito, mensaje = database_erp.registrar_evento(
        id_caso=req.id_caso,
        id_actividad=req.id_actividad,
        timestamp_str=req.timestamp,
        id_empleado=req.id_empleado,
        estado_calidad=req.estado_calidad,
        id_ubicacion=req.id_ubicacion
    )
    if not exito:
        raise HTTPException(status_code=400, detail=mensaje)
    return {"success": True, "message": mensaje}

@app.post("/api/erp/simulation/inject")
def inject_simulation_data():
    exito, mensaje = database_erp.simular_inyectar_datos(cantidad_eventos_aprox=1000)
    if not exito:
        raise HTTPException(status_code=400, detail=mensaje)
    return {"success": True, "message": mensaje}
