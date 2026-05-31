import streamlit as st
import pandas as pd
import plotly.express as px
import database as db

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="SAD Ganadero Predictivo v8", page_icon="🤖", layout="wide")

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
    st.title(f"🤖 SAD Inteligente: Estancia de @{usuario_activo.upper()}")
with col_logout:
    if st.button("🚪 Salir"):
        st.session_state["autenticado"] = False
        st.session_state["usuario"] = ""
        st.rerun()

st.write("Versión 8.0 (Módulo de Inteligencia Artificial): Modelado Predictivo de Biomasa Futura.")
st.markdown("---")

# 3. PARÁMETROS AGTECH (Umbrales e IA)
UMBRAL_NDVI_REQUERIDO = 0.60
TASA_RECUPERACION_DIARIA = 0.012  # Incremento estimado de NDVI por día soleado en Santa Cruz

# 4. INTERFAZ LATERAL
st.sidebar.header("⚙️ Simulación de Escenario")
epoca_actual = st.sidebar.selectbox("Condición Climática de la Zona:", ["Normal (Época de Lluvias)", "Sequía / Surazo Estacional"])
num_animales = st.sidebar.number_input("Cantidad de Novillos:", min_value=1, value=120)
peso_promedio = st.sidebar.number_input("Peso promedio (kg):", min_value=100, value=415)
consumo_diario_total = num_animales * (peso_promedio * 0.03)

# Ajuste de la tasa predictiva según el clima simulado en la barra lateral
tasa_ajustada = TASA_RECUPERACION_DIARIA if "Lluvias" in epoca_actual else TASA_RECUPERACION_DIARIA * 0.4

# 5. PANEL DE GESTIÓN
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
                st.success(f"¡Lote {nuevo_nombre} registrado exitosamente!")
                st.rerun()

# 6. LEER BASE DE DATOS Y EJECUTAR MOTOR IA PREDICTIVO
try:
    df_potreros = db.cargar_datos_desde_db(usuario_activo)
except Exception as e:
    st.error(f"Error al conectar con Supabase: {e}")
    st.stop()

if df_potreros.empty:
    st.info("👋 Registre su primer lote georreferenciado para activar el monitoreo predictivo.")
else:
    resultados = []
    mapa_data = []
    
    conteo_listos = 0
    conteo_criticos = 0

    for index, fila in df_potreros.iterrows():
        id_p = fila["ID"]
        nombre = fila["Potrero"]
        ha = fila["Hectáreas"]
        ndvi = fila["Índice NDVI Satelital"]
        gps_str = fila["Coordenadas GPS"]
        
        try:
            lat, lon = map(float, gps_str.split(","))
        except:
            lat, lon = -17.8, -63.1

        # ALGORITMO PREDICTIVO DE LA IA
        if ndvi >= UMBRAL_NDVI_REQUERIDO:
            estado = "🟢 Óptimo (Pastura Madura)"
            conteo_listos += 1
            
            # Cálculo de días de vida útil del pasto antes de agotarse
            ms_disponible = ha * (ndvi * 3000) 
            dias_utiles = int(ms_disponible / consumo_diario_total)
            dias_utiles = max(1, dias_utiles)
            
            proyeccion_ia = f"📈 DISPONIBLE. Soporta pastoreo continuo por {dias_utiles} días antes de degradarse."
        else:
            estado = "🔴 Crítico (Pasto Insuficiente)"
            conteo_criticos += 1
            
            # Ecuación matemática lineal de recuperación biológica: Días = (NDVI_objetivo - NDVI_actual) / Tasa_diaria
            dias_espera_ia = int((UMBRAL_NDVI_REQUERIDO - ndvi) / tasa_ajustada)
            dias_espera_ia = max(1, dias_espera_ia)
            
            proyeccion_ia = f"⏳ RECHAZADO. El modelo predictivo estima {dias_espera_ia} días de clausura para alcanzar el nivel óptimo."
            
        resultados.append({
            "ID": id_p, "Potrero": nombre, "Superficie (Ha)": ha, 
            "NDVI Satelital": ndvi, "Estado": estado, "Proyección Predictiva de la IA": proyeccion_ia
        })
        mapa_data.append({"name": nombre, "lat": lat, "lon": lon})

    df_resultados = pd.DataFrame(resultados)
    df_mapa = pd.DataFrame(mapa_data)

    # 7. TARJETAS DE INDICADORES (KPIs del Tablero Ejecutivo)
    st.subheader("📊 Indicadores Clave de la Estancia")
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.metric("Lotes Listos para Consumo", f"{conteo_listos} Potreros", delta=f"+{conteo_listos}" if conteo_listos > 0 else None)
    with kpi2:
        st.metric("Lotes en Clausura Ecológica", f"{conteo_criticos} Potreros", delta=f"-{conteo_criticos}" if conteo_criticos > 0 else None, delta_color="inverse")
    with kpi3:
        # El consumo total diario expresado en Kilogramos de Materia Seca
        st.metric("Consumo del Lote de Ganado", f"{int(consumo_diario_total)} kg MS/Día", f"Carga: {int(num_animales)} Novillos")

    st.markdown("<br>", unsafe_allow_html=True)

    # 8. RENDERIZADO GRÁFICO Y GEOGRÁFICO
    col_izq_dash, col_der_dash = st.columns([1.2, 1])

    with col_izq_dash:
        st.subheader("📈 Análisis de Densidad Foliar (NDVI)")
        fig = px.bar(
            df_resultados, x="Potrero", y="NDVI Satelital", text="NDVI Satelital", color="Estado",
            color_discrete_map={"🟢 Óptimo (Pastura Madura)": "#2ecc71", "🔴 Crítico (Pasto Insuficiente)": "#e74c3c"},
            range_y=[0, 1]
        )
        fig.add_hline(y=UMBRAL_NDVI_REQUERIDO, line_dash="dash", line_color="blue", annotation_text="Límite Biológico de Entrada (0.60)")
        st.plotly_chart(fig, use_container_width=True)

    with col_der_dash:
        st.subheader("📍 Mapa Satelital de los Lotes")
        st.map(df_mapa, size=20, zoom=11)

    # 9. REPORTE PREDICTIVO FINAL
    st.markdown("---")
    st.subheader("🤖 Reporte Predictivo del Motor de Inteligencia Artificial")
    st.dataframe(df_resultados.set_index('ID'), use_container_width=True)