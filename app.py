"""
SAD Ganadero Predictivo — Versión 9.0
Nuevas funcionalidades:
  - Objetivo A: Clima real por potrero vía Open-Meteo API (clima.py)
  - Objetivo B: Mapa satelital interactivo con streamlit-folium (Esri Imagery)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import database as db
import clima as cl

# ─────────────────────────────────────────────
# 1. CONFIGURACIÓN DE LA PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SAD Ganadero Predictivo v9",
    page_icon="🛰️",
    layout="wide",
)

# ─────────────────────────────────────────────
# 2. CONTROL DE SESIÓN Y AUTENTICACIÓN
# ─────────────────────────────────────────────
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""

# NOTA DE SEGURIDAD: En producción migrar a Supabase Auth o similar.
# Mantener aquí solo para mantener compatibilidad con la v8.
USUARIOS_VALIDOS = {"roberto": "cruz2026", "ganadero2": "agro123"}

if not st.session_state["autenticado"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col_izq, col_login, col_der = st.columns([1, 1.5, 1])
    with col_login:
        st.markdown("<h2 style='text-align: center;'>🔐 Acceso al SAD Ganadero</h2>", unsafe_allow_html=True)
        with st.container(border=True):
            with st.form("login_form", border=False):
                input_user = st.text_input("Usuario / Cuenta Estancia:")
                input_pass = st.text_input("Contraseña:", type="password")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("Iniciar Sesión", use_container_width=True):
                    if input_user in USUARIOS_VALIDOS and USUARIOS_VALIDOS[input_user] == input_pass:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario"] = input_user
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas.")
    st.stop()

usuario_activo = st.session_state["usuario"]

col_titulo, col_logout = st.columns([9, 1])
with col_titulo:
    st.title(f"🛰️ SAD Inteligente: Estancia de @{usuario_activo.upper()}")
with col_logout:
    if st.button("🚪 Salir"):
        st.session_state["autenticado"] = False
        st.session_state["usuario"] = ""
        st.rerun()

st.write("Versión 9.0 (Clima Real + Mapas Satelitales): Motor predictivo alimentado por telemetría Open-Meteo.")
st.markdown("---")

# ─────────────────────────────────────────────
# 3. PARÁMETROS AGTECH
# ─────────────────────────────────────────────
UMBRAL_NDVI_REQUERIDO = 0.60
TASA_RECUPERACION_BASE = 0.012  # NDVI/día en condiciones óptimas (Santa Cruz)

# ─────────────────────────────────────────────
# 4. BARRA LATERAL: Parámetros del lote de ganado
# ─────────────────────────────────────────────
st.sidebar.header("⚙️ Parámetros del Lote")
st.sidebar.caption("El clima ya no se simula — se obtiene de Open-Meteo en tiempo real.")

num_animales = st.sidebar.number_input("Cantidad de Novillos:", min_value=1, value=120)
peso_promedio = st.sidebar.number_input("Peso promedio (kg):", min_value=100, value=415)
consumo_diario_total = num_animales * (peso_promedio * 0.03)

if st.sidebar.button("🔄 Actualizar datos climáticos", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ─────────────────────────────────────────────
# 5. PANEL DE GESTIÓN DE POTREROS
# ─────────────────────────────────────────────
expander_gestion = st.expander("🛠️ Panel de Control (Añadir Nuevos Lotes Georreferenciados)")
with expander_gestion:
    with st.form("form_nuevo_potrero", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            nuevo_nombre = st.text_input("Nombre del Potrero:")
        with col_f2:
            nuevas_ha = st.number_input("Superficie (Ha):", min_value=1.0, value=40.0)
        with col_f3:
            coor_gps = st.text_input("Coordenadas GPS (Lat, Lon):", value="-17.31, -63.22")

        if st.form_submit_button("Registrar Potrero con GPS en Supabase", use_container_width=True):
            if nuevo_nombre.strip() != "":
                db.insertar_potrero(usuario_activo, nuevo_nombre, nuevas_ha, 30, coor_gps)
                st.success(f"¡Lote '{nuevo_nombre}' registrado exitosamente!")
                st.rerun()

# ─────────────────────────────────────────────
# 6. CARGA DE DATOS Y MOTOR IA PREDICTIVO
# ─────────────────────────────────────────────
try:
    df_potreros = db.cargar_datos_desde_db(usuario_activo)
except Exception as e:
    st.error(f"Error al conectar con Supabase: {e}")
    st.stop()

if df_potreros.empty:
    st.info("👋 Registre su primer lote georreferenciado para activar el monitoreo predictivo.")
    st.stop()

# Procesamiento de cada potrero
resultados = []
mapa_potreros = []   # Para Folium
conteo_listos = 0
conteo_criticos = 0

# Panel de clima en tiempo real (se construye en paralelo al procesamiento)
clima_por_potrero = {}

with st.spinner("🛰️ Consultando telemetría climática de Open-Meteo..."):
    for _, fila in df_potreros.iterrows():
        gps_str = fila["Coordenadas GPS"]
        try:
            lat, lon = map(float, gps_str.split(","))
        except Exception:
            lat, lon = -17.8, -63.1

        # ── OBJETIVO A: Clima real desde Open-Meteo ──────────────────────────
        datos_clima = cl.obtener_clima_potrero(lat, lon)
        tasa_ajustada = cl.calcular_tasa_ndvi_por_clima(datos_clima, TASA_RECUPERACION_BASE)
        clima_por_potrero[fila["ID"]] = datos_clima

        # ── ALGORITMO IA PREDICTIVO (ahora con tasa dinámica real) ───────────
        id_p = fila["ID"]
        nombre = fila["Potrero"]
        ha = fila["Hectáreas"]
        ndvi = fila["Índice NDVI Satelital"]

        if ndvi >= UMBRAL_NDVI_REQUERIDO:
            estado = "🟢 Óptimo (Pastura Madura)"
            conteo_listos += 1
            ms_disponible = ha * (ndvi * 3000)
            dias_utiles = max(1, int(ms_disponible / consumo_diario_total))
            proyeccion_ia = f"📈 DISPONIBLE. Soporta pastoreo por {dias_utiles} días antes de degradarse."
            color_mapa = "green"
        else:
            estado = "🔴 Crítico (Pasto Insuficiente)"
            conteo_criticos += 1
            dias_espera_ia = max(1, int((UMBRAL_NDVI_REQUERIDO - ndvi) / tasa_ajustada))
            proyeccion_ia = (
                f"⏳ RECHAZADO. Con el clima actual ({datos_clima['descripcion']}), "
                f"se estiman {dias_espera_ia} días de clausura."
            )
            color_mapa = "red"

        resultados.append({
            "ID": id_p,
            "Potrero": nombre,
            "Superficie (Ha)": ha,
            "NDVI Satelital": ndvi,
            "Estado": estado,
            "🌡️ Temp (°C)": datos_clima["temperatura_c"],
            "💧 Lluvia 24h (mm)": datos_clima["lluvia_mm_24h"],
            "Proyección IA (clima real)": proyeccion_ia,
        })
        mapa_potreros.append({
            "nombre": nombre, "lat": lat, "lon": lon,
            "ndvi": ndvi, "estado": estado, "color": color_mapa,
            "clima": datos_clima["descripcion"],
            "temp": datos_clima["temperatura_c"],
            "lluvia": datos_clima["lluvia_mm_24h"],
            "proyeccion": proyeccion_ia,
        })

df_resultados = pd.DataFrame(resultados)

# ─────────────────────────────────────────────
# 7. KPIs EJECUTIVOS
# ─────────────────────────────────────────────
st.subheader("📊 Indicadores Clave de la Estancia")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric("Lotes Listos para Consumo", f"{conteo_listos} Potreros",
              delta=f"+{conteo_listos}" if conteo_listos > 0 else None)
with kpi2:
    st.metric("Lotes en Clausura Ecológica", f"{conteo_criticos} Potreros",
              delta=f"-{conteo_criticos}" if conteo_criticos > 0 else None, delta_color="inverse")
with kpi3:
    st.metric("Consumo del Lote", f"{int(consumo_diario_total)} kg MS/Día",
              f"Carga: {int(num_animales)} Novillos")
with kpi4:
    # KPI nuevo: temperatura promedio de la zona
    if mapa_potreros:
        temp_prom = round(sum(p["temp"] for p in mapa_potreros) / len(mapa_potreros), 1)
        lluvia_prom = round(sum(p["lluvia"] for p in mapa_potreros) / len(mapa_potreros), 1)
        st.metric("Clima Promedio Zona", f"{temp_prom}°C", f"🌧️ {lluvia_prom} mm/24h")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 8. PANEL CLIMÁTICO EN TIEMPO REAL (OBJETIVO A)
# ─────────────────────────────────────────────
with st.expander("🌡️ Telemetría Climática en Tiempo Real por Potrero (Open-Meteo)", expanded=True):
    cols_clima = st.columns(len(mapa_potreros)) if len(mapa_potreros) <= 4 else st.columns(4)
    for idx, potrero in enumerate(mapa_potreros):
        c = potrero["clima"]
        with cols_clima[idx % 4]:
            st.markdown(f"**{potrero['nombre']}**")
            st.caption(c)
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Temp", f"{potrero['temp']}°C")
            with col_b:
                st.metric("Lluvia", f"{potrero['lluvia']} mm")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 9. GRÁFICO NDVI + MAPA SATELITAL (OBJETIVO B)
# ─────────────────────────────────────────────
col_izq_dash, col_der_dash = st.columns([1.2, 1])

with col_izq_dash:
    st.subheader("📈 Análisis de Densidad Foliar (NDVI)")
    fig = px.bar(
        df_resultados, x="Potrero", y="NDVI Satelital", text="NDVI Satelital",
        color="Estado",
        color_discrete_map={
            "🟢 Óptimo (Pastura Madura)": "#2ecc71",
            "🔴 Crítico (Pasto Insuficiente)": "#e74c3c",
        },
        range_y=[0, 1],
    )
    fig.add_hline(
        y=UMBRAL_NDVI_REQUERIDO, line_dash="dash", line_color="blue",
        annotation_text="Límite Biológico de Entrada (0.60)",
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

with col_der_dash:
    # ── OBJETIVO B: Mapa satelital con Folium ────────────────────────────────
    st.subheader("📍 Mapa Satelital de los Lotes (Esri Imagery)")

    if mapa_potreros:
        # Centro del mapa = promedio de coordenadas de los potreros del usuario
        lat_c = sum(p["lat"] for p in mapa_potreros) / len(mapa_potreros)
        lon_c = sum(p["lon"] for p in mapa_potreros) / len(mapa_potreros)

        m = folium.Map(
            location=[lat_c, lon_c],
            zoom_start=12,
            tiles=None,  # Sin capa base por defecto; la añadimos manualmente
        )

        # Capa satélite Esri (fotografía real desde el espacio, gratuita)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri, Maxar, Earthstar Geographics",
            name="🛰️ Satélite Esri",
            max_zoom=19,
        ).add_to(m)

        # Capa de etiquetas encima de la fotografía
        folium.TileLayer(
            tiles="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            name="Etiquetas",
            overlay=True,
            control=True,
        ).add_to(m)

        # Marcadores por potrero con popup detallado
        for potrero in mapa_potreros:
            popup_html = f"""
            <div style="font-family: sans-serif; font-size: 13px; min-width: 200px;">
                <b>🌿 {potrero['nombre']}</b><br>
                <hr style="margin: 4px 0;">
                <b>NDVI:</b> {potrero['ndvi']:.2f} · {potrero['estado']}<br>
                <b>Clima:</b> {potrero['clima']}<br>
                <b>Temperatura:</b> {potrero['temp']}°C<br>
                <b>Lluvia 24h:</b> {potrero['lluvia']} mm<br>
                <hr style="margin: 4px 0;">
                <i>{potrero['proyeccion']}</i>
            </div>
            """
            folium.Marker(
                location=[potrero["lat"], potrero["lon"]],
                popup=folium.Popup(popup_html, max_width=280),
                tooltip=f"{potrero['nombre']} · NDVI {potrero['ndvi']:.2f}",
                icon=folium.Icon(
                    color=potrero["color"],
                    icon="leaf",
                    prefix="fa",
                ),
            ).add_to(m)

            # Círculo de área visual (radio proporcional a la cobertura del mapa)
            folium.Circle(
                location=[potrero["lat"], potrero["lon"]],
                radius=300,  # metros
                color="#2ecc71" if potrero["color"] == "green" else "#e74c3c",
                fill=True,
                fill_opacity=0.18,
                weight=1.5,
            ).add_to(m)

        folium.LayerControl(collapsed=False).add_to(m)

        # Renderizar el mapa con st_folium (altura fija para el dashboard)
        st_folium(m, width=None, height=420, returned_objects=[])

# ─────────────────────────────────────────────
# 10. REPORTE PREDICTIVO FINAL
# ─────────────────────────────────────────────
st.markdown("---")
st.subheader("🤖 Reporte Predictivo del Motor de Inteligencia Artificial")
st.caption("La tasa de recuperación del NDVI se ajusta automáticamente según la precipitación real de cada potrero.")
st.dataframe(df_resultados.set_index("ID"), use_container_width=True)
