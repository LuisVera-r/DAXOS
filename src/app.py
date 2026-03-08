import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np
from typing import Union, List

# ==============================
# CONFIGURACIÓN DE RUTAS
# ==============================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = os.path.join(BASE_DIR, "data")

st.set_page_config(
    page_title="OPS · CE Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="⬡",
)

# ── Tema visual ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;700&family=DM+Mono:wght@400;500&display=swap');

/* --- Base --- */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    background-color: #080C14;
    color: #C9D4E8;
}
.block-container { padding: 1.8rem 2.5rem 3rem; max-width: 1600px; }

/* --- Barra superior decorativa --- */
.top-bar {
    height: 3px;
    background: linear-gradient(90deg, #00D9FF 0%, #6C63FF 50%, #FF4F7B 100%);
    margin: -1.8rem -2.5rem 2rem;
    border-radius: 0 0 4px 4px;
}

/* --- KPI Cards --- */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #0F1623 0%, #111927 100%);
    border: 1px solid #1C2640;
    border-top: 2px solid #00D9FF22;
    border-radius: 12px;
    padding: 1.2rem 1.5rem 1rem;
    transition: border-color 0.2s;
}
[data-testid="metric-container"]:hover { border-color: #00D9FF44; }
[data-testid="metric-container"] label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #4A5F80;
}
[data-testid="metric-container"] [data-testid="metric-value"] {
    font-family: 'DM Mono', monospace;
    font-size: 2.1rem;
    font-weight: 500;
    color: #00D9FF;
    letter-spacing: -0.02em;
}
[data-testid="stMetricDelta"] svg { display: none; }
[data-testid="stMetricDelta"] { font-size: 0.75rem; color: #4A5F80 !important; }

/* --- Headers --- */
h1 {
    font-family: 'DM Mono', monospace !important;
    font-size: 1.1rem !important;
    letter-spacing: 0.25em !important;
    text-transform: uppercase !important;
    color: #E8F0FF !important;
    font-weight: 500 !important;
}
h2, h3 {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    color: #4A5F80 !important;
    margin-top: 1.5rem !important;
    margin-bottom: 0.8rem !important;
}

/* --- Sidebar --- */
[data-testid="stSidebar"] {
    background: #080C14;
    border-right: 1px solid #1C2640;
    padding-top: 1rem;
}
[data-testid="stSidebar"] label {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #4A5F80;
}
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: #0F1623;
    border-color: #1C2640;
    color: #C9D4E8;
    font-size: 0.82rem;
}
[data-testid="stSidebar"] .stMultiSelect > div {
    background: #0F1623;
    border-color: #1C2640;
}

/* --- Tabs --- */
[data-testid="stTabs"] {
    border-bottom: 1px solid #1C2640;
}
[data-testid="stTabs"] button {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #4A5F80;
    padding: 0.5rem 1.1rem;
    border-radius: 0;
}
[data-testid="stTabs"] button:hover { color: #C9D4E8; }
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #00D9FF;
    border-bottom: 2px solid #00D9FF;
    background: transparent;
}

/* --- Dataframe --- */
[data-testid="stDataFrame"] {
    border: 1px solid #1C2640;
    border-radius: 10px;
    overflow: hidden;
}
.stDataFrame thead th {
    background: #0F1623 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.68rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: #4A5F80 !important;
}

/* --- Divider --- */
hr { border-color: #1C2640; margin: 1.2rem 0; }

/* --- Alert/info --- */
[data-testid="stAlert"] {
    background: #0F1623;
    border: 1px solid #1C2640;
    border-radius: 8px;
    font-size: 0.82rem;
    color: #4A5F80;
}

/* --- Caption --- */
.stCaption { font-family: 'DM Mono', monospace; font-size: 0.68rem; color: #4A5F80; letter-spacing: 0.06em; }

/* --- Progress bars y misc --- */
.stProgress > div > div { background: linear-gradient(90deg, #00D9FF, #6C63FF); }

/* --- Pill badge (html directo) --- */
.badge {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
    margin-right: 0.3rem;
    margin-bottom: 0.3rem;
}
.badge-imp { background: #00D9FF18; color: #00D9FF; border: 1px solid #00D9FF33; }
.badge-exp { background: #FF4F7B18; color: #FF7B9A; border: 1px solid #FF4F7B33; }
.badge-udn { background: #6C63FF18; color: #9D97FF; border: 1px solid #6C63FF33; }
</style>
""", unsafe_allow_html=True)

# ── Paleta matplotlib ─────────────────────────────────────────────────────────
C_CYAN    = "#00D9FF"
C_VIOLET  = "#6C63FF"
C_PINK    = "#FF4F7B"
C_AMBER   = "#FFB547"
C_GREEN   = "#34D399"
BG        = "#0A0F1A"
BG2       = "#0F1623"
GRID      = "#1C2640"
TXT       = "#4A5F80"
TXT2      = "#8899BB"

# ==============================
# EXTRACCIÓN DE LAS 4 TABLAS
# ==============================

UBICACIONES = ["AICM", "AIFA", "GUADALAJARA", "MONTERREY", "TOLUCA", "QUERETARO"]

FECHA_COLS_MAP = {
    "Fecha Generación": "f_generacion",
    "Fecha Llegada":    "f_llegada",
    "Fecha Revalida":   "f_revalida",
    "Fecha de Previo":  "f_previo",
    "Fech Pago":        "f_pago",
    "Fecha Despachos":  "f_despacho",
    "Fecha Pase a Contabilidad": "f_contabilidad",
    "Fecha de Facturación":      "f_facturacion",
}

COL_RENAME = {
    "UDN": "aduana",
    "# Importador": "importador_id",
    "Nombre Importador": "importador_nombre",
    "Cliente": "cliente",
    "Ejecutivo": "ejecutivo",
    "TO": "tipo_op",
    "Referencia": "referencia",
    "Pedimento": "pedimento",
}


def _leer_resumen(df_raw, header_row, next_row=None):
    """Lee una tabla de resumen y devuelve DataFrame con Ejecutivo + Operaciones + UDNs."""
    hdr = df_raw.iloc[header_row]
    col_ini = hdr.first_valid_index()
    fin = next_row if next_row is not None else len(df_raw)
    bloque = df_raw.loc[header_row: fin - 1, col_ini:].copy()
    encabezados = bloque.iloc[0].astype(str).str.strip().tolist()
    encabezados[0] = "Ejecutivo"
    bloque = bloque.iloc[1:].copy()
    bloque.columns = range(len(encabezados))
    bloque = bloque.rename(columns={i: encabezados[i] for i in range(len(encabezados))})
    bloque = bloque.loc[:, ~bloque.columns.duplicated()]
    bloque = bloque[bloque["Ejecutivo"].notna()]
    bloque = bloque[~bloque["Ejecutivo"].astype(str).str.upper().isin(["TOTAL", "NAN", ""])]
    bloque = bloque.dropna(how="all")
    cols_ubi = [c for c in bloque.columns if str(c).upper() in UBICACIONES]
    for col in cols_ubi:
        bloque[col] = pd.to_numeric(bloque[col], errors="coerce").fillna(0)
    if "TOTAL" in bloque.columns:
        bloque["Operaciones"] = pd.to_numeric(bloque["TOTAL"], errors="coerce").fillna(
            bloque[cols_ubi].sum(axis=1)
        )
    else:
        bloque["Operaciones"] = bloque[cols_ubi].sum(axis=1)
    bloque["Ejecutivo"] = bloque["Ejecutivo"].astype(str).str.strip()
    cols_out = ["Ejecutivo", "Operaciones"] + cols_ubi
    return bloque[[c for c in cols_out if c in bloque.columns]].reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_file(path: str):
    """
    Devuelve (df_detalle, df_equipos, df_individual, df_exportacion).
    df_detalle: tabla transaccional completa (filas de pedimentos).
    Las otras tres: tablas de resumen.
    """
    raw = pd.read_excel(path, header=None, engine="openpyxl")

    # ── Detectar filas de encabezado de tablas resumen ─────────────────────
    mask_imp = raw.apply(
        lambda r: r.astype(str).str.upper().str.contains(r"EJECUTIVO\s+IMPORTACION", regex=True).any(), axis=1
    )
    mask_exp = raw.apply(
        lambda r: r.astype(str).str.upper().str.contains(r"EJECUTIVO\s+EXPORTACION", regex=True).any(), axis=1
    )
    rows_imp = raw[mask_imp].index.tolist()
    rows_exp = raw[mask_exp].index.tolist()

    if len(rows_imp) < 2 or len(rows_exp) < 1:
        st.error("Estructura no reconocida: se necesitan ≥2 tablas IMPORTACION y ≥1 EXPORTACION.")
        st.stop()

    # ── Tabla detalle (pedimentos) ─────────────────────────────────────────
    # Encabezado en fila 10 (índice fijo del reporte), datos hasta primer resumen
    hdr_row = 10
    fin_detalle = rows_imp[0]
    bloque_det = raw.iloc[hdr_row: fin_detalle].copy()
    bloque_det.columns = bloque_det.iloc[0].astype(str).str.strip()
    bloque_det = bloque_det.iloc[1:].reset_index(drop=True).dropna(how="all")
    bloque_det = bloque_det.rename(columns={**COL_RENAME, **FECHA_COLS_MAP})
    for col in FECHA_COLS_MAP.values():
        if col in bloque_det.columns:
            bloque_det[col] = pd.to_datetime(bloque_det[col], errors="coerce")
    # Lead times derivados
    if {"f_llegada", "f_facturacion"} <= set(bloque_det.columns):
        bloque_det["lt_total"] = (bloque_det["f_facturacion"] - bloque_det["f_llegada"]).dt.days
    if {"f_llegada", "f_pago"} <= set(bloque_det.columns):
        bloque_det["lt_llegada_pago"] = (bloque_det["f_pago"] - bloque_det["f_llegada"]).dt.days
    if {"f_pago", "f_despacho"} <= set(bloque_det.columns):
        bloque_det["lt_pago_despacho"] = (bloque_det["f_despacho"] - bloque_det["f_pago"]).dt.days
    if {"f_despacho", "f_facturacion"} <= set(bloque_det.columns):
        bloque_det["lt_despacho_factura"] = (bloque_det["f_facturacion"] - bloque_det["f_despacho"]).dt.days
    # Columna mes
    if "f_llegada" in bloque_det.columns:
        bloque_det["mes"] = bloque_det["f_llegada"].dt.to_period("M").astype(str)

    # ── Tablas resumen ─────────────────────────────────────────────────────
    df_equipos    = _leer_resumen(raw, rows_imp[0], rows_imp[1])
    df_individual = _leer_resumen(raw, rows_imp[1], rows_exp[0])
    df_exportacion = _leer_resumen(raw, rows_exp[0])

    return bloque_det, df_equipos, df_individual, df_exportacion


# ==============================
# HELPERS DE GRÁFICAS
# ==============================

def make_fig(w: Union[int, float] = 10, h: Union[int, float] = 4):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.tick_params(colors=TXT2, labelsize=8)
    ax.xaxis.label.set_color(TXT)
    ax.yaxis.label.set_color(TXT)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)
    ax.yaxis.grid(True, color=GRID, linewidth=0.5, linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)
    return fig, ax


def bar_h(series, title, color=C_CYAN, top_n=None, label_fmt="{:,.0f}"):
    """Barras horizontales — ideal para nombres largos."""
    if top_n:
        series = series.head(top_n)
    series = series.sort_values(ascending=True)
    n = len(series)
    fig, ax = make_fig(w=9, h=max(3.5, n * 0.42))
    colors = [color] * n
    # Degradado sutil
    alphas = np.linspace(0.55, 1.0, n)
    bars = ax.barh(range(n), series.values, color=color, alpha=0.9, height=0.62, zorder=3)
    for i, (bar, a) in enumerate(zip(bars, alphas)):
        bar.set_alpha(a)
    # Etiquetas
    vmax = series.max() if series.max() > 0 else 1
    for i, (bar, v) in enumerate(zip(bars, series.values)):
        ax.text(v + vmax * 0.015, bar.get_y() + bar.get_height() / 2,
                label_fmt.format(v), va="center", ha="left",
                fontsize=7.5, color=TXT2, fontfamily="monospace")
    ax.set_yticks(range(n))
    ax.set_yticklabels(series.index, fontsize=8)
    ax.set_xlabel("Operaciones", labelpad=6)
    ax.set_xlim(0, vmax * 1.18)
    ax.set_title(title, color="#C9D4E8", fontsize=9.5,
                 fontfamily="monospace", pad=10, loc="left", fontweight="500")
    plt.tight_layout()
    return fig


def bar_v(series, title, color=C_CYAN, top_n=None):
    """Barras verticales — para pocas categorías."""
    if top_n:
        series = series.head(top_n)
    n = len(series)
    fig, ax = make_fig(w=max(7, n * 0.7), h=4.5)
    alphas = np.linspace(0.6, 1.0, n)
    bars = ax.bar(range(n), series.values, color=color, width=0.6, zorder=3, edgecolor="none")
    for bar, a in zip(bars, alphas):
        bar.set_alpha(a)
    vmax = series.max() if series.max() > 0 else 1
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + vmax * 0.02,
                f"{int(h):,}", ha="center", va="bottom",
                fontsize=7.5, color=TXT2, fontfamily="monospace")
    ax.set_xticks(range(n))
    ax.set_xticklabels(series.index, rotation=38, ha="right", fontsize=8)
    ax.set_ylim(0, vmax * 1.18)
    ax.set_ylabel("Operaciones", labelpad=6)
    ax.set_title(title, color="#C9D4E8", fontsize=9.5,
                 fontfamily="monospace", pad=10, loc="left", fontweight="500")
    plt.tight_layout()
    return fig


def multi_bar(df_pivot, title, colors=None):
    """Barras agrupadas: df_pivot index=categorías, columnas=series."""
    if colors is None:
        colors = [C_CYAN, C_VIOLET, C_PINK]
    n_cats = len(df_pivot)
    n_ser  = len(df_pivot.columns)
    width  = 0.7 / n_ser
    fig, ax = make_fig(w=max(7, n_cats * 0.8), h=4.5)
    xs = np.arange(n_cats)
    for i, (col, clr) in enumerate(zip(df_pivot.columns, colors)):
        offset = (i - n_ser / 2 + 0.5) * width
        bars = ax.bar(xs + offset, df_pivot[col].values,
                      width=width * 0.9, color=clr, label=str(col), zorder=3, alpha=0.9)
    ax.set_xticks(xs)
    ax.set_xticklabels(df_pivot.index, rotation=38, ha="right", fontsize=8)
    ax.set_title(title, color="#C9D4E8", fontsize=9.5,
                 fontfamily="monospace", pad=10, loc="left")
    ax.legend(fontsize=7.5, framealpha=0, labelcolor=TXT2,
              loc="upper right", ncol=n_ser)
    plt.tight_layout()
    return fig


def donut(sizes, labels, colors, title):
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, colors=colors,
        autopct=lambda p: f"{p:.1f}%" if p > 3 else "",
        startangle=90, pctdistance=0.78,
        wedgeprops={"width": 0.52, "edgecolor": BG, "linewidth": 2},
    )
    for at in autotexts:
        at.set(color="#C9D4E8", fontsize=7.5, fontfamily="monospace")
    # Centro
    ax.text(0, 0, f"{sum(sizes):,}", ha="center", va="center",
            fontsize=16, color="#E8F0FF", fontfamily="monospace", fontweight="bold")
    ax.set_title(title, color="#C9D4E8", fontsize=8.5,
                 fontfamily="monospace", pad=10, loc="center")
    patches = [mpatches.Patch(facecolor=c, label=l) for c, l in zip(colors, labels)]
    ax.legend(handles=patches, fontsize=7.5, framealpha=0, labelcolor=TXT2,
              loc="lower center", ncol=len(labels), bbox_to_anchor=(0.5, -0.05))
    plt.tight_layout()
    return fig


def timeline_ops(df, title):
    """Operaciones por mes, apiladas por tipo."""
    if "mes" not in df.columns or "tipo_op" not in df.columns:
        return None
    pivot = (
        df.groupby(["mes", "tipo_op"]).size().unstack(fill_value=0)
        .sort_index()
    )
    cols_order = [c for c in ["Importación", "Exportación"] if c in pivot.columns]
    pivot = pivot[cols_order]
    meses = pivot.index.tolist()
    n = len(meses)
    fig, ax = make_fig(w=max(7, n * 1.1), h=4)
    bottom = np.zeros(n)
    clrs = [C_CYAN, C_PINK]
    for col, clr in zip(pivot.columns, clrs):
        vals = pivot[col].values.astype(float)
        ax.bar(range(n), vals, bottom=bottom, color=clr, width=0.6,
               alpha=0.88, zorder=3, label=col)
        bottom += vals
    ax.set_xticks(range(n))
    ax.set_xticklabels(meses, rotation=30, ha="right", fontsize=8)
    ax.set_title(title, color="#C9D4E8", fontsize=9.5,
                 fontfamily="monospace", pad=10, loc="left")
    ax.legend(fontsize=7.5, framealpha=0, labelcolor=TXT2, loc="upper left")
    plt.tight_layout()
    return fig


def scatter_lt(df, title):
    """Scatter: ejecutivo vs lead time, tamaño = número de ops."""
    if "lt_total" not in df.columns or "ejecutivo" not in df.columns:
        return None
    g = (
        df.dropna(subset=["lt_total", "ejecutivo"])
        .groupby("ejecutivo")["lt_total"]
        .agg(prom="mean", ops="count")
        .reset_index()
    )
    fig, ax = make_fig(w=9, h=5)
    sc = ax.scatter(g["prom"], g.index, s=g["ops"] * 12,
                    c=g["prom"], cmap="cool", alpha=0.85, zorder=3,
                    vmin=g["prom"].min(), vmax=g["prom"].max())
    ax.set_yticks(range(len(g)))
    ax.set_yticklabels(g["ejecutivo"], fontsize=7.5)
    ax.set_xlabel("Lead Time Promedio (días)", labelpad=6)
    # Línea de promedio global
    prom_global = g["prom"].mean()
    ax.axvline(prom_global, color=C_AMBER, linewidth=1, linestyle="--", alpha=0.7)
    ax.text(prom_global + 0.3, len(g) - 0.5, f"  prom global: {prom_global:.1f}d",
            color=C_AMBER, fontsize=7.5, fontfamily="monospace", va="top")
    ax.set_title(title, color="#C9D4E8", fontsize=9.5,
                 fontfamily="monospace", pad=10, loc="left")
    # Leyenda tamaño
    for ops_val in [10, 30, 60]:
        ax.scatter([], [], s=ops_val * 12, c=TXT, alpha=0.6,
                   label=f"{ops_val} ops")
    ax.legend(fontsize=7, framealpha=0, labelcolor=TXT2,
              loc="lower right", title="# ops", title_fontsize=6.5)
    plt.tight_layout()
    return fig


def heatmap_eje_udn(df, title):
    """Heatmap ejecutivo × aduana."""
    if "ejecutivo" not in df.columns or "aduana" not in df.columns:
        return None
    pivot = df.groupby(["ejecutivo", "aduana"]).size().unstack(fill_value=0)
    fig, ax = make_fig(w=max(6, len(pivot.columns) * 1.5), h=max(4, len(pivot) * 0.45))
    im = ax.imshow(pivot.values, cmap="Blues", aspect="auto",
                   vmin=0, vmax=pivot.values.max())
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, fontsize=8.5)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=7.5)
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            v = pivot.values[i, j]
            if v > 0:
                ax.text(j, i, str(int(v)), ha="center", va="center",
                        fontsize=7.5, color="#E8F0FF" if v > pivot.values.max() * 0.5 else TXT2,
                        fontfamily="monospace")
    ax.set_title(title, color="#C9D4E8", fontsize=9.5,
                 fontfamily="monospace", pad=10, loc="left")
    plt.colorbar(im, ax=ax, fraction=0.03, pad=0.03).ax.tick_params(colors=TXT2, labelsize=7)
    plt.tight_layout()
    return fig


# ==============================
# SIDEBAR
# ==============================

files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".xlsx")]
if not files:
    st.error("No hay archivos `.xlsx` en la carpeta `data/`.")
    st.stop()

with st.sidebar:
    st.markdown("<div style='font-family:DM Mono,monospace;font-size:0.7rem;letter-spacing:0.2em;color:#4A5F80;text-transform:uppercase;margin-bottom:1rem'>⬡ OPS CE</div>", unsafe_allow_html=True)
    selected_file = st.selectbox("Archivo", files, label_visibility="visible")
    st.divider()

file_path = os.path.join(DATA_FOLDER, selected_file)

with st.spinner("Cargando…"):
    try:
        df_det, df_eq, df_ind, df_exp = load_file(file_path)
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        st.stop()

# ── Filtros ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("**Filtros**")

    opts_udn = ["Todas"] + sorted(df_det["aduana"].dropna().astype(str).unique().tolist()) if "aduana" in df_det.columns else ["Todas"]
    filtro_udn = st.selectbox("Aduana / UDN", opts_udn)

    opts_tipo = ["Todos"] + sorted(df_det["tipo_op"].dropna().astype(str).unique().tolist()) if "tipo_op" in df_det.columns else ["Todos"]
    filtro_tipo = st.selectbox("Tipo de operación", opts_tipo)

    opts_eje = ["Todos"] + sorted(df_det["ejecutivo"].dropna().astype(str).unique().tolist()) if "ejecutivo" in df_det.columns else ["Todos"]
    filtro_eje = st.selectbox("Ejecutivo", opts_eje)

    if "mes" in df_det.columns:
        meses_disp = sorted(df_det["mes"].dropna().unique().tolist())
        filtro_mes = st.multiselect("Mes(es)", meses_disp, default=meses_disp)
    else:
        filtro_mes = []

    st.divider()
    st.caption(f"v2.0 · {len(df_det):,} pedimentos")

# ── Aplicar filtros ──────────────────────────────────────────────────────────
dff = df_det.copy()
if filtro_udn != "Todas" and "aduana" in dff.columns:
    dff = dff[dff["aduana"].astype(str) == filtro_udn]
if filtro_tipo != "Todos" and "tipo_op" in dff.columns:
    dff = dff[dff["tipo_op"].astype(str) == filtro_tipo]
if filtro_eje != "Todos" and "ejecutivo" in dff.columns:
    dff = dff[dff["ejecutivo"].astype(str) == filtro_eje]
if filtro_mes and "mes" in dff.columns:
    dff = dff[dff["mes"].isin(filtro_mes)]

# ==============================
# ENCABEZADO
# ==============================

st.markdown('<div class="top-bar"></div>', unsafe_allow_html=True)
st.markdown("# OPS · COMERCIO EXTERIOR")
st.caption(f"Archivo: `{selected_file}` · {len(dff):,} de {len(df_det):,} pedimentos")

# Badges UDN
if "aduana" in df_det.columns:
    udns = df_det["aduana"].dropna().unique().tolist()
    badges = "".join(f'<span class="badge badge-udn">{u}</span>' for u in sorted(udns))
    st.markdown(badges, unsafe_allow_html=True)

st.divider()

# ==============================
# KPIs
# ==============================

imp_mask = dff["tipo_op"].astype(str).str.lower().str.contains("import", na=False) if "tipo_op" in dff.columns else pd.Series(False, index=dff.index)
exp_mask = dff["tipo_op"].astype(str).str.lower().str.contains("export", na=False) if "tipo_op" in dff.columns else pd.Series(False, index=dff.index)
n_eje = dff["ejecutivo"].nunique() if "ejecutivo" in dff.columns else 0
n_clientes = dff["cliente"].nunique() if "cliente" in dff.columns else 0
lt_prom = round(dff["lt_total"].median(), 1) if "lt_total" in dff.columns else "N/A"
lt_max  = int(dff["lt_total"].max()) if "lt_total" in dff.columns and dff["lt_total"].notna().any() else "N/A"

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Ops",        f"{len(dff):,}")
c2.metric("Importaciones",    f"{imp_mask.sum():,}")
c3.metric("Exportaciones",    f"{exp_mask.sum():,}")
c4.metric("Ejecutivos",       f"{n_eje:,}")
c5.metric("Clientes únicos",  f"{n_clientes:,}")
c6.metric("Lead Time Mediano", f"{lt_prom}d" if lt_prom != "N/A" else "N/A")

st.divider()

# ==============================
# PESTAÑAS
# ==============================

tab_eq, tab_ind, tab_exp, tab_lt, tab_heat, tab_trend, tab_raw = st.tabs([
    "EQUIPOS", "INDIVIDUAL", "EXPORTACIÓN", "LEAD TIME", "HEATMAP", "TENDENCIA", "RAW DATA"
])

# ── EQUIPOS ──────────────────────────────────────────────────────────────────
with tab_eq:
    st.subheader("Operaciones por Jefe de Equipo — Importación")
    st.caption("Suma acumulada incluyendo a toda la gente a cargo.")

    if not df_eq.empty:
        col_l, col_r = st.columns([3, 1])
        with col_l:
            serie = df_eq.set_index("Ejecutivo")["Operaciones"].sort_values(ascending=False)
            st.pyplot(bar_h(serie, "TOTAL OPERACIONES POR EQUIPO", color=C_CYAN))
        with col_r:
            # Mini donut por UDN si hay cols de ubicación
            ubi_cols = [c for c in df_eq.columns if c in UBICACIONES and df_eq[c].sum() > 0]
            if ubi_cols:
                sizes = [df_eq[c].sum() for c in ubi_cols]
                clrs  = [C_CYAN, C_VIOLET, C_PINK, C_AMBER, C_GREEN][:len(ubi_cols)]
                st.pyplot(donut(sizes, ubi_cols, clrs, "DIST. POR ADUANA"))
        st.dataframe(
            df_eq.sort_values("Operaciones", ascending=False).reset_index(drop=True),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Sin datos de equipos.")

# ── INDIVIDUAL ───────────────────────────────────────────────────────────────
with tab_ind:
    st.subheader("Operaciones Individuales por Ejecutivo")
    st.caption("Pedimentos asignados directamente, desglosados por aduana.")

    if not df_ind.empty:
        col_l, col_r = st.columns([3, 1])
        with col_l:
            serie = df_ind.set_index("Ejecutivo")["Operaciones"].sort_values(ascending=False)
            st.pyplot(bar_h(serie, "TOTAL OPS INDIVIDUALES", color=C_VIOLET))
        with col_r:
            ubi_cols = [c for c in df_ind.columns if c in UBICACIONES and df_ind[c].sum() > 0]
            if ubi_cols:
                sizes = [df_ind[c].sum() for c in ubi_cols]
                clrs  = [C_CYAN, C_VIOLET, C_PINK, C_AMBER][:len(ubi_cols)]
                st.pyplot(donut(sizes, ubi_cols, clrs, "DIST. POR ADUANA"))

        # Comparativa equipo vs individual (si coinciden nombres)
        eje_comunes = set(df_eq["Ejecutivo"]) & set(df_ind["Ejecutivo"])
        if eje_comunes:
            st.markdown("#### Comparativa equipo vs. individual")
            comp = df_eq.set_index("Ejecutivo")[["Operaciones"]].rename(columns={"Operaciones": "Equipo"}).join(
                df_ind.set_index("Ejecutivo")[["Operaciones"]].rename(columns={"Operaciones": "Individual"}),
                how="inner"
            )
            comp["Equipo restante"] = comp["Equipo"] - comp["Individual"]
            pivot_comp = comp[["Individual", "Equipo restante"]].sort_values("Individual", ascending=False)
            st.pyplot(multi_bar(pivot_comp, "OPS PROPIAS vs. RESTO DEL EQUIPO",
                                colors=[C_VIOLET, C_CYAN]))

        st.dataframe(
            df_ind.sort_values("Operaciones", ascending=False).reset_index(drop=True),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Sin datos individuales.")

# ── EXPORTACIÓN ──────────────────────────────────────────────────────────────
with tab_exp:
    st.subheader("Operaciones de Exportación")
    st.caption("Vista de resumen de la tabla de exportación del reporte.")

    col_l, col_r = st.columns([3, 1])
    with col_l:
        # Exportaciones reales desde tabla detalle (tiene datos reales)
        if "tipo_op" in dff.columns:
            exp_det = dff[dff["tipo_op"].str.lower().str.contains("export", na=False)]
            if not exp_det.empty and "ejecutivo" in exp_det.columns:
                serie_exp = exp_det.groupby("ejecutivo").size().sort_values(ascending=False)
                st.pyplot(bar_h(serie_exp, "EXPORTACIONES POR EJECUTIVO (DETALLE)", color=C_PINK))
                # por aduana
                if "aduana" in exp_det.columns:
                    serie_udn = exp_det.groupby("aduana").size()
                    st.pyplot(bar_v(serie_udn, "EXPORTACIONES POR ADUANA", color=C_PINK))
            else:
                st.info("Sin exportaciones en la selección actual.")
        else:
            st.info("Columna tipo_op no disponible.")
    with col_r:
        if not df_exp.empty:
            st.markdown("**Tabla Resumen (exportación)**")
            st.dataframe(df_exp, use_container_width=True, hide_index=True)

    # Detalle de exportaciones
    if "tipo_op" in dff.columns:
        exp_det = dff[dff["tipo_op"].str.lower().str.contains("export", na=False)]
        if not exp_det.empty:
            st.markdown("#### Clientes de Exportación")
            top_cli = exp_det["cliente"].value_counts().head(10) if "cliente" in exp_det.columns else pd.Series()
            if not top_cli.empty:
                st.pyplot(bar_h(top_cli, "TOP 10 CLIENTES DE EXPORTACIÓN", color=C_AMBER))

# ── LEAD TIME ────────────────────────────────────────────────────────────────
with tab_lt:
    st.subheader("Análisis de Lead Time")
    st.caption("Tiempos entre etapas del proceso aduanero.")

    if "lt_total" not in dff.columns:
        st.info("Columnas de fecha no encontradas.")
    else:
        # Resumen etapas
        etapas = {
            "Llegada → Pago":       "lt_llegada_pago",
            "Pago → Despacho":      "lt_pago_despacho",
            "Despacho → Factura":   "lt_despacho_factura",
            "Total (Llegada→Fact)": "lt_total",
        }
        rows = []
        for label, col in etapas.items():
            if col in dff.columns:
                s = dff[col].dropna()
                rows.append({"Etapa": label, "Mediana (d)": round(s.median(), 1),
                             "Promedio (d)": round(s.mean(), 1),
                             "P90 (d)": round(s.quantile(0.9), 1),
                             "Máx (d)": int(s.max()) if not s.empty else 0})
        if rows:
            df_etapas = pd.DataFrame(rows)
            col_l, col_r = st.columns([2, 3])
            with col_l:
                st.markdown("**Resumen por etapa**")
                st.dataframe(df_etapas, use_container_width=True, hide_index=True)
            with col_r:
                # Barras de medianas
                serie_et = df_etapas.set_index("Etapa")["Mediana (d)"]
                st.pyplot(bar_h(serie_et, "MEDIANA DÍAS POR ETAPA", color=C_AMBER,
                                label_fmt="{:.1f}d"))

        st.divider()

        col_l, col_r = st.columns(2)
        with col_l:
            fig = scatter_lt(dff, "LEAD TIME POR EJECUTIVO (mediana, tamaño=ops)")
            if fig:
                st.pyplot(fig)
        with col_r:
            if "aduana" in dff.columns:
                lt_udn = (
                    dff.dropna(subset=["lt_total", "aduana"])
                    .groupby("aduana")["lt_total"]
                    .agg(["median", "mean", "count"])
                    .rename(columns={"median": "Mediana", "mean": "Promedio", "count": "Ops"})
                    .reset_index()
                )
                lt_udn[["Mediana", "Promedio"]] = lt_udn[["Mediana", "Promedio"]].round(1)
                serie_lt_udn = lt_udn.set_index("aduana")["Mediana"]
                st.pyplot(bar_v(serie_lt_udn, "LEAD TIME MEDIANO POR ADUANA (días)", color=C_AMBER))

        # Lead time outliers
        lt_q90 = dff["lt_total"].quantile(0.9) if "lt_total" in dff.columns else None
        if lt_q90:
            outliers = dff[dff["lt_total"] > lt_q90][["pedimento", "ejecutivo", "cliente", "aduana", "lt_total"]].sort_values("lt_total", ascending=False)
            if not outliers.empty:
                st.markdown(f"**Outliers · Lead time > P90 ({lt_q90:.0f} días)**")
                st.dataframe(outliers.head(20), use_container_width=True, hide_index=True)

# ── HEATMAP ──────────────────────────────────────────────────────────────────
with tab_heat:
    st.subheader("Heatmap Ejecutivo × Aduana")
    st.caption("Concentración de operaciones por ejecutivo y ubicación.")

    col_l, col_r = st.columns(2)
    with col_l:
        fig = heatmap_eje_udn(dff, "OPERACIONES: EJECUTIVO × ADUANA")
        if fig:
            st.pyplot(fig)
        else:
            st.info("Sin datos suficientes.")
    with col_r:
        if "tipo_op" in dff.columns and "aduana" in dff.columns:
            pivot_tipo_udn = dff.groupby(["aduana", "tipo_op"]).size().unstack(fill_value=0)
            if not pivot_tipo_udn.empty:
                st.pyplot(multi_bar(pivot_tipo_udn,
                                    "IMPORTACIÓN vs EXPORTACIÓN POR ADUANA",
                                    colors=[C_CYAN, C_PINK]))

    # Top clientes global
    if "cliente" in dff.columns:
        st.markdown("#### Top Clientes")
        top_cli = dff["cliente"].value_counts().head(15)
        st.pyplot(bar_h(top_cli, "TOP 15 CLIENTES POR OPERACIONES", color=C_GREEN))

# ── TENDENCIA ────────────────────────────────────────────────────────────────
with tab_trend:
    st.subheader("Tendencia Mensual")
    st.caption("Evolución de operaciones a lo largo del tiempo.")

    fig_trend = timeline_ops(dff, "OPERACIONES MENSUALES — IMPORTACIÓN vs EXPORTACIÓN")
    if fig_trend:
        st.pyplot(fig_trend)
    else:
        st.info("Sin datos de fecha disponibles.")

    # Lead time tendencia mensual
    if "lt_total" in dff.columns and "mes" in dff.columns:
        lt_mes = (
            dff.dropna(subset=["lt_total", "mes"])
            .groupby("mes")["lt_total"]
            .agg(["median", "mean"])
            .rename(columns={"median": "Mediana", "mean": "Promedio"})
            .reset_index()
        )
        if not lt_mes.empty:
            lt_mes_series = lt_mes.set_index("mes")[["Mediana", "Promedio"]]
            st.pyplot(multi_bar(lt_mes_series.sort_index(),
                                "LEAD TIME MENSUAL (días)",
                                colors=[C_CYAN, C_AMBER]))

    # Ejecutivos más activos por mes
    if "ejecutivo" in dff.columns and "mes" in dff.columns:
        top5_eje = dff["ejecutivo"].value_counts().head(5).index.tolist()
        dff_top = dff[dff["ejecutivo"].isin(top5_eje)]
        if not dff_top.empty:
            pivot_eje_mes = dff_top.groupby(["mes", "ejecutivo"]).size().unstack(fill_value=0).sort_index()
            clrs5 = [C_CYAN, C_VIOLET, C_PINK, C_AMBER, C_GREEN]
            st.pyplot(multi_bar(pivot_eje_mes,
                                "TOP 5 EJECUTIVOS — OPERACIONES POR MES",
                                colors=clrs5))

# ── RAW DATA ─────────────────────────────────────────────────────────────────
with tab_raw:
    st.subheader("Tabla transaccional completa")

    # Búsqueda rápida
    search = st.text_input("🔍 Buscar (cliente, ejecutivo, pedimento…)", placeholder="Escribe para filtrar…")
    dfr = dff.copy()
    if search:
        mask_search = dfr.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
        dfr = dfr[mask_search]
    st.caption(f"{len(dfr):,} filas")

    cols_display = [c for c in dfr.columns if not c.startswith("lt_") or c == "lt_total"]
    st.dataframe(dfr[cols_display], use_container_width=True, hide_index=True)

    col_dl1, col_dl2 = st.columns([1, 5])
    with col_dl1:
        csv = dfr[cols_display].to_csv(index=False).encode("utf-8")
        st.download_button("⬇ CSV", csv, "operaciones_filtradas.csv", "text/csv")