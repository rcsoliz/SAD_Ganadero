import streamlit as st
import pandas as pd
import plotly.express as px
import database as db  # <-- IMPORTAMOS NUESTRA CAPA DE DATOS PROPIA

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="SAD Ganadero Cruceño v5", page_icon="🐂", layout="wide")

st.title("🐂 SAD Ganadero: Dashboard Analítico de Pasturas")
st.write("Versión 5.0 (Final): Arquitectura limpia con separación de responsabilidades y modularidad.")
st.markdown("---")

# 2. PARÁMETROS REGIONALES DE SANTA CRUZ (Reglas de negocio)
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

# 3. INTERFAZ LATERAL (Inputs del Decisor)
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


# 4. PANEL DE GESTIÓN DE DATOS (Formularios web que consumen el módulo 'db')
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
                    db.insertar_potrero(nuevo_nombre, nuevas_ha, nuevos_dias_ini) # <-- LLAMADA MODULAR
                    st.success(f"¡{nuevo_nombre} guardado con éxito!")
                    st.rerun()

    with col_form2:
        st.subheader("🔄 Registrar Fin de Pastoreo")
        try:
            df_temporal = db.cargar_datos_desde_db() # <-- LLAMADA MODULAR
            lista_potreros = df_temporal.set_index('ID')['Potrero'].to_dict()
        except:
            lista_potreros = {}

        with st.form("form_actualizar_potrero"):
            if lista_potreros:
                id_seleccionado = st.selectbox("Seleccione el potrero:", options=list(lista_potreros.keys()), format_func=lambda x: f"ID {x} - {lista_potreros[x]}")
                dias_actualizar = st.number_input("NUEVOS Días de Descanso (0 si el ganado acaba de salir):", min_value=0, value=0)
                if st.form_submit_button("Actualizar Potrero"):
                    db.actualizar_potrero_especifico(id_seleccionado, dias_actualizar) # <-- LLAMADA MODULAR
                    st.success("¡Registro actualizado!")
                    st.rerun()


# 5. LEER BASE DE DATOS MEDIANTE EL MÓDULO 'db' Y CORRER MOTOR DE DECISIÓN
try:
    df_potreros = db.cargar_datos_desde_db() # <-- LLAMADA MODULAR
except:
    st.error("Error crítico al intentar conectar con ganaderia.db a través del módulo database.py.")
    st.stop()

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


# 6. VISUALIZACIÓN GRÁFICA INTERACTIVA (Plotly)
st.subheader("📊 Gráfico de Control Analítico de Pasturas")
st.write(f"La línea roja discontinua representa los **{dias_requeridos} días mínimos** requeridos para la región seleccionada.")

fig = px.bar(
    df_resultados, x="Potrero", y="Días de Descanso", text="Días de Descanso", color="Estado",
    color_discrete_map={"🟢 Listo para Pastoreo": "#2ecc71", "🔴 En Recuperación": "#e74c3c"},
    title="Estado de Descanso Acumulado por Potrero"
)
fig.add_hline(y=dias_requeridos, line_dash="dash", line_color="red", annotation_text=f"Mínimo ({dias_requeridos} días)")
fig.update_layout(xaxis_title="Potreros de la Estancia", yaxis_title="Días de Descanso Transcurridos", height=400)
fig.update_traces(textposition='outside')
st.plotly_chart(fig, use_container_width=True)


# 7. RECOMENDACIONES DE ROTACIÓN EN TABLA TEXTUAL
st.markdown("---")
st.subheader("🤖 Tabla General de Recomendaciones")
st.dataframe(df_resultados.set_index('ID'), use_container_width=True)


# 8. RESUMEN ESTRATÉGICO
potreros_listos = [r["Potrero"] for r in resultados if "Listo" in r["Estado"]]
if potreros_listos:
    st.success(f"💡 **Decisión Sugerida por el SAD:** El ganado enfocado en exportación debe ser trasladado al **{potreros_listos[0]}**, ya que ha alcanzado el nivel de desarrollo biológico ideal en la zona.")
else:
    st.error("🚨 **Alerta Crítica del Sistema:** Ningún potrero de la base de datos se encuentra apto para el pastoreo en este momento.")