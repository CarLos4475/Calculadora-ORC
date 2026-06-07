# Calculadora de Ciclo Rankine Orgánico (ORC)

Aplicación web para calcular automáticamente la **potencia neta** generada en un Ciclo Rankine Orgánico (ORC), con diagrama T-s interactivo y validación de datos.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)
![CoolProp](https://img.shields.io/badge/CoolProp-6.6+-orange)
![License](https://img.shields.io/badge/License-MIT-green)

> https://orc-calculator.onrender.com/

---

## Tabla de contenidos

- [Descripción](#descripción)
- [Características](#características)
- [Tecnologías](#tecnologías)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Instalación local](#instalación-local)
- [Uso](#uso)
- [Modelo termodinámico](#modelo-termodinámico)
- [API](#api)
- [Validaciones](#validaciones)
- [Deploy en Render](#deploy-en-render)
- [Autores](#autores)

---

## Descripción

Esta aplicación implementa el cálculo del Ciclo Rankine Orgánico bajo las siguientes hipótesis:

- Estado estacionario
- Turbina y bomba adiabáticas
- Cambios de energía cinética y potencial despreciables
- Sin caídas de presión en evaporador, condensador ni tuberías
- Salida del condensador como líquido saturado (x = 0)
- Entrada a la turbina como vapor sobrecalentado o saturado seco
- Sin cálculo de eficiencia térmica (solo potencia neta)

El usuario ingresa las condiciones de operación y la herramienta devuelve la potencia neta, los seis estados termodinámicos y un diagrama T-s interactivo con la campana de saturación, los estados teóricos (isentrópicos) y reales, y todas las trayectorias del ciclo.

---

## Características

- **3 fluidos de trabajo** disponibles: R245fa, R134a, R1233zd(E)
- **Cálculo de los 6 estados termodinámicos** del ciclo
- **Diagrama T-s interactivo** con:
  - Campana de saturación
  - Estados teóricos (1, 2s, 3, 4s) y reales (2, 4)
  - Trayectorias teóricas y reales
  - Líneas de evaporación (4→1) y condensación (2→3)
- **Validación de datos de entrada** con mensajes específicos por campo
- **Interfaz web responsive** con Tailwind CSS y Plotly.js
- **API REST** documentada con FastAPI
- **Cálculo de propiedades termodinámicas** mediante CoolProp

---

## Tecnologías

| Capa | Tecnología |
|------|------------|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Cálculo termodinámico | CoolProp 7.x |
| Frontend | HTML5, Tailwind CSS (CDN), Plotly.js (CDN), Vanilla JS |
| Deploy | Render (Blueprint con render.yaml) |

---

## Estructura del proyecto

```
orc_calculator/
├── main.py                  # Aplicación FastAPI y endpoints
├── render.yaml              # Configuración de deploy en Render
├── runtime.txt              # Versión de Python (3.11.0)
├── requirements.txt         # Dependencias
├── .gitignore
├── README.md                # Este archivo
├── core/
│   ├── __init__.py
│   └── ciclo.py             # Lógica termodinámica (estados, potencias, campana)
└── templates/
    └── index.html           # Interfaz web (HTML + CSS + JS)
```

---

## Instalación local

### Requisitos previos

- Python 3.11 o superior
- pip

### Pasos

```powershell
# Clonar el repositorio
git clone https://github.com/CarLos4475/Calculadora-ORC.git
cd Calculadora-ORC

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el servidor
py main.py
```

El servidor quedará escuchando en `http://localhost:8000`.

Alternativa con uvicorn directamente (con auto-reload):

```powershell
py -m uvicorn main:app --reload
```

---

## Uso

1. Abrir el navegador en `http://localhost:8000`
2. Seleccionar el **fluido de trabajo** del menú desplegable
3. Ingresar los **parámetros de operación**:
   - Presión de entrada a la turbina [kPa]
   - Temperatura de entrada a la turbina [°C]
   - Presión de salida de la turbina [kPa]
   - Eficiencia isentrópica de la turbina [%] (slider o input)
   - Eficiencia isentrópica de la bomba [%] (slider o input)
   - Gasto másico del fluido [kg/s]
4. Presionar **CALCULAR**
5. Revisar:
   - Tabla de los 6 estados termodinámicos
   - Potencia neta, de turbina y de bomba
   - Diagrama T-s con todos los estados y trayectorias

### Ejemplo de cálculo (R245fa)

| Parámetro | Valor |
|-----------|-------|
| Presión de entrada | 500 kPa |
| Temperatura de entrada | 180 °C |
| Presión de salida | 200 kPa |
| η_turbina | 85 % |
| η_bomba | 75 % |
| Gasto másico | 1.5 kg/s |

**Resultado típico:**

| Cantidad | Valor |
|----------|-------|
| Potencia de turbina | 31.10 kW |
| Potencia de bomba | 0.43 kW |
| **Potencia neta** | **30.66 kW** |

---

## Modelo termodinámico

### Estados del ciclo

| Estado | Descripción | Cómo se obtiene |
|--------|-------------|-----------------|
| **1** | Entrada a la turbina (vapor sobrecalentado/saturado) | Ingresado por el usuario: P₁, T₁ |
| **2s** | Salida isentrópica de la turbina | P₂, s₂s = s₁ |
| **2** | Salida real de la turbina | h₂ = h₁ − η_t·(h₁ − h₂s) |
| **3** | Salida del condensador (líquido saturado) | P₃ = P₂, x = 0 |
| **4s** | Salida isentrópica de la bomba | P₄ = P₁, s₄s = s₃ |
| **4** | Salida real de la bomba | h₄ = h₃ + (h₄s − h₃) / η_p |

### Ecuaciones de potencia

```
W_turbina = ṁ · (h₁ − h₂)         [kW]
W_bomba   = ṁ · (h₄ − h₃)         [kW]
W_neta    = W_turbina − W_bomba    [kW]
```

### Diagrama T-s

El diagrama incluye:
- **Campana de saturación** (líquido y vapor saturados, calculada con CoolProp)
- **Estados teóricos (isentrópicos)**: 1, 2s, 4s (en verde)
- **Estados reales**: 2, 4 (en rojo y azul)
- **Trayectorias teóricas** (líneas discontinuas): 1→2s, 3→4s
- **Trayectorias reales** (líneas continuas): 1→2, 3→4
- **Procesos a presión constante**: 2→3 (condensación), 4→1 (evaporación)

---

## API

### `GET /`

Sirve la interfaz HTML de la calculadora.

### `GET /diagrama/{fluido}`

Devuelve los datos de la campana de saturación para un fluido.

**Parámetros:**
- `fluido` (path): uno de `R245fa`, `R134a`, `R1233zd(E)`

**Respuesta 200 (ejemplo):**
```json
{
  "saturacion": {
    "liquido": { "T": [-102.1, 55.4, ...], "s": [0.45, 1.25, ...] },
    "vapor":   { "T": [-102.1, 55.4, ...], "s": [1.94, 1.77, ...] }
  }
}
```

### `POST /calcular`

Calcula el ciclo completo y devuelve los estados y potencias.

**Body (JSON):**
```json
{
  "fluido": "R245fa",
  "p_entrada": 500,
  "t_entrada": 180,
  "p_salida": 200,
  "eficiencia_turbina": 85,
  "eficiencia_bomba": 75,
  "gasto_masico": 1.5
}
```

**Respuesta 200 (ejemplo):**
```json
{
  "estados": {
    "1":  { "P": 0.5,    "T": 180.0,  "h": 578.49, "s": 2.098,  "x": null },
    "2s": { "P": 0.2,    "T": 155.95, "h": 554.1,  "s": 2.098,  "x": null },
    "2":  { "P": 0.2,    "T": 159.27, "h": 557.76, "s": 2.1065, "x": null },
    "3":  { "P": 0.2,    "T": 33.31,  "h": 244.03, "s": 1.1519, "x": 0.0  },
    "4s": { "P": 0.5,    "T": 33.42,  "h": 244.25, "s": 1.1519, "x": null },
    "4":  { "P": 0.5,    "T": 33.47,  "h": 244.32, "s": 1.1521, "x": null }
  },
  "potencia_turbina": 31.1,
  "potencia_bomba": 0.43,
  "potencia_neta": 30.66
}
```

**Respuesta 422 (validación):**
```json
{
  "detail": [
    { "loc": ["body", "t_entrada"], "msg": "El estado en entrada a turbina no es vapor..." }
  ]
}
```

---

## Validaciones

La aplicación rechaza y muestra mensajes específicos en los siguientes casos:

| Campo | Regla |
|-------|-------|
| `fluido` | Debe ser uno de: R245fa, R134a, R1233zd(E) |
| `p_entrada` | Mayor a 0 y **mayor** que `p_salida` |
| `p_salida` | Mayor a 0 |
| `t_entrada` | T ≥ T_saturación(P_entrada) y T < T_crit del fluido |
| `eficiencia_turbina` | Entre 0 y 100 % |
| `eficiencia_bomba` | Entre 0 y 100 % |
| `gasto_masico` | Mayor a 0 |

---

## Deploy en Render

El proyecto está configurado para deploy automático en [Render](https://render.com) usando **Blueprint** (archivo `render.yaml`).

---

## Dependencias

```
fastapi>=0.115.0
uvicorn>=0.34.0
CoolProp>=6.6.0
numpy>=1.26.0
pydantic>=2.0.0
```

---

## Licencia

MIT
