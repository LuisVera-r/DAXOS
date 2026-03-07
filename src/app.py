import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ==============================
# CONFIGURACION
# ==============================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = os.path.join(BASE_DIR, "data")

st.set_page_config(page_title="Dashboard Operaciones", layout="wide")

st.title("Dashboard de Operaciones")

# ==============================
# DETECTAR TABLAS
# ==============================

def detect_tables(excel_file):

    df = pd.read_excel(excel_file, header=None)

    header_rows = df[
        df.apply(
            lambda row: row.astype(str)
            .str.contains("Ejecutivo Operación", case=False)
            .any(),
            axis=1,
        )
    ].index.tolist()

    if len(header_rows) < 2:
        st.error("No se detectaron dos tablas en el Excel")
        return None, None

    header1 = header_rows[0]
    header2 = header_rows[1]

    equipos = pd.read_excel(excel_file, skiprows=header1)
    individuales = pd.read_excel(excel_file, skiprows=header2)

    equipos = equipos.dropna(how="all")
    individuales = individuales.dropna(how="all")

    return equipos, individuales


# ==============================
# CARGAR ARCHIVOS
# ==============================

files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".xlsx")]

if not files:
    st.warning("No hay archivos Excel en la carpeta data")
    st.stop()

file_path = os.path.join(DATA_FOLDER, files[0])

equipos, individuales = detect_tables(file_path)

if equipos is None:
    st.stop()

# ==============================
# KPIs
# ==============================

total_operaciones = individuales["Operaciones"].sum()
total_ejecutivos = individuales["Ejecutivo Operación"].nunique()
total_equipos = equipos["Ejecutivo Operación"].nunique()
promedio = round(individuales["Operaciones"].mean(), 2)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Operaciones Totales", total_operaciones)
col2.metric("Ejecutivos", total_ejecutivos)
col3.metric("Equipos", total_equipos)
col4.metric("Promedio por Ejecutivo", promedio)

st.divider()

# ==============================
# GRAFICA EQUIPOS
# ==============================

st.subheader("Operaciones por Equipo")

equipos_group = (
    equipos.groupby("Ejecutivo Operación")["Operaciones"]
    .sum()
    .sort_values(ascending=False)
)

fig1, ax1 = plt.subplots()

equipos_group.plot(kind="bar", ax=ax1)

ax1.set_xlabel("Jefe de Equipo")
ax1.set_ylabel("Operaciones")

st.pyplot(fig1)

# ==============================
# GRAFICA TOP EJECUTIVOS
# ==============================

st.subheader("Top Ejecutivos")

top = (
    individuales.groupby("Ejecutivo Operación")["Operaciones"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

fig2, ax2 = plt.subplots()

top.plot(kind="bar", ax=ax2)

ax2.set_xlabel("Ejecutivo")
ax2.set_ylabel("Operaciones")

st.pyplot(fig2)

# ==============================
# TABLAS
# ==============================

st.subheader("Tabla de Equipos")
st.dataframe(equipos)

st.subheader("Tabla Individual")
st.dataframe(individuales)