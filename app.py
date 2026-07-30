from flask import Flask, jsonify, send_from_directory
import os
import re
import unicodedata
import requests
from datetime import datetime

app = Flask(__name__)

CACHE_PLAYAS_DATA = {
    "timestamp": None,
    "data": []
}
CACHE_EXPIRATION_SECS = 1800  # 30 minutos

def limpiar_texto(texto):
    if not texto:
        return ""
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-zA-Z0-9]', ' ', texto).lower()
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

# Base de datos completa con las coordenadas y nombres exactos
PLAYAS_BASE = [
    # --- ÁGUILAS ---
    {"nombre": "CALABARDINA", "municipio": "AGUILAS", "lat": 37.4317, "lng": -1.5019},
    {"nombre": "LA COLONIA", "municipio": "AGUILAS", "lat": 37.4032, "lng": -1.5831},
    {"nombre": "LA CABAÑA", "municipio": "AGUILAS", "lat": 37.4010, "lng": -1.5900},
    {"nombre": "HORNILLO", "municipio": "AGUILAS", "lat": 37.4090, "lng": -1.5680},
    {"nombre": "PONIENTE I", "municipio": "AGUILAS", "lat": 37.4025, "lng": -1.5862},
    {"nombre": "CALARREONA", "municipio": "AGUILAS", "lat": 37.3865, "lng": -1.6186},
    {"nombre": "LAS DELICIAS I", "municipio": "AGUILAS", "lat": 37.4070, "lng": -1.5730},
    {"nombre": "PONIENTE II", "municipio": "AGUILAS", "lat": 37.4020, "lng": -1.5870},
    {"nombre": "LA HIGUERICA", "municipio": "AGUILAS", "lat": 37.3795, "lng": -1.6248},
    {"nombre": "LAS DELICIAS II", "municipio": "AGUILAS", "lat": 37.4080, "lng": -1.5720},
    {"nombre": "CASICA VERDE", "municipio": "AGUILAS", "lat": 37.3951, "lng": -1.6033},
    {"nombre": "LA CAROLINA", "municipio": "AGUILAS", "lat": 37.3762, "lng": -1.6283},
    {"nombre": "LEVANTE", "municipio": "AGUILAS", "lat": 37.4048, "lng": -1.5778},
    {"nombre": "MATALENTISCO", "municipio": "AGUILAS", "lat": 37.3977, "lng": -1.6177},

    # --- CARTAGENA ---
    {"nombre": "PUNTA BRAVA", "municipio": "CARTAGENA", "lat": 37.6685, "lng": -0.8412},
    {"nombre": "LA GOLA", "municipio": "CARTAGENA", "lat": 37.6432, "lng": -0.7185},
    {"nombre": "CALBLANQUE", "municipio": "CARTAGENA", "lat": 37.6025, "lng": -0.7380},
    {"nombre": "LOS URRUTIAS", "municipio": "CARTAGENA", "lat": 37.6821, "lng": -0.8351},
    {"nombre": "CAVANNA", "municipio": "CARTAGENA", "lat": 37.6520, "lng": -0.7200},
    {"nombre": "CALA DEL BARCO", "municipio": "CARTAGENA", "lat": 37.6030, "lng": -0.8000},
    {"nombre": "LOS NIETOS", "municipio": "CARTAGENA", "lat": 37.6534, "lng": -0.7712},
    {"nombre": "CALA DEL PINO", "municipio": "CARTAGENA", "lat": 37.6470, "lng": -0.7300},
    {"nombre": "CALA CORTINA", "municipio": "CARTAGENA", "lat": 37.5891, "lng": -0.9721},
    {"nombre": "ISLAS MENORES", "municipio": "CARTAGENA", "lat": 37.6415, "lng": -0.7345},
    {"nombre": "MONTE BLANCO", "municipio": "CARTAGENA", "lat": 37.6450, "lng": -0.7180},
    {"nombre": "EL PORTUS", "municipio": "CARTAGENA", "lat": 37.5870, "lng": -1.0560},
    {"nombre": "MAR DE CRISTAL", "municipio": "CARTAGENA", "lat": 37.6362, "lng": -0.7425},
    {"nombre": "GALUA", "municipio": "CARTAGENA", "lat": 37.6480, "lng": -0.7120},
    {"nombre": "LA AZOHIA", "municipio": "CARTAGENA", "lat": 37.5612, "lng": -1.1685},
    {"nombre": "PLAYA HONDA", "municipio": "CARTAGENA", "lat": 37.6300, "lng": -0.7300},
    {"nombre": "ENTREMARES", "municipio": "CARTAGENA", "lat": 37.6420, "lng": -0.7150},
    {"nombre": "PLAYA PARAISO", "municipio": "CARTAGENA", "lat": 37.6350, "lng": -0.7350},
    {"nombre": "ISLA PLANA", "municipio": "CARTAGENA", "lat": 37.5720, "lng": -1.2110},
    {"nombre": "CALA REONA", "municipio": "CARTAGENA", "lat": 37.6250, "lng": -0.7080},

    # --- LA UNION ---
    {"nombre": "EL LASTRE", "municipio": "LA UNION", "lat": 37.5870, "lng": -0.8750},
    {"nombre": "LA BAHIA I", "municipio": "LA UNION", "lat": 37.5860, "lng": -0.8760},
    {"nombre": "LA BAHIA II", "municipio": "LA UNION", "lat": 37.5850, "lng": -0.8770},

    # --- LORCA ---
    {"nombre": "PUNTAS DE CALNEGRE", "municipio": "LORCA", "lat": 37.5170, "lng": -1.4060},
    {"nombre": "PARAZUELOS", "municipio": "LORCA", "lat": 37.5150, "lng": -1.4100},

    # --- LOS ALCAZARES ---
    {"nombre": "CARRION", "municipio": "LOS ALCAZARES", "lat": 37.7280, "lng": -0.8510},
    {"nombre": "LAS PALMERAS", "municipio": "LOS ALCAZARES", "lat": 37.7300, "lng": -0.8490},
    {"nombre": "MANZANARES", "municipio": "LOS ALCAZARES", "lat": 37.7340, "lng": -0.8480},
    {"nombre": "EL ESPEJO", "municipio": "LOS ALCAZARES", "lat": 37.7410, "lng": -0.8440},
    {"nombre": "LA CONCHA", "municipio": "LOS ALCAZARES", "lat": 37.7220, "lng": -0.8550},
    {"nombre": "LOS NAREJOS", "municipio": "LOS ALCAZARES", "lat": 37.7480, "lng": -0.8410},

    # --- MAZARRON ---
    {"nombre": "EL MOJON", "municipio": "MAZARRON", "lat": 37.5752, "lng": -1.2335},
    {"nombre": "LA REYA", "municipio": "MAZARRON", "lat": 37.5595, "lng": -1.2910},
    {"nombre": "BOLNUEVO", "municipio": "MAZARRON", "lat": 37.5618, "lng": -1.3025},
    {"nombre": "EL ALAMILLO", "municipio": "MAZARRON", "lat": 37.5710, "lng": -1.2430},
    {"nombre": "BAHIA", "municipio": "MAZARRON", "lat": 37.5622, "lng": -1.2642},
    {"nombre": "PUERTO - RIHUETE", "municipio": "MAZARRON", "lat": 37.5678, "lng": -1.2515},
    {"nombre": "NARES", "municipio": "MAZARRON", "lat": 37.5588, "lng": -1.2745},
    {"nombre": "PERCHELES", "municipio": "MAZARRON", "lat": 37.5255, "lng": -1.3535},
    {"nombre": "CASTELLAR", "municipio": "MAZARRON", "lat": 37.5580, "lng": -1.2825},

    # --- SAN JAVIER ---
    {"nombre": "BARNUEVO", "municipio": "SAN JAVIER", "lat": 37.7950, "lng": -0.8030},
    {"nombre": "COLON", "municipio": "SAN JAVIER", "lat": 37.7830, "lng": -0.8080},
    {"nombre": "CASTILLICOS", "municipio": "SAN JAVIER", "lat": 37.7890, "lng": -0.8060},
    {"nombre": "VENEZIOLA", "municipio": "SAN JAVIER", "lat": 37.7650, "lng": -0.7360},
    {"nombre": "MISTRAL", "municipio": "SAN JAVIER", "lat": 37.7670, "lng": -0.7350},

    # --- SAN PEDRO DEL PINATAR ---
    {"nombre": "BARRACA QUEMADA", "municipio": "SAN PEDRO DEL PINATAR", "lat": 37.8350, "lng": -0.7680},
    {"nombre": "TORRE DERRIBADA", "municipio": "SAN PEDRO DEL PINATAR", "lat": 37.8295, "lng": -0.7635},
    {"nombre": "LA PUNTICA", "municipio": "SAN PEDRO DEL PINATAR", "lat": 37.8230, "lng": -0.7810},
    {"nombre": "VILLANANITOS", "municipio": "SAN PEDRO DEL PINATAR", "lat": 37.8280, "lng": -0.7790},
    {"nombre": "PUNTA DE ALGAS", "municipio": "SAN PEDRO DEL PINATAR", "lat": 37.8100, "lng": -0.7550}
]

@app.route("/")
def index():
    return send_from_directory(os.getcwd(), "playas.html")

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
                hora = datetime.now().hour
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

def obtener_estados_banderas_112():
    banderas = {}
    url_api = "https://web-app.112rmurcia.com/copla-service/copla/state/all"[cite: 1]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://noticias.112rmurcia.es/"
    }
    
    try:
        print(f"[*] Consultando API oficial del 112: {url_api}")
        response = requests.get(url_api, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            for item in data:
                nombre_playa = item.get("nombre") or item.get("name") or item.get("beachName")
                estado_info = item.get("estado") or item.get("state") or item.get("flag") or item.get("color")
                
                if nombre_playa:
                    n_clean = limpiar_texto(nombre_playa)
                    e_str = str(estado_info).lower()
                    
                    if any(v in e_str for v in ["1", "verde", "apta", "green"]):
                        info = {"color": "Verde", "texto": "Apta para el baño", "hex": "#28a745"}
                    elif any(v in e_str for v in ["2", "amarilla", "precaucion", "yellow"]):
                        info = {"color": "Amarilla", "texto": "Precaución", "hex": "#e0a800"}
                    elif any(v in e_str for v in ["3", "roja", "prohibido", "red"]):
                        info = {"color": "Roja", "texto": "Prohibido el baño", "hex": "#dc3545"}
                    else:
                        info = {"color": "Azul", "texto": "Sin Bandera", "hex": "#0077b6"}
                        
                    banderas[n_clean] = info
            print(f"[ÉXITO] Se han obtenido {len(banderas)} estados de playas desde la API oficial.")
        else:
            print(f"[!] Error en la API del 112. Código HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"[!] Error al consultar la API del 112: {e}")
        
    return banderas

@app.route("/api/playas")
def api_playas():
    global CACHE_PLAYAS_DATA
    ahora = datetime.now()
    
    if CACHE_PLAYAS_DATA["data"] and CACHE_PLAYAS_DATA["timestamp"] and (ahora - CACHE_PLAYAS_DATA["timestamp"]).seconds < CACHE_EXPIRATION_SECS:
        return jsonify({
            "status": "ok",
            "ultima_actualizacion": CACHE_PLAYAS_DATA["timestamp"].strftime("%H:%M:%S"),
            "playas": CACHE_PLAYAS_DATA["data"]
        })

    CACHE_CLIMA.clear()
    banderas_112 = obtener_estados_banderas_112()
    playas_procesadas = []

    BANDERA_DEFECTO = {
        "color": "Azul",
        "texto": "Sin Bandera",
        "hex": "#0077b6"
    }

    for playa in PLAYAS_BASE:
        nombre_clean = limpiar_texto(playa["nombre"])
        
        bandera = BANDERA_DEFECTO
        for k, v in banderas_112.items():
            if nombre_clean in k or k in nombre_clean:
                bandera = v
                break
        
        clima = obtener_clima_por_municipio(playa["municipio"], playa["lat"], playa["lng"])
        
        playas_procesadas.append({
            "nombre": playa["nombre"],
            "municipio": playa["municipio"],
            "lat": playa["lat"],
            "lng": playa["lng"],
            "cielo": clima["cielo"],
            "temperatura": clima["temperatura"],
            "humedad": clima["humedad"],
            "prob_lluvia": clima["prob_lluvia"],
            "nubes": clima["nubes"],
            "viento": clima["viento"],
            "altura_olas": clima["altura_olas"],
            "bandera": bandera
        })

    CACHE_PLAYAS_DATA["data"] = playas_procesadas
    CACHE_PLAYAS_DATA["timestamp"] = ahora

    return jsonify({
        "status": "ok",
        "ultima_actualizacion": ahora.strftime("%H:%M:%S"),
        "playas": playas_procesadas
    })

if __name__ == "__main__":
    app.run(debug=True, port=8000)