import requests
import time
import telepot
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg') # Optimización crítica para servidores sin pantalla (Linux)
import matplotlib.pyplot as plt
from telepot.loop import MessageLoop
from flask import Flask
from threading import Thread
import os

# --- CONFIGURACIÓN DE SUPERVIVENCIA (Render) ---
app = Flask('')
@app.route('/')
def home(): return "Centinela Elite V9: El Oráculo Online"
def run_web(): app.run(host='0.0.0.0', port=8080)

# --- CREDENCIALES MAESTRAS ---
TOKEN = '8379504345:AAHZJh83607ehDN5-3X60NlDMWSke_Hf3ZE'
ID_CHAT = '8102187269'
bot = telepot.Bot(TOKEN)

def obtener_datos(symbol="BTCUSDT", interval="15m", limit=150):
    url = "https://api.binance.com/api/v3/klines"
    try:
        res = requests.get(url, params={"symbol": symbol, "interval": interval, "limit": limit}).json()
        df = pd.DataFrame(res, columns=['t', 'o', 'h', 'l', 'c', 'v', 'ct', 'qa', 'nt', 'tb', 'tq', 'i'])
        df[['c', 'v', 'h', 'l']] = df[['c', 'v', 'h', 'l']].astype(float)
        return df
    except: return None

def analizar_oraculo():
    df15 = obtener_datos("BTCUSDT", "15m", 150)
    df1h = obtener_datos("BTCUSDT", "1h", 100)
    if df15 is None or df1h is None: return None
    
    precio = df15['c'].iloc[-1]
    ema200_15 = df15['c'].rolling(100).mean().iloc[-1]
    ema200_1h = df1h['c'].rolling(100).mean().iloc[-1]
    
    # Indicadores Técnicos Profesionales
    delta = df15['c'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rsi = 100 - (100 / (1 + (gain/loss).iloc[-1]))
    atr = (df15['h'] - df15['l']).rolling(14).mean().iloc[-1]
    
    # Detección de Ballenas
    vol_avg = df15['v'].rolling(20).mean().iloc[-1]
    ballena = df15['v'].iloc[-1] > (vol_avg * 2.5)

    # Lógica de Decisión 2026
    if precio > ema200_15 and precio > ema200_1h and rsi < 40:
        dec, col = "🔥 TIEMPO DE COMPRAR (LONG)", "🟢"
    elif precio < ema200_15 and precio < ema200_1h and rsi > 60:
        dec, col = "❄️ TIEMPO DE VENDER (SHORT)", "🔴"
    else:
        dec, col = "⌛ ESPERAR (MERCADO NEUTRAL)", "⚪"
    
    return df15, precio, ema200_15, rsi, ballena, dec, col, atr

def handle(msg):
    chat_id = msg['chat']['id']
    txt = msg['text']

    # Menú de Botones para iPhone
    markup = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='🚀 ¿Comprar o Vender?')],
        [KeyboardButton(text='📈 Mapa Visual'), KeyboardButton(text='🛡️ Riesgo')]
    ], resize_keyboard=True)

    if txt in ['/start', '/menu']:
        bot.sendMessage(chat_id, "🏛️ **CENTINELA ORÁCULO V9**\nTu terminal está lista.", reply_markup=markup)

    elif txt == '🚀 ¿Comprar o Vender?':
        res = analizar_oraculo()
        if res:
            _, p, _, r, b, dec, col, _ = res
            msg = f"{col} **DECISIÓN:**\n`{dec}`\n\n💰 Precio: `${p}`\n🔥 RSI: `{round(r,1)}`"
            if b: msg += "\n\n⚠️ **¡ALERTA DE BALLENA DETECTADA!**"
            bot.sendMessage(chat_id, msg, parse_mode='Markdown')

    elif txt == '📈 Mapa Visual':
        bot.sendMessage(chat_id, "🎨 Dibujando mercado...")
        res = analizar_oraculo()
        if res:
            df, p, e, _, _, _, _, _ = res
            plt.figure(figsize=(8,4))
            plt.plot(df['c'].tail(45), color='orange', label='Bitcoin')
            plt.axhline(y=e, color='blue', linestyle='--', label='EMA 200')
            plt.title(f"BTC/USDT 15m - ${p}")
            plt.savefig('chart.png')
            plt.close()
            bot.sendPhoto(chat_id, open('chart.png', 'rb'))
            os.remove('chart.png')

    elif txt == '🛡️ Riesgo':
        res = analizar_oraculo()
        if res:
            _, p, _, _, _, _, _, atr = res
            bot.sendMessage(chat_id, f"🛡️ **RIESGO PROFESIONAL**\n\n🚩 Stop Loss: `${round(p - (atr*1.8), 2)}`"
                                     f"\n✅ Take Profit: `${round(p + (atr*3), 2)}`"
                                     f"\n⚖️ Ratio: 1:1.7")

def patrullar():
    while True:
        try:
            res = analizar_oraculo()
            if res:
                _, p, _, _, _, dec, _, _ = res
                if "COMPRAR" in dec or "VENDER" in dec:
                    bot.sendMessage(ID_CHAT, f"🚨 **ALERTA DE OPORTUNIDAD**\n{dec}\nPrecio: `${p}`")
            time.sleep(300) # Revisa cada 5 minutos
        except: time.sleep(60)

if __name__ == "__main__":
    Thread(target=run_web).start() # Mantiene vivo para UptimeRobot
    MessageLoop(bot, handle).run_as_thread() # Escucha tus botones
    patrullar() # Vigilancia automática
