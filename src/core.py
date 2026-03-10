"""
core.py — Extracción, normalización y persistencia.

Una sola tabla: ce_detalle (o historico.pkl en local/github).
Todo el análisis se calcula en app.py desde el detalle.

Backends (prioridad automática):
  1. SUPABASE  → secrets [supabase] url + key
  2. GITHUB    → secrets [github]   token + repo
  3. LOCAL     → data/historico.pkl
"""
from __future__ import annotations

import base64
import io
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

import pandas as pd

# ── Rutas ──────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).parent
DATA_DIR      = ROOT / "data"
HISTORICO_PKL = DATA_DIR / "historico.pkl"
EQUIPOS_JSON  = DATA_DIR / "equipos.json"
DATA_DIR.mkdir(exist_ok=True)

UBICACIONES = ["AICM", "AIFA", "GUADALAJARA", "MONTERREY", "TOLUCA", "QUERETARO"]

COL_RENAME = {
    "UDN": "aduana", "# Importador": "importador_id",
    "Nombre Importador": "importador_nombre", "Cliente": "cliente",
    "Ejecutivo": "ejecutivo", "TO": "tipo_op", "Referencia": "referencia",
    "Pedimento": "pedimento", "Fecha Generación": "f_generacion",
    "Fecha Llegada": "f_llegada", "Fecha Revalida": "f_revalida",
    "Fecha de Previo": "f_previo", "Fech Pago": "f_pago",
    "Fecha Despachos": "f_despacho",
    "Fecha Pase a Contabilidad": "f_contabilidad",
    "Fecha de Facturación": "f_facturacion",
}
FECHAS = ["f_generacion", "f_llegada", "f_revalida", "f_previo",
          "f_pago", "f_despacho", "f_contabilidad", "f_facturacion"]


# ══════════════════════════════════════════════════════════════════════════════
# DETECCIÓN DE ENTORNO
# ══════════════════════════════════════════════════════════════════════════════

def _sb_secrets() -> Optional[dict]:
    try:
        import streamlit as st
        sec = st.secrets.get("supabase", {})
        if sec.get("url") and sec.get("key"):
            return {"url": sec["url"].rstrip("/"), "key": sec["key"]}
    except Exception:
        pass
    return None


def _gh_secrets() -> Optional[dict]:
    try:
        import streamlit as st
        sec = st.secrets.get("github", {})
        if sec.get("token") and sec.get("repo"):
            return {"token": sec["token"], "repo": sec["repo"],
                    "branch": sec.get("branch", "main")}
    except Exception:
        pass
    return None


def _backend() -> str:
    if _sb_secrets():  return "supabase"
    if _gh_secrets():  return "github"
    return "local"


# ══════════════════════════════════════════════════════════════════════════════
# BACKEND SUPABASE
# ══════════════════════════════════════════════════════════════════════════════

def _sb_req(method: str, path: str, body=None, params: Optional[dict] = None):
    sec = _sb_secrets()
    url = f"{sec['url']}/rest/v1/{path}"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    headers = {"apikey": sec["key"], "Authorization": f"Bearer {sec['key']}",
               "Content-Type": "application/json", "Prefer": "return=minimal"}
    data = json.dumps(body).encode() if body is not None else None
    req  = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw.strip() else None
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Supabase {method} {path} → HTTP {e.code}: {e.read().decode()}") from e


def _sb_upsert(table: str, rows: list[dict]):
    """Upsert en lotes de 500."""
    sec = _sb_secrets()
    for i in range(0, len(rows), 500):
        chunk = rows[i: i + 500]
        url   = f"{sec['url']}/rest/v1/{table}"
        headers = {"apikey": sec["key"], "Authorization": f"Bearer {sec['key']}",
                   "Content-Type": "application/json",
                   "Prefer": "resolution=merge-duplicates,return=minimal"}
        req = urllib.request.Request(url, data=json.dumps(chunk).encode(),
                                     headers=headers, method="POST")
        with urllib.request.urlopen(req):
            pass


def _sb_delete_periodo(periodo: str):
    import urllib.parse
    sec = _sb_secrets()
    url = f"{sec['url']}/rest/v1/ce_detalle?periodo=eq.{urllib.parse.quote(periodo)}"
    headers = {"apikey": sec["key"], "Authorization": f"Bearer {sec['key']}"}
    req = urllib.request.Request(url, headers=headers, method="DELETE")
    with urllib.request.urlopen(req):
        pass


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    out = []
    for row in df.to_dict("records"):
        rec = {}
        for k, v in row.items():
            if k in FECHAS:
                rec[k] = v.isoformat() if pd.notna(v) and hasattr(v, "isoformat") else None
            elif not isinstance(v, (list, dict)) and pd.isna(v):
                rec[k] = None
            elif hasattr(v, "item"):
                rec[k] = v.item()
            else:
                rec[k] = v
        out.append(rec)
    return out


def _records_to_df(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    for col in FECHAS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _sb_load_detalle() -> pd.DataFrame:
    rows = _sb_req("GET", "ce_detalle", params={"select": "*"})
    return _records_to_df(rows or [])


def _sb_periodo_exists(periodo: str) -> bool:
    import urllib.parse
    rows = _sb_req("GET", "ce_detalle",
                   params={"select": "periodo",
                           "periodo": f"eq.{urllib.parse.quote(periodo)}",
                           "limit": "1"})
    return bool(rows)


def _sb_get_periodos() -> list[str]:
    rows = _sb_req("GET", "ce_detalle", params={"select": "periodo"})
    if not rows:
        return []
    return sorted({r["periodo"] for r in rows if r.get("periodo")})


# ── Equipos en Supabase (tabla ce_config) ─────────────────────────────────
def _sb_load_equipos() -> Optional[dict]:
    rows = _sb_req("GET", "ce_config", params={"select": "value", "key": "eq.equipos"})
    if rows:
        try:
            return json.loads(rows[0]["value"])
        except Exception:
            pass
    return None


def _sb_save_equipos(equipos: dict):
    _sb_upsert("ce_config", [{"key": "equipos", "value": json.dumps(equipos)}])


# ══════════════════════════════════════════════════════════════════════════════
# BACKEND GITHUB
# ══════════════════════════════════════════════════════════════════════════════

_GH_API = "https://api.github.com"

def _gh_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"}


def _gh_get_file(path: str) -> Optional[tuple[bytes, str]]:
    sec = _gh_secrets()
    url = f"{_GH_API}/repos/{sec['repo']}/contents/{path}?ref={sec['branch']}"
    req = urllib.request.Request(url, headers=_gh_headers(sec["token"]))
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            return base64.b64decode(data["content"]), data["sha"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def _gh_put_file(path: str, content_bytes: bytes, message: str, sha: Optional[str] = None):
    sec = _gh_secrets()
    url = f"{_GH_API}/repos/{sec['repo']}/contents/{path}"
    payload = {"message": message, "branch": sec["branch"],
               "content": base64.b64encode(content_bytes).decode()}
    if sha:
        payload["sha"] = sha
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={**_gh_headers(sec["token"]), "Content-Type": "application/json"},
        method="PUT")
    with urllib.request.urlopen(req):
        pass


def _gh_load_detalle() -> pd.DataFrame:
    result = _gh_get_file("data/historico.pkl")
    if result is None:
        return pd.DataFrame()
    try:
        store = pd.read_pickle(io.BytesIO(result[0]))
        return store if isinstance(store, pd.DataFrame) else store.get("detalle", pd.DataFrame())
    except Exception:
        return pd.DataFrame()


def _gh_save_detalle(df: pd.DataFrame):
    buf = io.BytesIO()
    pd.to_pickle(df, buf)
    existing = _gh_get_file("data/historico.pkl")
    sha = existing[1] if existing else None
    _gh_put_file("data/historico.pkl", buf.getvalue(), "chore: actualizar histórico", sha)


# ══════════════════════════════════════════════════════════════════════════════
# API PÚBLICA — todo trabaja con un solo DataFrame de detalle
# ══════════════════════════════════════════════════════════════════════════════

def get_detalle() -> pd.DataFrame:
    """Carga toda la tabla de pedimentos según el backend activo."""
    b = _backend()
    if b == "supabase":
        return _sb_load_detalle()
    if b == "github":
        return _gh_load_detalle()
    # local
    if HISTORICO_PKL.exists():
        try:
            obj = pd.read_pickle(HISTORICO_PKL)
            return obj if isinstance(obj, pd.DataFrame) else obj.get("detalle", pd.DataFrame())
        except Exception:
            pass
    return pd.DataFrame()


def get_periodos() -> list[str]:
    if _backend() == "supabase":
        return _sb_get_periodos()
    df = get_detalle()
    if df.empty or "periodo" not in df.columns:
        return []
    return sorted(df["periodo"].dropna().unique().tolist())


def add_periodo(parsed: dict) -> tuple[bool, str]:
    """Agrega el detalle de un nuevo periodo al histórico."""
    periodo  = parsed["periodo"]
    det_nuevo = parsed["detalle"]

    if _backend() == "supabase":
        if _sb_periodo_exists(periodo):
            return False, f"El periodo **{periodo}** ya existe. Se omitió."
        det_nuevo["mes"] = det_nuevo["mes"].astype(str) if "mes" in det_nuevo.columns else ""
        _sb_upsert("ce_detalle", _df_to_records(det_nuevo))
        return True, f"Periodo **{periodo}** guardado en Supabase ✓"

    # github / local
    df_actual = get_detalle()
    if not df_actual.empty and "periodo" in df_actual.columns and \
            periodo in df_actual["periodo"].values:
        return False, f"El periodo **{periodo}** ya existe. Se omitió."
    df_nuevo = pd.concat([df_actual, det_nuevo], ignore_index=True)
    _save_detalle(df_nuevo)
    return True, f"Periodo **{periodo}** agregado correctamente."


def _save_detalle(df: pd.DataFrame):
    if _backend() == "github":
        _gh_save_detalle(df)
    else:
        pd.to_pickle(df, HISTORICO_PKL)


def delete_periodo(periodo: str) -> str:
    if _backend() == "supabase":
        _sb_delete_periodo(periodo)
        return f"Periodo **{periodo}** eliminado de Supabase."
    df = get_detalle()
    if "periodo" in df.columns:
        df = df[df["periodo"] != periodo]
    _save_detalle(df)
    return f"Periodo **{periodo}** eliminado."


# ══════════════════════════════════════════════════════════════════════════════
# GESTIÓN DE EQUIPOS
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_EQUIPOS: dict = {
    "VANESSA TAPIA GARCIA": [
        "JAQUELIN CAROLINA CARMONA ROMERO", "SHARON CANALES",
        "MARIA NICOLAS CELIS", "NATALIA ORTIZ",
        "ERICK ALEJANDRO RIOS VANEGAS", "ERIKA LÓPEZ ALVAREZ",
    ],
    "BERNARDO RODRIGUEZ SERRANO": ["BERNARDO RODRIGUEZ SERRANO"],
    "BEATRIZ CABRERA HERNANDEZ": [
        "BEATRIZ CABRERA", "ARIADNA ROA MONROY",
        "DIANA LAURA CARBAJAL VILLALPANDO",
    ],
    "DIANA LAURA CARBAJAL": [
        "DIANA LAURA CARBAJAL VILLALPANDO", "MICHEL BARRERA REYES",
    ],
    "JENNIFER MARGARITA ZAMUDIO CAMACHO": [
        "JENNIFER MARGARITA ZAMUDIO CAMACHO", "ROSA ITZELA ROSALES URBINA",
        "DULCE PALOMA RAMIREZ GRIJALVA", "MILKA JULIAN ANTONIO",
    ],
    "XOCHITL BERENICE LEYVA GARAY": ["XOCHITL BERENICE LEYVA GARAY"],
    "SERGIO MORENO VENEGAS":        ["SERGIO MORENO VENEGAS"],
}


def load_equipos() -> dict:
    if _backend() == "supabase":
        r = _sb_load_equipos()
        if r is not None:
            return r
        _sb_save_equipos(DEFAULT_EQUIPOS)
        return DEFAULT_EQUIPOS
    if _backend() == "github":
        r = _gh_get_file("data/equipos.json")
        if r:
            try:
                return json.loads(r[0].decode("utf-8"))
            except Exception:
                pass
    if EQUIPOS_JSON.exists():
        try:
            return json.loads(EQUIPOS_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    save_equipos(DEFAULT_EQUIPOS)
    return DEFAULT_EQUIPOS


def save_equipos(equipos: dict):
    if _backend() == "supabase":
        _sb_save_equipos(equipos)
        return
    content = json.dumps(equipos, ensure_ascii=False, indent=2).encode("utf-8")
    if _backend() == "github":
        existing = _gh_get_file("data/equipos.json")
        sha = existing[1] if existing else None
        _gh_put_file("data/equipos.json", content, "chore: actualizar equipos", sha)
    EQUIPOS_JSON.write_text(content.decode("utf-8"), encoding="utf-8")


def get_ejecutivos_de_jefe(jefe: str, equipos: dict) -> list[str]:
    return equipos.get(jefe, [jefe])


# ══════════════════════════════════════════════════════════════════════════════
# EXTRACCIÓN DESDE EXCEL  (solo tabla detalle)
# ══════════════════════════════════════════════════════════════════════════════

def _detect_periodo(raw: pd.DataFrame) -> str:
    for i in range(15):
        row_vals = " ".join(raw.iloc[i].fillna("").astype(str).tolist()).upper()
        m = re.search(r"(\d{1,2})\s+DE\s+(\w+)\s+DEL?\s+(\d{4})", row_vals)
        if m:
            meses = {"ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4,
                     "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8,
                     "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12}
            mes_num = meses.get(m.group(2).upper(), 0)
            if mes_num:
                return f"{m.group(3)}-{mes_num:02d}"
    return "desconocido"


def _lt(df, col_out, col_a, col_b):
    if {col_a, col_b} <= set(df.columns):
        df[col_out] = (df[col_b] - df[col_a]).dt.days


def parse_excel(file_bytes: bytes) -> dict:
    """
    Parsea el Excel y devuelve solo:
      {'detalle': DataFrame, 'periodo': str}
    Todo el análisis se hace sobre el detalle en app.py.
    """
    raw = pd.read_excel(io.BytesIO(file_bytes), header=None, engine="openpyxl")
    periodo = _detect_periodo(raw)

    # Detectar fila donde termina el detalle (primera tabla resumen)
    mask_resumen = raw.apply(
        lambda r: r.astype(str).str.upper()
        .str.contains(r"EJECUTIVO\s+IMPORTACION", regex=True).any(), axis=1)
    filas_resumen = raw[mask_resumen].index.tolist()
    fin_detalle   = filas_resumen[0] if filas_resumen else len(raw)

    # Extraer solo la tabla de pedimentos
    det = raw.iloc[10: fin_detalle].copy()
    det.columns = det.iloc[0].astype(str).str.strip()
    det = det.iloc[1:].reset_index(drop=True).dropna(how="all")
    det = det.rename(columns=COL_RENAME)

    for col in FECHAS:
        if col in det.columns:
            det[col] = pd.to_datetime(det[col], errors="coerce")

    # Lead times
    _lt(det, "lt_total",            "f_llegada",  "f_facturacion")
    _lt(det, "lt_llegada_pago",     "f_llegada",  "f_pago")
    _lt(det, "lt_pago_despacho",    "f_pago",     "f_despacho")
    _lt(det, "lt_despacho_factura", "f_despacho", "f_facturacion")

    det["periodo"] = periodo
    if "f_llegada" in det.columns:
        det["mes"] = det["f_llegada"].dt.to_period("M").astype(str)

    return {"detalle": det, "periodo": periodo}
