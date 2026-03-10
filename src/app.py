"""
app.py — Dashboard Operaciones de Comercio Exterior
Incluye: SLA por etapa (días hábiles + feriados MX), asignación de clientes a jefes,
análisis de apoyo entre equipos, selector libre de etapas.
"""
from __future__ import annotations
import json
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import streamlit as st

import core
import sla as SLA
import clientes as CLI

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="OPS · CE", layout="wide",
                   initial_sidebar_state="expanded", page_icon="⬡")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;700&family=DM+Mono:wght@400;500&display=swap');
html,body,[class*="css"]{font-family:'Space Grotesk',sans-serif;background:#080C14;color:#C9D4E8}
.block-container{padding:1.6rem 2.2rem 3rem;max-width:1700px}
.top-bar{height:3px;background:linear-gradient(90deg,#00D9FF,#6C63FF,#FF4F7B);
         margin:-1.6rem -2.2rem 1.6rem;border-radius:0 0 4px 4px}
[data-testid="metric-container"]{background:linear-gradient(135deg,#0F1623,#111927);
  border:1px solid #1C2640;border-top:2px solid #00D9FF22;border-radius:12px;padding:.9rem 1.2rem .7rem}
[data-testid="metric-container"] label{font-family:'DM Mono',monospace;font-size:.6rem;
  letter-spacing:.16em;text-transform:uppercase;color:#4A5F80}
[data-testid="metric-container"] [data-testid="metric-value"]{font-family:'DM Mono',monospace;
  font-size:1.75rem;font-weight:500;color:#00D9FF}
h1{font-family:'DM Mono',monospace!important;font-size:.95rem!important;
   letter-spacing:.22em!important;text-transform:uppercase!important;color:#E8F0FF!important;font-weight:500!important}
h2,h3{font-family:'DM Mono',monospace!important;font-size:.65rem!important;
      letter-spacing:.16em!important;text-transform:uppercase!important;
      color:#4A5F80!important;margin-top:1rem!important;margin-bottom:.5rem!important}
[data-testid="stSidebar"]{background:#080C14;border-right:1px solid #1C2640}
[data-testid="stSidebar"] label{font-family:'DM Mono',monospace;font-size:.64rem;
  letter-spacing:.1em;text-transform:uppercase;color:#4A5F80}
[data-testid="stTabs"] button{font-family:'DM Mono',monospace;font-size:.63rem;
  letter-spacing:.12em;text-transform:uppercase;color:#4A5F80;padding:.45rem .9rem}
[data-testid="stTabs"] button[aria-selected="true"]{color:#00D9FF;border-bottom:2px solid #00D9FF}
[data-testid="stDataFrame"]{border:1px solid #1C2640;border-radius:10px;overflow:hidden}
hr{border-color:#1C2640;margin:.8rem 0}
.badge{display:inline-block;font-family:'DM Mono',monospace;font-size:.58rem;
  letter-spacing:.1em;text-transform:uppercase;padding:.16rem .5rem;border-radius:20px;margin:.12rem}
.imp{background:#00D9FF18;color:#00D9FF;border:1px solid #00D9FF33}
.exp{background:#FF4F7B18;color:#FF7B9A;border:1px solid #FF4F7B33}
.udn{background:#6C63FF18;color:#9D97FF;border:1px solid #6C63FF33}
.ok{background:#34D39918;color:#34D399;border:1px solid #34D39933}
.warn{background:#FFB54718;color:#FFB547;border:1px solid #FFB54733}
.fail{background:#FF4F7B18;color:#FF7B9A;border:1px solid #FF4F7B33}
</style>""", unsafe_allow_html=True)

C  = dict(cyan="#00D9FF", violet="#6C63FF", pink="#FF4F7B",
          amber="#FFB547", green="#34D399", slate="#4A5F80")
BG = "#0A0F1A"; GRID = "#1C2640"; TXT = "#4A5F80"; TXT2 = "#8899BB"
CLRS5 = [C["cyan"], C["violet"], C["pink"], C["amber"], C["green"]]
CLRS8 = CLRS5 + ["#FF6B6B", "#4ECDC4", "#45B7D1"]


# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICAS
# ══════════════════════════════════════════════════════════════════════════════

def _ax(w: float = 9, h: float = 4):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    ax.tick_params(colors=TXT2, labelsize=8)
    for sp in ax.spines.values(): sp.set_edgecolor(GRID)
    ax.yaxis.grid(True, color=GRID, lw=.5, ls="--", alpha=.7)
    ax.set_axisbelow(True)
    return fig, ax


def bar_h(series: pd.Series, title: str, color=None, top_n=None, fmt="{:,.0f}"):
    color = color or C["cyan"]
    if top_n: series = series.nlargest(top_n)
    series = series.sort_values()
    n = len(series)
    fig, ax = _ax(9, max(3, n * .42))
    alphas = np.linspace(.5, 1.0, n)
    vals = series.to_numpy()
    bars = ax.barh(range(n), vals, color=color, height=.62, zorder=3)
    for bar, a in zip(bars, alphas): bar.set_alpha(a)
    vmax = series.max() or 1
    for bar, v in zip(bars, vals):
        ax.text(v + vmax * .015, bar.get_y() + bar.get_height() / 2,
                fmt.format(v), va="center", ha="left", fontsize=7.5,
                color=TXT2, fontfamily="monospace")
    ax.set_yticks(range(n)); ax.set_yticklabels(series.index, fontsize=8)
    ax.set_xlim(0, vmax * 1.2)
    ax.set_title(title, color="#C9D4E8", fontsize=9, fontfamily="monospace", pad=8, loc="left")
    plt.tight_layout(); return fig


def bar_v(series: pd.Series, title: str, color=None):
    color = color or C["cyan"]
    n = len(series)
    fig, ax = _ax(max(5, n * .75), 4.5)
    bars = ax.bar(range(n), series.to_numpy(), color=color, width=.6, zorder=3, alpha=.9)
    vmax = series.max() or 1
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + vmax * .02,
                f"{h:,.0f}", ha="center", va="bottom", fontsize=7.5,
                color=TXT2, fontfamily="monospace")
    ax.set_xticks(range(n)); ax.set_xticklabels(series.index, rotation=38, ha="right", fontsize=8)
    ax.set_ylim(0, vmax * 1.2)
    ax.set_title(title, color="#C9D4E8", fontsize=9, fontfamily="monospace", pad=8, loc="left")
    plt.tight_layout(); return fig


def multi_bar(df_pivot: pd.DataFrame, title: str, colors=None, rot=38):
    colors = colors or CLRS5
    n_cats, n_ser = len(df_pivot), len(df_pivot.columns)
    w = 0.7 / n_ser
    fig, ax = _ax(max(6, n_cats * .8), 4.5)
    xs = np.arange(n_cats)
    for i, (col, clr) in enumerate(zip(df_pivot.columns, colors)):
        offset = (i - n_ser / 2 + .5) * w
        ax.bar(xs + offset, df_pivot[col].to_numpy(), width=w * .9,
               color=clr, label=str(col), zorder=3, alpha=.9)
    ax.set_xticks(xs); ax.set_xticklabels(df_pivot.index, rotation=rot, ha="right", fontsize=8)
    ax.set_title(title, color="#C9D4E8", fontsize=9, fontfamily="monospace", pad=8, loc="left")
    ax.legend(fontsize=7.5, framealpha=0, labelcolor=TXT2, ncol=n_ser)
    plt.tight_layout(); return fig


def donut(sizes, labels, colors, title):
    fig, ax = plt.subplots(figsize=(4, 4))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    result = ax.pie(sizes, colors=colors,
        autopct=lambda p: f"{p:.1f}%" if p > 4 else "",
        startangle=90, pctdistance=.78,
        wedgeprops={"width": .52, "edgecolor": BG, "linewidth": 2})
    wedges = result[0]
    ats = result[2] if len(result) > 2 else result[1]
    for at in ats: at.set(color="#C9D4E8", fontsize=7.5, fontfamily="monospace")
    total = sum(sizes)
    ax.text(0, 0, f"{total:,}", ha="center", va="center",
            fontsize=14, color="#E8F0FF", fontfamily="monospace", fontweight="bold")
    ax.set_title(title, color="#C9D4E8", fontsize=8.5,
                 fontfamily="monospace", pad=6, loc="center")
    patches = [mpatches.Patch(facecolor=c, label=l) for c, l in zip(colors, labels)]
    ax.legend(handles=patches, fontsize=7, framealpha=0, labelcolor=TXT2,
              loc="lower center", ncol=3, bbox_to_anchor=(.5, -.06))
    plt.tight_layout(); return fig


def heatmap(df_pivot: pd.DataFrame, title: str, fmt_int: bool = True):
    fig, ax = _ax(max(5, len(df_pivot.columns) * 1.5),
                  max(3.5, len(df_pivot) * .45))
    df_array = df_pivot.to_numpy().astype(float)
    im = ax.imshow(df_array, cmap="Blues", aspect="auto", vmin=0)
    ax.set_xticks(range(len(df_pivot.columns)))
    ax.set_xticklabels(df_pivot.columns, fontsize=8, rotation=30, ha="right")
    ax.set_yticks(range(len(df_pivot.index)))
    ax.set_yticklabels(df_pivot.index, fontsize=7.5)
    vmax = float(df_array.max()) or 1
    for i in range(len(df_pivot.index)):
        for j in range(len(df_pivot.columns)):
            v = float(df_array[i, j])
            if v > 0:
                clr = "#E8F0FF" if v > vmax * .5 else TXT2
                lbl = str(int(v)) if fmt_int else f"{v:.1f}"
                ax.text(j, i, lbl, ha="center", va="center",
                        fontsize=7.5, color=clr, fontfamily="monospace")
    ax.set_title(title, color="#C9D4E8", fontsize=9, fontfamily="monospace", pad=8, loc="left")
    plt.colorbar(im, ax=ax, fraction=.03, pad=.03).ax.tick_params(colors=TXT2, labelsize=7)
    plt.tight_layout(); return fig


def sla_bar(df_res: pd.DataFrame, title: str):
    """Barra horizontal % cumplimiento SLA por etapa."""
    n = len(df_res)
    fig, ax = _ax(10, max(3, n * .55))
    for idx, (_, row) in enumerate(df_res.iterrows()):
        pct  = row["% Cumple"]
        clr  = C["green"] if pct >= 90 else C["amber"] if pct >= 70 else C["pink"]
        ax.barh(idx, pct, color=clr, height=.55, zorder=3, alpha=.85)
        ax.barh(idx, 100, color=GRID, height=.55, zorder=2, alpha=.4)
        ax.text(pct + 1, idx, f"{pct:.1f}%", va="center", fontsize=8,
                color=TXT2, fontfamily="monospace")
        ax.text(-1, idx, row["Etapa"], va="center", ha="right", fontsize=8, color=TXT2)
    ax.set_xlim(0, 115); ax.set_yticks([])
    ax.axvline(90, color=C["green"], lw=1, ls="--", alpha=.5)
    ax.axvline(70, color=C["amber"], lw=1, ls="--", alpha=.5)
    ax.set_xlabel("% Cumplimiento SLA", color=TXT)
    ax.set_title(title, color="#C9D4E8", fontsize=9, fontfamily="monospace", pad=8, loc="left")
    plt.tight_layout(); return fig


def flujo_apoyo(pivot_apoyo: pd.DataFrame):
    """Heatmap de flujo: quién apoyó a quién (jefe_ejecutivo × jefe_cliente)."""
    if pivot_apoyo.empty:
        return None
    pv = pivot_apoyo.pivot_table(
        index="jefe_ejecutivo", columns="jefe_cliente",
        values="ops_apoyo", aggfunc="sum", fill_value=0)
    return heatmap(pv, "FLUJO DE APOYO: QUIÉN APOYÓ A QUIÉN\n(filas=equipo que apoyó, cols=equipo que recibió)")


def line_trend(df_pivot: pd.DataFrame, title: str, colors=None):
    colors = colors or [C["cyan"], C["pink"]]
    meses = df_pivot.index.tolist()
    fig, ax = _ax(max(7, len(meses) * 1.1), 4)
    for col, clr in zip(df_pivot.columns, colors):
        vals = df_pivot[col].to_numpy(dtype=float)
        ax.plot(range(len(meses)), vals, color=clr, lw=2, label=str(col), zorder=3)
        ax.fill_between(range(len(meses)), vals, alpha=.1, color=clr)
        ax.scatter(range(len(meses)), vals, color=clr, s=35, zorder=4)
    ax.set_xticks(range(len(meses)))
    ax.set_xticklabels(meses, rotation=30, ha="right", fontsize=8)
    ax.set_title(title, color="#C9D4E8", fontsize=9, fontfamily="monospace", pad=8, loc="left")
    ax.legend(fontsize=7.5, framealpha=0, labelcolor=TXT2)
    plt.tight_layout(); return fig


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("<p style='font-family:DM Mono,monospace;font-size:.7rem;"
                "letter-spacing:.2em;color:#4A5F80;text-transform:uppercase'>⬡ OPS · CE</p>",
                unsafe_allow_html=True)

    st.markdown("**Subir reporte**")
    uploaded = st.file_uploader("Excel mensual", type=["xlsx"], label_visibility="collapsed")
    if uploaded:
        with st.spinner("Procesando…"):
            try:
                parsed = core.parse_excel(uploaded.read())
                is_new, msg = core.add_periodo(parsed)
                st.success(msg) if is_new else st.warning(msg)
                if is_new: st.cache_data.clear()
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()

    periodos = core.get_periodos()
    if not periodos:
        st.info("Sube un archivo Excel para comenzar.")
        st.stop()

    st.markdown("**Periodo(s)**")
    sel_periodos = st.multiselect("Periodos", periodos, default=periodos,
                                   label_visibility="collapsed")
    if not sel_periodos:
        st.warning("Selecciona al menos un periodo.")
        st.stop()

    st.divider()

    # Cargar datos
    det_full = core.get_detalle()
    det = det_full[det_full["periodo"].isin(sel_periodos)].copy() \
          if "periodo" in det_full.columns else det_full.copy()

    equipos_cfg    = core.load_equipos()
    clientes_jefe  = core.load_clientes_jefe()
    feriados_extra = core.load_feriados_extra()
    feriados       = SLA.get_feriados(feriados_extra)

    st.markdown("**Filtros**")

    jefes = ["Todos"] + sorted(equipos_cfg.keys())
    sel_jefe = st.selectbox("Jefe de equipo", jefes)
    miembros_disp: list[str] | None = None
    if sel_jefe != "Todos":
        miembros = core.get_ejecutivos_de_jefe(sel_jefe, equipos_cfg)
        miembros_disp = st.multiselect("Integrantes", miembros, default=miembros)

    sel_area = st.selectbox("Área", ["Todas", "Importación", "Exportación"])

    udns = sorted(det["aduana"].dropna().astype(str).unique()) \
           if "aduana" in det.columns else []
    sel_udn = st.multiselect("Aduana", udns, default=udns)

    clientes_lista = sorted(det["cliente"].dropna().astype(str).unique()) \
                     if "cliente" in det.columns else []
    sel_cliente = st.multiselect("Cliente", clientes_lista, default=clientes_lista)

    st.divider()

    # Selector de etapas para SLA
    st.markdown("**Etapas a analizar**")
    etapas_labels = {e["id"]: e["label"] for e in SLA.ETAPAS}
    sel_etapas = st.multiselect("Etapas", list(etapas_labels.keys()),
                                 default=list(etapas_labels.keys()),
                                 format_func=lambda x: etapas_labels[x],
                                 label_visibility="collapsed")

    st.divider()

    with st.expander("🗑 Gestionar histórico"):
        per_del = st.selectbox("Eliminar periodo", ["—"] + periodos)
        if st.button("Eliminar", type="secondary") and per_del != "—":
            st.success(core.delete_periodo(per_del))
            st.cache_data.clear()
            st.rerun()

    st.caption(f"Histórico: {len(periodos)} periodo(s) · {len(det_full):,} pedimentos")
    st.caption(f"Backend: **{core._backend()}**")


# ══════════════════════════════════════════════════════════════════════════════
# APLICAR FILTROS
# ══════════════════════════════════════════════════════════════════════════════
dff = det.copy()

if miembros_disp and "ejecutivo" in dff.columns:
    def _match(n, members=miembros_disp):  # type: ignore[arg-type]
        n = str(n).upper()
        return any(m.upper() in n or n in m.upper() for m in members)
    dff = dff[dff["ejecutivo"].apply(_match)]

if sel_area != "Todas" and "tipo_op" in dff.columns:
    kw = "import" if sel_area == "Importación" else "export"
    dff = dff[dff["tipo_op"].astype(str).str.lower().str.contains(kw, na=False)]

if sel_udn and "aduana" in dff.columns:
    dff = dff[dff["aduana"].astype(str).isin(sel_udn)]

if sel_cliente and "cliente" in dff.columns:
    dff = dff[dff["cliente"].astype(str).isin(sel_cliente)]

# Calcular SLA días hábiles
dff_sla = SLA.calcular_sla(dff, feriados, etapas_activas=sel_etapas)

# Enriquecer con lógica de apoyo
dff_sla = CLI.enriquecer_apoyo(dff_sla, equipos_cfg, clientes_jefe)


# ══════════════════════════════════════════════════════════════════════════════
# HEADER + KPIs
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="top-bar"></div>', unsafe_allow_html=True)
st.markdown("# DASHBOARD · OPERACIONES CE")

col_info, col_badges = st.columns([2, 3])
with col_info:
    st.caption(f"{len(dff_sla):,} pedimentos · {', '.join(sorted(sel_periodos))}")
with col_badges:
    badges = ""
    if sel_jefe != "Todos":
        badges += f'<span class="badge udn">👤 {sel_jefe}</span>'
    if sel_area != "Todas":
        badges += f'<span class="badge {"imp" if sel_area == "Importación" else "exp"}">{sel_area}</span>'
    for u in sel_udn: badges += f'<span class="badge udn">{u}</span>'
    if badges: st.markdown(badges, unsafe_allow_html=True)

st.divider()

if dff_sla.empty:
    st.warning("Sin datos para la selección.")
    st.stop()

# KPIs
imp_n  = dff_sla["tipo_op"].astype(str).str.lower().str.contains("import", na=False).sum() \
          if "tipo_op" in dff_sla.columns else 0
exp_n  = dff_sla["tipo_op"].astype(str).str.lower().str.contains("export", na=False).sum() \
          if "tipo_op" in dff_sla.columns else 0
n_eje  = dff_sla["ejecutivo"].nunique() if "ejecutivo" in dff_sla.columns else 0
n_cli  = dff_sla["cliente"].nunique()    if "cliente"   in dff_sla.columns else 0

# SLA total operativo (desde pago)
dh_op  = dff_sla["dh_total_op"].dropna() if "dh_total_op" in dff_sla.columns else pd.Series()
lt_med = f"{dh_op.median():.1f}dh" if not dh_op.empty else "N/A"

# % cumplimiento global (etapas seleccionadas)
venc_cols = [f"vencido_{e}" for e in sel_etapas if f"vencido_{e}" in dff_sla.columns]
pct_cumple = "N/A"
if venc_cols:
    any_venc = dff_sla[venc_cols].any(axis=1).sum()
    pct_cumple = f"{100 - any_venc / len(dff_sla) * 100:.1f}%"

apoyo_n = int(dff_sla["es_apoyo"].sum()) if "es_apoyo" in dff_sla.columns else 0

k1,k2,k3,k4,k5,k6,k7 = st.columns(7)
k1.metric("Total Ops",      f"{len(dff_sla):,}")
k2.metric("Importaciones",  f"{imp_n:,}")
k3.metric("Exportaciones",  f"{exp_n:,}")
k4.metric("Ejecutivos",     f"{n_eje}")
k5.metric("Clientes",       f"{n_cli}")
k6.metric("LT Operativo",   lt_med)
k7.metric("% SLA Global",   pct_cumple)

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# PESTAÑAS
# ══════════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "EQUIPOS", "EJECUTIVOS", "SLA · TIEMPOS",
    "APOYO ENTRE EQUIPOS", "EXPORTACIÓN",
    "HEATMAP", "TENDENCIA",
    "CONFIG EQUIPOS", "CONFIG CLIENTES", "CONFIG FERIADOS",
    "RAW DATA"
])
(tab_eq, tab_eje, tab_sla, tab_apoyo, tab_exp,
 tab_heat, tab_trend, tab_cfg_eq, tab_cfg_cli,
 tab_cfg_fer, tab_raw) = tabs


# ── EQUIPOS ──────────────────────────────────────────────────────────────────
with tab_eq:
    st.subheader("Operaciones por Jefe de Equipo")

    def _ops_jefe(df, jefe, cfg):
        mbs = cfg.get(jefe, [jefe])
        def _m(n, mbs=mbs):
            n = str(n).upper()
            return any(m.upper() in n or n in m.upper() for m in mbs)
        return df[df["ejecutivo"].apply(_m)] if "ejecutivo" in df.columns else pd.DataFrame()

    ops_jefes = {j: len(_ops_jefe(dff_sla, j, equipos_cfg)) for j in equipos_cfg}
    ops_jefes = {k: v for k, v in ops_jefes.items() if v > 0}

    if not ops_jefes:
        st.info("Sin datos. Configura los equipos en la pestaña CONFIG EQUIPOS.")
    else:
        c_l, c_r = st.columns([3, 1])
        with c_l:
            st.pyplot(bar_h(pd.Series(ops_jefes).sort_values(),
                            "OPS TOTALES POR JEFE DE EQUIPO", C["cyan"]))
        with c_r:
            udn_d = dff_sla.groupby("aduana").size() if "aduana" in dff_sla.columns else pd.Series()
            if not udn_d.empty:
                st.pyplot(donut(udn_d.values.tolist(), udn_d.index.tolist(),
                                CLRS5[:len(udn_d)], "POR ADUANA"))

        # Tabla jefe × aduana × tipo_op
        filas = []
        for jefe in ops_jefes:
            sub = _ops_jefe(dff_sla, jefe, equipos_cfg)
            for (per, adn, tp), g in sub.groupby(["periodo", "aduana", "tipo_op"]):
                filas.append({"Jefe": jefe, "Periodo": per,
                              "Aduana": adn, "Tipo": tp, "Ops": len(g)})
        if filas:
            df_t = pd.DataFrame(filas).sort_values(["Jefe", "Aduana"])
            st.dataframe(df_t, use_container_width=True, hide_index=True)


# ── EJECUTIVOS ────────────────────────────────────────────────────────────────
with tab_eje:
    st.subheader("Operaciones por Ejecutivo")
    ops_eje = dff_sla.groupby("ejecutivo").size().sort_values(ascending=False) \
              if "ejecutivo" in dff_sla.columns else pd.Series()

    if ops_eje.empty:
        st.info("Sin datos.")
    else:
        c_l, c_r = st.columns([3, 1])
        with c_l:
            st.pyplot(bar_h(ops_eje, "OPS POR EJECUTIVO", C["violet"]))
        with c_r:
            if imp_n + exp_n > 0:
                st.pyplot(donut([imp_n, exp_n], ["Importación", "Exportación"],
                                [C["cyan"], C["pink"]], "IMP vs EXP"))

        # Tabla ejecutivo vs equipo con SLA
        st.markdown("#### Detalle ejecutivo · equipo · SLA")
        filas = []
        for jefe, mbs in equipos_cfg.items():
            ops_eq_total = len(_ops_jefe(dff_sla, jefe, equipos_cfg))
            for mb in mbs:
                def _mb(n, m=mb):
                    n = str(n).upper(); m = m.upper()
                    return m in n or n in m
                sub_mb = dff_sla[dff_sla["ejecutivo"].apply(_mb)] \
                         if "ejecutivo" in dff_sla.columns else pd.DataFrame()
                if sub_mb.empty: continue
                venc_mb = 0
                if venc_cols:
                    venc_mb = sub_mb[venc_cols].any(axis=1).sum()
                dh_mb = sub_mb["dh_total_op"].dropna() if "dh_total_op" in sub_mb.columns else pd.Series()
                filas.append({
                    "Jefe": jefe, "Ejecutivo": mb,
                    "Ops propias": len(sub_mb),
                    "Total equipo": ops_eq_total,
                    "LT med (dh)": round(dh_mb.median(), 1) if not dh_mb.empty else None,
                    "Vencidos SLA": int(venc_mb),
                    "% SLA ok": round((len(sub_mb) - venc_mb) / len(sub_mb) * 100, 1) if sub_mb.shape[0] else 0,
                })
        if filas:
            st.dataframe(pd.DataFrame(filas).sort_values(["Jefe", "Ops propias"], ascending=[True, False]),
                         use_container_width=True, hide_index=True)


# ── SLA · TIEMPOS ─────────────────────────────────────────────────────────────
with tab_sla:
    st.subheader("Cumplimiento SLA por Etapa · Días Hábiles")
    st.caption("🟢 ≥90%  🟡 70-90%  🔴 <70%  · Feriados México incluidos")

    df_res = SLA.resumen_sla(dff_sla)
    if df_res.empty:
        st.info("Selecciona al menos una etapa en el sidebar.")
    else:
        c_l, c_r = st.columns([2, 3])
        with c_l:
            # Colorear tabla
            def _color_pct(val):
                if isinstance(val, (int, float)):
                    if val >= 90: return "color:#34D399"
                    if val >= 70: return "color:#FFB547"
                    return "color:#FF7B9A"
                return ""
            st.dataframe(
                df_res.style.map(_color_pct, subset=["% Cumple"]),
                use_container_width=True, hide_index=True
            )
        with c_r:
            st.pyplot(sla_bar(df_res, "% CUMPLIMIENTO SLA POR ETAPA"))

        st.divider()
        st.markdown("#### SLA por ejecutivo (etapa seleccionada)")
        etapa_sel = st.selectbox("Ver etapa",
                                  [e["id"] for e in SLA.ETAPAS if e["id"] in sel_etapas],
                                  format_func=lambda x: etapas_labels[x],
                                  key="sla_etapa_sel")
        if etapa_sel and "ejecutivo" in dff_sla.columns:
            col_dh   = f"dh_{etapa_sel}"
            col_venc = f"vencido_{etapa_sel}"
            if col_dh in dff_sla.columns:
                g = (dff_sla.dropna(subset=[col_dh, "ejecutivo"])
                     .groupby("ejecutivo")
                     .agg(
                         mediana=(col_dh, "median"),
                         ops=(col_dh, "count"),
                         vencidos=(col_venc, "sum") if col_venc in dff_sla.columns else (col_dh, lambda x: 0)
                     ).reset_index()
                     .sort_values("mediana", ascending=False))
                g["% SLA ok"] = ((g["ops"] - g["vencidos"]) / g["ops"] * 100).round(1)
                c1, c2 = st.columns(2)
                with c1:
                    st.pyplot(bar_h(g.set_index("ejecutivo")["mediana"].sort_values(),
                                    f"MEDIANA DH · {etapas_labels[etapa_sel]}", C["amber"],
                                    fmt="{:.1f}"))
                with c2:
                    st.dataframe(g[["ejecutivo", "ops", "mediana", "vencidos", "% SLA ok"]],
                                 use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("#### Selector libre de fechas · lead time personalizado")
        col_fechas = [c for c in ["f_llegada", "f_revalida", "f_previo",
                                   "f_pago", "f_despacho", "f_contabilidad",
                                   "f_facturacion"] if c in dff_sla.columns]
        lbl_map = {"f_llegada": "Llegada", "f_revalida": "Recolección",
                   "f_previo": "Previo", "f_pago": "Pago",
                   "f_despacho": "Despacho", "f_contabilidad": "Contabilidad",
                   "f_facturacion": "Facturación"}
        cs, ce = st.columns(2)
        with cs:
            default_idx = col_fechas.index("f_pago") if "f_pago" in col_fechas else (0 if col_fechas else 0)
            col_inicio = st.selectbox("Desde", col_fechas,
                                       format_func=lambda x: str(lbl_map.get(x, x)),
                                       index=default_idx,
                                       key="lt_inicio")
        with ce:
            end_idx = len(col_fechas) - 1 if col_fechas else 0
            col_fin = st.selectbox("Hasta", col_fechas,
                                    format_func=lambda x: str(lbl_map.get(x, x)),
                                    index=end_idx,
                                    key="lt_fin")
        if col_inicio != col_fin:
            dff_sla["_lt_custom"] = dff_sla.apply(
                lambda r: SLA.dias_habiles(r[col_inicio], r[col_fin], feriados), axis=1)
            s = dff_sla["_lt_custom"].dropna()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Mediana (dh)", f"{s.median():.1f}")
            c2.metric("Promedio (dh)", f"{s.mean():.1f}")
            c3.metric("P90 (dh)", f"{s.quantile(.9):.1f}")
            c4.metric("Máx (dh)", f"{int(s.max())}")
            if "ejecutivo" in dff_sla.columns:
                g2 = dff_sla.dropna(subset=["_lt_custom", "ejecutivo"]) \
                             .groupby("ejecutivo")["_lt_custom"].median().sort_values()
                st.pyplot(bar_h(g2, f"MEDIANA DH · {lbl_map.get(col_inicio,col_inicio)} → {lbl_map.get(col_fin,col_fin)}",
                                C["violet"], fmt="{:.1f}"))


# ── APOYO ENTRE EQUIPOS ───────────────────────────────────────────────────────
with tab_apoyo:
    st.subheader("Análisis de Apoyo entre Equipos")

    if not clientes_jefe:
        st.info("⚠️ Primero asigna clientes a jefes en la pestaña **CONFIG CLIENTES** para activar el análisis de apoyo.")
    elif apoyo_n == 0:
        st.success("No se detectaron ops de apoyo en la selección actual.")
    else:
        st.caption(f"Se detectaron **{apoyo_n:,}** operaciones de apoyo "
                   f"({apoyo_n / len(dff_sla) * 100:.1f}% del total)")

        # KPIs de apoyo
        a1, a2, a3 = st.columns(3)
        a1.metric("Ops de apoyo", f"{apoyo_n:,}")
        a2.metric("Ops propias",  f"{len(dff_sla) - apoyo_n:,}")
        a3.metric("% Apoyo",      f"{apoyo_n / len(dff_sla) * 100:.1f}%")

        st.divider()

        # Resumen por jefe
        df_res_apoyo = CLI.resumen_por_jefe(dff_sla)
        c_l, c_r = st.columns(2)
        with c_l:
            st.markdown("#### Ops propias vs apoyo dado por jefe")
            if not df_res_apoyo.empty:
                pivot_ap = df_res_apoyo.set_index("Jefe")[["Ops propias", "Apoyo dado"]].sort_values("Ops propias", ascending=False)
                st.pyplot(multi_bar(pivot_ap, "OPS PROPIAS vs APOYO DADO",
                                    [C["cyan"], C["amber"]]))
        with c_r:
            st.markdown("#### Apoyo recibido por jefe")
            if not df_res_apoyo.empty:
                rec = df_res_apoyo.set_index("Jefe")["Apoyo recibido"].sort_values()
                if rec.sum() > 0:
                    st.pyplot(bar_h(rec, "APOYO RECIBIDO POR JEFE", C["pink"]))

        st.divider()

        # Mapa de flujo
        st.markdown("#### Mapa de flujo · quién apoyó a quién")
        pivot_flujo = CLI.tabla_apoyo_entre_jefes(dff_sla)
        if not pivot_flujo.empty:
            fig_flujo = flujo_apoyo(pivot_flujo)
            if fig_flujo:
                st.pyplot(fig_flujo)
            with st.expander("Ver tabla detalle de flujo"):
                st.dataframe(pivot_flujo, use_container_width=True, hide_index=True)

        st.divider()

        # Ranking clientes con más apoyo externo
        st.markdown("#### Clientes con más apoyo externo recibido")
        df_cli_apoyo = CLI.clientes_con_mas_apoyo(dff_sla)
        if not df_cli_apoyo.empty:
            c1, c2 = st.columns([2, 1])
            with c1:
                st.pyplot(bar_h(df_cli_apoyo.set_index("cliente")["ops_apoyo"],
                                "TOP CLIENTES POR OPS DE APOYO RECIBIDAS", C["pink"]))
            with c2:
                st.dataframe(df_cli_apoyo, use_container_width=True, hide_index=True)

        st.divider()

        # Comparativa ops propias vs apoyo por ejecutivo
        st.markdown("#### Ops propias vs apoyo por ejecutivo")
        if "ejecutivo" in dff_sla.columns:
            pivot_eje = (dff_sla.groupby(["ejecutivo", "tipo_participacion"])
                         .size().unstack(fill_value=0))
            if "Propia" in pivot_eje.columns or "Apoyo dado" in pivot_eje.columns:
                cols_piv = [c for c in ["Propia", "Apoyo dado"] if c in pivot_eje.columns]
                pivot_eje = pivot_eje[cols_piv].sort_values(
                    cols_piv[0], ascending=False).head(20)
                st.pyplot(multi_bar(pivot_eje,
                                    "OPS PROPIAS vs APOYO DADO POR EJECUTIVO",
                                    [C["cyan"], C["amber"]]))


# ── EXPORTACIÓN ───────────────────────────────────────────────────────────────
with tab_exp:
    st.subheader("Operaciones de Exportación")
    exp_df = dff_sla[dff_sla["tipo_op"].astype(str).str.lower()
                     .str.contains("export", na=False)] \
             if "tipo_op" in dff_sla.columns else pd.DataFrame()
    if exp_df.empty:
        st.info("Sin exportaciones en la selección.")
    else:
        c_l, c_r = st.columns(2)
        with c_l:
            if "ejecutivo" in exp_df.columns:
                st.pyplot(bar_h(exp_df.groupby("ejecutivo").size().sort_values(),
                                "EXPORTACIONES POR EJECUTIVO", C["pink"]))
        with c_r:
            if "aduana" in exp_df.columns:
                st.pyplot(bar_v(exp_df.groupby("aduana").size(),
                                "EXPORTACIONES POR ADUANA", C["pink"]))
        if "cliente" in exp_df.columns:
            st.pyplot(bar_h(exp_df["cliente"].value_counts().head(10),
                            "TOP 10 CLIENTES EXPORTACIÓN", C["amber"]))


# ── HEATMAP ───────────────────────────────────────────────────────────────────
with tab_heat:
    st.subheader("Heatmaps")
    c_l, c_r = st.columns(2)
    with c_l:
        if "ejecutivo" in dff_sla.columns and "aduana" in dff_sla.columns:
            pv = dff_sla.groupby(["ejecutivo", "aduana"]).size().unstack(fill_value=0)
            st.pyplot(heatmap(pv, "OPS: EJECUTIVO × ADUANA"))
    with c_r:
        if "tipo_op" in dff_sla.columns and "aduana" in dff_sla.columns:
            pv2 = dff_sla.groupby(["aduana", "tipo_op"]).size().unstack(fill_value=0)
            st.pyplot(multi_bar(pv2, "IMP vs EXP POR ADUANA", [C["cyan"], C["pink"]]))
    if "cliente" in dff_sla.columns:
        st.pyplot(bar_h(dff_sla["cliente"].value_counts().head(15),
                        "TOP 15 CLIENTES", C["green"]))


# ── TENDENCIA ─────────────────────────────────────────────────────────────────
with tab_trend:
    st.subheader("Tendencia Histórica")
    if len(sel_periodos) < 2:
        st.info("Selecciona ≥2 periodos para ver tendencia.")
    else:
        if "tipo_op" in dff_sla.columns and "periodo" in dff_sla.columns:
            pv = dff_sla.groupby(["periodo", "tipo_op"]).size().unstack(fill_value=0).sort_index()
            if not pv.empty:
                st.pyplot(line_trend(pv, "OPS POR PERIODO Y TIPO", [C["cyan"], C["pink"]]))

        # SLA cumplimiento por periodo
        if "periodo" in dff_sla.columns and venc_cols:
            pct_per = (dff_sla.groupby("periodo")
                       .apply(lambda g: 100 - g[venc_cols].any(axis=1).mean() * 100)
                       .rename("% SLA cumplido").sort_index())
            if not pct_per.empty:
                fig, ax = _ax(max(6, len(pct_per) * 1.1), 4)
                pct_vals = pct_per.to_numpy()
                ax.plot(range(len(pct_per)), pct_vals, color=C["green"], lw=2, zorder=3)
                ax.fill_between(range(len(pct_per)), pct_vals, alpha=.1, color=C["green"])
                ax.scatter(range(len(pct_per)), pct_vals, color=C["green"], s=35, zorder=4)
                ax.axhline(90, color=C["amber"], lw=1, ls="--", alpha=.6)
                ax.set_xticks(range(len(pct_per)))
                ax.set_xticklabels(pct_per.index, rotation=30, ha="right", fontsize=8)
                ax.set_ylim(0, 105)
                ax.set_title("% CUMPLIMIENTO SLA POR PERIODO", color="#C9D4E8",
                             fontsize=9, fontfamily="monospace", pad=8, loc="left")
                plt.tight_layout()
                st.pyplot(fig)

        if "ejecutivo" in dff_sla.columns and "periodo" in dff_sla.columns:
            top5 = dff_sla["ejecutivo"].value_counts().head(5).index
            pv_eje = (dff_sla[dff_sla["ejecutivo"].isin(top5)]
                      .groupby(["periodo", "ejecutivo"]).size()
                      .unstack(fill_value=0).sort_index())
            if not pv_eje.empty:
                st.pyplot(multi_bar(pv_eje, "TOP 5 EJECUTIVOS POR PERIODO", CLRS5))


# ── CONFIG EQUIPOS ────────────────────────────────────────────────────────────
with tab_cfg_eq:
    st.subheader("Configurar Equipos")
    equipos_actual = core.load_equipos()
    todos_eje = sorted(dff_sla["ejecutivo"].dropna().unique()) \
                if "ejecutivo" in dff_sla.columns else []

    c_l, c_r = st.columns([1, 2])
    with c_l:
        sel_j = st.selectbox("Jefe", ["➕ Nuevo"] + list(equipos_actual.keys()), key="cfge_j")
    with c_r:
        if sel_j == "➕ Nuevo":
            nj = st.text_input("Nombre del nuevo jefe")
            mbs = st.multiselect("Integrantes", todos_eje, key="cfge_n")
            if st.button("Crear") and nj:
                equipos_actual[nj.upper()] = mbs
                core.save_equipos(equipos_actual); st.success("Creado."); st.rerun()
        else:
            mbs_e = st.multiselect("Integrantes", todos_eje,
                                    default=[m for m in equipos_actual.get(sel_j, []) if m in todos_eje],
                                    key="cfge_e")
            cs, cd = st.columns(2)
            with cs:
                if st.button("💾 Guardar", type="primary", key="cfge_save"):
                    equipos_actual[sel_j] = mbs_e
                    core.save_equipos(equipos_actual); st.success("Guardado."); st.rerun()
            with cd:
                if st.button("🗑 Eliminar", type="secondary", key="cfge_del"):
                    equipos_actual.pop(sel_j, None)
                    core.save_equipos(equipos_actual); st.success("Eliminado."); st.rerun()

    st.divider()
    rows_e = [{"Jefe": j, "Integrante": m}
              for j, mbs in equipos_actual.items() for m in mbs]
    if rows_e:
        st.dataframe(pd.DataFrame(rows_e), use_container_width=True, hide_index=True)

    with st.expander("Editar JSON"):
        jt = st.text_area("JSON", value=json.dumps(equipos_actual,
                           ensure_ascii=False, indent=2), height=250)
        if st.button("Aplicar JSON", key="cfge_json"):
            try:
                core.save_equipos(json.loads(jt)); st.success("OK"); st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"JSON inválido: {e}")


# ── CONFIG CLIENTES POR JEFE ──────────────────────────────────────────────────
with tab_cfg_cli:
    st.subheader("Asignación de Clientes por Jefe")
    st.caption("Define qué clientes son responsabilidad de cada jefe. "
               "Esto permite detectar automáticamente las operaciones de apoyo.")

    cli_actual = core.load_clientes_jefe()
    todos_clientes = sorted(dff_sla["cliente"].dropna().astype(str).unique()) \
                     if "cliente" in dff_sla.columns else []
    jefes_lista = list(equipos_cfg.keys())

    if not jefes_lista:
        st.warning("Primero configura los jefes de equipo en la pestaña CONFIG EQUIPOS.")
    else:
        c_l, c_r = st.columns([1, 2])
        with c_l:
            sel_jcli = st.selectbox("Jefe", jefes_lista, key="cfgcli_j")
        with c_r:
            clientes_actuales = cli_actual.get(sel_jcli, [])
            clientes_nuevos = st.multiselect(
                "Clientes a cargo", todos_clientes,
                default=[c for c in clientes_actuales if c in todos_clientes],
                key="cfgcli_sel"
            )
            if st.button("💾 Guardar asignación", type="primary", key="cfgcli_save"):
                cli_actual[sel_jcli] = clientes_nuevos
                core.save_clientes_jefe(cli_actual)
                st.success(f"Asignados {len(clientes_nuevos)} clientes a **{sel_jcli}**.")
                st.rerun()

        st.divider()
        st.markdown("**Asignaciones actuales**")
        rows_cli = [{"Jefe": j, "Cliente": c}
                    for j, cls in cli_actual.items() for c in cls]
        if rows_cli:
            df_cli_t = pd.DataFrame(rows_cli)
            # Mostrar con conteo de ops reales
            if "cliente" in dff_sla.columns:
                ops_por_cli = dff_sla.groupby("cliente").size().rename("Ops (filtro actual)")
                df_cli_t = df_cli_t.merge(ops_por_cli, left_on="Cliente",
                                           right_index=True, how="left")
            st.dataframe(df_cli_t.sort_values("Jefe"), use_container_width=True, hide_index=True)

            # Clientes sin asignar
            asignados = set(c for cls in cli_actual.values() for c in cls)
            sin_asignar = [c for c in todos_clientes if c not in asignados]
            if sin_asignar:
                with st.expander(f"⚠️ {len(sin_asignar)} clientes sin asignar"):
                    st.dataframe(pd.DataFrame({"Cliente": sin_asignar}),
                                 use_container_width=True, hide_index=True)
        else:
            st.info("No hay asignaciones aún. Selecciona un jefe y sus clientes arriba.")

        with st.expander("Editar JSON directamente"):
            jt2 = st.text_area("JSON", value=json.dumps(cli_actual,
                                ensure_ascii=False, indent=2), height=250)
            if st.button("Aplicar JSON", key="cfgcli_json"):
                try:
                    core.save_clientes_jefe(json.loads(jt2)); st.success("OK"); st.rerun()
                except json.JSONDecodeError as e:
                    st.error(f"JSON inválido: {e}")


# ── CONFIG FERIADOS ───────────────────────────────────────────────────────────
with tab_cfg_fer:
    st.subheader("Feriados Adicionales")
    st.caption("Los feriados oficiales México ya están incluidos automáticamente. "
               "Agrega aquí feriados aduanales o días puente específicos.")

    feriados_extra_actual = core.load_feriados_extra()

    # Mostrar feriados oficiales del año actual como referencia
    with st.expander("📅 Ver feriados oficiales México incluidos"):
        import datetime
        anos = [datetime.date.today().year, datetime.date.today().year + 1]
        fer_of = SLA.get_feriados([])
        fer_of_df = pd.DataFrame({"Fecha": fer_of.strftime("%Y-%m-%d"),
                                   "Día": fer_of.strftime("%A")})
        st.dataframe(fer_of_df[fer_of_df["Fecha"] >= f"{min(anos)}-01-01"]
                     .head(20), use_container_width=True, hide_index=True)

    st.markdown("**Agregar feriado extra**")
    c1, c2 = st.columns([1, 2])
    with c1:
        nueva_fecha = st.date_input("Fecha", key="fer_nueva")
    with c2:
        desc = st.text_input("Descripción (opcional)", key="fer_desc")
        if st.button("➕ Agregar", key="fer_add"):
            iso = str(nueva_fecha)
            if iso not in feriados_extra_actual:
                feriados_extra_actual.append(iso)
                feriados_extra_actual.sort()
                core.save_feriados_extra(feriados_extra_actual)
                st.success(f"Feriado **{iso}** agregado.")
                st.rerun()
            else:
                st.warning("Esa fecha ya está en la lista.")

    if feriados_extra_actual:
        st.markdown("**Feriados extra configurados**")
        for i, f in enumerate(feriados_extra_actual):
            c1, c2 = st.columns([3, 1])
            c1.write(f)
            if c2.button("🗑", key=f"fer_del_{i}"):
                feriados_extra_actual.remove(f)
                core.save_feriados_extra(feriados_extra_actual)
                st.rerun()
    else:
        st.info("Sin feriados extra configurados.")


# ── RAW DATA ──────────────────────────────────────────────────────────────────
with tab_raw:
    st.subheader("Datos transaccionales")
    search = st.text_input("🔍 Buscar…", placeholder="Cliente, ejecutivo, pedimento…")
    dfr = dff_sla.copy()
    if search:
        mask = dfr.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
        dfr = dfr[mask]

    # Columnas visibles (excluir internas)
    excluir = {"dh_total_op", "jefe_ejecutivo", "jefe_cliente",
               "es_apoyo", "tipo_participacion"}
    visible = [c for c in dfr.columns
               if not c.startswith("dh_") and not c.startswith("vencido_")
               and c not in excluir]
    # Añadir columnas útiles si existen
    extra = [c for c in ["dh_total_op", "tipo_participacion", "jefe_ejecutivo"]
             if c in dfr.columns]
    visible = visible + extra

    st.caption(f"{len(dfr):,} filas · {len(visible)} columnas")
    st.dataframe(dfr[visible], use_container_width=True, hide_index=True)
    st.download_button("⬇ CSV", dfr[visible].to_csv(index=False).encode("utf-8"),
                       "operaciones.csv", "text/csv")
