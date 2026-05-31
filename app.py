import streamlit as st
import pandas as pd
import plotly.express as px
import database as db

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="SAD Ganadero Satelital v7", page_icon="🛰️", layout="wide")

# 2. CONTROL DE SESIÓN
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""

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
    st.title(f"🛰️ SAD Satelital: Estancia de @{usuario_activo.upper()}")
with col_logout:
    if st.button("🚪 Salir"):
        st.session_state["autenticado"] = False
        st.session_state["usuario"] = ""
        st.rerun()

st.write("Versión 7.0: Telemetría de Índices de Vegetación (NDVI) y Georreferenciación.")
st.markdown("---")

# 3. PARÁMETROS REGIONALES DE SANTA CRUZ (Umbrales de NDVI biológico)
# En lugar de días, el negocio ganadero moderno evalúa la madurez por densidad foliar (NDVI)
UMBRAL_NDVI_REQUERIDO = 0.60 

# 4. INTERFAZ LATERAL
st.sidebar.header("⚙️ Configuración")
num_animales = st.sidebar.number_input("Cantidad de Novillos:", min_value=1, value=120)
peso_promedio = st.sidebar.number_input("Peso promedio (kg):", min_value=100, value=415)
consumo_diario_total = num_animales * (peso_promedio * 0.03)

# 5. PANEL DE CONTROL ADMINISTRATIVO
expander_gestion = st.expander("🛠️ Panel de Control (Añadir Nuevos Lotes Georreferenciados)")
with expander_gestion:
    with st.form("form_nuevo_potrero", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            nuevo_nombre = st.text_input("Nombre del Potrero:")
        with col_f2:
            nuevas_ha = st.number_input("Superficie (Ha):", min_value=1.0, value=40.0)
        with col_f3:
            # Coordenadas por defecto en zonas productivas de Santa Cruz
            coor_gps = st.text_input("Coordenadas GPS (Lat, Lon):", value="-17.31, -63.22")
            
        if st.form_submit_button("Registrar Potrero con GPS en Supabase", use_container_width=True):
            if nuevo_nombre.strip() != "":
                db.insertar_potrero(usuario_activo, nuevo_nombre, nuevas_ha, 30, coor_gps)
                st.success(f"¡Lote {nuevo_nombre} registrado exitosamente!")
                st.rerun()

# 6. LEER BASE DE DATOS CON TELEMETRÍA
try:
    df_potreros = db.cargar_datos_desde_db(usuario_activo)
except Exception as e:
    st.error(f"Error al conectar con Supabase: {e}")
    st.stop()

if df_potreros.empty:
    st.info("👋 Registre su primer lote georreferenciado para activar el monitoreo satelital.")
else:
    resultados = []
    mapa_data = []

    for index, fila in df_potreros.iterrows():
        id_p = fila["ID"]
        nombre = fila["Potrero"]
        ha = fila["Hectáreas"]
        ndvi = fila["Índice NDVI Satelital"]
        gps_str = fila["Coordenadas GPS"]
        
        # Procesar coordenadas para el mapa de Streamlit
        try:
            lat, lon = map(float, gps_str.split(","))
        except:
            lat, lon = -17.8, -63.1 # Coordenadas de respaldo (Santa Cruz centro)

        # MOTOR DE DECISIÓN AGTECH: Evaluación basada en NDVI
        if ndvi >= UMBRAL_NDVI_REQUERIDO:
            estado = "🟢 Óptimo (Pastura Madura)"
            # Estimación de materia seca (MS) basada directamente en el vigor fotosintético
            ms_disponible = ha * (ndvi * 3000) 
            dias_capacidad = max(1, int(ms_disponible / consumo_diario_total))
            recomendacion = f"APTO. Capacidad de carga estimada para {dias_capacidad} días de pastoreo continuo."
        else:
            estado = "🔴 Crítico (Pasto Insuficiente)"
            recomendacion = f"RECHAZADO. Vigor fotosintético bajo ({ndvi}). Requiere descanso biológico."
            
        resultados.append({
            "ID": id_p, "Potrero": nombre, "Superficie (Ha)": ha, 
            "NDVI Satelital": ndvi, "Estado": estado, "Dictamen del SAD": recomendacion
        })
        
        mapa_data.append({"name": nombre, "lat": lat, "lon": lon})

    df_resultados = pd.DataFrame(resultados)
    df_mapa = pd.DataFrame(mapa_data)

    # 7. RENDERIZADO DEL DASHBOARD (Distribución de pantallas profesional)
    col_izq_dash, col_der_dash = st.columns([1.2, 1])

    with col_izq_dash:
        st.subheader("📊 Monitoreo del Vigor Fotosintético (NDVI)")
        fig = px.bar(
            df_resultados, x="Potrero", y="NDVI Satelital", text="NDVI Satelital", color="Estado",
            color_discrete_map={"🟢 Óptimo (Pastura Madura)": "#2ecc71", "🔴 Crítico (Pasto Insuficiente)": "#e74c3c"},
            range_y=[0, 1]
        )
        fig.add_hline(y=UMBRAL_NDVI_REQUERIDO, line_dash="dash", line_color="blue", annotation_text="Umbral Crítico (0.60)")
        st.plotly_chart(fig, use_container_width=True)

    with col_der_dash:
        st.subheader("📍 Geolocalización de los Lotes")
        # El widget st.map lee automáticamente un DataFrame con columnas 'lat' y 'lon'
        st.map(df_mapa, size=20, zoom=11)

    # 8. TABLA DE RECOMENDACIONES ESTRATÉGICAS
    st.markdown("---")
    st.subheader("🤖 Reporte de Telemetría e Instrucciones de Rotación")
    st.dataframe(df_resultados.set_index('ID'), use_container_width=True)