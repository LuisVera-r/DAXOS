import os
from typing import Tuple
import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# CONFIGURACIÓN DE RUTAS
# ==============================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = os.path.join(BASE_DIR, "data")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

UBICACIONES = ["AICM", "AIFA", "GUADALAJARA", "MONTERREY", "TOLUCA", "QUERETARO"]


def _leer_tabla_resumen(df_raw: pd.DataFrame, header_row: int, next_table_row: int | None = None) -> pd.DataFrame:
    """
    Extrae una tabla de resumen dado el índice de su fila de encabezado.
    next_table_row limita hasta dónde leer (fila de inicio del siguiente bloque).
    """
    header_series = df_raw.iloc[header_row]
    col_inicio = header_series.first_valid_index()

    fin = next_table_row if next_table_row is not None else len(df_raw)
    bloque = df_raw.loc[header_row: fin - 1, col_inicio:].copy()

    encabezados = bloque.iloc[0].astype(str).str.strip().tolist()
    encabezados[0] = "Ejecutivo"
    bloque = bloque.iloc[1:].copy()

    # Índice numérico para evitar columnas duplicadas en pandas
    bloque.columns = list(range(len(encabezados)))
    col_map = {i: encabezados[i] for i in range(len(encabezados))}
    bloque = bloque.rename(columns=col_map)
    bloque = bloque.loc[:, ~bloque.columns.duplicated()]

    # Filtrar filas válidas
    bloque = bloque[bloque["Ejecutivo"].notna()]
    bloque = bloque[
        ~bloque["Ejecutivo"].astype(str).str.upper().isin(["TOTAL", "NAN", ""])
    ]
    bloque = bloque.dropna(how="all")

    cols_ubi = [c for c in bloque.columns if str(c).upper() in UBICACIONES]
    for col in cols_ubi:
        bloque[col] = pd.to_numeric(bloque[col], errors="coerce").fillna(0)

    if "TOTAL" in bloque.columns:
        bloque["Operaciones"] = pd.to_numeric(
            bloque["TOTAL"], errors="coerce"
        ).fillna(bloque[cols_ubi].sum(axis=1))
    else:
        bloque["Operaciones"] = bloque[cols_ubi].sum(axis=1)

    bloque["Ejecutivo"] = bloque["Ejecutivo"].astype(str).str.strip()

    cols_salida = ["Ejecutivo", "Operaciones"] + cols_ubi
    cols_salida = [c for c in cols_salida if c in bloque.columns]
    return bloque[cols_salida].reset_index(drop=True)


# ==============================
# DETECTAR Y EXTRAER LAS 3 TABLAS
# ==============================
def detect_tables(excel_file: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Detecta las tres tablas de resumen dentro del Excel:
      - tabla_equipos:      1ª tabla EJECUTIVO IMPORTACION (jefes + su equipo)
      - tabla_individual:   2ª tabla EJECUTIVO IMPORTACION (ejecución individual)
      - tabla_exportacion:  tabla EJECUTIVO EXPORTACION
    """
    df = pd.read_excel(excel_file, header=None)

    mask_imp = df.apply(
        lambda row: row.astype(str)
        .str.upper()
        .str.contains(r"EJECUTIVO\s+IMPORTACION", regex=True)
        .any(),
        axis=1,
    )
    mask_exp = df.apply(
        lambda row: row.astype(str)
        .str.upper()
        .str.contains(r"EJECUTIVO\s+EXPORTACION", regex=True)
        .any(),
        axis=1,
    )

    rows_imp = df[mask_imp].index.tolist()
    rows_exp = df[mask_exp].index.tolist()

    if len(rows_imp) < 2:
        raise Exception(
            f"Se esperaban ≥2 tablas de importación; "
            f"se encontraron {len(rows_imp)} en {excel_file}"
        )
    if len(rows_exp) < 1:
        raise Exception(f"No se encontró tabla de exportación en {excel_file}")

    # Cada tabla termina donde empieza la siguiente
    tabla_equipos     = _leer_tabla_resumen(df, rows_imp[0], next_table_row=rows_imp[1])
    tabla_individual  = _leer_tabla_resumen(df, rows_imp[1], next_table_row=rows_exp[0])
    tabla_exportacion = _leer_tabla_resumen(df, rows_exp[0])

    return tabla_equipos, tabla_individual, tabla_exportacion


# ==============================
# CARGAR ARCHIVOS EXCEL
# ==============================
def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".xlsx")]
    if not files:
        raise Exception("No hay archivos Excel en la carpeta data")

    equipos_total, individuales_total, exportacion_total = [], [], []

    for file in files:
        path = os.path.join(DATA_FOLDER, file)
        print(f"Procesando: {file}")
        eq, ind, exp = detect_tables(path)
        equipos_total.append(eq)
        individuales_total.append(ind)
        exportacion_total.append(exp)

    return (
        pd.concat(equipos_total,      ignore_index=True),
        pd.concat(individuales_total,  ignore_index=True),
        pd.concat(exportacion_total,   ignore_index=True),
    )


# ==============================
# KPIs
# ==============================
def calculate_kpis(equipos: pd.DataFrame, individuales: pd.DataFrame, exportacion: pd.DataFrame) -> None:
    total_imp    = individuales["Operaciones"].sum()
    total_exp    = exportacion["Operaciones"].sum()
    n_ejecutivos = individuales["Ejecutivo"].nunique()
    n_equipos    = equipos["Ejecutivo"].nunique()
    promedio     = individuales["Operaciones"].mean()

    print("\n===== KPIs =====")
    print(f"Operaciones totales (importación individual): {total_imp:.0f}")
    print(f"Operaciones totales (exportación):            {total_exp:.0f}")
    print(f"Ejecutivos individuales únicos:               {n_ejecutivos}")
    print(f"Jefes de equipo únicos:                       {n_equipos}")
    print(f"Promedio ops/ejecutivo (importación):         {promedio:.2f}")


# ==============================
# GRÁFICAS
# ==============================
def grafica_equipos(equipos: pd.DataFrame) -> None:
    data = equipos.groupby("Ejecutivo")["Operaciones"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(12, 5))
    data.plot(kind="bar", ax=ax, color="steelblue")
    ax.set_title("Operaciones por Jefe de Equipo (Importación)")
    ax.set_xlabel("Jefe de Equipo")
    ax.set_ylabel("Operaciones")
    plt.xticks(rotation=45, ha="right")
    path = os.path.join(OUTPUT_FOLDER, "operaciones_equipos.png")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    print(f"Gráfica guardada: {path}")


def grafica_individual(individuales: pd.DataFrame) -> None:
    top = (
        individuales.groupby("Ejecutivo")["Operaciones"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    fig, ax = plt.subplots(figsize=(12, 5))
    top.plot(kind="bar", ax=ax, color="teal")
    ax.set_title("Top 10 Ejecutivos — Importación Individual")
    ax.set_xlabel("Ejecutivo")
    ax.set_ylabel("Operaciones")
    plt.xticks(rotation=45, ha="right")
    path = os.path.join(OUTPUT_FOLDER, "top_ejecutivos.png")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    print(f"Gráfica guardada: {path}")


def grafica_exportacion(exportacion: pd.DataFrame) -> None:
    data = exportacion.groupby("Ejecutivo")["Operaciones"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(12, 5))
    data.plot(kind="bar", ax=ax, color="darkorange")
    ax.set_title("Operaciones por Ejecutivo — Exportación")
    ax.set_xlabel("Ejecutivo")
    ax.set_ylabel("Operaciones")
    plt.xticks(rotation=45, ha="right")
    path = os.path.join(OUTPUT_FOLDER, "operaciones_exportacion.png")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    print(f"Gráfica guardada: {path}")


# ==============================
# MAIN
# ==============================
def main() -> None:
    equipos, individuales, exportacion = load_data()
    calculate_kpis(equipos, individuales, exportacion)
    grafica_equipos(equipos)
    grafica_individual(individuales)
    grafica_exportacion(exportacion)
    print("\nDashboard generado correctamente ✓")


if __name__ == "__main__":
    main()