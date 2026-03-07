import os
import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# CONFIGURACIÓN DE RUTAS
# ==============================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_FOLDER = os.path.join(BASE_DIR, "data")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ==============================
# DETECTAR TABLAS EN EL EXCEL
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
        raise Exception("No se detectaron dos tablas en el Excel")

    header1 = header_rows[0]
    header2 = header_rows[1]

    tabla_equipos = pd.read_excel(excel_file, skiprows=header1)
    tabla_individual = pd.read_excel(excel_file, skiprows=header2)

    tabla_equipos = tabla_equipos.dropna(how="all")
    tabla_individual = tabla_individual.dropna(how="all")

    return tabla_equipos, tabla_individual


# ==============================
# CARGAR ARCHIVOS EXCEL
# ==============================

def load_data():

    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".xlsx")]

    if not files:
        raise Exception("No hay archivos Excel en la carpeta data")

    equipos_total = []
    individuales_total = []

    for file in files:

        path = os.path.join(DATA_FOLDER, file)

        print(f"Procesando: {file}")

        equipos, individuales = detect_tables(path)

        equipos_total.append(equipos)
        individuales_total.append(individuales)

    equipos_df = pd.concat(equipos_total, ignore_index=True)
    individuales_df = pd.concat(individuales_total, ignore_index=True)

    return equipos_df, individuales_df


# ==============================
# KPIs
# ==============================

def calculate_kpis(equipos, individuales):

    total_operaciones = individuales["Operaciones"].sum()

    total_ejecutivos = individuales["Ejecutivo Operación"].nunique()

    total_equipos = equipos["Ejecutivo Operación"].nunique()

    promedio = individuales["Operaciones"].mean()

    print("\n===== KPIs =====")

    print("Operaciones totales:", total_operaciones)
    print("Total ejecutivos:", total_ejecutivos)
    print("Total equipos:", total_equipos)
    print("Promedio operaciones por ejecutivo:", round(promedio, 2))


# ==============================
# GRAFICA EQUIPOS
# ==============================

def grafica_equipos(equipos):

    equipos_group = (
        equipos.groupby("Ejecutivo Operación")["Operaciones"]
        .sum()
        .sort_values(ascending=False)
    )

    plt.figure()

    equipos_group.plot(kind="bar")

    plt.title("Operaciones por Equipo")
    plt.xlabel("Jefe de Equipo")
    plt.ylabel("Operaciones")

    path = os.path.join(OUTPUT_FOLDER, "operaciones_equipos.png")

    plt.tight_layout()
    plt.savefig(path)

    print("Gráfica guardada:", path)


# ==============================
# GRAFICA INDIVIDUAL
# ==============================

def grafica_individual(individuales):

    top = (
        individuales.groupby("Ejecutivo Operación")["Operaciones"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    plt.figure()

    top.plot(kind="bar")

    plt.title("Top 10 Ejecutivos")
    plt.xlabel("Ejecutivo")
    plt.ylabel("Operaciones")

    path = os.path.join(OUTPUT_FOLDER, "top_ejecutivos.png")

    plt.tight_layout()
    plt.savefig(path)

    print("Gráfica guardada:", path)


# ==============================
# MAIN
# ==============================

def main():

    equipos, individuales = load_data()

    calculate_kpis(equipos, individuales)

    grafica_equipos(equipos)

    grafica_individual(individuales)

    print("\nDashboard generado correctamente")


if __name__ == "__main__":
    main()