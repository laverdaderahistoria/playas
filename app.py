from flask import Flask, jsonify, send_from_directory
import os
import requests
import unicodedata
import re

app = Flask(__name__)

# Configuración de sesión con los headers que imitan al navegador
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://web-app.112rmurcia.com/"
})

BASE_URL_112 = "https://web-app.112rmurcia.com/copla-service/copla"

def limpiar_texto(texto):
    if not texto:
        return ""
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-zA-Z0-9]', ' ', texto).lower()
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def traducir_codigo_tiempo(codigo):
    traducciones = {
        0: "Despejado", 1: "Principalmente despejado", 2: "Parcialmente nuboso",
        3: "Nuboso", 45: "Niebla", 51: "Llovizna", 61: "Lluvia ligera", 
        63: "Lluvia moderada", 80: "Chubascos", 95: "Tormenta"
    }
    return traducciones.get(codigo, "Despejado")

CACHE_CLIMA = {}

def obtener_clima_por_municipio(municipio, lat, lng):
    m_key = limpiar_texto(municipio)
    if m_key in CACHE_CLIMA:
        return CACHE_CLIMA[m_key]

    clima = {
        "temperatura": "N/D", "humedad": "N/D", "prob_lluvia": "0%",
        "cielo": "Despejado", "nubes": "N/D", "viento": "N/D", "altura_olas": "0.2 m"
    }
    try:
        url_meteo = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&current=temperature_2m,relative_humidity_2m,weather_code,cloud_cover,wind_speed_10m&hourly=precipitation_probability&forecast_days=1&timezone=auto"
        res_m = requests.get(url_meteo, timeout=3)
        if res_m.status_code == 200:
            data = res_m.json()
            cur = data.get("current", {})
            clima["temperatura"] = f"{cur.get('temperature_2m', 'N/D')}°C"
            clima["humedad"] = f"{cur.get('relative_humidity_2m', 'N/D')}%"
            clima["cielo"] = traducir_codigo_tiempo(cur.get("weather_code", 0))
            clima["nubes"] = f"{cur.get('cloud_cover', 'N/D')}%"
            clima["viento"] = f"{cur.get('wind_speed_10m', 'N/D')} km/h"
            
            hourly_prob = data.get("hourly", {}).get("precipitation_probability", [])
            if hourly_prob:
                import datetime
                hora = datetime.datetime.now().hour
                clima["prob_lluvia"] = f"{hourly_prob[hora]}%"

        url_mar = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lng}&current=wave_height&timezone=auto"
        res_mar = requests.get(url_mar, timeout=3)
        if res_mar.status_code == 200:
            wave = res_mar.json().get("current", {}).get("wave_height")
            if wave is not None:
                clima["altura_olas"] = f"{wave} m"
    except Exception as e:
        print(f"[ERROR METEO {municipio}]: {e}")
        
    CACHE_CLIMA[m_key] = clima
    return clima

@app.route("/")
def index():
    return send_from_directory(os.getcwd(), "playas.html")

@app.route("/api/playas")
def api_playas():
    try:
        CACHE_CLIMA.clear()
        
        # 1. Obtener municipios y sus IDs desde el endpoint descubierto
        res_mun = session.get(f"{BASE_URL_112}/BeachMunicipality", timeout=5)
        municipios_map = {}
        if res_mun.status_code == 200:
            mun_data = res_mun.json()
            # Dependiendo de la estructura JSON devuelta, mapeamos el id y nombre
            # Ej: [{"id": 30003, "name": "MAZARRON"}, ...]
            for m in mun_data:
                m_id = m.get("id") or m.get("munId") or m.get("idmun")
                m_nombre = m.get("name") or m.get("munName") or m.get("nombre")
                if m_id and m_nombre:
                    municipios_map[m_id] = m_nombre.upper()

        playas_procesadas = []

        # 2. Consultar las banderas por cada ID de municipio encontrado
        for mun_id, mun_nombre in municipios_map.items():
            res_flag = session.get(f"{BASE_URL_112}/BeachFlag?idmun={mun_id}", timeout=5)
            if res_flag.status_code == 200:
                flags_data = res_flag.json()
                items = flags_data if isinstance(flags_data, list) else [flags_data]
                
                for playa_info in items:
                    nombre_playa = playa_info.get("beachName") or playa_info.get("nombre") or "Playa"
                    lat = playa_info.get("lat") or 37.5678
                    lng = playa_info.get("lng") or -1.2515
                    
                    # Extraer estado de bandera real
                    flag_name = playa_info.get("flagName") or playa_info.get("estadoBandera") or "VERDE"
                    
                    # Definir color según la bandera oficial
                    color_hex = "#28a745" # Verde por defecto
                    if "AMARILL" in str(flag_name).upper():
                        color_hex = "#ffc107"
                    elif "ROJ" in str(flag_name).upper():
                        color_hex = "#dc3545"
                    elif "CERRAD" in str(flag_name).upper():
                        color_hex = "#343a40"

                    clima = obtener_clima_por_municipio(mun_nombre, lat, lng)

                    playas_procesadas.append({
                        "nombre": nombre_playa,
                        "municipio": mun_nombre,
                        "lat": lat,
                        "lng": lng,
                        "cielo": clima["cielo"],
                        "temperatura": clima["temperatura"],
                        "humedad": clima["humedad"],
                        "prob_lluvia": clima["prob_lluvia"],
                        "nubes": clima["nubes"],
                        "viento": clima["viento"],
                        "altura_olas": clima["altura_olas"],
                        "bandera": {
                            "color": flag_name,
                            "texto": flag_name,
                            "hex": color_hex
                        }
                    })

        return jsonify({
            "status": "ok",
            "playas": playas_procesadas
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "mensaje": str(e),
            "playas": []
        }), 500

if __name__ == "__main__":
    app.run(debug=True, port=8000)