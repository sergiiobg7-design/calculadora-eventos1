import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# Configuración de página
# =========================
st.set_page_config(
    page_title="Calculadora de impacto económico de reuniones",
    layout="wide"
)

# =========================
# Utilidades
# =========================
def formato_es(numero):
    return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def safe_float(valor):
    try:
        if pd.isna(valor):
            return 0.0
        return float(valor)
    except Exception:
        return 0.0

# =========================
# Carga de datos
# =========================
@st.cache_data
def cargar_parametros():
    df = pd.read_excel("gasto_medio.xlsx", sheet_name="2025")
    df = df.iloc[:, :5].copy()
    df.columns = ["TIPO", "METRICA", "CONGRESO", "JORNADA", "CONVENCIÓN"]
    df = df.dropna(how="all")

    df["TIPO"] = df["TIPO"].astype(str).str.strip()
    df["METRICA"] = df["METRICA"].astype(str).str.strip()

    mask = df["METRICA"] == "%PARTICIPACION"
    if mask.any():
        valores = df.loc[mask, ["CONGRESO", "JORNADA", "CONVENCIÓN"]].apply(pd.to_numeric, errors="coerce")
        if valores.max().max() <= 1:
            df.loc[mask, ["CONGRESO", "JORNADA", "CONVENCIÓN"]] = valores * 100

    df = df.set_index(["TIPO", "METRICA"])
    return df

@st.cache_data
def cargar_desglose():
    df = pd.read_excel("gasto_medio.xlsx", sheet_name="DESGLOSE_GASTO")
    df = df.iloc[:, :5].copy()
    df.columns = ["TIPO", "CATEGORIA", "CONGRESO", "JORNADA", "CONVENCIÓN"]
    df = df.dropna(how="all")

    df["TIPO"] = df["TIPO"].astype(str).str.strip()
    df["CATEGORIA"] = df["CATEGORIA"].astype(str).str.strip()

    df = df.set_index(["TIPO", "CATEGORIA"])
    return df

parametros = cargar_parametros()
desglose = cargar_desglose()

# =========================
# App
# =========================
st.title("🧮 Calculadora de impacto económico de reuniones")
st.markdown(
    "Introduce los datos básicos del evento. La herramienta estima automáticamente el impacto económico "
    "a partir del tipo de reunión, el origen de los asistentes y la pernoctación media prevista."
)

# =========================
# Inputs
# =========================
st.markdown("## Datos del evento")

col1, col2 = st.columns(2)

with col1:
    evento_sel = st.selectbox("Tipo de evento", parametros.columns)
    part_nac = st.number_input("Número de participantes nacionales", min_value=0, value=100, step=1)

with col2:
    part_int = st.number_input("Número de participantes internacionales", min_value=0, value=50, step=1)
    pernoctacion_media_evento = st.number_input(
        "Pernoctación media del evento",
        min_value=0.0,
        value=2.0,
        step=0.1
    )

# =========================
# Parámetros 2025
# =========================
dias_nac_ref = safe_float(parametros.loc[("Nacional", "DIAS MEDIOS"), evento_sel])
dias_int_ref = safe_float(parametros.loc[("Internacional", "DIAS MEDIOS"), evento_sel])

porc_nac_ref = safe_float(parametros.loc[("Nacional", "%PARTICIPACION"), evento_sel])
porc_int_ref = safe_float(parametros.loc[("Internacional", "%PARTICIPACION"), evento_sel])

# Desglose por categorías
viaje_nac = safe_float(desglose.loc[("Nacional", "Viaje hasta la ciudad"), evento_sel])
inscripcion_nac = safe_float(desglose.loc[("Nacional", "Inscripción"), evento_sel])
alojamiento_nac = safe_float(desglose.loc[("Nacional", "Alojamiento"), evento_sel])
extras_nac = safe_float(desglose.loc[("Nacional", "Gastos extras de la reunión"), evento_sel])

viaje_int = safe_float(desglose.loc[("Internacional", "Viaje hasta la ciudad"), evento_sel])
inscripcion_int = safe_float(desglose.loc[("Internacional", "Inscripción"), evento_sel])
alojamiento_int = safe_float(desglose.loc[("Internacional", "Alojamiento"), evento_sel])
extras_int = safe_float(desglose.loc[("Internacional", "Gastos extras de la reunión"), evento_sel])

# =========================
# Referencia media 2025
# =========================
st.markdown("## Referencia media 2025")
st.markdown(
    f"""
    <div style="background-color:#eef4ff; padding:14px; border-radius:12px; margin-bottom:14px;">
        <b>{evento_sel}</b><br><br>
        <b>Nacionales</b> → Días medios: {formato_es(dias_nac_ref)} | Participación media: {formato_es(porc_nac_ref)}%<br>
        <b>Internacionales</b> → Días medios: {formato_es(dias_int_ref)} | Participación media: {formato_es(porc_int_ref)}%
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# Cálculo
# =========================
if st.button("Calcular impacto económico"):

    total_asistentes = part_nac + part_int
    porc_nac_real = (part_nac / total_asistentes * 100) if total_asistentes > 0 else 0
    porc_int_real = (part_int / total_asistentes * 100) if total_asistentes > 0 else 0

    pernoctaciones_por_asistente = pernoctacion_media_evento
    pernoctaciones_totales = total_asistentes * pernoctaciones_por_asistente

    # -------------------------
    # Costes fijos por asistente
    # -------------------------
    gasto_fijo_nac = viaje_nac + inscripcion_nac
    gasto_fijo_int = viaje_int + inscripcion_int

    # -------------------------
    # Coste variable por noche
    # -------------------------
    gasto_variable_noche_nac = ((alojamiento_nac + extras_nac) / dias_nac_ref) if dias_nac_ref > 0 else 0
    gasto_variable_noche_int = ((alojamiento_int + extras_int) / dias_int_ref) if dias_int_ref > 0 else 0

    # -------------------------
    # Coste variable ajustado a la pernoctación media real
    # -------------------------
    gasto_variable_ajustado_nac = gasto_variable_noche_nac * pernoctaciones_por_asistente
    gasto_variable_ajustado_int = gasto_variable_noche_int * pernoctaciones_por_asistente

    # -------------------------
    # Gasto total estimado por asistente
    # -------------------------
    gasto_estimado_nac = gasto_fijo_nac + gasto_variable_ajustado_nac
    gasto_estimado_int = gasto_fijo_int + gasto_variable_ajustado_int

    # -------------------------
    # Recaudación por origen
    # -------------------------
    recaudacion_nac = part_nac * gasto_estimado_nac
    recaudacion_int = part_int * gasto_estimado_int
    recaudacion_total = recaudacion_nac + recaudacion_int

    # -------------------------
    # Gasto medio por asistente total
    # -------------------------
    gasto_medio_asistente = (recaudacion_total / total_asistentes) if total_asistentes > 0 else 0

    # -------------------------
    # Gasto medio diario por asistente y origen
    # Importante: depende de costes fijos, variables, noches, evento y origen
    # -------------------------
    gasto_diario_nac = (
        (gasto_fijo_nac / pernoctaciones_por_asistente) + gasto_variable_noche_nac
        if pernoctaciones_por_asistente > 0 else 0
    )

    gasto_diario_int = (
        (gasto_fijo_int / pernoctaciones_por_asistente) + gasto_variable_noche_int
        if pernoctaciones_por_asistente > 0 else 0
    )

    gasto_medio_diario_asistente = (
        ((part_nac * gasto_diario_nac) + (part_int * gasto_diario_int)) / total_asistentes
        if total_asistentes > 0 else 0
    )

    # =========================
    # Desglose total por categorías
    # =========================
    total_viaje = (part_nac * viaje_nac) + (part_int * viaje_int)
    total_inscripcion = (part_nac * inscripcion_nac) + (part_int * inscripcion_int)

    total_alojamiento = (
        (part_nac * ((alojamiento_nac / dias_nac_ref) * pernoctaciones_por_asistente) if dias_nac_ref > 0 else 0) +
        (part_int * ((alojamiento_int / dias_int_ref) * pernoctaciones_por_asistente) if dias_int_ref > 0 else 0)
    )

    total_extras = (
        (part_nac * ((extras_nac / dias_nac_ref) * pernoctaciones_por_asistente) if dias_nac_ref > 0 else 0) +
        (part_int * ((extras_int / dias_int_ref) * pernoctaciones_por_asistente) if dias_int_ref > 0 else 0)
    )

    # =========================
    # Resultados
    # =========================
    st.markdown("## Resultados estimados del evento")

    col_res1, col_res2, col_res3 = st.columns(3)

    with col_res1:
        st.metric("Asistentes totales", f"{int(total_asistentes)}")
        st.metric("Pernoctaciones totales estimadas", f"{formato_es(pernoctaciones_totales)}")

    with col_res2:
        st.metric("Recaudación total estimada", f"{formato_es(recaudacion_total)} €")
        st.metric("Pernoctaciones por asistente", f"{formato_es(pernoctaciones_por_asistente)}")

    with col_res3:
        st.metric("Gasto medio por asistente", f"{formato_es(gasto_medio_asistente)} €")
        st.metric("Gasto medio diario por asistente", f"{formato_es(gasto_medio_diario_asistente)} €")

    st.markdown("### Detalle por origen")
    col_o1, col_o2 = st.columns(2)

    with col_o1:
        st.markdown(
            f"""
            <div style="background-color:#f7f7f7; padding:12px; border-radius:10px;">
                <b>Nacionales</b><br>
                Participantes: {part_nac}<br>
                Gasto estimado por asistente: {formato_es(gasto_estimado_nac)} €<br>
                Gasto medio diario por asistente: {formato_es(gasto_diario_nac)} €<br>
                Recaudación estimada: {formato_es(recaudacion_nac)} €
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_o2:
        st.markdown(
            f"""
            <div style="background-color:#f7f7f7; padding:12px; border-radius:10px;">
                <b>Internacionales</b><br>
                Participantes: {part_int}<br>
                Gasto estimado por asistente: {formato_es(gasto_estimado_int)} €<br>
                Gasto medio diario por asistente: {formato_es(gasto_diario_int)} €<br>
                Recaudación estimada: {formato_es(recaudacion_int)} €
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        f"""
        <div style="background-color:#fff8b3; padding:12px; border-radius:10px; margin-top:12px; margin-bottom:10px;">
            <b>Porcentaje de participación real del evento:</b>
            Nacionales: {formato_es(porc_nac_real)}% &nbsp;&nbsp; | &nbsp;&nbsp;
            Internacionales: {formato_es(porc_int_real)}%
        </div>
        """,
        unsafe_allow_html=True
    )

    # =========================
    # Gráfico 1 - Recaudación por origen
    # =========================
    df_origen = pd.DataFrame({
        "Origen": ["Nacionales", "Internacionales"],
        "Recaudación (€)": [recaudacion_nac, recaudacion_int],
        "Texto": [formato_es(recaudacion_nac), formato_es(recaudacion_int)]
    })

    fig1 = px.bar(
        df_origen,
        x="Origen",
        y="Recaudación (€)",
        text="Texto",
        title="Recaudación estimada por origen de asistentes",
        color="Origen",
        color_discrete_map={"Nacionales": "#f4a582", "Internacionales": "#92c5de"}
    )
    fig1.update_traces(textposition="outside")
    fig1.update_layout(yaxis_tickformat=",.2f", separators=".,")
    st.plotly_chart(fig1, use_container_width=True)

    # =========================
    # Gráfico 2 - Gasto por categorías
    # =========================
    df_categorias = pd.DataFrame({
        "Categoría": [
            "Viaje hasta la ciudad",
            "Inscripción",
            "Alojamiento",
            "Gastos extras de la reunión"
        ],
        "Importe (€)": [total_viaje, total_inscripcion, total_alojamiento, total_extras],
        "Texto": [
            formato_es(total_viaje),
            formato_es(total_inscripcion),
            formato_es(total_alojamiento),
            formato_es(total_extras)
        ]
    })

    fig2 = px.bar(
        df_categorias,
        x="Categoría",
        y="Importe (€)",
        text="Texto",
        title="Gastos estimados por categorías"
    )
    fig2.update_traces(textposition="outside")
    fig2.update_layout(yaxis_tickformat=",.2f", separators=".,")
    st.plotly_chart(fig2, use_container_width=True)

    # =========================
    # Gráfico 3 - Gasto medio diario por origen
    # =========================
    df_diario = pd.DataFrame({
        "Origen": ["Nacionales", "Internacionales"],
        "Gasto medio diario (€)": [gasto_diario_nac, gasto_diario_int],
        "Texto": [formato_es(gasto_diario_nac), formato_es(gasto_diario_int)]
    })

    fig3 = px.bar(
        df_diario,
        x="Origen",
        y="Gasto medio diario (€)",
        text="Texto",
        title="Gasto medio diario por asistente",
        color="Origen",
        color_discrete_map={"Nacionales": "#d95f02", "Internacionales": "#1b9e77"}
    )
    fig3.update_traces(textposition="outside")
    fig3.update_layout(yaxis_tickformat=",.2f", separators=".,")
    st.plotly_chart(fig3, use_container_width=True)

    # =========================
    # Resumen
    # =========================
    st.markdown("## Resumen del cálculo")

    resumen = (
        f"Tipo de evento: {evento_sel}\n"
        f"Participantes nacionales: {part_nac}\n"
        f"Participantes internacionales: {part_int}\n"
        f"Asistentes totales: {total_asistentes}\n"
        f"Pernoctación media del evento: {formato_es(pernoctaciones_por_asistente)}\n"
        f"Pernoctaciones totales estimadas: {formato_es(pernoctaciones_totales)}\n"
        f"Participación nacional: {formato_es(porc_nac_real)}%\n"
        f"Participación internacional: {formato_es(porc_int_real)}%\n"
        f"Gasto estimado por asistente nacional: {formato_es(gasto_estimado_nac)} €\n"
        f"Gasto estimado por asistente internacional: {formato_es(gasto_estimado_int)} €\n"
        f"Gasto medio diario nacional: {formato_es(gasto_diario_nac)} €\n"
        f"Gasto medio diario internacional: {formato_es(gasto_diario_int)} €\n"
        f"Recaudación estimada nacionales: {formato_es(recaudacion_nac)} €\n"
        f"Recaudación estimada internacionales: {formato_es(recaudacion_int)} €\n"
        f"Recaudación total estimada: {formato_es(recaudacion_total)} €\n"
        f"Gasto medio por asistente: {formato_es(gasto_medio_asistente)} €\n"
        f"Gasto medio diario por asistente: {formato_es(gasto_medio_diario_asistente)} €\n"
        f"Gasto estimado en viaje hasta la ciudad: {formato_es(total_viaje)} €\n"
        f"Gasto estimado en inscripción: {formato_es(total_inscripcion)} €\n"
        f"Gasto estimado en alojamiento: {formato_es(total_alojamiento)} €\n"
        f"Gasto estimado en gastos extras de la reunión: {formato_es(total_extras)} €"
    )

    st.text_area("Resumen del cálculo", value=resumen, height=360)
