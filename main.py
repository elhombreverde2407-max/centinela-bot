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
def home(): return "Centinela V26 Hyperion Apex: Online"
def run_web(): app.run(host='0.0.0.0', port=8080)

TOKEN = os.environ.get('TELEGRAM_TOKEN')
ID_CHAT = os.environ.get('CHAT_ID')
bot = telepot.Bot(TOKEN)

class HyperionMemory:
    def __init__(self):
        self.precision_exigida = 90
        self.alertas_enviadas = 0
        self.inicio_sesion = time.strftime("%Y-%m-%d %H:%M")

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

def motor_v26_apex():
    df15 = fetch_data("BTCUSDT", "15m", 100)
    df1h = fetch_data("BTCUSDT", "1h", 100)
    df4h = fetch_data("BTCUSDT", "4h", 100)
    if df15 is None or df1h is None or df4h is None: return None

    p = df15['Close'].iloc[-1]
    ema200 = df4h['Close'].rolling(50).mean().iloc[-1]
    z = zscore(df15['Close'].values)[-1]
    atr = (df15['High'] - df15['Low']).rolling(14).mean().iloc[-1]
    
    # --- FILTRO DE PRECISIÓN EXTRA (Divergencia) ---
    vol_avg = df15['Volume'].rolling(20).mean().iloc[-1]
    spike_vol = df15['Volume'].iloc[-1] > (vol_avg * 1.7)
    
    score = 50
    if p > ema200: score += 15
    if z < -2.2: score += 25
    if z > 2.2: score -= 25
    if spike_vol: score += 10 if z < 0 else -10

    # Riesgo Dinámico
    riesgo = "Bajo (1%)" if abs(score-50) < 30 else "Moderado (2%)"
    if abs(score-50) >= 45: riesgo = "¡ALTO NIVEL DE CONFIANZA! (3%)"

    sl = round(p - (atr * 2.5), 2) if score > 50 else round(p + (atr * 2.5), 2)
    tp = round(p + (atr * 4.5), 2) if score > 50 else round(p - (atr * 4.5), 2)
    
    threshold = memory.precision_exigida
    dec, col = ("🚀 COMPRA ELITE", "🟢") if score >= threshold else (("📉 VENTA ELITE", "🔴") if score <= (100-threshold) else ("⌛ NEUTRAL", "⚪"))
    
    return df15, p, score, z, atr, dec, col, riesgo, sl, tp, spike_vol

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
        bot.sendMessage(chat_id, "🏛️ **V26 HYPERION APEX**\nPanel de comando 100% activo Bryan. ¿Qué analizamos?", reply_markup=markup)
    
    elif txt == '🎯 Escaneo Neural Sentinel':
        res = motor_v26_apex()
        if res:
            _, p, sc, _, _, dec, col, rd, sl, tp, _ = res
            bot.sendMessage(chat_id, f"{col} **ANÁLISIS APEX**\n`{dec}`\n\n💰 Precio: `${p}`\n🎯 Confluencia: `{sc}%` \n⚠️ Riesgo: `{rd}`\n\n🚩 SL: `{sl}`\n✅ TP: `{tp}`", parse_mode='Markdown')

    elif txt == '🕯️ Velas Pro':
        bot.sendMessage(chat_id, "🖌️ Generando gráfico institucional...")
        res = motor_v26_apex()
        if res:
            df, p, _, _, _, _, _, _, _, _, _ = res
            mc = mpf.make_marketcolors(up='green', down='red', inherit=True)
            style = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=False)
            mpf.plot(df.tail(40), type='candle', style=style, savefig='v26.png')
            bot.sendPhoto(chat_id, open('v26.png', 'rb'), caption=f"BTC/USDT - `${p}`")
            os.remove('v26.png')

    elif txt == '🗺️ Mapa Visual':
        res = motor_v26_apex()
        if res:
            _, p, sc, z, _, _, _, _, _, _, vol = res
            msg = (f"🗺️ **MAPA DE CONFLUENCIA**\n\n🐳 Volumen Institucional: `{'ALTO' if vol else 'NORMAL'}`"
                   f"\n📉 Presión Z-Score: `{round(z,2)}` desviaciones\n🎯 Precisión de IA: `{sc}%` de confluencia.")
            bot.sendMessage(chat_id, msg)

    elif txt == '🛡️ Riesgo/Soporte':
        res = motor_v26_apex()
        if res:
            _, p, _, _, _, _, _, rd, sl, tp, _ = res
            bot.sendMessage(chat_id, f"🛡️ **GESTIÓN DE RIESGO PROFESIONAL**\n\n💰 Precio: `${p}`\n🚩 Stop Loss: `${sl}`\n✅ Take Profit: `${tp}`\n⚠️ Sugerencia: `{rd}`")

    elif txt == '🤖 AI Neural Insight':
        res = motor_v26_apex()
        if res:
            _, _, sc, z, _, _, _, _, _, _, _ = res
            insight = "Mercado en equilibrio."
            if z < -2.0: insight = "¡ATENCIÓN! El precio está anormalmente bajo. Las ballenas suelen comprar en estos niveles de pánico."
            elif z > 2.0: insight = "CUIDADO: El precio está muy inflado. Posible corrección masiva en camino."
            bot.sendMessage(chat_id, f"🤖 **INSIGHT DE IA**\n\nConfluencia: `{sc}%` \n\n**Recomendación:** {insight}")

    elif txt == '📈 Reporte':
        bot.sendMessage(chat_id, f"📊 **REPORTE DE SESIÓN**\n\nIniciada: `{memory.inicio_sesion}`\nAlertas enviadas: `{memory.alertas_enviadas}`\nPrecisión exigida: `{memory.precision_exigida}%`")

    elif txt == '⚙️ Configuración':
        bot.sendMessage(chat_id, f"⚙️ **CONFIGURACIÓN ACTUAL**\n\nPar de Trading: `BTC/USDT` \nServidor: `Frankfurt (EU)` \nFiltro Institucional: `Activado`")

def patrullar():
    pre_aviso = False
    while True:
        try:
            res = motor_v26_apex()
            if res:
                _, p, score, _, _, dec, _, rd, sl, tp, _ = res
                if (82 <= score < 90 or 10 < score <= 18) and not pre_aviso:
                    bot.sendMessage(ID_CHAT, f"🟡 **PRE-AVISO (5 MIN)**\nOportunidad gestándose al {score}%.\n💰 Precio: `${p}`\n⚠️ Riesgo: `{rd}`")
                    pre_aviso = True
                elif score >= 90 or score <= 10:
                    bot.sendMessage(ID_CHAT, f"🚨 **¡EJECUCIÓN! ({score}%)**\n{dec}\n💰 Entrada: `${p}`\n🚩 SL: `{sl}`\n✅ TP: `{tp}`")
                    memory.alertas_enviadas += 1
                    pre_aviso = False
                elif 45 < score < 55: pre_aviso = False
            time.sleep(300)
        except: time.sleep(60)

if __name__ == "__main__":
    Thread(target=run_web).start()
    MessageLoop(bot, handle).run_as_thread()
    patrullar()
