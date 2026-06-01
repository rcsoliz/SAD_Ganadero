"""
CAPA DE SERVICIO CLIMÁTICO — SAD Ganadero v9.0
Consume la API gratuita de Open-Meteo para obtener datos meteorológicos
en tiempo real a partir de coordenadas GPS de cada potrero.
Sin API key requerida. Límite: 10.000 llamadas/día (suficiente para producción).
"""

import requests
import streamlit as st

# URL base de la API Open-Meteo (abierta, sin autenticación)
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

@st.cache_data(ttl=1800)  # Cache de 30 minutos para no saturar la API
def obtener_clima_potrero(lat: float, lon: float) -> dict:
    """
    Consulta el clima actual y la precipitación acumulada de las últimas 24h
    para una coordenada GPS dada.

    Retorna un diccionario con:
        - temperatura_c     : float  (°C, temperatura actual)
        - humedad_pct       : int    (%, humedad relativa)
        - viento_kmh        : float  (km/h, velocidad del viento)
        - lluvia_mm_24h     : float  (mm acumulados en 24 horas)
        - descripcion       : str    (texto legible para el dashboard)
        - exito             : bool   (False si hubo error de conexión)
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
        ],
        # Suma de precipitación de las últimas 24 horas (1 período de 1 hora × 24)
        "hourly": "precipitation",
        "forecast_days": 1,
        "timezone": "America/La_Paz",  # Zona horaria de Bolivia/Santa Cruz
    }

    try:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()

        # Extraer valores actuales
        current = data.get("current", {})
        temp = current.get("temperature_2m", 0.0)
        humedad = current.get("relative_humidity_2m", 0)
        viento = current.get("wind_speed_10m", 0.0)

        # Sumar precipitaciones horarias de las últimas 24h
        precipitaciones = data.get("hourly", {}).get("precipitation", [])
        lluvia_24h = round(sum(precipitaciones), 1)

        # Descripción amigable
        if lluvia_24h > 20:
            desc = f"🌧️ Lluvias intensas ({lluvia_24h} mm)"
        elif lluvia_24h > 5:
            desc = f"🌦️ Lluvias moderadas ({lluvia_24h} mm)"
        elif lluvia_24h > 0:
            desc = f"🌤️ Llovizna leve ({lluvia_24h} mm)"
        elif temp > 35:
            desc = "☀️ Calor intenso, sin lluvia"
        else:
            desc = "⛅ Seco / despejado"

        return {
            "temperatura_c": round(temp, 1),
            "humedad_pct": int(humedad),
            "viento_kmh": round(viento, 1),
            "lluvia_mm_24h": lluvia_24h,
            "descripcion": desc,
            "exito": True,
        }

    except requests.exceptions.ConnectionError:
        return _clima_fallback("Sin conexión a la API climática")
    except requests.exceptions.Timeout:
        return _clima_fallback("Tiempo de espera agotado")
    except Exception as e:
        return _clima_fallback(f"Error: {str(e)[:60]}")


def _clima_fallback(motivo: str) -> dict:
    """Retorna un diccionario neutro cuando la API no responde."""
    return {
        "temperatura_c": 0.0,
        "humedad_pct": 0,
        "viento_kmh": 0.0,
        "lluvia_mm_24h": 0.0,
        "descripcion": f"⚠️ {motivo}",
        "exito": False,
    }


def calcular_tasa_ndvi_por_clima(clima: dict, tasa_base: float) -> float:
    """
    Ajusta la tasa de recuperación diaria del NDVI en función del clima real.

    Lógica agronómica para Santa Cruz, Bolivia:
    - Lluvia >= 10mm/día → condición óptima, tasa completa
    - Lluvia 5–10mm    → condición favorable, 80% de tasa
    - Lluvia 1–5mm     → condición seca, 50% de tasa
    - Lluvia < 1mm     → sequía, 30% de tasa
    - Temperatura > 38°C añade penalización adicional por estrés térmico

    Args:
        clima: Diccionario retornado por obtener_clima_potrero()
        tasa_base: La tasa base de recuperación diaria de NDVI del sistema

    Returns:
        float: Tasa ajustada por clima real
    """
    if not clima["exito"]:
        # Sin datos climáticos: usamos tasa conservadora (50%)
        return tasa_base * 0.5

    lluvia = clima["lluvia_mm_24h"]
    temp = clima["temperatura_c"]

    # Factor base por precipitación
    if lluvia >= 10:
        factor = 1.0
    elif lluvia >= 5:
        factor = 0.8
    elif lluvia >= 1:
        factor = 0.5
    else:
        factor = 0.3

    # Penalización por estrés térmico extremo (temperatura > 38°C)
    if temp > 38:
        factor *= 0.75

    return round(tasa_base * factor, 5)
