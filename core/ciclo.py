from CoolProp.CoolProp import PropsSI
import numpy as np

FLUIDOS = ["R245fa", "R134a", "R1233zd(E)"]


def _kpa_to_pa(kpa: float) -> float:
    return kpa * 1000.0


def _pa_to_mpa(pa: float) -> float:
    return pa / 1e6


def _k_to_c(k: float) -> float:
    return k - 273.15


def _c_to_k(c: float) -> float:
    return c + 273.15


def _j_to_kj(j: float) -> float:
    return j / 1000.0


def _get_quality(P: float, T: float, fluido: str) -> float | None:
    """Return vapor quality (0-1) or None if subcooled/superheated."""
    try:
        Tsat = PropsSI("T", "P", P, "Q", 0, fluido)
        if T < Tsat:
            return None  # subcooled liquid
        Tcrit = PropsSI("Tcrit", fluido)
        if T > Tcrit:
            return None  # supercritical
        Q = PropsSI("Q", "P", P, "T", T, fluido)
        if Q < 0 or Q > 1:
            return None
        return Q
    except Exception:
        return None


def _get_quality_ps(P: float, s: float, fluido: str) -> float | None:
    """Return vapor quality from P and s."""
    try:
        sf = PropsSI("S", "P", P, "Q", 0, fluido)
        sg = PropsSI("S", "P", P, "Q", 1, fluido)
        if s < sf or s > sg:
            return None
        return (s - sf) / (sg - sf)
    except Exception:
        return None


def _state_PT(P: float, T: float, fluido: str) -> dict:
    """State from pressure (Pa) and temperature (K)."""
    h = _j_to_kj(PropsSI("H", "P", P, "T", T, fluido))
    s = _j_to_kj(PropsSI("S", "P", P, "T", T, fluido))
    x = _get_quality(P, T, fluido)
    return {
        "P": round(_pa_to_mpa(P), 4),
        "T": round(_k_to_c(T), 2),
        "h": round(h, 2),
        "s": round(s, 4),
        "x": round(x, 4) if x is not None else None,
    }


def _state_PS(P: float, s_kj: float, fluido: str) -> dict:
    """State from pressure (Pa) and entropy (kJ/kg·K)."""
    s = s_kj * 1000.0
    h = _j_to_kj(PropsSI("H", "P", P, "S", s, fluido))
    T = PropsSI("T", "P", P, "S", s, fluido)
    x = _get_quality_ps(P, s, fluido)
    return {
        "P": round(_pa_to_mpa(P), 4),
        "T": round(_k_to_c(T), 2),
        "h": round(h, 2),
        "s": round(s_kj, 4),
        "x": round(x, 4) if x is not None else None,
    }


def _state_Px(P: float, x: float, fluido: str) -> dict:
    """State from pressure (Pa) and quality."""
    T = PropsSI("T", "P", P, "Q", x, fluido)
    h = _j_to_kj(PropsSI("H", "P", P, "Q", x, fluido))
    s = _j_to_kj(PropsSI("S", "P", P, "Q", x, fluido))
    return {
        "P": round(_pa_to_mpa(P), 4),
        "T": round(_k_to_c(T), 2),
        "h": round(h, 2),
        "s": round(s, 4),
        "x": round(x, 4),
    }


def calcular_ciclo(
    fluido: str,
    p_entrada_kpa: float,
    t_entrada_c: float,
    p_salida_kpa: float,
    eficiencia_turbina_pct: float,
    eficiencia_bomba_pct: float,
    gasto_masico: float,
) -> dict:
    """Calculate all states and power for the ORC cycle."""
    P1 = _kpa_to_pa(p_entrada_kpa)
    T1 = _c_to_k(t_entrada_c)
    P2 = _kpa_to_pa(p_salida_kpa)
    eta_t = eficiencia_turbina_pct / 100.0
    eta_p = eficiencia_bomba_pct / 100.0

    # State 1: Turbine inlet (given)
    st1 = _state_PT(P1, T1, fluido)

    # State 2s: Isentropic turbine exit (P2, s2s = s1)
    s1 = st1["s"] * 1000.0  # back to J/kg·K
    st2s = _state_PS(P2, st1["s"], fluido)

    # State 2: Real turbine exit
    # h2 = h1 - eta_t * (h1 - h2s)
    h1 = st1["h"] * 1000.0  # J/kg
    h2s = st2s["h"] * 1000.0
    h2_real = h1 - eta_t * (h1 - h2s)
    # Get T and x from P2 and h2_real
    try:
        T2 = PropsSI("T", "P", P2, "H", h2_real, fluido)
        x2 = _get_quality(P2, T2, fluido)
        s2 = _j_to_kj(PropsSI("S", "P", P2, "H", h2_real, fluido))
    except Exception:
        # Fallback: try to get T from P,H
        T2 = PropsSI("T", "P", P2, "H", h2_real, fluido)
        s2 = _j_to_kj(PropsSI("S", "P", P2, "H", h2_real, fluido))
        x2 = None
    st2 = {
        "P": round(_pa_to_mpa(P2), 4),
        "T": round(_k_to_c(T2), 2),
        "h": round(h2_real / 1000.0, 2),
        "s": round(s2, 4),
        "x": round(x2, 4) if x2 is not None else None,
    }

    # State 3: Condenser exit (saturated liquid at P2)
    st3 = _state_Px(P2, 0.0, fluido)

    # State 4s: Isentropic pump exit (P1, s4s = s3)
    st4s = _state_PS(P1, st3["s"], fluido)

    # State 4: Real pump exit
    # h4 = h3 + (h4s - h3) / eta_p
    h3 = st3["h"] * 1000.0
    h4s = st4s["h"] * 1000.0
    h4_real = h3 + (h4s - h3) / eta_p
    try:
        T4 = PropsSI("T", "P", P1, "H", h4_real, fluido)
        s4 = _j_to_kj(PropsSI("S", "P", P1, "H", h4_real, fluido))
    except Exception:
        T4 = PropsSI("T", "P", P1, "H", h4_real, fluido)
        s4 = _j_to_kj(PropsSI("S", "P", P1, "H", h4_real, fluido))
    st4 = {
        "P": round(_pa_to_mpa(P1), 4),
        "T": round(_k_to_c(T4), 2),
        "h": round(h4_real / 1000.0, 2),
        "s": round(s4, 4),
        "x": None,
    }

    # Power calculations
    w_turbina = gasto_masico * (st1["h"] - st2["h"])  # kW
    w_bomba = gasto_masico * (st4["h"] - st3["h"])  # kW
    w_neta = w_turbina - w_bomba

    return {
        "estados": {
            "1": st1,
            "2s": st2s,
            "2": st2,
            "3": st3,
            "4s": st4s,
            "4": st4,
        },
        "potencia_turbina": round(w_turbina, 2),
        "potencia_bomba": round(w_bomba, 2),
        "potencia_neta": round(w_neta, 2),
    }


def generar_campana(fluido: str, n_puntos: int = 100) -> dict:
    """Generate saturation dome data for T-s diagram."""
    try:
        Tcrit = PropsSI("Tcrit", fluido)
        Pcrit = PropsSI("Pcrit", fluido)
    except Exception:
        return {"saturacion": {"liquido": {"T": [], "s": []}, "vapor": {"T": [], "s": []}}}

    # Generate points from triple point to critical point
    # Use pressure sweep from low pressure to critical pressure
    Pmin = PropsSI("P", "T", PropsSI("Tmin", fluido), "Q", 0, fluido)
    Pmax = Pcrit * 0.999  # Just below critical

    pressures = np.linspace(Pmin, Pmax, n_puntos)

    T_liq = []
    s_liq = []
    T_vap = []
    s_vap = []

    for P in pressures:
        try:
            Tl = PropsSI("T", "P", P, "Q", 0, fluido)
            sl = PropsSI("S", "P", P, "Q", 0, fluido)
            Tv = PropsSI("T", "P", P, "Q", 1, fluido)
            sv = PropsSI("S", "P", P, "Q", 1, fluido)

            T_liq.append(_k_to_c(Tl))
            s_liq.append(_j_to_kj(sl))
            T_vap.append(_k_to_c(Tv))
            s_vap.append(_j_to_kj(sv))
        except Exception:
            continue

    # Add critical point
    T_liq.append(_k_to_c(Tcrit))
    s_liq.append(_j_to_kj(PropsSI("S", "P", Pcrit, "Q", 0.5, fluido)))
    T_vap.append(_k_to_c(Tcrit))
    s_vap.append(_j_to_kj(PropsSI("S", "P", Pcrit, "Q", 0.5, fluido)))

    return {
        "saturacion": {
            "liquido": {"T": [round(t, 2) for t in T_liq], "s": [round(s, 4) for s in s_liq]},
            "vapor": {"T": [round(t, 2) for t in T_vap], "s": [round(s, 4) for s in s_vap]},
        }
    }
