import os
import requests
import time
import telepot
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
import numpy as np
import pandas as pd
from scipy.stats import zscore
from telepot.loop import MessageLoop
from flask import Flask
from threading import Thread

# --- NÚCLEO DE ESTABILIDAD ---
app = Flask('')
@app.route('/')
def home(): return "Centinela V21 Interpreter: Online"
def run_web(): app.run(host='0.0.0.0', port=8080)

# --- SEGURIDAD (Render Secrets) ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ID_CHAT = os.environ.get('CHAT_ID')
bot = telepot.Bot(TOKEN)

# --- MEMORIA DINÁMICA ---
class NeuralMemory:
    def __init__(self):
        self.precision_ajustada = 90
        self.ultima_interpretacion = ""

memory = NeuralMemory()

def fetch_data_pro(symbol="BTCUSDT", interval="15m", limit=150):
    url = "https://api.binance.com/api/v3/klines"
    try:
        r = requests.get(url, params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=8).json()
        df = pd.DataFrame(r, columns=['Date','Open','High','Low','Close','Volume','ct','qa','nt','tb','tq','i'])
        df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
        return df
    except: return None

def motor_interpreter():
    df15 = fetch_data_pro("BTCUSDT", "15m", 150)
    df4h = fetch_data_pro("BTCUSDT", "4h", 100)
    if df15 is None or df4h is None: return None

    p = df15['Close'].iloc[-1]
    ema200 = df4h['Close'].rolling(100).mean().iloc[-1]
    z = zscore(df15['Close'].values)[-1]
    atr = (df15['High'] - df15['Low']).rolling(14).mean().iloc[-1]
    
    # --- INTERPRETACIÓN AUTOMÁTICA DEL Z-SCORE ---
    if z < -2.0:
        inter_z = "🚨 SOBREVENTA EXTREMA: El precio está anormalmente bajo. Las ballenas suelen comprar aquí."
    elif z < -1.0:
        inter_z = "📉 DESVIACIÓN BAJISTA: El precio busca un piso. Posible rebote cerca."
    elif z > 2.0:
        inter_z = "⚠️ SOBRECOMPRA CRÍTICA: El precio está muy inflado. Riesgo alto de caída inminente."
    elif z > 1.0:
        inter_z = "📈 DESVIACIÓN ALCISTA: El precio tiene mucha fuerza, pero cuidado con una corrección."
    else:
        inter_z = "⚖️ EQUILIBRIO: El precio está en su zona justa. Sin ventaja estadística clara."

    # --- PÁNIC MODE ---
    panic = abs(df15['Close'].pct_change().iloc[-1]) > 0.025

    # --- SCORE NEURAL ---
    score = 50
    if p > ema200: score += 15
    if z < -2.1: score += 25
    if z > 2.1: score -= 25
    
    if score >= memory.precision_ajustada: dec, col = "🚀 COMPRA SINGULARIDAD", "🟢"
    elif score <= (100 - memory.precision_ajustada): dec, col = "📉 VENTA SINGULARIDAD", "🔴"
    else: dec, col = "⌛ PATRULLAJE NEUTRAL", "⚪"

    return p, score, z, panic, atr, dec, col, inter_z

def handle(msg):
    chat_id = msg['chat']['id']
    if msg['text'] in ['/start', '/menu']:
        markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='🎯 Escaneo con Intérprete AI')]], resize_keyboard=True)
        bot.sendMessage(chat_id, "🏛️ **V21 INTERPRETER ACTIVADO**\nAnalizando y traduciendo el mercado en tiempo real.", reply_markup=markup)
    elif msg['text'] == '🎯 Escaneo con Intérprete AI':
        p, sc, z, panic, atr, dec, col, iz = motor_interpreter()
        msg_final = (f"{col} **ANÁLISIS NEURAL V21**\n\nPrecio: `${p}`\nConfluencia: `{sc}%`"
                     f"\n\n**Interpretación del Oráculo:**\n_{iz}_")
        bot.sendMessage(chat_id, msg_final, parse_mode='Markdown')

def patrullar():
    pre_aviso_dado = False
    while True:
        try:
            p, score, z, panic, atr, dec, col, iz = motor_interpreter()
            
            if panic:
                bot.sendMessage(ID_CHAT, "🛡️ **MODO PÁNICO**: Volatilidad extrema detectada. Pausando para proteger capital.")
                time.sleep(900)
            
            # --- PRE-AVISO CON INTERPRETACIÓN ---
            if (memory.precision_ajustada - 8 <= score < memory.precision_ajustada) and not pre_aviso_dado:
                bot.sendMessage(ID_CHAT, f"🟡 **PRE-AVISO (5 MIN)**\n\nOportunidad al {score}%.\n💰 Precio: `${p}`\n\n🔍 **Vistazo Técnico:**\n{iz}")
                pre_aviso_dado = True

            # --- EJECUCIÓN ---
            elif score >= memory.precision_ajustada or score <= (100 - memory.precision_ajustada):
                msj = (f"🔥 **¡EJECUCIÓN INMEDIATA! ({score}%)**\n\n{dec}\n💰 Entrada: `${p}`"
                       f"\n🚩 SL: `${round(p - (atr*2.5), 2) if score > 50 else round(p + (atr*2.5), 2)}`"
                       f"\n✅ TP: `${round(p + (atr*4), 2) if score > 50 else round(p - (atr*4), 2)}`"
                       f"\n\n🧠 **Análisis Final:**\n{iz}")
                bot.sendMessage(ID_CHAT, msj)
                pre_aviso_dado = False

            elif 45 < score < 55: pre_aviso_dado = False
            
            time.sleep(300) # Sincronizado con UptimeRobot
        except: time.sleep(60)

if __name__ == "__main__":
    Thread(target=run_web).start()
    MessageLoop(bot, handle).run_as_thread()
    patrullar()
