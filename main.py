import requests
import time
import telepot
import numpy as np
from telepot.loop import MessageLoop
from flask import Flask
from threading import Thread

# --- NÚCLEO DE SUPERVIVENCIA (Render + Uptime) ---
app = Flask('')
@app.route('/')
def home(): return "Centinela Elite V5 Online"
def run_web(): app.run(host='0.0.0.0', port=8080)

# --- CREDENCIALES ---
TOKEN = '8379504345:AAHZJh83607ehDN5-3X60NlDMWSke_Hf3ZE'
ID_CHAT = '8102187269'
bot = telepot.Bot(TOKEN)

def obtener_datos_elite():
    url = "https://api.binance.com/api/v3/klines"
    res = requests.get(url, params={"symbol": "BTCUSDT", "interval": "15m", "limit": 200}).json()
    c = np.array([float(v[4]) for v in res])
    h = np.array([float(v[2]) for v in res])
    l = np.array([float(v[3]) for v in res])
    vols = np.array([float(v[5]) for v in res])
    
    # 1. Filtro de Tendencia (EMA 200)
    ema200 = sum(c) / 200
    # 2. Fuerza (RSI)
    rsi = 100 - (100 / (1 + (sum(np.maximum(0, np.diff(c[-15:]))) / max(1, sum(np.maximum(0, -np.diff(c[-15:])))))))
    # 3. Volatilidad (ATR para Stop Loss profesional)
    atr = sum([max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1])) for i in range(-14, 0)]) / 14
    
    precio = c[-1]
    vol_fuerte = vols[-1] > (np.mean(vols[-20:]) * 1.5)
    
    # Gestión de Riesgo 2026
    stop_loss = precio - (atr * 1.5)
    take_profit = precio + (atr * 2.5) # Ratio beneficio 1:1.6
    
    return precio, ema200, rsi, vol_fuerte, stop_loss, take_profit

def handle(msg):
    chat_id = msg['chat']['id']
    txt = msg['text'].lower()

    if txt in ['/start', '/menu']:
        menu = ("🎮 **MENÚ CENTINELA ELITE 2026**\n\n"
                "📊 /reporte - Análisis técnico detallado\n"
                "🎯 /señal - ¿Hay alguna oportunidad ahora?\n"
                "🛡️ /riesgo - Ver niveles de protección\n"
                "🧠 /sugerencia - Recomendación de IA")
        bot.sendMessage(chat_id, menu, parse_mode='Markdown')
    
    elif txt == '/reporte':
        p, e, r, v, sl, tp = obtener_datos_elite()
        tnd = "🟢 ALCISTA" if p > e else "🔴 BAJISTA"
        msg = (f"📊 **REPORTE BTC**\n💰 Precio: `${p}`\n🔥 RSI: `{round(r,1)}`"
               f"\n🚀 Tendencia: `{tnd}`\n💎 Vol: `{'FUERTE' if v else 'NORMAL'}`")
        bot.sendMessage(chat_id, msg, parse_mode='Markdown')

    elif txt == '/sugerencia':
        p, e, r, v, sl, tp = obtener_datos_elite()
        if p > e and r < 40:
            bot.sendMessage(chat_id, "💡 **SUGERENCIA:** El precio está sobre soporte de tendencia. Busca entradas en largo si el volumen confirma.")
        elif p < e and r > 60:
            bot.sendMessage(chat_id, "💡 **SUGERENCIA:** Tendencia bajista y RSI alto. Riesgo de caída. Protege tus ganancias.")
        else:
            bot.sendMessage(chat_id, "💡 **SUGERENCIA:** Mercado lateral. Mejor esperar a una ruptura con volumen.")

def patrullar():
    while True:
        try:
            p, e, r, v, sl, tp = obtener_datos_elite()
            # SEÑAL DE CONFLUENCIA MAESTRA: Tendencia + RSI Sobrevendido + Vol
            if p > e and r < 35 and v:
                msj = (f"🚨 **SEÑAL DE CONFLUENCIA ELITE**\n"
                       f"Instituciones comprando en tendencia.\n\n"
                       f"💰 Entrada: `${p}`\n🚩 Stop Loss: `${round(sl, 2)}`"
                       f"\n✅ Take Profit: `${round(tp, 2)}`")
                bot.sendMessage(ID_CHAT, msj)
            time.sleep(300) # Revisa cada 5 minutos
        except: time.sleep(60)

if __name__ == "__main__":
    Thread(target=run_web).start() # Servidor para UptimeRobot
    MessageLoop(bot, handle).run_as_thread() # Escucha de comandos
    patrullar() # Vigilancia automática
