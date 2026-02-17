import requests
import time
import telepot
from flask import Flask
from threading import Thread

# --- SERVIDOR WEB PARA MANTENERLO VIVO ---
app = Flask('')

@app.route('/')
def home():
    return "Centinela Elite está patrullando..."

def run_web():
    app.run(host='0.0.0.0', port=8080)

# --- TUS DATOS MAESTROS ---
TOKEN_TELEGRAM = '8379504345:AAHZJh83607ehDN5-3X60NlDMWSke_Hf3ZE'
ID_CHAT = '8102187269'
bot = telepot.Bot(TOKEN_TELEGRAM)

def obtener_datos():
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": "BTCUSDT", "interval": "15m", "limit": 60}
    res = requests.get(url, params=params).json()
    cierres = [float(v[4]) for v in res]
    volumenes = [float(v[5]) for v in res]
    
    # Fibonacci 0.618 y Volumen institucional
    fib = max(cierres) - ((max(cierres) - min(cierres)) * 0.618)
    vol_p = sum(volumenes[-10:]) / 10
    v_fuerte = volumenes[-1] > (vol_p * 1.5)
    
    return cierres[-1], fib, v_fuerte

def patrullar():
    bot.sendMessage(ID_CHAT, "🛡️ **CENTINELA 24/7 ACTIVO**\nPatrullando desde la nube sin interrupciones.")
    while True:
        try:
            precio, fib, vol = obtener_datos()
            if precio <= fib * 1.001 and vol:
                bot.sendMessage(ID_CHAT, f"🚨 **ALERTA ELITE:**\nBitcoin en zona Fibonacci con volumen institucional.\nPrecio: `${precio}`")
            time.sleep(60)
        except Exception as e:
            time.sleep(30)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    patrullar()
