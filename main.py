import os
import requests
import time
import telepot
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mplfinance as mpf
from scipy.stats import zscore
from telepot.loop import MessageLoop
from flask import Flask
from threading import Thread

# --- NÚCLEO DE ESTABILIDAD (Render + UptimeRobot) ---
app = Flask('')
@app.route('/')
def home(): return "Centinela Quantum V15 Online"
def run_web(): app.run(host='0.0.0.0', port=8080)

# --- CREDENCIALES SEGURAS ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ID_CHAT = os.environ.get('CHAT_ID')
bot = telepot.Bot(TOKEN)

def fetch_data(symbol="BTCUSDT", interval="15m", limit=200):
    url = "https://api.binance.com/api/v3/klines"
    try:
        r = requests.get(url, params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=10).json()
        df = pd.DataFrame(r, columns=['Date','Open','High','Low','Close','Volume','ct','qa','nt','tb','tq','i'])
        df['Date'] = pd.to_datetime(df['Date'], unit='ms')
        df.set_index('Date', inplace=True)
        df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
        return df
    except: return None

def motor_quantum_autonomo():
    # Análisis Fractal Institucional (15m, 1h, 4h)
    df15 = fetch_data("BTCUSDT", "15m", 150)
    df1h = fetch_data("BTCUSDT", "1h", 100)
    df4h = fetch_data("BTCUSDT", "4h", 100)
    
    if df15 is None or df1h is None or df4h is None: return None

    p = df15['Close'].iloc[-1]
    ema200_4h = df4h['Close'].rolling(100).mean().iloc[-1]
    ema200_1h = df1h['Close'].rolling(100).mean().iloc[-1]
    
    # Inteligencia Estadística (Z-Score) para filtrar señales falsas
    z_actual = zscore(df15['Close'].values)[-1]
    
    # Noción de Tiempo Chronos (ATR + Velocidad)
    atr = (df15['High'] - df15['Low']).rolling(14).mean().iloc[-1]
    velocidad = abs(df15['Close'].diff().iloc[-1])
    tiempo_est = "5-10 min (Inminente)" if velocidad > (atr * 0.4) else "30-45 min (Desarrollo)"

    # Score de Confluencia Institucional (0-100)
    score = 50
    if p > ema200_4h and p > ema200_1h: score += 20 # Tendencia macro a favor
    if z_actual < -1.9: score += 20                # Punto estadístico de rebote
    if z_actual > 1.9: score -= 20                 # Punto estadístico de caída
    
    # Lógica de Relevancia: Solo califica si el score es extremo
    if score >= 90:
        return df15, p, score, "🚀 COMPRA INSTITUCIONAL", "🟢", tiempo_est, atr
    elif score <= 10:
        return df15, p, score, "📉 VENTA ELITE (SHORT)", "🔴", tiempo_est, atr
    else:
        return df15, p, score, "⌛ MERCADO NEUTRAL", "⚪", tiempo_est, atr

def handle(msg):
    chat_id = msg['chat']['id']
    txt = msg['text']
    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='🎯 Escaneo Quantum')], [KeyboardButton(text='📈 Ver Velas Japonesas'), KeyboardButton(text='🛡️ Riesgo/Soporte')]], resize_keyboard=True)

    if txt in ['/start', '/menu']:
        bot.sendMessage(chat_id, "🏛️ **CENTINELA QUANTUM V15**\nSistema autónomo activo. Solo recibirás alertas de alta relevancia.", reply_markup=markup)
    elif txt == '🎯 Escaneo Quantum':
        res = motor_quantum_autonomo()
        if res:
            _, p, sc, dec, col, t, _ = res
            bot.sendMessage(chat_id, f"{col} **ANÁLISIS DE ORÁCULO**\n`{dec}`\n\n💰 Precio: `${p}`\n🎯 Confluencia: `{sc}%` \n⏳ Ventana: `{t}`", parse_mode='Markdown')

def patrullar_y_notificar():
    while True:
        try:
            res = motor_quantum_autonomo()
            if res:
                _, p, score, dec, col, t, atr = res
                # AUTONOMÍA TOTAL: Solo notifica si es MUY relevante (90% o más)
                if score >= 90 or score <= 10:
                    msj = (f"🚨 **ALERTA DE ALTA RELEVANCIA**\n\n{dec}\n💰 Entrada: `${p}`\n⏳ Actuar en: `{t}`"
                           f"\n\n🚩 Stop Loss: `${round(p - (atr*2), 2) if 'COMPRA' in dec else round(p + (atr*2), 2)}`"
                           f"\n✅ Take Profit: `${round(p + (atr*3), 2) if 'COMPRA' in dec else round(p - (atr*3), 2)}`"
                           f"\n\n📊 *Confluencia estadística validada al {score}%*")
                    bot.sendMessage(ID_CHAT, msj)
            time.sleep(300) # Revisa cada 5 minutos exactos para coincidir con UptimeRobot
        except: time.sleep(60)

if __name__ == "__main__":
    Thread(target=run_web).start()
    MessageLoop(bot, handle).run_as_thread()
    patrullar_y_notificar()
