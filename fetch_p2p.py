import json, os
from datetime import datetime
import pytz
import requests
import firebase_admin
from firebase_admin import credentials, firestore

# Configuración Binance
URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
HEADERS = { "Content-Type": "application/json" }

# Configuración Firebase (ahora usando variables de entorno)
# El contenido del JSON se almacena como una variable de entorno en GitHub Actions
FIREBASE_CONFIG = json.loads(os.environ["FIREBASE_CREDENTIALS"])
cred = credentials.Certificate(FIREBASE_CONFIG)
firebase_admin.initialize_app(cred)
db = firestore.client()

def hora_venezuela():
    vzla = pytz.timezone("America/Caracas")
    return datetime.now(vzla).strftime("%Y-%m-%d %H:%M:%S %Z")

def build_body(trade_type):
    return {
        "asset": "USDT",
        "fiat": "VES",
        "tradeType": trade_type,
        "page": 1,
        "rows": 20, # Aumentado para obtener más opciones
        "publisherType": "merchant"
    }

def fetch_offers_from_api(trade_type):
    body = build_body(trade_type)
    res = requests.post(URL, headers=HEADERS, json=body, timeout=20)
    res.raise_for_status()
    # Analizamos el JSON completo, que es más seguro y fiable
    return res.json()["data"]

def extract_offers(data, trade_type):
    offers = [{"price": float(item["adv"]["price"]), "name": item["advertiser"]["nickName"]} for item in data]
    
    if trade_type == "BUY":
        # Ordenar por precio de forma descendente y tomar el segundo (es lo que tu lógica original intentaba hacer)
        offers.sort(key=lambda x: x["price"], reverse=True)
        return offers[1] if len(offers) > 1 else None
    else: # "SELL"
        # Tomar el precio máximo
        return max(offers, key=lambda x: x["price"]) if offers else None

def guardar_en_firebase(data):
    # Usamos un documento fijo para que siempre se actualice el mismo
    doc_ref = db.collection("binance_p2p").document("precios_actuales")
    doc_ref.set(data)
    print("📤 Datos enviados a Firebase")

def main():
    try:
        data_buy = fetch_offers_from_api("BUY")
        data_sell = fetch_offers_from_api("SELL")
        
        buy = extract_offers(data_buy, "BUY")
        sell = extract_offers(data_sell, "SELL")
        
        if buy and sell:
            avg = round((buy["price"] + sell["price"]) / 2, 2)
        else:
            avg = None

        data_to_firebase = {
            "timestamp_utc": datetime.utcnow().isoformat(),
            "actualizado_vzla": hora_venezuela(),
            "compra_segundo": buy,
            "venta_maxima": sell,
            "promedio": avg,
            "fuente": "Binance P2P (solo comerciantes verificados)"
        }
        
        guardar_en_firebase(data_to_firebase)

    except requests.exceptions.RequestException as e:
        print(f"❌ Error de red: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ Error al decodificar JSON de la API de Binance: {e}")
    except Exception as e:
        print(f"❌ Un error inesperado ocurrió: {e}")

if __name__ == "__main__":
    main()
