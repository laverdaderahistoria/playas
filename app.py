from flask import Flask, jsonify, send_from_directory
import os
import requests

app = Flask(__name__)

@app.route("/")
def index():
    return send_from_directory(os.getcwd(), "playas.html")

@app.route("/api/test-single-beach")
def test_single_beach():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://web-app.112rmurcia.com/"
    })
    
    # Consultamos el endpoint de banderas para Mazarrón (idmun=30003)
    url = "https://web-app.112rmurcia.com/copla-service/copla/BeachFlag?idmun=30003"
    try:
        res = session.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            items = data if isinstance(data, list) else [data]
            
            # Buscamos la playa de Castellar para ver exactamente sus claves JSON
            playa_encontrada = None
            for item in items:
                nombre = str(item.get("beachName") or item.get("nombre") or "").upper()
                if "CASTELLAR" in nombre:
                    playa_encontrada = item
                    break
            
            return jsonify({
                "status": "success",
                "total_playas_recibidas": len(items),
                "playa_encontrada": playa_encontrada if playa_encontrada else "No encontrada",
                "todas_las_claves": list(items[0].keys()) if items else []
            })
        else:
            return jsonify({"status": "error", "code": res.status_code, "text": res.text})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)})

if __name__ == "__main__":
    app.run(debug=True, port=8000)