import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from core.ciclo import FLUIDOS, calcular_ciclo, generar_campana
from CoolProp.CoolProp import PropsSI

app = FastAPI(title="Calculadora ORC")


class CalculoRequest(BaseModel):
    fluido: str
    p_entrada: float
    t_entrada: float
    p_salida: float
    eficiencia_turbina: float
    eficiencia_bomba: float
    gasto_masico: float


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/diagrama/{fluido}")
async def diagrama(fluido: str):
    if fluido not in FLUIDOS:
        return JSONResponse(
            status_code=400,
            content={"detail": [{"loc": ["path", "fluido"], "msg": f"Fluido no válido. Opciones: {', '.join(FLUIDOS)}"}]},
        )
    return generar_campana(fluido)


@app.post("/calcular")
async def calcular(req: CalculoRequest):
    errors = []

    if req.fluido not in FLUIDOS:
        errors.append({"loc": ["body", "fluido"], "msg": f"Fluido no válido. Opciones: {', '.join(FLUIDOS)}"})

    if req.p_entrada <= 0:
        errors.append({"loc": ["body", "p_entrada"], "msg": "La presión de entrada debe ser mayor a 0"})

    if req.p_salida <= 0:
        errors.append({"loc": ["body", "p_salida"], "msg": "La presión de salida debe ser mayor a 0"})

    if req.p_entrada > 0 and req.p_salida > 0 and req.p_entrada <= req.p_salida:
        errors.append({"loc": ["body", "p_entrada"], "msg": "La presión de entrada debe ser mayor que la presión de salida"})

    if req.eficiencia_turbina <= 0 or req.eficiencia_turbina > 100:
        errors.append({"loc": ["body", "eficiencia_turbina"], "msg": "La eficiencia de la turbina debe estar entre 0 y 100%"})

    if req.eficiencia_bomba <= 0 or req.eficiencia_bomba > 100:
        errors.append({"loc": ["body", "eficiencia_bomba"], "msg": "La eficiencia de la bomba debe estar entre 0 y 100%"})

    if req.gasto_masico <= 0:
        errors.append({"loc": ["body", "gasto_masico"], "msg": "El gasto másico debe ser mayor a 0"})

    if errors:
        return JSONResponse(status_code=422, content={"detail": errors})

    # Validate state 1 is superheated or saturated vapor
    try:
        P1 = req.p_entrada * 1000.0  # kPa to Pa
        T1 = req.t_entrada + 273.15  # °C to K
        Tsat = PropsSI("T", "P", P1, "Q", 0, req.fluido)
        Tcrit = PropsSI("Tcrit", req.fluido)

        if T1 < Tsat:
            errors.append({
                "loc": ["body", "t_entrada"],
                "msg": f"El estado en entrada a turbina no es vapor. T de saturación a {req.p_entrada} kPa es {Tsat - 273.15:.1f} °C. Ingrese una temperatura mayor o igual."
            })

        if T1 > Tcrit:
            errors.append({
                "loc": ["body", "t_entrada"],
                "msg": f"La temperatura de entrada ({req.t_entrada} °C) supera la temperatura crítica del {req.fluido} ({Tcrit - 273.15:.1f} °C). Reduzca la temperatura."
            })
    except Exception as e:
        errors.append({"loc": ["body", "t_entrada"], "msg": f"Error calculando propiedades del fluido: {str(e)}"})

    if errors:
        return JSONResponse(status_code=422, content={"detail": errors})

    # Calculate cycle
    try:
        resultado = calcular_ciclo(
            fluido=req.fluido,
            p_entrada_kpa=req.p_entrada,
            t_entrada_c=req.t_entrada,
            p_salida_kpa=req.p_salida,
            eficiencia_turbina_pct=req.eficiencia_turbina,
            eficiencia_bomba_pct=req.eficiencia_bomba,
            gasto_masico=req.gasto_masico,
        )
        return resultado
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": [{"loc": ["body", "general"], "msg": f"Error en cálculo del ciclo: {str(e)}"}]},
        )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
