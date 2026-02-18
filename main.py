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
def home(): return "Centinela V22 Ultimate: Online"
def run_web(): app.run(host='0.0.0.0', port=8080)

# --- SEGURIDAD (Variables de Entorno) ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ID_CHAT = os.environ.get('CHAT_ID')
bot = telepot.Bot(TOKEN)

# --- MEMORIA Y APRENDIZAJE ---
class NeuralMemory:
    def __init__(self):
        self.precision_ajustada = 90
        self.noticias_flash = "Sin eventos críticos detectados."

memory = NeuralMemory()

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

def get_sentiment():
    try:
        r = requests.get("https://api.alternative.me/fng/", timeout=5).json()
        return int(r['data'][0]['value']), r['data'][0]['value_classification']
    except: return 50, "Neutral"

def motor_ultimate():
    df15 = fetch_data("BTCUSDT", "15m", 150)
    df4h = fetch_data("BTCUSDT", "4h", 100)
    fng_val, fng_class = get_sentiment()
    if df15 is None or df4h is None: return None

    p = df15['Close'].iloc[-1]
    ema200 = df4h['Close'].rolling(100).mean().iloc[-1]
    z = zscore(df15['Close'].values)[-1]
    atr = (df15['High'] - df15['Low']).rolling(14).mean().iloc[-1]
    
    # --- INTERPRETACIÓN DEL ORÁCULO ---
    if z < -2.0: iz = "🚨 SOBREVENTA: El precio está muy bajo. Oportunidad de rebote."
    elif z > 2.0: iz = "⚠️ SOBRECOMPRA: El precio está inflado. Riesgo de caída."
    else: iz = "⚖️ EQUILIBRIO: El precio está en zona neutral."

    # --- PÁNIC MODE Y TIEMPO ---
    panic = abs(df15['Close'].pct_change().iloc[-1]) > 0.025
    t_est = "3-8 min" if abs(z) > 1.8 else "25-50 min"

    # --- SCORE DE CONFLUENCIA ---
    score = 50
    if p > ema200: score += 15
    if z < -2.1: score += 25
    if z > 2.1: score -= 25
    
    if score >= memory.precision_ajustada: dec, col = "🚀 COMPRA ELITE", "🟢"
    elif score <= (100 - memory.precision_ajustada): dec, col = "📉 VENTA ELITE", "🔴"
    else: dec, col = "⌛ ESPERAR", "⚪"

    return df15, p, score, z, panic, atr, dec, col, iz, fng_val, fng_class, t_est

def handle(msg):
    chat_id = msg['chat']['id']
    txt = msg['text']
    
    # MENÚ 100% FUNCIONAL CON MÁS BOTONES
    markup = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='🎯 Escaneo Quantum AI')],
        [KeyboardButton(text='🕯️ Velas Japonesas'), KeyboardButton(text='📊 Sentimiento')],
        [KeyboardButton(text='🛡️ Riesgo/Soporte'), KeyboardButton(text='🗞️ Noticias Flash')]
    ], resize_keyboard=True)

    if txt in ['/start', '/menu']:
        bot.sendMessage(chat_id, "🏛️ **V22 ULTIMATE ORACLE ACTIVADO**\nElige una herramienta del panel profesional:", reply_markup=markup)
    
    elif txt == '🎯 Escaneo Quantum AI':
        res = motor_ultimate()
        if res:
            _, p, sc, z, pan, _, dec, col, iz, _, _, t = res
            bot.sendMessage(chat_id, f"{col} **ANÁLISIS V22**\n`{dec}`\n\n💰 Precio: `${p}`\n🎯 Confluencia: `{sc}%` | `{t}`\n\n**Oráculo:** _{iz}_", parse_mode='Markdown')

    elif txt == '🕯️ Velas Japonesas':
        bot.sendMessage(chat_id, "🖌️ Dibujando niveles institucionales...")
        res = motor_ultimate()
        if res:
            df, p, _, _, _, _, _, _, _, _, _, _ = res
            mc = mpf.make_marketcolors(up='green', down='red', inherit=True)
            s = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=False)
            mpf.plot(df.tail(40), type='candle', style=s, savefig='v22.png')
            bot.sendPhoto(chat_id, open('v22.png', 'rb'), caption=f"BTC/USDT - `${p}`")
            os.remove('v22.png')

    elif txt == '📊 Sentimiento':
        res = motor_ultimate()
        if res:
            _, _, _, _, _, _, _, _, _, fv, fc, _ = res
            bot.sendMessage(chat_id, f"🎭 **SENTIMIENTO DEL MERCADO**\n\nÍndice: `{fv}/100`\nEstado: `{fc}`\n\n*Recuerda: Compramos en miedo, vendemos en euforia.*")

    elif txt == '🛡️ Riesgo/Soporte':
        res = motor_ultimate()
        if res:
            _, p, _, _, _, atr, _, _, iz, _, _, _ = res
            bot.sendMessage(chat_id, f"🛡️ **GESTIÓN DE RIESGO**\n\n🚩 Stop Loss: `${round(p - (atr*2.5), 2)}`"
                                     f"\n✅ Take Profit: `${round(p + (atr*4), 2)}`"
                                     f"\n\n🔍 **Contexto:** {iz}")

    elif txt == '🗞️ Noticias Flash':
        bot.sendMessage(chat_id, f"🗞️ **RADAR DE NOTICIAS**\n\nEstado: `{memory.noticias_flash}`\n\n*El bot monitorea volatilidad inusual para detectar eventos antes que nadie.*")

def patrullar():
    pre_aviso = False
    while True:
        try:
            res = motor_ultimate()
            if res:
                df, p, score, z, panic, atr, dec, col, iz, _, _, t = res
                if panic:
                    bot.sendMessage(ID_CHAT, "🛡️ **MODO PÁNICO**: Crash detectado. Pausando 15 min.")
                    time.sleep(900)
                
                # PRE-AVISO Y EJECUCIÓN
                if (82 <= score < 90 or 10 < score <= 18) and not pre_aviso:
                    bot.sendMessage(ID_CHAT, f"🟡 **PRE-AVISO (5 MIN)**\nOportunidad al {score}%.\n💰 Precio: `${p}`\n🔍 {iz}")
                    pre_aviso = True
                elif score >= 90 or score <= 10:
                    bot.sendMessage(ID_CHAT, f"🚨 **¡EJECUCIÓN! ({score}%)**\n{dec}\n💰 Entrada: `${p}`\n⏳ Ventana: `{t}`")
                    pre_aviso = False
                elif 45 < score < 55: pre_aviso = False
            time.sleep(300)
        except: time.sleep(60)

if __name__ == "__main__":
    Thread(target=run_web).start()
    MessageLoop(bot, handle).run_as_thread()
    patrullar()
