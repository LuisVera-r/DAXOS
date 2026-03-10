"""
sla.py — Lógica de días hábiles, feriados y SLA por etapa.

Feriados oficiales México (Ley Federal del Trabajo + SEP):
  1 ene, primer lun feb, tercer lun mar, 1 may, 16 sep,
  tercer lun nov, 25 dic  +  años electorales: primer lun jun

La lista es editable desde la app (ce_config key='feriados').
"""
from __future__ import annotations
import json
from datetime import date, timedelta
from typing import Optional
import numpy as np
import pandas as pd

# ── Feriados fijos por año ─────────────────────────────────────────
def _feriados_mx(years: list[int]) -> list[date]:
    """Genera feriados oficiales México para los años indicados."""
    feriados = []
    for y in years:
        feriados += [
            date(y, 1, 1),                     # Año nuevo
            _nth_weekday(y, 2, 0, 1),          # 1er lun feb (Constitución)
            _nth_weekday(y, 3, 0, 3),          # 3er lun mar (Benito Juárez)
            date(y, 5, 1),                     # Día del trabajo
            date(y, 9, 16),                    # Independencia
            _nth_weekday(y, 11, 0, 3),         # 3er lun nov (Revolución)
            date(y, 12, 25),                   # Navidad
        ]
    return feriados


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Devuelve el n-ésimo weekday (0=lun) del mes."""
    first = date(year, month, 1)
    delta = (weekday - first.weekday()) % 7
    first_match = first + timedelta(days=delta)
    return first_match + timedelta(weeks=n - 1)


# ── Cache de feriados ──────────────────────────────────────────────
_FERIADOS_CACHE: Optional[pd.DatetimeIndex] = None


def get_feriados(extra: list[str] | None = None) -> pd.DatetimeIndex:
    """
    Devuelve índice de feriados.
    extra: lista de fechas ISO adicionales ['2026-05-15', ...]
    """
    global _FERIADOS_CACHE
    years = list(range(2023, 2030))
    base  = _feriados_mx(years)
    extra_dates = []
    if extra:
        for s in extra:
            try:
                extra_dates.append(pd.Timestamp(s).date())
            except Exception:
                pass
    all_dates = sorted(set(base + extra_dates))
    return pd.DatetimeIndex([pd.Timestamp(d) for d in all_dates])


def set_feriados_cache(feriados: pd.DatetimeIndex):
    global _FERIADOS_CACHE
    _FERIADOS_CACHE = feriados


# ── Cálculo de días hábiles entre dos fechas ──────────────────────
def dias_habiles(fecha_a, fecha_b, feriados: pd.DatetimeIndex) -> float:
    """
    Días hábiles de fecha_a a fecha_b (exclusivo inicio, inclusivo fin).
    Retorna NaN si alguna fecha es nula.
    """
    if pd.isna(fecha_a) or pd.isna(fecha_b):
        return np.nan
    if fecha_b <= fecha_a:
        return 0.0
    bd = pd.bdate_range(fecha_a, fecha_b, freq="C", holidays=feriados)
    return float(max(0, len(bd) - 1))


def _apply_dh(df: pd.DataFrame, col_a: str, col_b: str,
              col_out: str, feriados: pd.DatetimeIndex):
    """Agrega columna col_out con días hábiles entre col_a y col_b."""
    if {col_a, col_b} <= set(df.columns):
        df[col_out] = df.apply(
            lambda r: dias_habiles(r[col_a], r[col_b], feriados), axis=1
        )
    else:
        df[col_out] = np.nan


# ── Definición de etapas SLA ──────────────────────────────────────
#  SLA en días hábiles; None = sin SLA definido
ETAPAS: list[dict] = [
    {"id": "llegada_recoleccion", "label": "Llegada → Recolección",
     "col_a": "f_llegada",       "col_b": "f_revalida",      "sla": 1},
    {"id": "recoleccion_previo",  "label": "Recolección → Previo",
     "col_a": "f_revalida",      "col_b": "f_previo",        "sla": 1},
    {"id": "previo_pago",         "label": "Previo → Pago",
     "col_a": "f_previo",        "col_b": "f_pago",          "sla": 1},
    {"id": "pago_despacho",       "label": "Pago → Despacho",
     "col_a": "f_pago",          "col_b": "f_despacho",      "sla": 1},
    {"id": "despacho_contab",     "label": "Despacho → Contabilidad",
     "col_a": "f_despacho",      "col_b": "f_contabilidad",  "sla": 3},
    {"id": "contab_factura",      "label": "Contabilidad → Factura",
     "col_a": "f_contabilidad",  "col_b": "f_facturacion",   "sla": 1},
]

# Etapas que componen el "total operativo" (desde Pago, no Llegada)
ETAPAS_OPERATIVAS = ["pago_despacho", "despacho_contab", "contab_factura"]


def calcular_sla(df: pd.DataFrame, feriados: pd.DatetimeIndex,
                 etapas_activas: list[str] | None = None) -> pd.DataFrame:
    """
    Agrega columnas dh_<id> (días hábiles) y vencido_<id> (bool) para cada etapa.
    etapas_activas: lista de ids a calcular; None = todas.
    """
    df = df.copy()
    for e in ETAPAS:
        if etapas_activas and e["id"] not in etapas_activas:
            continue
        col_dh  = f"dh_{e['id']}"
        col_venc = f"vencido_{e['id']}"
        _apply_dh(df, e["col_a"], e["col_b"], col_dh, feriados)
        if e["sla"] is not None:
            df[col_venc] = df[col_dh] > e["sla"]
        else:
            df[col_venc] = False

    # Total operativo (desde Pago)
    dh_cols_op = [f"dh_{e['id']}" for e in ETAPAS if e["id"] in ETAPAS_OPERATIVAS
                  and f"dh_{e['id']}" in df.columns]
    if dh_cols_op:
        df["dh_total_op"] = df[dh_cols_op].sum(axis=1, skipna=False)

    return df


def resumen_sla(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tabla resumen de cumplimiento SLA por etapa.
    Columnas: Etapa, SLA, Total, Cumple, Vencido, %Cumple, Mediana, P90
    """
    rows = []
    for e in ETAPAS:
        col_dh   = f"dh_{e['id']}"
        col_venc = f"vencido_{e['id']}"
        if col_dh not in df.columns:
            continue
        serie = df[col_dh].dropna()
        if serie.empty:
            continue
        total   = len(serie)
        vencido = int(df[col_venc].sum()) if col_venc in df.columns else 0
        cumple  = total - vencido
        rows.append({
            "Etapa":    e["label"],
            "SLA (dh)": e["sla"],
            "Total":    total,
            "✅ Cumple": cumple,
            "❌ Vencido": vencido,
            "% Cumple": round(cumple / total * 100, 1) if total else 0,
            "Mediana":  round(serie.median(), 1),
            "P90":      round(serie.quantile(0.9), 1),
        })
    return pd.DataFrame(rows)
