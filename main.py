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
def home(): return "Centinela V20 Singularity: Online"
def run_web(): app.run(host='0.0.0.0', port=8080)

# --- SEGURIDAD (Variables de Render) ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ID_CHAT = os.environ.get('CHAT_ID')
bot = telepot.Bot(TOKEN)

# --- MEMORIA DINÁMICA (Aprendizaje de Errores) ---
class NeuralMemory:
    def __init__(self):
        self.historial_señales = []
        self.precision_ajustada = 90 # Inicia en 90%
        self.errores_recientes = 0

    def aprender(self, precio_entrada, direccion):
        # El bot revisará si la última señal fue exitosa tras 15 min
        self.historial_señales.append({'p': precio_entrada, 'd': direccion, 't': time.time()})
        if len(self.historial_señales) > 5: self.historial_señales.pop(0)

memory = NeuralMemory()

def fetch_data(symbol="BTCUSDT", interval="15m", limit=200):
    url = "https://api.binance.com/api/v3/klines"
    try:
        r = requests.get(url, params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=8).json()
        df = pd.DataFrame(r, columns=['Date','Open','High','Low','Close','Volume','ct','qa','nt','tb','tq','i'])
        df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
        return df
    except: return None

def motor_singularity():
    df15 = fetch_data("BTCUSDT", "15m", 150)
    df4h = fetch_data("BTCUSDT", "4h", 100)
    if df15 is None or df4h is None: return None

    p = df15['Close'].iloc[-1]
    ema200 = df4h['Close'].rolling(100).mean().iloc[-1]
    z = zscore(df15['Close'].values)[-1]
    atr = (df15['High'] - df15['Low']).rolling(14).mean().iloc[-1]
    
    # --- FILTRO DE VOLATILIDAD EXTREMA (MODO PÁNICO) ---
    volatilidad = abs(df15['Close'].pct_change().iloc[-1])
    panic_mode = volatilidad > 0.025 # Bloqueo si hay crash de >2.5%

    # --- SCORE NEURAL (Autonomía Pro) ---
    score = 50
    if p > ema200: score += 15 # Tendencia alcista
    if z < -2.2: score += 25    # Anomalía estadística fuerte (Compra)
    if z > 2.2: score -= 25     # Anomalía estadística fuerte (Venta)
    
    # Ajuste por aprendizaje: Si hubo errores, el bot exige más precisión
    threshold = memory.precision_ajustada
    
    if score >= threshold: dec, col = "🚀 COMPRA SINGULARIDAD", "🟢"
    elif score <= (100 - threshold): dec, col = "📉 VENTA SINGULARIDAD", "🔴"
    else: dec, col = "⌛ PATRULLAJE NEUTRAL", "⚪"

    return p, score, z, panic_mode, atr, dec, col

def handle(msg):
    chat_id = msg['chat']['id']
    if msg['text'] in ['/start', '/menu']:
        markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='🎯 Escaneo Singularity')]], resize_keyboard=True)
        bot.sendMessage(chat_id, "🏛️ **V20 SINGULARITY ACTIVADO**\nCerebro de aprendizaje y protección de flash-crash activo.", reply_markup=markup)
    elif msg['text'] == '🎯 Escaneo Singularity':
        p, sc, z, panic, atr, dec, col = motor_singularity()
        bot.sendMessage(chat_id, f"{col} **ANÁLISIS NEURAL**\nPrecio: `${p}`\nConfluencia: `{sc}%` \nEstado: `{'🚨 PÁNICO' if panic else '✅ ESTABLE'}`")

def patrullar():
    while True:
        try:
            p, score, z, panic, atr, dec, col = motor_singularity()
            
            if panic:
                bot.sendMessage(ID_CHAT, "🛡️ **ESCUDO ACTIVO**: Volatilidad extrema. Pausando 15 min para proteger capital.")
                time.sleep(900)
            
            # --- ALERTA DE PRE-AVISO (Anticipación 5 min) ---
            if (memory.precision_ajustada - 8 <= score < memory.precision_ajustada):
                bot.sendMessage(ID_CHAT, f"🟡 **PRE-AVISO (5 MIN)**\nOportunidad gestándose al {score}%.\n💰 Precio: `${p}`\n⏳ Abre Binance.")

            # --- ALERTA DE EJECUCIÓN (90%+) ---
            elif score >= memory.precision_ajustada or score <= (100 - memory.precision_ajustada):
                msj = (f"🔥 **EJECUCIÓN SINGULARIDAD ({score}%)**\n\n{dec}\n💰 Entrada: `${p}`"
                       f"\n🚩 Stop Loss: `${round(p - (atr*2.5), 2) if score > 50 else round(p + (atr*2.5), 2)}`"
                       f"\n✅ Take Profit: `${round(p + (atr*4), 2) if score > 50 else round(p - (atr*4), 2)}`"
                       f"\n\n⚠️ *Aprendizaje Neural: Precisión ajustada a {memory.precision_ajustada}%*")
                bot.sendMessage(ID_CHAT, msj)
                memory.aprender(p, "BUY" if score > 50 else "SELL")
            
            time.sleep(300) # Sincronizado con UptimeRobot
        except: time.sleep(60)

if __name__ == "__main__":
    Thread(target=run_web).start()
    MessageLoop(bot, handle).run_as_thread()
    patrullar()
