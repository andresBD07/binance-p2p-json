import requests, time
from datetime import datetime
import pytz

URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

def consultar(trade_type):
    body = {
        "asset": "USDT",
        "fiat": "VES",
        "tradeType": trade_type,
        "page": 1,
        "rows": 20,
        "payTypes": [],              # Todos los métodos de pago
        "publisherType": "merchant"  # Solo comerciantes verificados
    }
    r = requests.post(URL, headers=HEADERS, json=body, timeout=20)
    r.raise_for_status()
    return r.json().get("data", [])

def hora_venezuela():
    vzla = pytz.timezone("America/Caracas")
    ahora = datetime.now(vzla)
    return ahora.strftime("%d/%m/%Y %I:%M:%S %p")

def elegir_compra(data):
    candidatos = data[1:] if len(data) > 1 else []
    if not candidatos: return None
    return max(candidatos, key=lambda x: float(x["adv"]["price"]))

def elegir_venta(data):
    if not data: return None
    return max(data, key=lambda x: float(x["adv"]["price"]))

def mostrar():
    try:
        compras = consultar("BUY")
        ventas  = consultar("SELL")

        mejor_compra = elegir_compra(compras)
        mejor_venta  = elegir_venta(ventas)

        hora = hora_venezuela()
        print(f"\n🕒 {hora}")

        if mejor_compra:
            precio = round(float(mejor_compra["adv"]["price"]), 2)
            nombre = mejor_compra["advertiser"]["nickName"]
            print(f"🟢 Compra (mejor tras promo): {precio} Bs — {nombre}")
        else:
            print("🟢 Compra: No disponible")

        if mejor_venta:
            precio = round(float(mejor_venta["adv"]["price"]), 2)
            nombre = mejor_venta["advertiser"]["nickName"]
            print(f"🔴 Venta (máxima): {precio} Bs — {nombre}")
        else:
            print("🔴 Venta: No disponible")

    except Exception as e:
        print("❌ Error al consultar:", e)

def ciclo():
    while True:
        mostrar()
        time.sleep(30)

if __name__ == "__main__":
    ciclo()
