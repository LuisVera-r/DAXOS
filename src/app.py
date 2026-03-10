"""
app.py — Dashboard Operaciones de Comercio Exterior
Todo calculado desde ce_detalle (una sola tabla).
"""
from __future__ import annotations
import json
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import core

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="OPS · CE", layout="wide",
                   initial_sidebar_state="expanded", page_icon="⬡")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;700&family=DM+Mono:wght@400;500&display=swap');
html,body,[class*="css"]{font-family:'Space Grotesk',sans-serif;background:#080C14;color:#C9D4E8}
.block-container{padding:1.6rem 2.2rem 3rem;max-width:1600px}
.top-bar{height:3px;background:linear-gradient(90deg,#00D9FF,#6C63FF,#FF4F7B);
         margin:-1.6rem -2.2rem 1.6rem;border-radius:0 0 4px 4px}
[data-testid="metric-container"]{background:linear-gradient(135deg,#0F1623,#111927);
  border:1px solid #1C2640;border-top:2px solid #00D9FF22;border-radius:12px;padding:1rem 1.3rem .8rem}
[data-testid="metric-container"] label{font-family:'DM Mono',monospace;font-size:.62rem;
  letter-spacing:.16em;text-transform:uppercase;color:#4A5F80}
[data-testid="metric-container"] [data-testid="metric-value"]{font-family:'DM Mono',monospace;
  font-size:1.9rem;font-weight:500;color:#00D9FF;letter-spacing:-.02em}
h1{font-family:'DM Mono',monospace!important;font-size:1rem!important;
   letter-spacing:.25em!important;text-transform:uppercase!important;
   color:#E8F0FF!important;font-weight:500!important}
h2,h3{font-family:'DM Mono',monospace!important;font-size:.68rem!important;
      letter-spacing:.18em!important;text-transform:uppercase!important;
      color:#4A5F80!important;margin-top:1.2rem!important;margin-bottom:.6rem!important}
[data-testid="stSidebar"]{background:#080C14;border-right:1px solid #1C2640}
[data-testid="stSidebar"] label{font-family:'DM Mono',monospace;font-size:.66rem;
  letter-spacing:.1em;text-transform:uppercase;color:#4A5F80}
[data-testid="stTabs"] button{font-family:'DM Mono',monospace;font-size:.66rem;
  letter-spacing:.14em;text-transform:uppercase;color:#4A5F80;padding:.5rem 1rem}
[data-testid="stTabs"] button[aria-selected="true"]{color:#00D9FF;border-bottom:2px solid #00D9FF}
[data-testid="stDataFrame"]{border:1px solid #1C2640;border-radius:10px;overflow:hidden}
hr{border-color:#1C2640;margin:1rem 0}
.badge{display:inline-block;font-family:'DM Mono',monospace;font-size:.6rem;
  letter-spacing:.1em;text-transform:uppercase;padding:.18rem .55rem;
  border-radius:20px;margin:.15rem}
.imp{background:#00D9FF18;color:#00D9FF;border:1px solid #00D9FF33}
.exp{background:#FF4F7B18;color:#FF7B9A;border:1px solid #FF4F7B33}
.udn{background:#6C63FF18;color:#9D97FF;border:1px solid #6C63FF33}
</style>""", unsafe_allow_html=True)

# ── Paleta ──────────────────────────────────────────────────────────────────
C  = dict(cyan="#00D9FF", violet="#6C63FF", pink="#FF4F7B",
          amber="#FFB547", green="#34D399", slate="#4A5F80")
BG = "#0A0F1A"; BG2 = "#0F1623"; GRID = "#1C2640"; TXT = "#4A5F80"; TXT2 = "#8899BB"
CLRS5 = [C["cyan"], C["violet"], C["pink"], C["amber"], C["green"]]


# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICAS
# ══════════════════════════════════════════════════════════════════════════════

def _ax(w: float | int = 9, h: float | int = 4):
    fig, ax = plt.subplots(figsize=(w, h))
    for obj in [fig, ax]:
        try: obj.set_facecolor(BG)
        except: pass
    ax.tick_params(colors=TXT2, labelsize=8)
    for sp in ax.spines.values(): sp.set_edgecolor(GRID)
    ax.yaxis.grid(True, color=GRID, lw=.5, ls="--", alpha=.7)
    ax.set_axisbelow(True)
    return fig, ax


def bar_h(series: pd.Series, title: str, color=None, top_n=None):
    color = color or C["cyan"]
    if top_n: series = series.nlargest(top_n)
    series = series.sort_values()
    n = len(series)
    fig, ax = _ax(9, max(3, n * .42))
    alphas = np.linspace(.55, 1.0, n)
    bars = ax.barh(range(n), series.to_numpy().astype(float), color=color, height=.62, zorder=3)
    for bar, a in zip(bars, alphas): bar.set_alpha(a)
    vmax = series.max() or 1
    for bar, v in zip(bars, series.to_numpy().astype(float)):
        ax.text(v + vmax * .015, bar.get_y() + bar.get_height() / 2,
                f"{v:,.0f}", va="center", ha="left", fontsize=7.5,
                color=TXT2, fontfamily="monospace")
    ax.set_yticks(range(n)); ax.set_yticklabels(series.index, fontsize=8)
    ax.set_xlim(0, vmax * 1.2)
    ax.set_title(title, color="#C9D4E8", fontsize=9, fontfamily="monospace", pad=10, loc="left")
    plt.tight_layout(); return fig


def bar_v(series: pd.Series, title: str, color=None):
    color = color or C["cyan"]
    n = len(series)
    fig, ax = _ax(max(6, n * .75), 4.5)
    bars = ax.bar(range(n), series.to_numpy().astype(float), color=color, width=.6, zorder=3, alpha=.9)
    vmax = series.max() or 1
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + vmax * .02,
                f"{h:,.0f}", ha="center", va="bottom", fontsize=7.5,
                color=TXT2, fontfamily="monospace")
    ax.set_xticks(range(n)); ax.set_xticklabels(series.index, rotation=38, ha="right", fontsize=8)
    ax.set_ylim(0, vmax * 1.2)
    ax.set_title(title, color="#C9D4E8", fontsize=9, fontfamily="monospace", pad=10, loc="left")
    plt.tight_layout(); return fig


def multi_bar(df_pivot: pd.DataFrame, title: str, colors=None):
    colors = colors or CLRS5
    n_cats, n_ser = len(df_pivot), len(df_pivot.columns)
    w = 0.7 / n_ser
    fig, ax = _ax(max(6, n_cats * .8), 4.5)
    xs = np.arange(n_cats)
    for i, (col, clr) in enumerate(zip(df_pivot.columns, colors)):
        offset = (i - n_ser / 2 + .5) * w
        ax.bar(xs + offset, df_pivot[col].to_numpy().astype(float), width=w * .9,
               color=clr, label=str(col), zorder=3, alpha=.9)
    ax.set_xticks(xs); ax.set_xticklabels(df_pivot.index, rotation=38, ha="right", fontsize=8)
    ax.set_title(title, color="#C9D4E8", fontsize=9, fontfamily="monospace", pad=10, loc="left")
    ax.legend(fontsize=7.5, framealpha=0, labelcolor=TXT2, loc="upper right", ncol=n_ser)
    plt.tight_layout(); return fig


def donut(sizes, labels, colors, title):
    fig, ax = plt.subplots(figsize=(4.2, 4.2))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    total = sum(sizes)
    result = ax.pie(
        sizes, colors=colors,
        autopct=lambda p: f"{p:.1f}%" if p > 4 else "",
        startangle=90, pctdistance=.78,
        wedgeprops={"width": .52, "edgecolor": BG, "linewidth": 2})
    wedges, texts, autotexts = result if len(result) == 3 else (result[0], result[1], [])
    for at in autotexts:
        at.set(color="#C9D4E8", fontsize=7.5, fontfamily="monospace")
    ax.text(0, 0, f"{total:,}", ha="center", va="center",
            fontsize=15, color="#E8F0FF", fontfamily="monospace", fontweight="bold")
    ax.set_title(title, color="#C9D4E8", fontsize=8.5,
                 fontfamily="monospace", pad=8, loc="center")
    patches = [mpatches.Patch(facecolor=c, label=l) for c, l in zip(colors, labels)]
    ax.legend(handles=patches, fontsize=7, framealpha=0, labelcolor=TXT2,
              loc="lower center", ncol=3, bbox_to_anchor=(.5, -.06))
    plt.tight_layout(); return fig


def heatmap(df_pivot: pd.DataFrame, title: str):
    fig, ax = _ax(max(5, len(df_pivot.columns) * 1.6), max(3.5, len(df_pivot) * .45))
    im = ax.imshow(df_pivot.to_numpy().astype(float), cmap="Blues", aspect="auto", vmin=0)
    ax.set_xticks(range(len(df_pivot.columns))); ax.set_xticklabels(df_pivot.columns, fontsize=8.5)
    ax.set_yticks(range(len(df_pivot.index)));   ax.set_yticklabels(df_pivot.index, fontsize=7.5)
    vmax = df_pivot.values.max() or 1
    for i in range(len(df_pivot.index)):
        for j in range(len(df_pivot.columns)):
            v = df_pivot.values[i, j]
            if v > 0:
                clr = "#E8F0FF" if v > vmax * .5 else TXT2
                ax.text(j, i, str(int(v)), ha="center", va="center",
                        fontsize=7.5, color=clr, fontfamily="monospace")
    ax.set_title(title, color="#C9D4E8", fontsize=9, fontfamily="monospace", pad=10, loc="left")
    plt.colorbar(im, ax=ax, fraction=.03, pad=.03).ax.tick_params(colors=TXT2, labelsize=7)
    plt.tight_layout(); return fig


def line_trend(df_pivot: pd.DataFrame, title: str, colors=None):
    colors = colors or [C["cyan"], C["pink"]]
    meses  = df_pivot.index.tolist()
    fig, ax = _ax(max(7, len(meses) * 1.1), 4)
    for col, clr in zip(df_pivot.columns, colors):
        vals = df_pivot[col].to_numpy().astype(float)
        ax.plot(range(len(meses)), vals, color=clr, lw=2, label=str(col), zorder=3)
        ax.fill_between(range(len(meses)), vals, alpha=.1, color=clr)
        ax.scatter(range(len(meses)), vals, color=clr, s=35, zorder=4)
    ax.set_xticks(range(len(meses)))
    ax.set_xticklabels(meses, rotation=30, ha="right", fontsize=8)
    ax.set_title(title, color="#C9D4E8", fontsize=9, fontfamily="monospace", pad=10, loc="left")
    ax.legend(fontsize=7.5, framealpha=0, labelcolor=TXT2)
    plt.tight_layout(); return fig


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("<p style='font-family:DM Mono,monospace;font-size:.7rem;"
                "letter-spacing:.2em;color:#4A5F80;text-transform:uppercase'>⬡ OPS · CE</p>",
                unsafe_allow_html=True)

    # ── Subir archivo ──────────────────────────────────────────────────────
    st.markdown("**Subir reporte**")
    uploaded = st.file_uploader("Excel mensual", type=["xlsx"], label_visibility="collapsed")
    if uploaded:
        with st.spinner("Procesando…"):
            try:
                parsed  = core.parse_excel(uploaded.read())
                is_new, msg = core.add_periodo(parsed)
                if is_new:
                    st.success(msg)
                    st.cache_data.clear()
                else:
                    st.warning(msg)
            except Exception as e:
                st.error(f"Error al procesar: {e}")

    st.divider()

    # ── Periodos ───────────────────────────────────────────────────────────
    periodos = core.get_periodos()
    if not periodos:
        st.info("Sube un archivo Excel para comenzar.")
        st.stop()

    st.markdown("**Periodo(s)**")
    sel_periodos = st.multiselect("Periodos", periodos,
                                  default=periodos, label_visibility="collapsed")
    if not sel_periodos:
        st.warning("Selecciona al menos un periodo.")
        st.stop()

    st.divider()

    # ── Cargar detalle filtrado por periodos ───────────────────────────────
    det_full = core.get_detalle()
    det = det_full[det_full["periodo"].isin(sel_periodos)].copy() \
          if "periodo" in det_full.columns else det_full.copy()

    # ── Filtros ────────────────────────────────────────────────────────────
    st.markdown("**Filtros**")
    equipos_cfg = core.load_equipos()

    # Jefe de equipo
    jefes = ["Todos"] + sorted(equipos_cfg.keys())
    sel_jefe = st.selectbox("Jefe de equipo", jefes)
    if sel_jefe != "Todos":
        miembros = core.get_ejecutivos_de_jefe(sel_jefe, equipos_cfg)
        miembros_disp = st.multiselect("Integrantes", miembros, default=miembros)
    else:
        miembros_disp = None

    # Área
    sel_area = st.selectbox("Área", ["Todas", "Importación", "Exportación"])

    # Aduana
    udns = sorted(det["aduana"].dropna().astype(str).unique()) \
           if "aduana" in det.columns else []
    sel_udn = st.multiselect("Aeropuerto / Aduana", udns, default=udns)

    # Cliente
    clientes = sorted(det["cliente"].dropna().astype(str).unique()) \
               if "cliente" in det.columns else []
    sel_cliente = st.multiselect("Cliente", clientes, default=clientes)

    st.divider()

    # ── Gestión histórico ──────────────────────────────────────────────────
    with st.expander("🗑 Gestionar histórico"):
        per_del = st.selectbox("Eliminar periodo", ["—"] + periodos)
        if st.button("Eliminar", type="secondary") and per_del != "—":
            st.success(core.delete_periodo(per_del))
            st.cache_data.clear()
            st.rerun()

    st.caption(f"Histórico: {len(periodos)} periodo(s) · {len(det_full):,} pedimentos totales")
    st.caption(f"Backend: **{core._backend()}**")


# ══════════════════════════════════════════════════════════════════════════════
# APLICAR FILTROS
# ══════════════════════════════════════════════════════════════════════════════
dff = det.copy()

if miembros_disp is not None and "ejecutivo" in dff.columns:
    def _match(name):
        n = str(name).upper()
        return any(m.upper() in n or n in m.upper() for m in miembros_disp) if miembros_disp else True
    dff = dff[dff["ejecutivo"].apply(_match)]

if sel_area != "Todas" and "tipo_op" in dff.columns:
    kw = "import" if sel_area == "Importación" else "export"
    dff = dff[dff["tipo_op"].astype(str).str.lower().str.contains(kw, na=False)]

if sel_udn and "aduana" in dff.columns:
    dff = dff[dff["aduana"].astype(str).isin(sel_udn)]

if sel_cliente and "cliente" in dff.columns:
    dff = dff[dff["cliente"].astype(str).isin(sel_cliente)]


# ══════════════════════════════════════════════════════════════════════════════
# HEADER + KPIs
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="top-bar"></div>', unsafe_allow_html=True)
st.markdown("# DASHBOARD · OPERACIONES CE")

col_info, col_badges = st.columns([2, 3])
with col_info:
    st.caption(f"{len(dff):,} pedimentos · {', '.join(sorted(sel_periodos))}")
with col_badges:
    badges = ""
    if sel_jefe != "Todos":
        badges += f'<span class="badge udn">👤 {sel_jefe}</span>'
    if sel_area != "Todas":
        badge_class = "imp" if sel_area == "Importación" else "exp"
        badges += f'<span class="badge {badge_class}">{sel_area}</span>'
    for u in sel_udn:
        badges += f'<span class="badge udn">{u}</span>'
    if badges:
        st.markdown(badges, unsafe_allow_html=True)

st.divider()

if dff.empty:
    st.warning("Sin datos para la selección actual.")
    st.stop()

# KPIs
imp_n  = dff["tipo_op"].astype(str).str.lower().str.contains("import", na=False).sum() \
          if "tipo_op" in dff.columns else 0
exp_n  = dff["tipo_op"].astype(str).str.lower().str.contains("export", na=False).sum() \
          if "tipo_op" in dff.columns else 0
n_eje  = dff["ejecutivo"].nunique()       if "ejecutivo" in dff.columns else 0
n_cli  = dff["cliente"].nunique()          if "cliente"   in dff.columns else 0
lt_med = round(dff["lt_total"].median(), 1) \
         if "lt_total" in dff.columns and dff["lt_total"].notna().any() else "N/A"

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Ops",         f"{len(dff):,}")
k2.metric("Importaciones",     f"{imp_n:,}")
k3.metric("Exportaciones",     f"{exp_n:,}")
k4.metric("Ejecutivos",        f"{n_eje}")
k5.metric("Clientes",          f"{n_cli}")
k6.metric("Lead Time Mediano", f"{lt_med}d" if lt_med != "N/A" else "N/A")

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS de cálculo (todo desde dff)
# ══════════════════════════════════════════════════════════════════════════════

def _imp(df): return df[df["tipo_op"].astype(str).str.lower().str.contains("import", na=False)] \
                if "tipo_op" in df.columns else df

def _exp(df): return df[df["tipo_op"].astype(str).str.lower().str.contains("export", na=False)] \
               if "tipo_op" in df.columns else pd.DataFrame()

def _ops_por_jefe(df, cfg) -> pd.Series:
    """Ops totales por jefe = suma de todas las ops de sus miembros."""
    rows = {}
    for jefe, miembros in cfg.items():
        def _m(n, mbs=miembros):
            n = str(n).upper()
            return any(m.upper() in n or n in m.upper() for m in mbs)
        rows[jefe] = df[df["ejecutivo"].apply(_m)].shape[0] \
                     if "ejecutivo" in df.columns else 0
    return pd.Series(rows)

def _ops_por_ejecutivo(df) -> pd.Series:
    if "ejecutivo" not in df.columns: return pd.Series()
    return df.groupby("ejecutivo").size().sort_values(ascending=False)

def _ops_por_aduana(df) -> pd.Series:
    if "aduana" not in df.columns: return pd.Series()
    return df.groupby("aduana").size()


# ══════════════════════════════════════════════════════════════════════════════
# PESTAÑAS
# ══════════════════════════════════════════════════════════════════════════════
tabs = st.tabs(["EQUIPOS", "EJECUTIVOS", "EXPORTACIÓN",
                "LEAD TIME", "HEATMAP", "TENDENCIA",
                "EQUIPOS CONFIG", "RAW DATA"])
tab_eq, tab_eje, tab_exp, tab_lt, tab_heat, tab_trend, tab_cfg, tab_raw = tabs


# ── EQUIPOS ──────────────────────────────────────────────────────────────────
with tab_eq:
    st.subheader("Operaciones por Jefe de Equipo")
    ops_jefes = _ops_por_jefe(dff, equipos_cfg)
    ops_jefes = ops_jefes[ops_jefes > 0]

    if ops_jefes.empty:
        st.info("Sin datos. Verifica la configuración de equipos.")
    else:
        c_l, c_r = st.columns([3, 1])
        with c_l:
            st.pyplot(bar_h(ops_jefes.sort_values(), "OPS TOTALES POR JEFE DE EQUIPO", C["cyan"]))
        with c_r:
            udn_dist = _ops_por_aduana(dff)
            if not udn_dist.empty:
                st.pyplot(donut(udn_dist.values.tolist(),
                                udn_dist.index.tolist(),
                                CLRS5[:len(udn_dist)], "DIST. POR ADUANA"))

        # Tabla: jefes × aduana × periodo
        if "aduana" in dff.columns:
            filas = []
            for jefe, miembros in equipos_cfg.items():
                def _m(n, mbs=miembros):
                    n = str(n).upper()
                    return any(m.upper() in n or n in m.upper() for m in mbs)
                sub = dff[dff["ejecutivo"].apply(_m)] if "ejecutivo" in dff.columns else pd.DataFrame()
                if sub.empty: continue
                for (per, adn), g in sub.groupby(["periodo", "aduana"]):
                    filas.append({"Jefe": jefe, "Periodo": per, "Aduana": adn, "Ops": len(g)})
            if filas:
                df_tabla = pd.DataFrame(filas)
                st.dataframe(df_tabla.sort_values(["Periodo", "Ops"], ascending=[True, False]),
                             use_container_width=True, hide_index=True)


# ── EJECUTIVOS ────────────────────────────────────────────────────────────────
with tab_eje:
    st.subheader("Operaciones por Ejecutivo")
    ops_eje = _ops_por_ejecutivo(dff)

    if ops_eje.empty:
        st.info("Sin datos.")
    else:
        c_l, c_r = st.columns([3, 1])
        with c_l:
            st.pyplot(bar_h(ops_eje, "OPS POR EJECUTIVO", C["violet"]))
        with c_r:
            # Donut importación vs exportación
            i_n = imp_n; e_n = exp_n
            if i_n + e_n > 0:
                st.pyplot(donut([i_n, e_n], ["Importación", "Exportación"],
                                [C["cyan"], C["pink"]], "IMP vs EXP"))

        # Comparativa ejecutivo vs equipo al que pertenece
        st.markdown("#### Ejecutivo vs. equipo (ops totales)")
        filas = []
        for jefe, miembros in equipos_cfg.items():
            def _m(n, mbs=miembros):
                n = str(n).upper()
                return any(m.upper() in n or n in m.upper() for m in mbs)
            ops_total_equipo = dff[dff["ejecutivo"].apply(_m)].shape[0] \
                               if "ejecutivo" in dff.columns else 0
            for mb in miembros:
                def _mb(n, m=mb):
                    n = str(n).upper(); m = m.upper()
                    return m in n or n in m
                ops_mb = dff[dff["ejecutivo"].apply(_mb)].shape[0] \
                         if "ejecutivo" in dff.columns else 0
                if ops_mb > 0:
                    filas.append({"Ejecutivo": mb, "Jefe": jefe,
                                  "Ops propias": ops_mb,
                                  "Total equipo": ops_total_equipo})
        if filas:
            df_comp = pd.DataFrame(filas).sort_values("Ops propias", ascending=False)
            st.dataframe(df_comp, use_container_width=True, hide_index=True)


# ── EXPORTACIÓN ───────────────────────────────────────────────────────────────
with tab_exp:
    st.subheader("Operaciones de Exportación")
    exp_df = _exp(dff)

    if exp_df.empty:
        st.info("Sin exportaciones en la selección actual.")
    else:
        c_l, c_r = st.columns(2)
        with c_l:
            st.pyplot(bar_h(_ops_por_ejecutivo(exp_df),
                            "EXPORTACIONES POR EJECUTIVO", C["pink"]))
        with c_r:
            st.pyplot(bar_v(_ops_por_aduana(exp_df),
                            "EXPORTACIONES POR ADUANA", C["pink"]))
        if "cliente" in exp_df.columns:
            top = exp_df["cliente"].value_counts().head(10)
            st.pyplot(bar_h(top, "TOP 10 CLIENTES EXPORTACIÓN", C["amber"]))


# ── LEAD TIME ─────────────────────────────────────────────────────────────────
with tab_lt:
    st.subheader("Análisis de Lead Time")
    etapas = {"Llegada→Pago": "lt_llegada_pago",
              "Pago→Despacho": "lt_pago_despacho",
              "Despacho→Factura": "lt_despacho_factura",
              "Total": "lt_total"}
    rows_et = []
    for lbl, col in etapas.items():
        if col in dff.columns:
            s = dff[col].dropna()
            if not s.empty:
                rows_et.append({"Etapa": lbl, "Mediana": round(s.median(), 1),
                                "Promedio": round(s.mean(), 1),
                                "P90": round(s.quantile(.9), 1),
                                "Máx": int(s.max())})
    if rows_et:
        df_et = pd.DataFrame(rows_et)
        c_l, c_r = st.columns([2, 3])
        with c_l:
            st.dataframe(df_et, use_container_width=True, hide_index=True)
        with c_r:
            st.pyplot(bar_h(df_et.set_index("Etapa")["Mediana"],
                            "MEDIANA DÍAS POR ETAPA", C["amber"]))
        st.divider()

    c_l, c_r = st.columns(2)
    with c_l:
        if "lt_total" in dff.columns and "ejecutivo" in dff.columns:
            g = (dff.dropna(subset=["lt_total", "ejecutivo"])
                 .groupby("ejecutivo")["lt_total"]
                 .agg(prom="mean", ops="count").reset_index())
            if not g.empty:
                fig, ax = _ax(9, max(4, len(g) * .42))
                sc = ax.scatter(g["prom"], range(len(g)), s=g["ops"] * 14,
                                c=g["prom"], cmap="cool", alpha=.85, zorder=3)
                ax.set_yticks(range(len(g))); ax.set_yticklabels(g["ejecutivo"], fontsize=7.5)
                ax.set_xlabel("Lead Time Prom (días)")
                prom_g = g["prom"].mean()
                ax.axvline(prom_g, color=C["amber"], lw=1, ls="--", alpha=.6)
                ax.set_title("LEAD TIME POR EJECUTIVO", color="#C9D4E8",
                             fontsize=9, fontfamily="monospace", pad=10, loc="left")
                plt.tight_layout(); st.pyplot(fig)
    with c_r:
        if "lt_total" in dff.columns and "aduana" in dff.columns:
            lt_udn = dff.dropna(subset=["lt_total"]).groupby("aduana")["lt_total"].median()
            st.pyplot(bar_v(lt_udn, "LEAD TIME MEDIANO POR ADUANA (días)", C["amber"]))

    if "lt_total" in dff.columns:
        q90 = dff["lt_total"].quantile(.9)
        out = (dff[dff["lt_total"] > q90]
               [["pedimento", "ejecutivo", "cliente", "aduana", "lt_total"]]
               .sort_values("lt_total", ascending=False).head(20))
        if not out.empty:
            st.markdown(f"**Outliers · P90 > {q90:.0f} días**")
            st.dataframe(out, use_container_width=True, hide_index=True)


# ── HEATMAP ───────────────────────────────────────────────────────────────────
with tab_heat:
    st.subheader("Heatmap y Distribuciones")
    c_l, c_r = st.columns(2)
    with c_l:
        if "ejecutivo" in dff.columns and "aduana" in dff.columns:
            pv = dff.groupby(["ejecutivo", "aduana"]).size().unstack(fill_value=0)
            st.pyplot(heatmap(pv, "OPS: EJECUTIVO × ADUANA"))
    with c_r:
        if "tipo_op" in dff.columns and "aduana" in dff.columns:
            pv2 = dff.groupby(["aduana", "tipo_op"]).size().unstack(fill_value=0)
            st.pyplot(multi_bar(pv2, "IMP vs EXP POR ADUANA", [C["cyan"], C["pink"]]))
    if "cliente" in dff.columns:
        st.markdown("#### Top clientes")
        st.pyplot(bar_h(dff["cliente"].value_counts().head(15),
                        "TOP 15 CLIENTES", C["green"]))


# ── TENDENCIA ─────────────────────────────────────────────────────────────────
with tab_trend:
    st.subheader("Tendencia Histórica")
    if len(sel_periodos) < 2:
        st.info("Selecciona al menos 2 periodos para ver la tendencia.")
    else:
        if "tipo_op" in dff.columns and "periodo" in dff.columns:
            pv = dff.groupby(["periodo", "tipo_op"]).size().unstack(fill_value=0).sort_index()
            # normalizar nombres de columnas
            col_map = {c: c for c in pv.columns}
            pv = pv.rename(columns=col_map)
            if not pv.empty:
                st.pyplot(line_trend(pv, "OPS POR PERIODO Y TIPO", [C["cyan"], C["pink"]]))

        if "lt_total" in dff.columns and "periodo" in dff.columns:
            lt_per = (dff.dropna(subset=["lt_total"])
                      .groupby("periodo")
                      .apply(lambda x: pd.Series({
                          "Mediana": x["lt_total"].median(),
                          "Promedio": x["lt_total"].mean()
                      }))
                      .sort_index())
            if not lt_per.empty:
                st.pyplot(line_trend(lt_per, "LEAD TIME POR PERIODO (días)",
                                     [C["amber"], C["violet"]]))

        if "ejecutivo" in dff.columns and "periodo" in dff.columns:
            top5 = dff["ejecutivo"].value_counts().head(5).index
            pv_eje = (dff[dff["ejecutivo"].isin(top5)]
                      .groupby(["periodo", "ejecutivo"]).size()
                      .unstack(fill_value=0).sort_index())
            if not pv_eje.empty:
                st.pyplot(multi_bar(pv_eje, "TOP 5 EJECUTIVOS POR PERIODO", CLRS5))


# ── EQUIPOS CONFIG ────────────────────────────────────────────────────────────
with tab_cfg:
    st.subheader("Configurar Jerarquía de Equipos")
    st.caption("Define qué ejecutivos pertenecen a cada jefe. Se guarda automáticamente.")

    equipos_actual = core.load_equipos()
    todos_eje = sorted(dff["ejecutivo"].dropna().unique().tolist()) \
                if "ejecutivo" in dff.columns else []

    c_l, c_r = st.columns([1, 2])
    with c_l:
        sel_jefe_cfg = st.selectbox("Jefe", ["➕ Nuevo jefe"] + list(equipos_actual.keys()),
                                    key="cfg_jefe")
    with c_r:
        if sel_jefe_cfg == "➕ Nuevo jefe":
            nuevo_jefe = st.text_input("Nombre del nuevo jefe")
            mbs_sel    = st.multiselect("Integrantes", todos_eje, key="cfg_nuevos")
            if st.button("Crear equipo") and nuevo_jefe:
                equipos_actual[nuevo_jefe.upper()] = mbs_sel
                core.save_equipos(equipos_actual)
                st.success(f"Equipo **{nuevo_jefe}** creado.")
                st.rerun()
        else:
            mbs_actuales = equipos_actual.get(sel_jefe_cfg, [])
            mbs_edit = st.multiselect("Integrantes", todos_eje,
                                      default=[m for m in mbs_actuales if m in todos_eje],
                                      key="cfg_edit")
            cs, cd = st.columns(2)
            with cs:
                if st.button("💾 Guardar", type="primary"):
                    equipos_actual[sel_jefe_cfg] = mbs_edit
                    core.save_equipos(equipos_actual)
                    st.success("Cambios guardados.")
                    st.rerun()
            with cd:
                if st.button("🗑 Eliminar jefe", type="secondary"):
                    equipos_actual.pop(sel_jefe_cfg, None)
                    core.save_equipos(equipos_actual)
                    st.success(f"Jefe **{sel_jefe_cfg}** eliminado.")
                    st.rerun()

    st.divider()
    st.markdown("**Estructura actual**")
    rows_cfg = [{"Jefe": j, "Integrante": m}
                for j, mbs in equipos_actual.items() for m in mbs]
    if rows_cfg:
        st.dataframe(pd.DataFrame(rows_cfg), use_container_width=True, hide_index=True)

    with st.expander("Editar JSON directamente"):
        json_txt = st.text_area("JSON", value=json.dumps(equipos_actual,
                                ensure_ascii=False, indent=2), height=300)
        if st.button("Aplicar JSON"):
            try:
                core.save_equipos(json.loads(json_txt))
                st.success("Configuración actualizada.")
                st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"JSON inválido: {e}")


# ── RAW DATA ──────────────────────────────────────────────────────────────────
with tab_raw:
    st.subheader("Datos transaccionales")
    search = st.text_input("🔍 Buscar…", placeholder="Cliente, ejecutivo, pedimento…")
    dfr = dff.copy()
    if search:
        mask = dfr.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
        dfr = dfr[mask]

    visible = [c for c in dfr.columns
               if c not in ("lt_llegada_pago", "lt_pago_despacho", "lt_despacho_factura")]
    st.caption(f"{len(dfr):,} filas")
    st.dataframe(dfr[visible], use_container_width=True, hide_index=True)
    st.download_button("⬇ CSV", dfr[visible].to_csv(index=False).encode("utf-8"),
                       "operaciones.csv", "text/csv")
