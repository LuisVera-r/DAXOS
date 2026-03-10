"""
clientes.py — Asignación de clientes a jefes y detección de apoyo entre equipos.

Estructura en ce_config key='clientes_jefe':
{
  "VANESSA TAPIA GARCIA": ["TERNIUM", "DSV AIR & SEA"],
  "BEATRIZ CABRERA HERNANDEZ": ["TUBOS DE ACERO", "HENKEL"],
  ...
}

Lógica de apoyo:
  - Para cada pedimento: jefe_ejecutivo = jefe al que pertenece el ejecutivo
  - jefe_cliente  = jefe al que pertenece el cliente
  - Si jefe_ejecutivo != jefe_cliente → es una op de APOYO
  - Si no hay asignación de cliente → se considera op PROPIA (neutral)
"""
from __future__ import annotations
import pandas as pd

DEFAULT_CLIENTES: dict = {}   # vacío — el usuario los configura


def get_jefe_de_ejecutivo(ejecutivo: str, equipos: dict) -> str | None:
    """Devuelve el jefe al que pertenece un ejecutivo."""
    if not ejecutivo:
        return None
    eje_up = str(ejecutivo).upper()
    for jefe, miembros in equipos.items():
        for m in miembros:
            m_up = m.upper()
            if m_up in eje_up or eje_up in m_up:
                return jefe
    return None


def get_jefe_de_cliente(cliente: str, clientes_jefe: dict) -> str | None:
    """Devuelve el jefe responsable de un cliente."""
    if not cliente:
        return None
    cli_up = str(cliente).upper()
    for jefe, clientes in clientes_jefe.items():
        for c in clientes:
            if c.upper() in cli_up or cli_up in c.upper():
                return jefe
    return None


def enriquecer_apoyo(df: pd.DataFrame, equipos: dict,
                     clientes_jefe: dict) -> pd.DataFrame:
    """
    Agrega columnas:
      jefe_ejecutivo  — jefe del ejecutivo que atendió la op
      jefe_cliente    — jefe responsable del cliente
      es_apoyo        — True si jefe_ejecutivo != jefe_cliente (y ambos conocidos)
      tipo_participacion — 'Propia' | 'Apoyo dado' | 'Sin asignación'
    """
    df = df.copy()

    df["jefe_ejecutivo"] = df["ejecutivo"].apply(
        lambda x: get_jefe_de_ejecutivo(x, equipos)
    )
    df["jefe_cliente"] = df["cliente"].apply(
        lambda x: get_jefe_de_cliente(x, clientes_jefe)
    )

    def _tipo(row):
        je = row["jefe_ejecutivo"]
        jc = row["jefe_cliente"]
        if je is None or jc is None:
            return "Sin asignación"
        if je == jc:
            return "Propia"
        return "Apoyo dado"

    df["tipo_participacion"] = df.apply(_tipo, axis=1)
    df["es_apoyo"] = df["tipo_participacion"] == "Apoyo dado"
    return df


def tabla_apoyo_entre_jefes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Matriz jefe_ejecutivo × jefe_cliente con conteo de ops de apoyo.
    Útil para el mapa de flujo.
    """
    apoyo = df[df["es_apoyo"] == True].copy()
    if apoyo.empty:
        return pd.DataFrame()
    pivot = (apoyo
             .groupby(["jefe_ejecutivo", "jefe_cliente"])
             .size()
             .reset_index(name="ops_apoyo")
             .sort_values("ops_apoyo", ascending=False))
    return pivot


def resumen_por_jefe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Por cada jefe: ops propias, ops de apoyo dado, ops recibidas de apoyo.
    """
    rows = []
    jefes = set(df["jefe_ejecutivo"].dropna()) | set(df["jefe_cliente"].dropna())
    for jefe in sorted(jefes):
        propias   = len(df[(df["jefe_ejecutivo"] == jefe) & (df["tipo_participacion"] == "Propia")])
        apoyo_dado = len(df[(df["jefe_ejecutivo"] == jefe) & (df["es_apoyo"] == True)])
        apoyo_rec  = len(df[(df["jefe_cliente"] == jefe) & (df["es_apoyo"] == True)])
        rows.append({
            "Jefe": jefe,
            "Ops propias": propias,
            "Apoyo dado": apoyo_dado,
            "Apoyo recibido": apoyo_rec,
            "Total atendidas": propias + apoyo_dado,
        })
    return pd.DataFrame(rows).sort_values("Total atendidas", ascending=False)


def clientes_con_mas_apoyo(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """
    Ranking de clientes que más apoyo externo recibieron.
    """
    apoyo = df[df["es_apoyo"] == True]
    if apoyo.empty or "cliente" not in apoyo.columns:
        return pd.DataFrame()
    return (apoyo.groupby("cliente")
            .agg(ops_apoyo=("es_apoyo", "sum"),
                 ejecutivos_distintos=("ejecutivo", "nunique"),
                 jefe_cliente=("jefe_cliente", "first"))
            .reset_index()
            .sort_values("ops_apoyo", ascending=False)
            .head(top_n))
