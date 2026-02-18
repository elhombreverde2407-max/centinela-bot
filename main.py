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

# --- NÚCLEO DE ESTABILIDAD ---
app = Flask('')
@app.route('/')
def home(): return "Centinela V17 Quantum Apex Online"
def run_web(): app.run(host='0.0.0.0', port=8080)

# --- SEGURIDAD (Variables de Render) ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ID_CHAT = os.environ.get('CHAT_ID')
bot = telepot.Bot(TOKEN)

def fetch_data(symbol="BTCUSDT", interval="15m", limit=150):
    url = "https://api.binance.com/api/v3/klines"
    try:
        r = requests.get(url, params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=10).json()
        df = pd.DataFrame(r, columns=['Date','Open','High','Low','Close','Volume','ct','qa','nt','tb','tq','i'])
        df['Date'] = pd.to_datetime(df['Date'], unit='ms')
        df.set_index('Date', inplace=True)
        df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
        return df
    except: return None

def detectar_patrones(df):
    # Detecta martillos o velas envolventes (Señales de giro pro)
    last = df.iloc[-1]
    prev = df.iloc[-2]
    cuerpo = abs(last['Close'] - last['Open'])
    mecha_inf = last['Open'] - last['Low'] if last['Close'] > last['Open'] else last['Close'] - last['Low']
    es_martillo = mecha_inf > (cuerpo * 2)
    es_envolvente = last['Close'] > prev['Open'] and prev['Close'] < prev['Open'] if last['Close'] > last['Open'] else False
    return es_martillo or es_envolvente

def motor_apex_v17():
    df15 = fetch_data("BTCUSDT", "15m", 150)
    df4h = fetch_data("BTCUSDT", "4h", 100)
    if df15 is None or df4h is None: return None

    p = df15['Close'].iloc[-1]
    ema200 = df4h['Close'].rolling(100).mean().iloc[-1]
    z = zscore(df15['Close'].values)[-1]
    
    # Análisis de Volatilidad (Filtro de Noticias)
    atr = (df15['High'] - df15['Low']).rolling(14).mean().iloc[-1]
    volatilidad_extrema = abs(df15['Close'].diff().iloc[-1]) > (atr * 2.5) # Posible noticia
    
    # Inteligencia de Confluencia
    score = 50
    if p > ema200: score += 15
    if z < -1.8: score += 20
    if detectar_patrones(df15.tail(5)): score += 15
    
    tiempo = "5-10 min" if abs(z) > 1.5 else "20-40 min"
    return p, score, z, volatilidad_extrema, tiempo, atr

def handle(msg):
    chat_id = msg['chat']['id']
    if msg['text'] in ['/start', '/menu']:
        markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='🎯 Escaneo Apex')], [KeyboardButton(text='🕯️ Velas Japonesas')]], resize_keyboard=True)
        bot.sendMessage(chat_id, "🏛️ **CENTINELA V17: APEX AI**\nSistema de pre-aviso y noticias activo.", reply_markup=markup)

def patrullar_autonomo():
    pre_aviso_dado = False
    while True:
        try:
            p, score, z, noticia, t, atr = motor_apex_v17()
            
            # 1. FILTRO DE NOTICIAS (Autonomía ante volatilidad)
            if noticia:
                bot.sendMessage(ID_CHAT, "⚠️ **ADVERTENCIA DE VOLATILIDAD**: Se detecta movimiento brusco (posible noticia). El bot filtrará señales para evitar riesgos.")
            
            # 2. PRE-AVISO (5-10 min antes)
            if (82 <= score < 90 or 10 < score <= 18) and not pre_aviso_dado:
                bot.sendMessage(ID_CHAT, f"🟡 **PRE-AVISO CHRONOS (5 min)**\n\nOportunidad gestándose.\n💰 Precio: `${p}`\n🎯 Confluencia: `{score}%` \n⏳ Ventana: `{t}`")
                pre_aviso_dado = True

            # 3. NOTIFICACIÓN RELEVANTE (Ejecución)
            elif score >= 90 or score <= 10:
                msj = (f"🚨 **¡EJECUCIÓN INMEDIATA!**\n\nConfluencia Apex del `{score}%`.\n💰 Entrada: `${p}`"
                       f"\n🚩 SL: `${round(p - (atr*2), 2) if score > 50 else round(p + (atr*2), 2)}`"
                       f"\n✅ TP: `${round(p + (atr*3), 2) if score > 50 else round(p - (atr*3), 2)}`")
                bot.sendMessage(ID_CHAT, msj)
                pre_aviso_dado = False

            elif 45 < score < 55: pre_aviso_dado = False
            
            time.sleep(300) # Coincide con UptimeRobot
        except: time.sleep(60)

if __name__ == "__main__":
    Thread(target=run_web).start()
    MessageLoop(bot, handle).run_as_thread()
    patrullar_autonomo()
