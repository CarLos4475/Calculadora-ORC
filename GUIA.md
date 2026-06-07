# ¿Cómo funciona esto? — Guía en cristiano

> Una explicación del programa **para quien NO sabe programar**. Si alguna vez te preguntaste "¿qué hace cada archivo y por qué?", esta guía es para ti.

---

## La idea general (en 30 segundos)

El programa es una **calculadora de potencia** para un tipo de máquina térmica llamada **Ciclo Rankine Orgánico** (ORC, por sus siglas en inglés). Básicamente, estas máquinas convierten calor en electricidad usando un refrigerante en vez de agua (como las plantas de vapor convencionales).

El usuario mete unos números por una página web, el servidor hace cuentas con propiedades de fluidos reales, y devuelve cuánto poder genera el ciclo, más un dibujito del proceso.

**Tres partes grandes:**
1. **Lo que ves** → la página web (HTML + colores + gráfica)
2. **El cerebro** → el servidor en Python que hace las cuentas
3. **La biblioteca mágica** → CoolProp, que sabe TODO sobre los fluidos

---

## El stack tecnológico (qué usamos y para qué)

| Tecnología | ¿Qué es? | ¿Para qué la usamos? |
|------------|----------|---------------------|
| **Python 3.11** | Un lenguaje de programación | El lenguaje en el que está escrito todo el backend |
| **FastAPI** | Un framework para crear APIs web | Para recibir las peticiones del navegador y devolver respuestas |
| **Uvicorn** | Un servidor web para Python | Para que FastAPI "escuche" las peticiones HTTP |
| **CoolProp** | Una biblioteca termodinámica | Para obtener presión, temperatura, entalpía, entropía de los fluidos |
| **NumPy** | Una biblioteca de matemáticas | Para generar los puntos de la campana de saturación |
| **Pydantic** | Una biblioteca de validación | Para verificar que los datos que llegan del frontend tengan sentido |
| **HTML + CSS + JS** | El lenguaje de las páginas web | Para la interfaz que ve el usuario |
| **Tailwind CSS** | Un framework de estilos | Para que se vea bonito sin escribir mil líneas de CSS |
| **Plotly.js** | Una biblioteca de gráficas | Para dibujar el diagrama T-s interactivo |
| **Render** | Una plataforma de hosting | Para que la app esté en internet y cualquiera pueda usarla |

---

## Las líneas de código (cuánto tiene cada archivo)

| Archivo | Líneas | ¿Qué hace? |
|---------|:------:|-------------|
| `main.py` | **114** | Recibe peticiones, valida, llama a ciclo.py y devuelve JSON |
| `core/ciclo.py` | **235** | Hace todas las cuentas termodinámicas |
| `templates/index.html` | **595** | Toda la página web (estructura + estilo + lógica JS) |
| `requirements.txt` | **5** | Lista de paquetes que hay que instalar |
| `render.yaml` | **9** | Instrucciones para que Render arme el servidor |
| `runtime.txt` | **1** | Dice qué versión de Python usar |
| `README.md` | **317** | La documentación "seria" del proyecto |
| `GUIA.md` | **este** | Esta guía en lenguaje humano |

**Total de código del backend:** ~349 líneas de Python
**Total del frontend:** 595 líneas (todo en un solo HTML)

---

## ¿Cómo se conecta todo? (el flujo de datos)

Imagínate que el programa es un restaurante:

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   EL CLIENTE    │       │    EL MESERO    │       │     EL COCINERO │
│   (navegador)   │──────▶│   (main.py)     │──────▶│   (ciclo.py)    │
│                 │       │                 │       │                 │
│ Llena el        │  JSON │ Recibe la       │ Llama │ Hace las        │
│ formulario      │◀──────│ orden, valida   │◀──────│ cuentas         │
│ y le da CALCULAR│ Datos │ y la pasa       │ Datos │ con CoolProp    │
└─────────────────┘       └─────────────────┘       └─────────────────┘
       ▲                                                     │
       │                                                     │
       │                                                     ▼
       │                                             ┌─────────────────┐
       └────────────── Tabla + Gráfica ──────────────│  CoolProp       │
                                                     │  (la biblioteca │
                                                     │  de fluidos)    │
                                                     └─────────────────┘
```

### Paso a paso, lo que pasa cuando le das "CALCULAR":

1. **El usuario** llena el formulario en el navegador (fluido, presiones, temperaturas, eficiencias, gasto másico).

2. **JavaScript** (el cerebro de la página) agarra esos números, los mete en un JSON y los manda al servidor con un `fetch()`.

3. **FastAPI** (en `main.py`) recibe el JSON, lo convierte a un objeto de Pydantic y empieza a validar:
   - ¿El fluido es uno de los 3 permitidos?
   - ¿La presión de entrada es mayor que la de salida?
   - ¿Las eficiencias están entre 0 y 100?
   - ¿La temperatura corresponde a vapor (no a líquido)?
   - Si algo está mal, devuelve un error 422 con mensajes específicos.

4. **Si todo está bien**, `main.py` llama a `calcular_ciclo()` de `ciclo.py` y le pasa los datos.

5. **`ciclo.py`** hace su trabajo:
   - Le pregunta a CoolProp: "¿Cuánto vale h y s para R245fa a 500 kPa y 180°C?"
   - CoolProp responde al instante con valores exactos.
   - Con esos valores calcula los 6 estados y las 3 potencias.

6. **`main.py`** recibe el resultado y lo devuelve como JSON al navegador.

7. **JavaScript** toma ese JSON, llena la tabla de resultados, pinta los números de potencia y dibuja el diagrama T-s con Plotly.

8. **Tú ves** la tabla con los 6 estados, la potencia neta en grande, y la gráfica con la campana, los puntitos y las líneas.

---

## El ciclo ORC explicado sin fórmulas raras

Un ORC es como una caldera que hierve agua, pero en vez de agua usa un refrigerante. Tiene 4 pasos:

```
  CALOR ENTRA              TRABAJO SALE              CALOR SALE
       │                         │                         │
       ▼                         │                         ▼
   ┌────────┐  VAPOR  ┌──────────┴──┐  GASES  ┌──────────────┐
   │EVAPORA-│────────▶│  TURBINA    │────────▶│  CONDENSADOR │
   │DOR     │ Caliente│ (genera elec)│ Fríos  │  (líquido)   │
   └────────┘         └─────────────┘         └──────┬───────┘
       ▲                                            │
       │             TRABAJO ENTRA                  │
       │                 │                          │
       │          ┌──────┴───────┐                  │
       └──────────│    BOMBA     │◀─────────────────┘
       LÍQUIDO    │  (empuja el  │  LÍQUIDO FRÍO
       a presión  │   fluido)    │
                  └──────────────┘
```

### Los 4 procesos:

1. **Bomba (estado 3 → 4)**: Toma el líquido frío que sale del condensador y lo empuja para que tenga alta presión. Consume un poquito de electricidad.

2. **Evaporador (estado 4 → 1)**: Ese líquido a alta presión se calienta (con calor de la fuente, por ejemplo geotérmica o solar) hasta que se vuelve vapor sobrecalentado. Aquí es donde entra calor al sistema.

3. **Turbina (estado 1 → 2)**: El vapor a alta presión pasa por una turbina que gira y genera electricidad. El vapor sale con menos presión y temperatura. Aquí sale trabajo útil.

4. **Condensador (estado 2 → 3)**: El vapor "gastado" se enfría (con agua o aire) hasta volverse líquido de nuevo, listo para repetir el ciclo. Aquí sale calor del sistema.

### ¿Qué calcula el programa?

La **potencia neta** = lo que genera la turbina − lo que consume la bomba. Si la turbina genera 31 kW y la bomba consume 0.4 kW, la potencia neta son **30.6 kW**.

---

## Los 6 estados termodinámicos (lo que ves en la tabla)

| Estado | Qué es | Cómo se calcula |
|--------|--------|-----------------|
| **1** | Vapor caliente que entra a la turbina | Lo mete el usuario (P y T) |
| **2s** | Cómo saldría SI la turbina fuera perfecta | Se mantiene la entropía: s₂s = s₁ |
| **2** | Cómo SALE en la realidad | h₂ = h₁ − eficiencia × (h₁ − h₂s) |
| **3** | Líquido frío que sale del condensador | x = 0 (100% líquido) a baja presión |
| **4s** | Cómo saldría SI la bomba fuera perfecta | s₄s = s₃ a alta presión |
| **4** | Cómo SALE en la realidad | h₄ = h₃ + (h₄s − h₃) / eficiencia |

Los puntos con "s" son los **teóricos** (máquinas perfectas) y los demás son los **reales** (con pérdidas).

---

## El diagrama T-s (la gráfica bonita)

En el eje horizontal va la **entropía** (s, en kJ/kg·K) y en el vertical la **temperatura** (T, en °C). Es el "mapa" del ciclo.

```
   T (°C)
    │         ╱‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾╲
    │        ╱   CAMPANA DE           ╲
    │       ╱    SATURACIÓN            ╲
    │      │                            │
    │      │  1 ●─────────────● 2s       │
    │      │   ╲              ╲         │
    │      │    ╲  (real)      ╲        │
    │      │     ● 2            ╲       │
    │      │      ╲              ● 2    │
    │      │       ╲            ╱       │
    │      │        ● 3────────╱        │
    │      │         │                  │
    │      │         │ (condensación)   │
    │      │         ● 3                │
    │      │         │                  │
    │      │         ● 4s (teórica)    │
    │      │          ╲                │
    │      │           ● 4 (real)      │
    │      │           │                │
    │      │           │ (evaporación)  │
    │      │            ╲               │
    │      │             ● 1            │
    │       ╲                           ╱
    │        ╲_________________________╱
    └──────────────────────────────────── s (kJ/kg·K)
```

**Lo que se dibuja:**
- La **campana de saturación** (el domblito ese del medio): delimita dónde existe el fluido como líquido, como vapor, o como mezcla de ambos.
- Los **6 puntos** con sus etiquetas (1, 2s, 2, 3, 4s, 4)
- Las **líneas punteadas verdes** son los procesos ideales (1→2s, 3→4s)
- Las **líneas rojas/azules** son los procesos reales (1→2, 3→4)
- Las **líneas naranjas/cyan** son evaporación y condensación (a presión constante)

---

## Las validaciones (los "guardianes" del programa)

Antes de hacer cualquier cálculo, el servidor revisa que los datos tengan sentido. Si algo está mal, NO calcula y devuelve un mensaje claro:

| Si pones... | El programa dice... |
|-------------|---------------------|
| Temperatura de entrada menor a la de saturación | "El estado en entrada a turbina no es vapor. T de saturación a X kPa es Y °C" |
| Temperatura mayor a la crítica del fluido | "La temperatura de entrada (X °C) supera la temperatura crítica del fluido (Y °C)" |
| Presión de entrada menor o igual a la de salida | "La presión de entrada debe ser mayor que la presión de salida" |
| Eficiencia de 150% | "La eficiencia debe estar entre 0 y 100%" |
| Gasto másico negativo o cero | "El gasto másico debe ser mayor a 0" |
| Un fluido que no existe | "Fluido no válido. Opciones: R245fa, R134a, R1233zd(E)" |

Cada error se muestra en rojo justo abajo del campo que tiene el problema, así el usuario sabe exactamente qué corregir.

---

## ¿Y cómo se pone en internet?

El proyecto usa **Render**, que es como un "alojamiento" gratuito para aplicaciones web.

1. El código está en **GitHub** (el repo `CarLos4475/Calculadora-ORC`).
2. El archivo `render.yaml` le dice a Render: "instala estas dependencias, arranca este comando, expón esto en internet".
3. Cada vez que subimos cambios a GitHub, Render detecta el cambio y vuelve a desplegar automáticamente.
4. La app queda en una URL tipo `https://calculadora-orc-xxxx.onrender.com`.

El plan gratuito de Render "duerme" el servidor tras 15 minutos sin uso (para no gastar recursos), así que el primer request después de un rato tarda unos 30 segundos. Los siguientes son instantáneos.

---

## Resumen en una frase

> Es una calculadora web donde metes condiciones de operación, Python + CoolProp hacen los cálculos termodinámicos del ciclo, y el navegador te muestra la potencia generada más una gráfica T-s interactiva, todo validado y desplegado en internet.
