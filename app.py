from flask import Flask, jsonify, send_from_directory
import os
import re
import unicodedata
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

app = Flask(__name__)

def limpiar_texto(texto):
    """Limpia paréntesis, acentos y caracteres especiales para comparar nombres."""
    if not texto:
        return ""
    texto = re.sub(r'\(.*?\)', '', texto) # Elimina parentesis y su contenido
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-zA-Z0-9\s]', '', texto).lower().strip()
    return texto

# Coordenadas por defecto en la costa de cada municipio (ajustadas a la orilla)
DEFAULTS_MUNICIPIOS = {
    "san pedro del pinatar": (37.8280, -0.7680),
    "san javier": (37.7400, -0.7380),
    "los alcazares": (37.7420, -0.8450),
    "cartagena": (37.6200, -0.7300),
    "mazarron": (37.5630, -1.2580),
    "aguilas": (37.4040, -1.5800),
    "lorca": (37.5180, -1.4050),
}

# Diccionario exacto de coordenadas para las playas de Murcia
COORDENADAS_PLAYAS = {
    # SAN PEDRO DEL PINATAR
    ("san pedro del pinatar", "el mojon"): (37.8420, -0.7720),
    ("san pedro del pinatar", "torre derribada"): (37.8295, -0.7635),
    ("san pedro del pinatar", "la llana"): (37.8210, -0.7580),
    ("san pedro del pinatar", "villananitos"): (37.8280, -0.7790),
    ("san pedro del pinatar", "la puntica"): (37.8230, -0.7810),
    ("san pedro del pinatar", "la mota"): (37.8250, -0.7850),

    # SAN JAVIER / LA MANGA
    ("san javier", "barnuevo"): (37.7950, -0.8030),
    ("san javier", "el castillico"): (37.7890, -0.8060),
    ("san javier", "colon"): (37.7830, -0.8080),
    ("san javier", "el pescador"): (37.7980, -0.8010),
    ("san javier", "la ensenada"): (37.7780, -0.8110),
    ("san javier", "lebeche"): (37.7380, -0.7390),
    ("san javier", "el pedruchillo"): (37.7120, -0.7380),
    ("san javier", "pedrucho"): (37.7120, -0.7380),
    ("san javier", "el galan"): (37.6980, -0.7360),
    ("san javier", "eurovosa"): (37.6890, -0.7350),
    ("san javier", "playa chica"): (37.7460, -0.7390),
    ("san javier", "veneziola"): (37.7650, -0.7360),
    ("san javier", "isla del ciervo"): (37.6620, -0.7230),

    # LOS ALCÁZARES
    ("los alcazares", "las salinas"): (37.7550, -0.8380),
    ("los alcazares", "los narejos"): (37.7480, -0.8410),
    ("los alcazares", "el espejo"): (37.7410, -0.8440),
    ("los alcazares", "manzanares"): (37.7340, -0.8480),
    ("los alcazares", "carrion"): (37.7280, -0.8510),
    ("los alcazares", "la concha"): (37.7220, -0.8550),

    # CARTAGENA
    ("cartagena", "punta brava"): (37.6685, -0.8412),
    ("cartagena", "los urrutias"): (37.6821, -0.8351),
    ("cartagena", "los nietos"): (37.6534, -0.7712),
    ("cartagena", "islas menores"): (37.6415, -0.7345),
    ("cartagena", "mar de cristal"): (37.6362, -0.7425),
    ("cartagena", "playa honda"): (37.6300, -0.7300),
    ("cartagena", "la gola"): (37.6432, -0.7185),
    ("cartagena", "marchamalo"): (37.6350, -0.7100),
    ("cartagena", "entremares"): (37.6420, -0.7150),
    ("cartagena", "galua"): (37.6480, -0.7120),
    ("cartagena", "cavanna"): (37.6520, -0.7200),
    ("cartagena", "calblanque"): (37.6025, -0.7380),
    ("cartagena", "cala cortina"): (37.5891, -0.9721),
    ("cartagena", "el portus"): (37.5870, -1.0560),
    ("cartagena", "isla plana"): (37.5720, -1.2110),
    ("cartagena", "la azohia"): (37.5612, -1.1685),
    ("cartagena", "san gines"): (37.5612, -1.1685),
    ("cartagena", "cala reona"): (37.6250, -0.7080),
    ("cartagena", "portman"): (37.5850, -0.8520),

    # MAZARRÓN (COORDINADAS REVISADAS Y CORREGIDAS EN LÍNEA DE COSTA)
    ("mazarron", "bolnuevo"): (37.5618, -1.3025),
    ("mazarron", "castellar"): (37.5580, -1.2825),
    ("mazarron", "nares"): (37.5588, -1.2745),
    ("mazarron", "la isla"): (37.5608, -1.2690),
    ("mazarron", "bahia"): (37.5622, -1.2642),
    ("mazarron", "puerto"): (37.5638, -1.2580),
    ("mazarron", "rihuete"): (37.5678, -1.2515),
    ("mazarron", "sillas"): (37.5678, -1.2515),
    ("mazarron", "el alamillo"): (37.5710, -1.2430),
    ("mazarron", "alamillo"): (37.5710, -1.2430),
    ("mazarron", "el mojon"): (37.5752, -1.2335),
    ("mazarron", "mojon"): (37.5752, -1.2335),
    ("mazarron", "percheles"): (37.5255, -1.3535),
    ("mazarron", "covaticas"): (37.5350, -1.3360),

    # ÁGUILAS
    ("aguilas", "levante"): (37.4048, -1.5778),
    ("aguilas", "la colonia"): (37.4032, -1.5831),
    ("aguilas", "poniente"): (37.4025, -1.5862),
    ("aguilas", "casica verde"): (37.3951, -1.6033),
    ("aguilas", "matalentisco"): (37.3977, -1.6177),
    ("aguilas", "la cabana"): (37.3982, -1.6005),
    ("aguilas", "calarreona"): (37.3865, -1.6186),
    ("aguilas", "la higuerica"): (37.3795, -1.6248),
    ("aguilas", "la carolina"): (37.3762, -1.6283),
    ("aguilas", "hornillo"): (37.4090, -1.5680),
    ("aguilas", "calabardina"): (37.4317, -1.5019),
    ("aguilas", "las delicias"): (37.4070, -1.5730),
    ("aguilas", "los cocedores"): (37.3740, -1.6310),

    # LORCA
    ("lorca", "puntas de calnegre"): (37.5180, -1.4050),
    ("lorca", "cala lena"): (37.5100, -1.4150),
    ("lorca", "cala blanca"): (37.5020, -1.4250),
}

@app.route("/")
def index():
    return send_from_directory(os.getcwd(), "playas.html")

def obtener_coordenadas(nombre_playa, municipio):
    p_clean = limpiar_texto(nombre_playa)
    m_clean = limpiar_texto(municipio)

    # 1. Búsqueda exacta por municipio + palabra clave de playa
    for (m, p), coords in COORDENADAS_PLAYAS.items():
        m_dict = limpiar_texto(m)
        p_dict = limpiar_texto(p)
        if m_dict in m_clean or m_clean in m_dict:
            if p_dict in p_clean or p_clean in p_dict:
                return coords

    # 2. Búsqueda flexible por nombre de playa (si el municipio falla)
    for (m, p), coords in COORDENADAS_PLAYAS.items():
        p_dict = limpiar_texto(p)
        if len(p_dict) >= 4 and (p_dict in p_clean or p_clean in p_dict):
            return coords

    # 3. Fallback a municipio
    for mun_key, coords in DEFAULTS_MUNICIPIOS.items():
        if mun_key in m_clean or m_clean in mun_key:
            return coords

    return (37.6252, -0.7732)

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
        "temperatura": "N/D",
        "humedad": "N/D",
        "prob_lluvia": "0%",
        "cielo": "Despejado",
        "nubes": "N/D",
        "viento": "N/D",
        "altura_olas": "0.2 m"
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

def extraer_playas_con_playwright():
    playas_brutas = []
    try:
        print("[SCRAPER] Abriendo navegador Playwright...")
        with sync_playwright() as p:
            # CORRECCIÓN PARA RENDER: Se añaden args de seguridad esenciales
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.goto("https://noticias.112rmurcia.es/playas/", timeout=40000)
            page.wait_for_timeout(4000)

            target_frame = page
            for frame in page.frames:
                try:
                    if frame.query_selector("select"):
                        target_frame = frame
                        print(f"[SCRAPER] Selector encontrado dentro del iframe: {frame.url or 'subframe'}")
                        break
                except Exception:
                    continue

            municipios = target_frame.evaluate("""() => {
                const select = document.querySelector('select');
                if (!select) return [];
                return Array.from(select.options)
                    .map(opt => ({ text: opt.innerText.trim(), value: opt.value }))
                    .filter(o => o.value && !o.text.toLowerCase().includes('selecciona'));
            }""")
            
            print(f"[SCRAPER] Municipios encontrados en el selector: {len(municipios)}")
            nombres_vistos = set()

            if municipios:
                for mun in municipios:
                    nombre_municipio = mun["text"]
                    val_municipio = mun["value"]
                    
                    try:
                        target_frame.select_option("select", value=val_municipio)
                        target_frame.wait_for_timeout(1000)
                        
                        tarjetas = target_frame.evaluate("""() => {
                            const divs = document.querySelectorAll('div, article, tr, li');
                            let results = [];
                            divs.forEach(div => {
                                let text = div.innerText;
                                if (text && (text.includes('BAÑO') || text.includes('PRECAUCIÓN') || text.includes('PELIGROSO') || text.includes('PROHIBIDO')) && text.length < 350) {
                                    let lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                                    if (lines.length >= 2) {
                                        results.push({
                                            nombre: lines[0],
                                            textoCompleto: text
                                        });
                                    }
                                }
                            });
                            return results;
                        }""")
                        
                        for item in tarjetas:
                            nombre = item["nombre"]
                            texto = item["textoCompleto"].upper()
                            
                            if len(nombre) < 3 or len(nombre) > 60:
                                continue
                                
                            skip_words = ["cookie", "aviso", "inicio", "contacto", "112", "murcia", "noticias", "estado", "menu", "emergencias", "todas", "playas", "prevención", "verano", "síguenos"]
                            if any(w in nombre.lower() for w in skip_words):
                                continue
                                
                            clave_unica = f"{nombre_municipio.lower()}_{nombre.lower()}"
                            if clave_unica in nombres_vistos:
                                continue
                            nombres_vistos.add(clave_unica)

                            color = "Verde"
                            hex_col = "#28a745"
                            estado = "Apto para el baño"
                            
                            if "ROJA" in texto or "PROHIBIDO" in texto or "PELIGROSO" in texto:
                                color = "Roja"
                                hex_col = "#dc3545"
                                estado = "Peligroso / Prohibido (112)"
                            elif "AMARILLA" in texto or "PRECAUCIÓN" in texto:
                                color = "Amarilla"
                                hex_col = "#e0a800"
                                estado = "Precaución (112)"
                                
                            playas_brutas.append({
                                "nombre": nombre,
                                "municipio": nombre_municipio,
                                "bandera": {"color": color, "texto": estado, "hex": hex_col}
                            })
                    except Exception as e:
                        print(f"[SCRAPER ERROR {nombre_municipio}]: {e}")

            browser.close()
        print(f"[SCRAPER] Total de playas extraídas de toda Murcia: {len(playas_brutas)}")
    except Exception as e:
        print(f"[ERROR SCRAPING PLAYWRIGHT]: {e}")
        
    return playas_brutas

@app.route("/api/playas")
def api_playas():
    CACHE_CLIMA.clear()
    hora_actual = datetime.now().strftime("%H:%M:%S")
    brutas = extraer_playas_con_playwright()
    
    playas_procesadas = []
    for p in brutas:
        lat, lng = obtener_coordenadas(p["nombre"], p["municipio"])
        clima = obtener_clima_por_municipio(p["municipio"], lat, lng)
        
        playas_procesadas.append({
            "nombre": p["nombre"],
            "municipio": p["municipio"],
            "lat": lat,
            "lng": lng,
            "cielo": clima["cielo"],
            "temperatura": clima["temperatura"],
            "humedad": clima["humedad"],
            "prob_lluvia": clima["prob_lluvia"],
            "nubes": clima["nubes"],
            "viento": clima["viento"],
            "altura_olas": clima["altura_olas"],
            "bandera": p["bandera"]
        })

    print(f"[API] Enviando {len(playas_procesadas)} playas procesadas.")
    return jsonify({
        "status": "ok",
        "ultima_actualizacion": hora_actual,
        "playas": playas_procesadas
    })

if __name__ == "__main__":
    app.run(debug=True, port=8000)