from flask import Flask, jsonify, send_from_directory
import os
import requests
import unicodedata
import re
from datetime import datetime

app = Flask(__name__)

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

PLAYAS_COORDS = {
    # Águilas
    "CALABARDINA": {"lat": 37.4317, "lng": -1.5019},
    "LA COLONIA": {"lat": 37.4032, "lng": -1.5831},
    "LA CABAÑA": {"lat": 37.4010, "lng": -1.5900},
    "HORNILLO": {"lat": 37.4090, "lng": -1.5680},
    "PONIENTE I": {"lat": 37.4025, "lng": -1.5862},
    "CALARREONA": {"lat": 37.3865, "lng": -1.6186},
    "LAS DELICIAS I": {"lat": 37.4070, "lng": -1.5730},
    "PONIENTE II": {"lat": 37.4020, "lng": -1.5870},
    "LA HIGUERICA": {"lat": 37.3795, "lng": -1.6248},
    "LAS DELICIAS II": {"lat": 37.4080, "lng": -1.5720},
    "CASICA VERDE": {"lat": 37.3951, "lng": -1.6033},
    "LA CAROLINA": {"lat": 37.3762, "lng": -1.6283},
    "LEVANTE": {"lat": 37.4048, "lng": -1.5778},
    "MATALENTISCO": {"lat": 37.3977, "lng": -1.6177},
    # Mazarrón
    "EL MOJON": {"lat": 37.5752, "lng": -1.2335},
    "LA REYA": {"lat": 37.5595, "lng": -1.2910},
    "BOLNUEVO": {"lat": 37.5618, "lng": -1.3025},
    "EL ALAMILLO": {"lat": 37.5710, "lng": -1.2430},
    "BAHIA": {"lat": 37.5622, "lng": -1.2642},
    "PUERTO - RIHUETE": {"lat": 37.5678, "lng": -1.2515},
    "NARES": {"lat": 37.5588, "lng": -1.2745},
    "PERCHELES": {"lat": 37.5255, "lng": -1.3535},
    "CASTELLAR": {"lat": 37.5580, "lng": -1.2825},
}

def traducir_bandera(codigo_flag):
    mapeo = {
        100: {"texto": "SIN BANDERA", "hex": "#6c757d"},
        200: {"texto": "VERDE", "hex": "#28a745"},
        300: {"texto": "AMARILLA", "hex": "#ffc107"},
        400: {"texto": "ROJA", "hex": "#dc3545"},
        500: {"texto": "PLAYA CERRADA", "hex": "#343a40"}
    }
    return mapeo.get(codigo_flag, {"texto": "DESCONOCIDO", "hex": "#6c757d"})

def traducir_estado_mar(codigo_sea):
    mapeo = {
        0: "SIN ESTADO", 1: "LLANA", 2: "RIZADA", 3: "MAREJADILLA",
        4: "MAREJADA", 5: "FUERTE MAREJADA", 6: "GRUESA", 7: "MUY GRUESA"
    }
    return mapeo.get(codigo_sea, "NORMAL")

def traducir_codigo_tiempo(codigo):
    traducciones = {
        0: "Despejado", 1: "Principalmente despejado", 2: "Parcialmente nuboso",
        3: "Nuboso", 45: "Niebla", 51: "Llovizna", 61: "Lluvia ligera", 
        63: "Lluvia moderada", 80: "Chubascos", 95: "Tormenta"
    }
    return traducciones.get(codigo, "Despejado")

CACHE_CLIMA = {}

CACHE_PLAYAS_EMERGENCIA = [
    {
        "nombre": "LA COLONIA", "municipio": "ÁGUILAS", "lat": 37.4032, "lng": -1.5831,
        "cielo": "Despejado", "temperatura": "25°C", "humedad": "50%", "prob_lluvia": "0%",
        "nubes": "10%", "viento": "10 km/h", "altura_olas": "0.2 m", "estado_mar": "LLANA",
        "bandera": {"color": "VERDE", "texto": "VERDE", "hex": "#28a745"}
    },
    {
        "nombre": "LEVANTE", "municipio": "ÁGUILAS", "lat": 37.4048, "lng": -1.5778,
        "cielo": "Despejado", "temperatura": "25°C", "humedad": "50%", "prob_lluvia": "0%",
        "nubes": "10%", "viento": "10 km/h", "altura_olas": "0.2 m", "estado_mar": "LLANA",
        "bandera": {"color": "VERDE", "texto": "VERDE", "hex": "#28a745"}
    },
    {
        "nombre": "PUERTO - RIHUETE", "municipio": "MAZARRÓN", "lat": 37.5678, "lng": -1.2515,
        "cielo": "Despejado", "temperatura": "26°C", "humedad": "48%", "prob_lluvia": "0%",
        "nubes": "5%", "viento": "12 km/h", "altura_olas": "0.3 m", "estado_mar": "RIZADA",
        "bandera": {"color": "VERDE", "texto": "VERDE", "hex": "#28a745"}
    }
]

def obtener_clima(lat, lng, municipio):
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
                hora = datetime.now().hour
                clima["prob_lluvia"] = f"{hourly_prob[hora]}%"

        url_mar = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lng}&current=wave_height&timezone=auto"
        res_mar = requests.get(url_mar, timeout=3)
        if res_mar.status_code == 200:
            wave = res_mar.json().get("current", {}).get("wave_height")
            if wave is not None:
                clima["altura_olas"] = f"{wave} m"
    except Exception as e:
        print(f"[ERROR METEO]: {e}")
        
    CACHE_CLIMA[m_key] = clima
    return clima

@app.route("/")
def index():
    return send_from_directory(os.getcwd(), "playas.html")

@app.route("/api/playas")
def api_playas():
    global CACHE_PLAYAS_EMERGENCIA
    try:
        CACHE_CLIMA.clear()
        playas_procesadas = []

        res_mun = session.get(f"{BASE_URL_112}/BeachMunicipality", timeout=4)
        
        if res_mun.status_code == 200:
            municipios = res_mun.json()
            for mun in municipios:
                mun_id = mun.get("id")
                mun_nombre = mun.get("name", "").upper()

                res_flag = session.get(f"{BASE_URL_112}/BeachFlag?idmun={mun_id}", timeout=4)
                if res_flag.status_code == 200:
                    items = res_flag.json()
                    items = items if isinstance(items, list) else [items]

                    for p in items:
                        nombre_playa = p.get("name", "PLAYA")
                        coords = PLAYAS_COORDS.get(nombre_playa.upper(), {"lat": 37.5678, "lng": -1.2515})
                        flag_info = traducir_bandera(p.get("flag", 100))
                        sea_text = traducir_estado_mar(p.get("seaState", 0))
                        clima = obtener_clima(coords["lat"], coords["lng"], mun_nombre)

                        playas_procesadas.append({
                            "nombre": nombre_playa,
                            "municipio": mun_nombre,
                            "lat": coords["lat"],
                            "lng": coords["lng"],
                            "cielo": clima["cielo"],
                            "temperatura": clima["temperatura"],
                            "humedad": clima["humedad"],
                            "prob_lluvia": clima["prob_lluvia"],
                            "nubes": clima["nubes"],
                            "viento": clima["viento"],
                            "altura_olas": clima["altura_olas"],
                            "estado_mar": sea_text,
                            "bandera": {
                                "color": flag_info["texto"],
                                "texto": flag_info["texto"],
                                "hex": flag_info["hex"]
                            }
                        })
            
            if playas_procesadas:
                CACHE_PLAYAS_EMERGENCIA = playas_procesadas

        if not playas_procesadas:
            playas_procesadas = CACHE_PLAYAS_EMERGENCIA

        return jsonify({
            "status": "ok",
            "ultima_actualizacion": datetime.now().strftime("%H:%M:%S"),
            "playas": playas_procesadas
        })

    except Exception as e:
        print(f"[ERROR EN RENDER/112]: {e}")
        return jsonify({
            "status": "ok",
            "ultima_actualizacion": datetime.now().strftime("%H:%M:%S"),
            "playas": CACHE_PLAYAS_EMERGENCIA
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)