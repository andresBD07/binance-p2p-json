import requests, json, time

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
        "payTypes": [],
        "publisherType": None
    }
    r = requests.post(URL, headers=HEADERS, json=body, timeout=20)
    r.raise_for_status()
    return r.json().get("data", [])

def extraer():
    compra = consultar("BUY")
    venta = consultar("SELL")

    segundo = compra[1] if len(compra) > 1 else None
    max_venta = max(venta, key=lambda x: float(x["adv"]["price"])) if venta else None

    def info(anuncio):
        if not anuncio: return {"precio": None, "comerciante": None}
        return {
            "precio": round(float(anuncio["adv"]["price"]), 2),
            "comerciante": anuncio["advertiser"]["nickName"]
        }

    compra_info = info(segundo)
    venta_info = info(max_venta)

    promedio = None
    if compra_info["precio"] is not None and venta_info["precio"] is not None:
        promedio = round((compra_info["precio"] + venta_info["precio"]) / 2, 2)

    fecha = time.strftime("%d/%m/%Y")
    hora = time.strftime("%I:%M %p")

    return {
        "compra_segundo": compra_info,
        "venta_maxima": venta_info,
        "promedio": promedio,
        "actualizado": f"{fecha} {hora}"
    }

def guardar():
    datos = extraer()
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print("✅ JSON actualizado:", datos)

if __name__ == "__main__":
    guardar()
