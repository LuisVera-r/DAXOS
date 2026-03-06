import pandas as pd
import plotly.express as px
import os

DATA_FOLDER = "../data"
OUTPUT_FILE = "../output/dashboard.html"


def load_data():

    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".xlsx")]

    dfs = []

    for file in files:

        path = os.path.join(DATA_FOLDER, file)

        df = pd.read_excel(path, header=10)

        df = df.dropna(subset=["UDN"])

        df["Fecha Generación"] = pd.to_datetime(
            df["Fecha Generación"], errors="coerce"
        )

        df["Mes"] = df["Fecha Generación"].dt.to_period("M").astype(str)

        dfs.append(df)

    return pd.concat(dfs)


def create_dashboard(data):

    udn = data["UDN"].value_counts().reset_index()
    udn.columns = ["UDN", "Operaciones"]

    fig1 = px.bar(udn, x="UDN", y="Operaciones", title="Operaciones por UDN")

    mes = data.groupby("Mes").size().reset_index(name="Operaciones")

    fig2 = px.line(mes, x="Mes", y="Operaciones", markers=True)

    ejecutivos = data["Ejecutivo"].value_counts().head(10).reset_index()
    ejecutivos.columns = ["Ejecutivo", "Operaciones"]

    fig3 = px.bar(ejecutivos, x="Ejecutivo", y="Operaciones")

    clientes = data["Cliente"].value_counts().head(10).reset_index()
    clientes.columns = ["Cliente", "Operaciones"]

    fig4 = px.bar(clientes, x="Cliente", y="Operaciones")

    from plotly.subplots import make_subplots

    dashboard = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Operaciones por UDN",
            "Operaciones por Mes",
            "Top Ejecutivos",
            "Top Clientes",
        ),
    )

    for trace in fig1.data:
        dashboard.add_trace(trace, row=1, col=1)

    for trace in fig2.data:
        dashboard.add_trace(trace, row=1, col=2)

    for trace in fig3.data:
        dashboard.add_trace(trace, row=2, col=1)

    for trace in fig4.data:
        dashboard.add_trace(trace, row=2, col=2)

    dashboard.write_html(OUTPUT_FILE)

    print("Dashboard generado:", OUTPUT_FILE)


def main():

    data = load_data()

    create_dashboard(data)


if __name__ == "__main__":
    main()