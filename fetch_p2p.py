import json
from datetime import datetime
import pytz
import requests

URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (compatible; ImportVE/1.0)"
}

def consultar(trade_type: str):
    body = {
        "asset": "USDT",
        "fiat": "VES",
        "tradeType": trade_type,
        "page": 1,
        "rows": 30,
        "payTypes": [],
        "publisherType": "merchant"
    }
    r = requests.post(URL, headers=HEADERS, json=body, timeout=25)
    r.raise_for_status()
    return r.json().get("data", []) or []

def elegir_compra(data: list):
    candidatos = data[1:] if len(data) > 1 else []
    return max(candidatos, key=lambda x: float(x["adv"]["price"])) if candidatos else None

def elegir_venta(data: list):
    return max(data, key=lambda x: float(x["adv"]["price"])) if data else None

def hora_venezuela_str():
    vzla = pytz.timezone("America/Caracas")
    return datetime.now(vzla).strftime("%Y-%m-%d %H:%M:%S %Z")

def safe_float(s):
    try:
        return float(s)
    except Exception:
        return None

def main():
    try:
        compras = consultar("BUY")
        ventas  = consultar("SELL")

        best_buy  = elegir_compra(compras)
        best_sell = elegir_venta(ventas)

        compra_precio = safe_float(best_buy["adv"]["price"]) if best_buy else None
        compra_merchant = best_buy["advertiser"]["nickName"] if best_buy else None

        venta_precio = safe_float(best_sell["adv"]["price"]) if best_sell else None
        venta_merchant = best_sell["advertiser"]["nickName"] if best_sell else None

        promedio = round((compra_precio + venta_precio) / 2, 2) if compra_precio and venta_precio else None

        if compra_precio: compra_precio = round(compra_precio, 2)
        if venta_precio: venta_precio = round(venta_precio, 2)

        data = {
            "fiat": "VES",
            "asset": "USDT",
            "actualizado": hora_venezuela_str(),
            "compra_segundo": {
                "precio": compra_precio,
                "comerciante": compra_merchant
            },
            "venta_maxima": {
                "precio": venta_precio,
                "comerciante": venta_merchant
            },
            "promedio": promedio,
            "meta": {
                "publisherType": "merchant",
                "payTypes": "ALL",
                "notas": "Compra ignora anuncio promocionado; venta elige precio más alto"
            }
        }

        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print("✅ data.json actualizado")

    except Exception as e:
        error_data = {
            "error": str(e),
            "actualizado": hora_venezuela_str()
        }
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(error_data, f, ensure_ascii=False, indent=2)
        print("❌ Error:", e)

if __name__ == "__main__":
    main()
