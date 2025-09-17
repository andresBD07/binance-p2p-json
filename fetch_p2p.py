import json, re
from datetime import datetime
import pytz
import requests
import firebase_admin
from firebase_admin import credentials, firestore

# Configuración
URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
HEADERS = { "Content-Type": "application/json" }

def hora_venezuela():
    vzla = pytz.timezone("America/Caracas")
    return datetime.now(vzla).strftime("%Y-%m-%d %H:%M:%S %Z")

def build_body(trade_type):
    return {
        "asset": "USDT",
        "fiat": "VES",
        "tradeType": trade_type,
        "page": 1,
        "rows": 10,
        "publisherType": "merchant"
    }

def extract_offers(text):
    regex = re.compile(r'"adv"\s*:\s*{[^}]*"price"\s*:\s*"([\d.]+)".*?"nickName"\s*:\s*"([^"]+)"', re.DOTALL)
    return [ { "price": float(p), "name": n } for p, n in regex.findall(text) if p.replace('.', '', 1).isdigit() ]

def fetch_offer(trade_type):
    body = build_body(trade_type)
    res = requests.post(URL, headers=HEADERS, json=body, timeout=20)
    res.raise_for_status()
    offers = extract_offers(res.text)
    if trade_type == "BUY":
        return offers[1] if len(offers) >= 2 else offers[-1] if offers else None
    else:
        return max(offers, key=lambda x: x["price"]) if offers else None

def guardar_en_firebase(data):
    cred = credentials.Certificate("firebase-cred.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    db.collection("binance_p2p").add(data)
    print("📤 Datos enviados a Firebase")

def main():
    try:
        buy = fetch_offer("BUY")
        sell = fetch_offer("SELL")
        avg = round((buy["price"] + sell["price"]) / 2, 2) if buy and sell else None

        data = {
            "actualizado": hora_venezuela(),
            "compra_segundo": buy,
            "venta_maxima": sell,
            "promedio": avg,
            "fuente": "Binance P2P (solo comerciantes verificados)"
        }

        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        guardar_en_firebase({
            "timestamp": datetime.utcnow().isoformat(),
            "compra": buy,
            "venta": sell,
            "promedio": avg
        })

        print("✅ data.json actualizado")

    except Exception as e:
        error_data = {
            "error": str(e),
            "actualizado": hora_venezuela()
        }
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(error_data, f, ensure_ascii=False, indent=2)
        print("❌ Error:", e)

if __name__ == "__main__":
    main()
