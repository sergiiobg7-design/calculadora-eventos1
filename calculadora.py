import streamlit as st
import pandas as pd
import plotly.express as px

# --- Función formato español ---
def formato_es(numero):
    return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- Cargar datos desde Excel (hoja 2025) ---
@st.cache_data
def cargar_datos():
    df = pd.read_excel("gasto_medio.xlsx", sheet_name="2025")

    # Nos quedamos solo con las columnas útiles
    df = df.iloc[:, :5].copy()
    df.columns = ["TIPO", "METRICA", "CONGRESO", "JORNADA", "CONVENCIÓN"]

    # Eliminar filas completamente vacías
    df = df.dropna(how="all")

    # Limpiar texto
    df["TIPO"] = df["TIPO"].astype(str).str.strip()
    df["METRICA"] = df["METRICA"].astype(str).str.strip()

    # Convertir %PARTICIPACION si viniera en decimal
    mask = df["METRICA"] == "%PARTICIPACION"
    if mask.any():
        valores = df.loc[mask, ["CONGRESO", "JORNADA", "CONVENCIÓN"]].astype(float)
        if (valores.max().max() <= 1.0):
            df.loc[mask, ["CONGRESO", "JORNADA", "CONVENCIÓN"]] = valores * 100

    df = df.set_index(["TIPO", "METRICA"])
    return df

df = cargar_datos()

# --- Interfaz ---
st.title("🧮 Calculadora de impacto económico de reuniones")
st.markdown(
    "Introduce los datos reales del evento. La herramienta utiliza como referencia las medias 2025 "
    "por tipología de reunión y tipo de asistente."
)

evento_sel = st.selectbox("Tipo de reunión", df.columns)

# --- Parámetros medios 2025 desde Excel ---
dias_nac_ref = float(df.loc[("Nacional", "DIAS MEDIOS"), evento_sel])
dias_int_ref = float(df.loc[("Internacional", "DIAS MEDIOS"), evento_sel])

gasto_nac_ref = float(df.loc[("Nacional", "GASTO MEDIO"), evento_sel])
gasto_int_ref = float(df.loc[("Internacional", "GASTO MEDIO"), evento_sel])

porc_nac_ref = float(df.loc[("Nacional", "%PARTICIPACION"), evento_sel])
porc_int_ref = float(df.loc[("Internacional", "%PARTICIPACION"), evento_sel])

# --- Datos manuales del evento ---
st.markdown("### 📥 Datos del evento")

part_nac = st.number_input("Número de participantes nacionales", min_value=0, value=0, step=1)
part_int = st.number_input("Número de participantes internacionales", min_value=0, value=0, step=1)
pernoctaciones = st.number_input("Número total de pernoctaciones", min_value=0, value=0, step=1)

st.markdown("### 💰 Ingresos del evento")
ing_inscripciones = st.number_input("Ingresos por inscripciones (€)", min_value=0.0, value=0.0, step=100.0)
ing_alojamiento = st.number_input("Ingresos por alojamiento (€)", min_value=0.0, value=0.0, step=100.0)
ing_acompanantes = st.number_input("Ingresos por acompañantes (€)", min_value=0.0, value=0.0, step=100.0)
otros_ingresos = st.number_input("Otros ingresos (€)", min_value=0.0, value=0.0, step=100.0)

# --- Referencia 2025 ---
st.markdown("### 📊 Referencia media 2025")
st.markdown(
    f"""
    <div style="background-color:#eef4ff; padding:12px; border-radius:10px; margin-bottom:10px;">
        <b>{evento_sel}</b><br>
        Nacionales → Gasto medio: {formato_es(gasto_nac_ref)} € | Días medios: {formato_es(dias_nac_ref)} | % participación: {formato_es(porc_nac_ref)}%<br>
        Internacionales → Gasto medio: {formato_es(gasto_int_ref)} € | Días medios: {formato_es(dias_int_ref)} | % participación: {formato_es(porc_int_ref)}%
    </div>
    """,
    unsafe_allow_html=True
)

# --- Cálculo ---
if st.button("Calcular"):
    total_asistentes = part_nac + part_int
    ingresos_totales = ing_inscripciones + ing_alojamiento + ing_acompanantes + otros_ingresos

    gasto_medio_asistente = ingresos_totales / total_asistentes if total_asistentes > 0 else 0
    pernoctaciones_por_asistente = pernoctaciones / total_asistentes if total_asistentes > 0 else 0

    porc_nac_real = (part_nac / total_asistentes * 100) if total_asistentes > 0 else 0
    porc_int_real = (part_int / total_asistentes * 100) if total_asistentes > 0 else 0

    # Impacto teórico según medias 2025
    impacto_teorico_nac = part_nac * gasto_nac_ref
    impacto_teorico_int = part_int * gasto_int_ref
    impacto_teorico_total = impacto_teorico_nac + impacto_teorico_int

    estancia_media_real = pernoctaciones_por_asistente

    # --- Resultados principales ---
    st.markdown("## ✅ Resultados del evento")

    st.success(f"💰 Ingresos totales del evento: {formato_es(ingresos_totales)} €")

    st.markdown(
        f"""
        <div style="background-color:#f6f6f6; padding:12px; border-radius:10px; margin-bottom:10px;">
            <b>Asistentes totales:</b> {total_asistentes}<br>
            <b>Nacionales:</b> {part_nac} ({formato_es(porc_nac_real)}%)<br>
            <b>Internacionales:</b> {part_int} ({formato_es(porc_int_real)}%)<br>
            <b>Pernoctaciones totales:</b> {pernoctaciones}<br>
            <b>Gasto medio por asistente:</b> {formato_es(gasto_medio_asistente)} €<br>
            <b>Pernoctaciones por asistente:</b> {formato_es(pernoctaciones_por_asistente)}
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Comparativa con referencia ---
    st.markdown("## 📌 Comparativa con referencia 2025")
    st.info(
        f"👉 Impacto teórico según medias 2025: {formato_es(impacto_teorico_total)} €\n"
        f"👉 Impacto teórico nacionales: {formato_es(impacto_teorico_nac)} €\n"
        f"👉 Impacto teórico internacionales: {formato_es(impacto_teorico_int)} €"
    )

    st.markdown(
        f"""
        <div style="background-color:#fff8b3; padding:10px; border-radius:10px; margin-top:10px;">
            <b>Referencia media {evento_sel} 2025:</b><br>
            Participación media nacionales: {formato_es(porc_nac_ref)}% &nbsp;&nbsp; | &nbsp;&nbsp;
            Participación media internacionales: {formato_es(porc_int_ref)}%<br>
            Estancia media nacionales: {formato_es(dias_nac_ref)} días &nbsp;&nbsp; | &nbsp;&nbsp;
            Estancia media internacionales: {formato_es(dias_int_ref)} días
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Gráfico 1: asistentes por origen ---
    df_asistentes = pd.DataFrame({
        "Origen": ["Nacionales", "Internacionales"],
        "Asistentes": [part_nac, part_int],
        "Texto": [str(part_nac), str(part_int)]
    })

    fig1 = px.bar(
        df_asistentes,
        x="Origen",
        y="Asistentes",
        text="Texto",
        title="Asistentes por origen",
        color="Origen",
        color_discrete_map={"Nacionales": "#f4a582", "Internacionales": "#92c5de"}
    )
    fig1.update_traces(textposition="outside")
    st.plotly_chart(fig1, use_container_width=True)

    # --- Gráfico 2: ingresos por categoría ---
    df_ingresos = pd.DataFrame({
        "Categoría": ["Inscripciones", "Alojamiento", "Acompañantes", "Otros ingresos"],
        "Importe (€)": [ing_inscripciones, ing_alojamiento, ing_acompanantes, otros_ingresos],
        "Texto": [
            formato_es(ing_inscripciones),
            formato_es(ing_alojamiento),
            formato_es(ing_acompanantes),
            formato_es(otros_ingresos)
        ]
    })

    fig2 = px.bar(
        df_ingresos,
        x="Categoría",
        y="Importe (€)",
        text="Texto",
        title="Ingresos por categoría"
    )
    fig2.update_traces(textposition="outside")
    fig2.update_layout(yaxis_tickformat=",.2f", separators=".,")
    st.plotly_chart(fig2, use_container_width=True)

    # --- Gráfico 3: impacto teórico por origen según medias 2025 ---
    df_impacto = pd.DataFrame({
        "Origen": ["Nacionales", "Internacionales"],
        "Impacto teórico (€)": [impacto_teorico_nac, impacto_teorico_int],
        "Texto": [formato_es(impacto_teorico_nac), formato_es(impacto_teorico_int)]
    })

    fig3 = px.bar(
        df_impacto,
        x="Origen",
        y="Impacto teórico (€)",
        text="Texto",
        title="Impacto teórico por origen según medias 2025",
        color="Origen",
        color_discrete_map={"Nacionales": "#d95f02", "Internacionales": "#1b9e77"}
    )
    fig3.update_traces(textposition="outside")
    fig3.update_layout(yaxis_tickformat=",.2f", separators=".,")
    st.plotly_chart(fig3, use_container_width=True)

    # --- Resumen final listo para copiar ---
    st.markdown("## 📝 Resumen")
    st.text_area(
        "Resumen del cálculo",
        value=(
            f"Tipo de reunión: {evento_sel}\n"
            f"Asistentes totales: {total_asistentes}\n"
            f"Nacionales: {part_nac} ({formato_es(porc_nac_real)}%)\n"
            f"Internacionales: {part_int} ({formato_es(porc_int_real)}%)\n"
            f"Pernoctaciones totales: {pernoctaciones}\n"
            f"Ingresos por inscripciones: {formato_es(ing_inscripciones)} €\n"
            f"Ingresos por alojamiento: {formato_es(ing_alojamiento)} €\n"
            f"Ingresos por acompañantes: {formato_es(ing_acompanantes)} €\n"
            f"Otros ingresos: {formato_es(otros_ingresos)} €\n"
            f"Ingresos totales: {formato_es(ingresos_totales)} €\n"
            f"Gasto medio por asistente: {formato_es(gasto_medio_asistente)} €\n"
            f"Pernoctaciones por asistente: {formato_es(pernoctaciones_por_asistente)}\n"
            f"Impacto teórico según medias 2025: {formato_es(impacto_teorico_total)} €"
        ),
        height=280
    )
