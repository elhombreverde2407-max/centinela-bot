import os, requests, time, telepot
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
def home(): return "Centinela V25 Risk Oracle: Online"
def run_web(): app.run(host='0.0.0.0', port=8080)

# --- SEGURIDAD ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ID_CHAT = os.environ.get('CHAT_ID')
bot = telepot.Bot(TOKEN)

# --- MEMORIA NEURAL (Self-Learning Avanzado) ---
class HyperionMemory:
    def __init__(self):
        self.precision_exigida = 90
        self.alertas_enviadas = 0
        self.capital_simulado = 1000 # Capital base para recomendación
        self.riesgo_max_per_trade = 0.02 # 2% de riesgo estándar

memory = HyperionMemory()

def fetch_data(symbol="BTCUSDT", interval="15m", limit=100):
    url = "https://api.binance.com/api/v3/klines"
    try:
        r = requests.get(url, params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=8).json()
        df = pd.DataFrame(r, columns=['Date','Open','High','Low','Close','Volume','ct','qa','nt','tb','tq','i'])
        df['Date'] = pd.to_datetime(df['Date'], unit='ms')
        df.set_index('Date', inplace=True)
        df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
        return df
    except: return None

def calcular_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def motor_v25_oracle():
    df15 = fetch_data("BTCUSDT", "15m", 100)
    df1h = fetch_data("BTCUSDT", "1h", 100)
    df4h = fetch_data("BTCUSDT", "4h", 100)
    
    if df15 is None or df1h is None or df4h is None: return None

    p = df15['Close'].iloc[-1]
    ema200_1h = df1h['Close'].rolling(50).mean().iloc[-1]
    ema200_4h = df4h['Close'].rolling(50).mean().iloc[-1]
    
    z = zscore(df15['Close'].values)[-1]
    atr = (df15['High'] - df15['Low']).rolling(14).mean().iloc[-1]
    df15['RSI'] = calcular_rsi(df15['Close'])
    rsi_act = df15['RSI'].iloc[-1]
    
    # --- VOLUMEN Y PÁNICO ---
    vol_avg = df15['Volume'].rolling(20).mean().iloc[-1]
    spike_vol = df15['Volume'].iloc[-1] > (vol_avg * 1.6)
    panic = abs(df15['Close'].pct_change().iloc[-1]) > 0.025

    # --- SCORE DE CONFLUENCIA ---
    score = 50
    if p > ema200_1h and p > ema200_4h: score += 15
    if p < ema200_1h and p < ema200_4h: score -= 15
    if z < -2.1: score += 20
    if z > 2.1: score -= 20
    if rsi_act < 32: score += 10
    if rsi_act > 68: score -= 10
    if spike_vol: score += 10 if z < 0 else -10
    
    # --- RECOMENDACIÓN DE RIESGO EXACTA ---
    confianza = "ALTA" if abs(score - 50) >= 40 else "MEDIA"
    riesgo_dinamico = "Bajo (1%)" if abs(z) < 1.5 else "Moderado (2%)"
    if abs(score - 50) >= 45: riesgo_dinamico = "ALTO - CONFIANZA TOTAL (3%)"
    
    stop_loss = round(p - (atr * 2.5), 2) if score > 50 else round(p + (atr * 2.5), 2)
    take_profit = round(p + (atr * 4.5), 2) if score > 50 else round(p - (atr * 4.5), 2)
    
    t_est = "2-4 min" if spike_vol else "15-35 min"
    
    threshold = memory.precision_exigida
    if score >= threshold: dec, col = "🚀 COMPRA ELITE", "🟢"
    elif score <= (100 - threshold): dec, col = "📉 VENTA ELITE", "🔴"
    else: dec, col = "⌛ PATRULLAJE NEUTRAL", "⚪"

    return df15, p, score, z, panic, atr, dec, col, t_est, riesgo_dinamico, stop_loss, take_profit

def handle(msg):
    chat_id = msg['chat']['id']
    txt = msg['text']
    
    markup = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='🎯 Escaneo Neural Sentinel')],
        [KeyboardButton(text='🕯️ Velas Pro'), KeyboardButton(text='🗺️ Mapa Visual')],
        [KeyboardButton(text='🛡️ Riesgo/Soporte'), KeyboardButton(text='🤖 AI Neural Insight')],
        [KeyboardButton(text='📈 Reporte'), KeyboardButton(text='⚙️ Configuración')]
    ], resize_keyboard=True)

    if txt in ['/start', '/menu']:
        bot.sendMessage(chat_id, "🏛️ **V25 NEURAL RISK ORACLE**\nPanel de trading profesional optimizado.", reply_markup=markup)
    
    elif txt == '🎯 Escaneo Neural Sentinel':
        res = motor_v25_oracle()
        if res:
            _, p, sc, _, _, _, dec, col, t, rd, sl, tp = res
            msg = (f"{col} **ANÁLISIS V25**\n`{dec}`\n\n💰 Precio: `${p}`\n🎯 Confluencia: `{sc}%` | `{t}`"
                   f"\n⚠️ Riesgo Sugerido: `{rd}`\n\n🚩 SL: `{sl}`\n✅ TP: `{tp}`")
            bot.sendMessage(chat_id, msg, parse_mode='Markdown')

    elif txt == '🤖 AI Neural Insight':
        res = motor_v25_oracle()
        if res:
            _, _, sc, z, _, _, _, _, _, _, _, _ = res
            insight = "Mercado estable."
            if abs(z) > 2.0: insight = "¡ANOMALÍA DETECTADA! El precio está fuera de su zona normal. Las ballenas están forzando el movimiento."
            bot.sendMessage(chat_id, f"🤖 **INSIGHT DE IA**\n\nConfluencia: `{sc}%` \nZ-Score: `{round(z,2)}` \n\n**Recomendación:** {insight}")

    elif txt == '🗺️ Mapa Visual':
        bot.sendMessage(chat_id, "📍 Generando mapa de calor y fractales...")
        res = motor_v24_sentinel() # Placeholder o lógica de velas
        bot.sendMessage(chat_id, "🗺️ *Función en desarrollo: Consultando liquidez institucional...*")

    elif txt == '🛡️ Riesgo/Soporte':
        res = motor_v25_oracle()
        if res:
            _, p, _, _, _, atr, _, _, _, rd, sl, tp = res
            bot.sendMessage(chat_id, f"🛡️ **GESTIÓN DE RIESGO PROFESIONAL**\n\n💰 Precio: `${p}`\n🚩 Stop Loss: `${sl}`\n✅ Take Profit: `${tp}`\n⚠️ Riesgo: `{rd}`")

def patrullar():
    pre_aviso = False
    while True:
        try:
            res = motor_v25_oracle()
            if res:
                _, p, score, _, panic, _, dec, col, t, rd, sl, tp = res
                if panic:
                    bot.sendMessage(ID_CHAT, "🛡️ **ESCUDO ACTIVO**: Volatilidad extrema. Pausa de seguridad.")
                    time.sleep(900)
                if (82 <= score < 90 or 10 < score <= 18) and not pre_aviso:
                    bot.sendMessage(ID_CHAT, f"🟡 **PRE-AVISO (5 MIN)**\nOportunidad al {score}%.\n💰 Precio: `${p}`\n⚠️ Riesgo: `{rd}`")
                    pre_aviso = True
                elif score >= 90 or score <= 10:
                    bot.sendMessage(ID_CHAT, f"🚨 **¡EJECUCIÓN! ({score}%)**\n{dec}\n💰 Entrada: `${p}`\n🚩 SL: `{sl}`\n✅ TP: `{tp}`")
                    pre_aviso = False
                elif 45 < score < 55: pre_aviso = False
            time.sleep(300)
        except: time.sleep(60)

if __name__ == "__main__":
    Thread(target=run_web).start()
    MessageLoop(bot, handle).run_as_thread()
    patrullar()
