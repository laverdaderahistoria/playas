from flask import Flask, jsonify, send_from_directory
import os
import re
import unicodedata
import requests
from bs4 import BeautifulSoup
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
    texto = re.sub(r'\(.*?\)', '', texto)
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-zA-Z0-9\s]', '', texto).lower().strip()
    return texto

# Base de datos completa de playas de la Región de Murcia
PLAYAS_BASE = [
    # San Pedro del Pinatar
    {"nombre": "El Mojón", "municipio": "San Pedro del Pinatar", "lat": 37.8420, "lng": -0.7720},
    {"nombre": "Torre Derribada", "municipio": "San Pedro del Pinatar", "lat": 37.8295, "lng": -0.7635},
    {"nombre": "La Llana", "municipio": "San Pedro del Pinatar", "lat": 37.8210, "lng": -0.7580},
    {"nombre": "Villananitos", "municipio": "San Pedro del Pinatar", "lat": 37.8280, "lng": -0.7790},
    {"nombre": "La Puntica", "municipio": "San Pedro del Pinatar", "lat": 37.8230, "lng": -0.7810},
    {"nombre": "La Mota", "municipio": "San Pedro del Pinatar", "lat": 37.8250, "lng": -0.7850},

    # San Javier
    {"nombre": "Barnuevo", "municipio": "San Javier", "lat": 37.7950, "lng": -0.8030},
    {"nombre": "El Castillico", "municipio": "San Javier", "lat": 37.7890, "lng": -0.8060},
    {"nombre": "Colón", "municipio": "San Javier", "lat": 37.7830, "lng": -0.8080},
    {"nombre": "El Pescador", "municipio": "San Javier", "lat": 37.7980, "lng": -0.8010},
    {"nombre": "La Ensenada", "municipio": "San Javier", "lat": 37.7780, "lng": -0.8110},
    {"nombre": "Lebeche", "municipio": "San Javier", "lat": 37.7380, "lng": -0.7390},
    {"nombre": "El Pedruchillo", "municipio": "San Javier", "lat": 37.7120, "lng": -0.7380},
    {"nombre": "El Galán", "municipio": "San Javier", "lat": 37.6980, "lng": -0.7360},
    {"nombre": "Eurovosa", "municipio": "San Javier", "lat": 37.6890, "lng": -0.7350},
    {"nombre": "Playa Chica", "municipio": "San Javier", "lat": 37.7460, "lng": -0.7390},
    {"nombre": "Veneziola", "municipio": "San Javier", "lat": 37.7650, "lng": -0.7360},
    {"nombre": "Isla del Ciervo", "municipio": "San Javier", "lat": 37.6620, "lng": -0.7230},

    # Los Alcázares
    {"nombre": "Las Salinas", "municipio": "Los Alcázares", "lat": 37.7550, "lng": -0.8380},
    {"nombre": "Los Narejos", "municipio": "Los Alcázares", "lat": 37.7480, "lng": -0.8410},
    {"nombre": "El Espejo", "municipio": "Los Alcázares", "lat": 37.7410, "lng": -0.8440},
    {"nombre": "Manzanares", "municipio": "Los Alcázares", "lat": 37.7340, "lng": -0.8480},
    {"nombre": "Carrión", "municipio": "Los Alcázares", "lat": 37.7280, "lng": -0.8510},
    {"nombre": "La Concha", "municipio": "Los Alcázares", "lat": 37.7220, "lng": -0.8550},

    # Cartagena
    {"nombre": "Punta Brava", "municipio": "Cartagena", "lat": 37.6685, "lng": -0.8412},
    {"nombre": "Los Urrutias", "municipio": "Cartagena", "lat": 37.6821, "lng": -0.8351},
    {"nombre": "Los Nietos", "municipio": "Cartagena", "lat": 37.6534, "lng": -0.7712},
    {"nombre": "Islas Menores", "municipio": "Cartagena", "lat": 37.6415, "lng": -0.7345},
    {"nombre": "Mar de Cristal", "municipio": "Cartagena", "lat": 37.6362, "lng": -0.7425},
    {"nombre": "Playa Honda", "municipio": "Cartagena", "lat": 37.6300, "lng": -0.7300},
    {"nombre": "La Gola", "municipio": "Cartagena", "lat": 37.6432, "lng": -0.7185},
    {"nombre": "Marchamalo", "municipio": "Cartagena", "lat": 37.6350, "lng": -0.7100},
    {"nombre": "Entremares", "municipio": "Cartagena", "lat": 37.6420, "lng": -0.7150},
    {"nombre": "Galuá", "municipio": "Cartagena", "lat": 37.6480, "lng": -0.7120},
    {"nombre": "Cavanna", "municipio": "Cartagena", "lat": 37.6520, "lng": -0.7200},
    {"nombre": "Calblanque", "municipio": "Cartagena", "lat": 37.6025, "lng": -0.7380},
    {"nombre": "Cala Cortina", "municipio": "Cartagena", "lat": 37.5891, "lng": -0.9721},
    {"nombre": "El Portús", "municipio": "Cartagena", "lat": 37.5870, "lng": -1.0560},
    {"nombre": "Isla Plana", "municipio": "Cartagena", "lat": 37.5720, "lng": -1.2110},
    {"nombre": "La Azohía", "municipio": "Cartagena", "lat": 37.5612, "lng": -1.1685},
    {"nombre": "San Ginés", "municipio": "Cartagena", "lat": 37.5612, "lng": -1.1685},
    {"nombre": "Cala Reona", "municipio": "Cartagena", "lat": 37.6250, "lng": -0.7080},
    {"nombre": "Portmán", "municipio": "Cartagena", "lat": 37.5850, "lng": -0.8520},

    # Mazarrón
    {"nombre": "Bolnuevo", "municipio": "Mazarrón", "lat": 37.5618, "lng": -1.3025},
    {"nombre": "Castellar", "municipio": "Mazarrón", "lat": 37.5580, "lng": -1.2825},
    {"nombre": "Nares", "municipio": "Mazarrón", "lat": 37.5588, "lng": -1.2745},
    {"nombre": "La Isla", "municipio": "Mazarrón", "lat": 37.5608, "lng": -1.2690},
    {"nombre": "Bahía", "municipio": "Mazarrón", "lat": 37.5622, "lng": -1.2642},
    {"nombre": "Puerto", "municipio": "Mazarrón", "lat": 37.5638, "lng": -1.2580},
    {"nombre": "Rihuete", "municipio": "Mazarrón", "lat": 37.5678, "lng": -1.2515},
    {"nombre": "El Alamillo", "municipio": "Mazarrón", "lat": 37.5710, "lng": -1.2430},
    {"nombre": "El Mojón (Mazarrón)", "municipio": "Mazarrón", "lat": 37.5752, "lng": -1.2335},
    {"nombre": "Percheles", "municipio": "Mazarrón", "lat": 37.5255, "lng": -1.3535},
    {"nombre": "La Reya", "municipio": "Mazarrón", "lat": 37.5595, "lng": -1.2910},

    # Águilas
    {"nombre": "Levante", "municipio": "Águilas", "lat": 37.4048, "lng": -1.5778},
    {"nombre": "La Colonia", "municipio": "Águilas", "lat": 37.4032, "lng": -1.5831},
    {"nombre": "Poniente", "municipio": "Águilas", "lat": 37.4025, "lng": -1.5862},
    {"nombre": "Casica Verde", "municipio": "Águilas", "lat": 37.3951, "lng": -1.6033},
    {"nombre": "Matalentisco", "municipio": "Águilas", "lat": 37.3977, "lng": -1.6177},
    {"nombre": "Calarreona", "municipio": "Águilas", "lat": 37.3865, "lng": -1.6186},
    {"nombre": "La Higuerica", "municipio": "Águilas", "lat": 37.3795, "lng": -1.6248},
    {"nombre": "La Carolina", "municipio": "Águilas", "lat": 37.3762, "lng": -1.6283},
    {"nombre": "Hornillo", "municipio": "Águilas", "lat": 37.4090, "lng": -1.5680},
    {"nombre": "Calabardina", "municipio": "Águilas", "lat": 37.4317, "lng": -1.5019},
    {"nombre": "Las Delicias", "municipio": "Águilas", "lat": 37.4070, "lng": -1.5730},
    {"nombre": "Los Cocedores", "municipio": "Águilas", "lat": 37.3740, "lng": -1.6310},

    # Lorca
    {"nombre": "Puntas de Calnegre", "municipio": "Lorca", "lat": 37.5180, "lng": -1.4050},
    {"nombre": "Cala Leña", "municipio": "Lorca", "lat": 37.5100, "lng": -1.4150},
    {"nombre": "Cala Blanca", "municipio": "Lorca", "lat": 37.5020, "lng": -1.4250}
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
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        url_main = "https://noticias.112rmurcia.es/playas/"
        res = requests.get(url_main, headers=headers, timeout=10)
        
        html_contenido = ""
        if res.status_code == 200:
            html_contenido += res.text
            soup = BeautifulSoup(res.text, 'html.parser')
            iframe = soup.find('iframe')
            if iframe and iframe.get('src'):
                sub_url = iframe['src']
                if sub_url.startswith('/'):
                    sub_url = "https://noticias.112rmurcia.es" + sub_url
                try:
                    res_sub = requests.get(sub_url, headers=headers, timeout=5)
                    if res_sub.status_code == 200:
                        html_contenido += " " + res_sub.text
                except Exception:
                    pass

        soup_full = BeautifulSoup(html_contenido, 'html.parser')
        tarjetas = soup_full.find_all(['div', 'article', 'li', 'tr'])
        
        for tarjeta in tarjetas:
            txt_tarjeta = tarjeta.get_text(separator=' ', strip=True)
            if not txt_tarjeta or len(txt_tarjeta) > 400:
                continue
            
            txt_upper = txt_tarjeta.upper()
            txt_clean = limpiar_texto(txt_tarjeta)
            
            color_tarjeta = "Verde"
            texto_tarj = "Apto para el baño"
            hex_tarj = "#28a745"
            
            if any(w in txt_upper for w in ['ROJA', 'PROHIBIDO', 'PELIGROSO']):
                color_tarjeta = "Roja"
                texto_tarj = "Peligroso / Prohibido (112)"
                hex_tarj = "#dc3545"
            elif any(w in txt_upper for w in ['AMARILLA', 'PRECAUCIÓN', 'PRECAUCION']):
                color_tarjeta = "Amarilla"
                texto_tarj = "Precaución (112)"
                hex_tarj = "#e0a800"

            for playa in PLAYAS_BASE:
                n_clean = limpiar_texto(playa['nombre'])
                palabras_sig = [p for p in n_clean.split() if p not in ['el', 'la', 'los', 'las', 'de', 'del']]
                
                match = False
                if n_clean in txt_clean:
                    match = True
                elif palabras_sig:
                    for palabra in palabras_sig:
                        if len(palabra) >= 4 and palabra in txt_clean:
                            match = True
                            break
                
                if match:
                    if color_tarjeta != "Verde" or n_clean not in banderas:
                        banderas[n_clean] = {
                            "color": color_tarjeta,
                            "texto": texto_tarj,
                            "hex": hex_tarj
                        }
    except Exception as e:
        print(f"[ERROR 112 BANDERAS]: {e}")
        
    return banderas

@app.route("/api/playas")
def api_playas():
    global CACHE_PLAYAS_DATA
    ahora = datetime.now()
    
    if CACHE_PLAYAS_DATA["data"] and CACHE_PLAYAS_DATA["timestamp"] and (ahora - CACHE_PLAYAS_DATA["timestamp"]).seconds < CACHE_EXPIRATION_SECS:
        print("[API] Sirviendo playas desde la caché.")
        return jsonify({
            "status": "ok",
            "ultima_actualizacion": CACHE_PLAYAS_DATA["timestamp"].strftime("%H:%M:%S"),
            "playas": CACHE_PLAYAS_DATA["data"]
        })

    CACHE_CLIMA.clear()
    banderas_112 = obtener_estados_banderas_112()
    playas_procesadas = []

    for playa in PLAYAS_BASE:
        nombre_clean = limpiar_texto(playa["nombre"])
        
        bandera = banderas_112.get(nombre_clean, {
            "color": "Verde",
            "texto": "Apto para el baño",
            "hex": "#28a745"
        })
        
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

    print(f"[API] Enviando {len(playas_procesadas)} playas procesadas.")
    return jsonify({
        "status": "ok",
        "ultima_actualizacion": ahora.strftime("%H:%M:%S"),
        "playas": playas_procesadas
    })

if __name__ == "__main__":
    app.run(debug=True, port=8000)