import streamlit as st
import pandas as pd
import plotly.express as px
import database as db  # <-- IMPORTAMOS NUESTRA CAPA DE DATOS PROPIA

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="SAD Ganadero Cruceño v6", page_icon="🐂", layout="wide")

# 2. CONTROL DE SESIÓN (SISTEMA DE AUTENTICACIÓN)
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""

# Diccionario de credenciales para la defensa
USUARIOS_VALIDOS = {
    "roberto": "cruz2026",
    "ganadero2": "agro123"
}

# Si no está logueado, bloqueamos la pantalla con el formulario de Login
if not st.session_state["autenticado"]:
# 1. Espaciador vertical para despegar el formulario del techo de la pantalla
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    # 2. Creamos 3 columnas con proporciones [1, 2, 1] o [1, 1.5, 1]
    # La columna del centro (col_login) contendrá el formulario y se mantendrá centrada en pantallas grandes
    col_izq, col_login, col_der = st.columns([1, 1.5, 1])
    
    with col_login:
        # Contenedor visual para agrupar el título y la tarjeta de acceso
        st.markdown("<h2 style='text-align: center;'>🔐 Acceso al SAD Ganadero</h2>", unsafe_allow_html=True)
        st.write("<p style='text-align: center; color: gray;'>Sistema de Apoyo a las Decisiones Cruceñas</p>", unsafe_allow_html=True)
        
        with st.container(border=True): # Agrega un recuadro estético alrededor del formulario
            with st.form("login_form", border=False): # Quitamos el borde interno del formulario para evitar doble línea
                input_user = st.text_input("Usuario / Cuenta Estancia:")
                input_pass = st.text_input("Contraseña:", type="password")
                
                # Usamos una columna interna para alinear el botón o hacerlo resaltar
                st.markdown("<br>", unsafe_allow_html=True)
                btn_login = st.form_submit_button("Iniciar Sesión", use_container_width=True) # Botón ancho completo de la tarjeta
                
                if btn_login:
                    if input_user in USUARIOS_VALIDOS and USUARIOS_VALIDOS[input_user] == input_pass:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario"] = input_user
                        st.success("¡Acceso concedido! Cargando entorno...")
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos. Intente de nuevo.")
                        
    st.stop() # Detiene la renderización del resto del dashboard

# Si llegó aquí, está autenticado
usuario_activo = st.session_state["usuario"]

# Barra superior con título y botón de salir
col_titulo, col_logout = st.columns([9, 1])
with col_titulo:
    st.title(f"🐂 SAD Ganadero: Dashboard de @{usuario_activo.upper()}")
with col_logout:
    if st.button("🚪 Salir"):
        st.session_state["autenticado"] = False
        st.session_state["usuario"] = ""
        st.rerun()

st.write("Versión 6.0: Arquitectura limpia, multi-usuario y persistencia en Supabase (PostgreSQL).")
st.markdown("---")

# 3. PARÁMETROS REGIONALES DE SANTA CRUZ (Reglas de negocio)
PARAMETROS_REGIONALES = {
    "Norte Integrado (Montero, Mineros, Ichilo)": {
        "pasto": "Mombaça / Tanzania", "descanso_lluvia": 28, "descanso_seca": 45, "rendimiento_ms": 1.5
    },
    "Chiquitania (San Ignacio, Concepción, Chiquitos)": {
        "pasto": "Brachiaria Marandú", "descanso_lluvia": 38, "descanso_seca": 60, "rendimiento_ms": 0.9
    },
    "Chaco Cruceño (Cordillera, Boyuibe)": {
        "pasto": "Gatton Panic", "descanso_lluvia": 42, "descanso_seca": 90, "rendimiento_ms": 0.6
    }
}

# 4. INTERFAZ LATERAL (Inputs del Decisor)
st.sidebar.header("⚙️ Configuración de la Estancia")
region_elegida = st.sidebar.selectbox("Seleccione la Región/Provincia:", list(PARAMETROS_REGIONALES.keys()))
epoca_ano = st.sidebar.radio("Época del Año Actual:", ["Época de Lluvias (Verano)", "Época Seca (Invierno/Primavera)"])

config_local = PARAMETROS_REGIONALES[region_elegida]
dias_requeridos = config_local["descanso_lluvia"] if "Lluvias" in epoca_ano else config_local["descanso_seca"]

st.sidebar.markdown("---")
st.sidebar.subheader("📈 Datos del Lote de Ganado")
num_animales = st.sidebar.number_input("Cantidad de Novillos:", min_value=1, value=120)
peso_promedio = st.sidebar.number_input("Peso promedio (kg):", min_value=100, value=415)
consumo_diario_total = num_animales * (peso_promedio * 0.03)


# 5. PANEL DE GESTIÓN DE DATOS (Formularios web)
expander_gestion = st.expander("🛠️ Panel de Control Administrativo (Añadir / Actualizar Potreros)")
with expander_gestion:
    col_form1, col_form2 = st.columns(2)
    with col_form1:
        st.subheader("➕ Añadir Nuevo Potrero")
        with st.form("form_nuevo_potrero", clear_on_submit=True):
            nuevo_nombre = st.text_input("Nombre del Potrero:")
            nuevas_ha = st.number_input("Superficie en Hectáreas:", min_value=1.0, value=40.0, step=1.0)
            nuevos_dias_ini = st.number_input("Días de descanso iniciales:", min_value=0, value=30, step=1)
            if st.form_submit_button("Guardar Potrero en DB"):
                if nuevo_nombre.strip() != "":
                    # CORREGIDO: Ahora le enviamos el usuario activo a la DB
                    db.insertar_potrero(usuario_activo, nuevo_nombre, nuevas_ha, nuevos_dias_ini) 
                    st.success(f"¡{nuevo_nombre} guardado con éxito!")
                    st.rerun()

    with col_form2:
        st.subheader("🔄 Registrar Fin de Pastoreo")
        try:
            # CORREGIDO: Cargamos solo los potreros del usuario activo
            df_temporal = db.cargar_datos_desde_db(usuario_activo) 
            lista_potreros = df_temporal.set_index('ID')['Potrero'].to_dict()
        except:
            lista_potreros = {}

        with st.form("form_actualizar_potrero"):
            if lista_potreros:
                id_seleccionado = st.selectbox("Seleccione el potrero:", options=list(lista_potreros.keys()), format_func=lambda x: f"ID {x} - {lista_potreros[x]}")
                dias_actualizar = st.number_input("NUEVOS Días de Descanso (0 si el ganado acaba de salir):", min_value=0, value=0)
                if st.form_submit_button("Actualizar Potrero"):
                    db.actualizar_potrero_especifico(id_seleccionado, dias_actualizar) 
                    st.success("¡Registro actualizado!")
                    st.rerun()


# 6. LEER BASE DE DATOS FILTRADA Y CORRER MOTOR DE DECISIÓN
try:
    # CORREGIDO: Le pasamos el usuario logueado para aislar los datos
    df_potreros = db.cargar_datos_desde_db(usuario_activo) 
except Exception as e:
    st.error(f"Error crítico al intentar conectar con Supabase de @{usuario_activo}: {e}")
    st.stop()

if df_potreros.empty:
    st.info("👋 ¡Bienvenido! Aún no tiene potreros registrados. Use el panel administrativo de arriba para añadir el primero.")
else:
    resultados = []
    for index, fila in df_potreros.iterrows():
        id_p = fila["ID"]
        nombre = fila["Potrero"]
        ha = fila["Hectáreas"]
        dias_actuales = fila["Días de Descanso"]
        
        if dias_actuales >= dias_requeridos:
            estado = "🟢 Listo para Pastoreo"
            pasto_disponible_estimado = ha * (config_local["rendimiento_ms"] * 1000) * (dias_actuales / 365)
            dias_capacidad = int(pasto_disponible_estimado / consumo_diario_total)
            dias_capacidad = max(1, dias_capacidad)
            recomendacion = f"ÓPTIMO. Capacidad de carga estimada para {dias_capacidad} días."
        else:
            estado = "🔴 En Recuperación"
            dias_faltantes = dias_requeridos - dias_actuales
            recomendacion = f"NO INGRESAR. Faltan {dias_faltantes} días de descanso."
            
        resultados.append({
            "ID": id_p,
            "Potrero": nombre,
            "Superficie (Ha)": ha,
            "Días de Descanso": dias_actuales,
            "Estado": estado,
            "Recomendación del SAD": recomendacion
        })

    df_resultados = pd.DataFrame(resultados)

    # 7. VISUALIZACIÓN GRÁFICA INTERACTIVA (Plotly)
    st.subheader("📊 Gráfico de Control Analítico de Pasturas")
    fig = px.bar(
        df_resultados, x="Potrero", y="Días de Descanso", text="Días de Descanso", color="Estado",
        color_discrete_map={"🟢 Listo para Pastoreo": "#2ecc71", "🔴 En Recuperación": "#e74c3c"},
        title="Estado de Descanso Acumulado por Potrero"
    )
    fig.add_hline(y=dias_requeridos, line_dash="dash", line_color="red", annotation_text=f"Mínimo ({dias_requeridos} días)")
    fig.update_layout(xaxis_title="Potreros de la Estancia", yaxis_title="Días de Descanso Transcurridos", height=400)
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

    # 8. RECOMENDACIONES DE ROTACIÓN EN TABLA TEXTUAL
    st.subheader("🤖 Tabla General de Recomendaciones")
    st.dataframe(df_resultados.set_index('ID'), use_container_width=True)