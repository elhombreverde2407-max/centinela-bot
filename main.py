import requests
import time
import telepot
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from telepot.loop import MessageLoop
from flask import Flask
from threading import Thread
import os

# --- NÚCLEO ---
app = Flask('')
@app.route('/')
def home(): return "Centinela Elite V6 Online"
def run_web(): app.run(host='0.0.0.0', port=8080)

TOKEN = '8379504345:AAHZJh83607ehDN5-3X60NlDMWSke_Hf3ZE'
ID_CHAT = '8102187269'
bot = telepot.Bot(TOKEN)

def obtener_datos_master():
    url = "https://api.binance.com/api/v3/klines"
    res = requests.get(url, params={"symbol": "BTCUSDT", "interval": "15m", "limit": 100}).json()
    df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
    df['close'] = df['close'].astype(float)
    df['vol'] = df['vol'].astype(float)
    
    precio = df['close'].iloc[-1]
    ema200 = df['close'].rolling(100).mean().iloc[-1]
    vol_promedio = df['vol'].rolling(20).mean().iloc[-1]
    es_ballena = df['vol'].iloc[-1] > (vol_promedio * 3.0) # Radar de Ballenas x3
    
    # RSI y ATR
    diff = df['close'].diff()
    gain = diff.where(diff > 0, 0).rolling(14).mean()
    loss = -diff.where(diff < 0, 0).rolling(14).mean()
    rsi = 100 - (100 / (1 + (gain/loss).iloc[-1]))
    atr = (df['close'].max() - df['close'].min()) / 20 # Simulación ATR
    
    return df, precio, ema200, rsi, es_ballena, precio - (atr*2), precio + (atr*3)

def enviar_grafica(chat_id):
    df, p, e, r, b, sl, tp = obtener_datos_master()
    plt.figure(figsize=(10,5))
    plt.plot(df['close'].tail(50), label='Precio BTC', color='#F7931A', linewidth=2)
    plt.axhline(y=e, color='blue', linestyle='--', label='EMA 200 (Tendencia)')
    plt.title(f"Análisis Centinela - Precio Actual: ${p}")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig('chart.png')
    plt.close()
    bot.sendPhoto(chat_id, open('chart.png', 'rb'))
    os.remove('chart.png')

def handle(msg):
    chat_id = msg['chat']['id']
    txt = msg['text'].lower()

    if txt in ['/start', '/menu']:
        msj = ("🏦 **ESTACIÓN ELITE PUEBLA 2026**\n\n"
               "/reporte - Datos en tiempo real\n"
               "/grafica - Generar mapa visual\n"
               "/riesgo - Niveles de protección\n"
               "/sugerencia - Estrategia agresiva")
        bot.sendMessage(chat_id, msj)
    
    elif txt == '/grafica':
        bot.sendMessage(chat_id, "⌛ Generando gráfica institucional...")
        enviar_grafica(chat_id)

    elif txt == '/riesgo':
        p, e, r, b, sl, tp = obtener_datos_master()[1:]
        msj = (f"🛡️ **GESTIÓN DE RIESGO**\n\n"
               f"🚩 Stop Loss sugerido: `${round(sl, 2)}`"
               f"\n✅ Take Profit sugerido: `${round(tp, 2)}`"
               f"\n⚠️ Riesgo: 1% de tu capital máximo por operación.")
        bot.sendMessage(chat_id, msj)

    elif txt == '/sugerencia':
        p, e, r, b, sl, tp = obtener_datos_master()[1:]
        if p > e and r < 38:
            txt_s = f"🔥 **ORDEN AGRESIVA:** Compra inmediata. Confluencia alcista detectada. Entrada: `${p}`"
        elif p < e and r > 62:
            txt_s = f"🧊 **ORDEN AGRESIVA:** Venta/Short. Tendencia bajista confirmada. Entrada: `${p}`"
        else:
            txt_s = "⌛ **ESTADO:** Sin confluencia clara. Las ballenas están laterales. Mantente fuera."
        bot.sendMessage(chat_id, txt_s)

def patrullar():
    while True:
        try:
            df, p, e, r, b, sl, tp = obtener_datos_master()
            if b: # ALERTA DE BALLENAS
                bot.sendMessage(ID_CHAT, f"🐋 **RADAR DE BALLENAS:** ¡Volumen masivo detectado! Movimiento institucional inminente en `${p}`.")
            if p > e and r < 32:
                bot.sendMessage(ID_CHAT, f"🚨 **SEÑAL ELITE:** Compra en soporte con RSI bajo.\nPrecio: `${p}`")
            time.sleep(300)
        except: time.sleep(60)

if __name__ == "__main__":
    Thread(target=run_web).start()
    MessageLoop(bot, handle).run_as_thread()
    patrullar()
