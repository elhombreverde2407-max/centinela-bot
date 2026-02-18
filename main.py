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
def home(): return "Centinela Quantum V15 Online"
def run_web(): app.run(host='0.0.0.0', port=8080)

# --- CREDENCIALES SEGURAS (Desde el cofre de Render) ---
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

def analizar_quantum():
    df15 = fetch_data("BTCUSDT", "15m", 150)
    df1h = fetch_data("BTCUSDT", "1h", 100)
    df4h = fetch_data("BTCUSDT", "4h", 100)
    if df15 is None or df1h is None or df4h is None: return None

    p = df15['Close'].iloc[-1]
    ema200 = df4h['Close'].rolling(100).mean().iloc[-1]
    z_actual = zscore(df15['Close'].values)[-1]
    atr = (df15['High'] - df15['Low']).rolling(14).mean().iloc[-1]
    sop = df4h['Low'].tail(20).min()
    resis = df4h['High'].tail(20).max()

    score = 50
    if p > ema200: score += 20
    if z_actual < -1.8: score += 20
    
    if score >= 90: dec, col = "🚀 COMPRA INSTITUCIONAL", "🟢"
    elif score <= 10: dec, col = "📉 VENTA ELITE (SHORT)", "🔴"
    else: dec, col = "⌛ MERCADO NEUTRAL", "⚪"
    
    return df15, p, score, dec, col, atr, sop, resis

def handle(msg):
    chat_id = msg['chat']['id']
    txt = msg['text']
    
    # Menú de Botones Profesional
    markup = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='🎯 Escaneo Quantum')],
        [KeyboardButton(text='📈 Ver Velas Japonesas'), KeyboardButton(text='🛡️ Riesgo/Soporte')]
    ], resize_keyboard=True)

    if txt in ['/start', '/menu']:
        bot.sendMessage(chat_id, "🏛️ **CENTINELA QUANTUM V15**\nSistema autónomo activo y protegido.", reply_markup=markup)
    
    elif txt == '🎯 Escaneo Quantum':
        res = analizar_quantum()
        if res:
            _, p, sc, dec, col, _, _, _ = res
            bot.sendMessage(chat_id, f"{col} **ANÁLISIS:**\n`{dec}`\n\n💰 Precio: `${p}`\n🎯 Confluencia: `{sc}%`", parse_mode='Markdown')

    elif txt == '📈 Ver Velas Japonesas':
        bot.sendMessage(chat_id, "🖌️ Generando gráfico institucional...")
        res = analizar_quantum()
        if res:
            df, p, _, _, _, _, s, r = res
            mc = mpf.make_marketcolors(up='green', down='red', inherit=True)
            style = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=False)
            mpf.plot(df.tail(40), type='candle', style=style, hlines=dict(hlines=[s, r], colors=['g', 'r'], alpha=0.5), savefig='v15.png')
            bot.sendPhoto(chat_id, open('v15.png', 'rb'), caption=f"BTC/USDT - `${p}`")
            os.remove('v15.png')

    elif txt == '🛡️ Riesgo/Soporte':
        res = analizar_quantum()
        if res:
            _, p, _, _, _, atr, s, r = res
            msg = (f"🛡️ **GESTIÓN PROFESIONAL**\n\n🟢 Soporte: `${s}`\n🔴 Resistencia: `${r}`"
                   f"\n\n🚩 Stop Loss: `${round(p - (atr*2), 2)}`"
                   f"\n✅ Take Profit: `${round(p + (atr*3), 2)}`")
            bot.sendMessage(chat_id, msg)

def patrullar():
    while True:
        try:
            res = analizar_quantum()
            if res:
                _, p, score, dec, col, _, _, _ = res
                if score >= 90 or score <= 10:
                    bot.sendMessage(ID_CHAT, f"🚨 **ALERTA RELEVANTE**\n{dec}\n💰 Entrada: `${p}`")
            time.sleep(300)
        except: time.sleep(60)

if __name__ == "__main__":
    Thread(target=run_web).start()
    MessageLoop(bot, handle).run_as_thread()
    patrullar()
