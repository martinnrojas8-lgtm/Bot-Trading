import os
import time
import requests
from dotenv import load_dotenv
from connection import BrokerConnection, formatear_datos
from engine import analizar_señal

# Cargamos las credenciales que pusiste en el .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Lista de activos de tu captura de Olymp Trade
ACTIVOS = [
    "Asia Composite Index", "BrasIndex", "Cafeina Index", 
    "Compound Index", "Crypto Composite Index", 
    "Europe Composite Index", "LATAM Index"
]

def enviar_telegram(mensaje):
    """Envía la alerta directamente a tu chat personal"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

def ejecutar_bot():
    print(f"--- {time.strftime('%H:%M:%S')} | Revisando Activos ---")
    
    for activo in ACTIVOS:
        conexion = BrokerConnection(activo)
        datos_crudos = conexion.obtener_velas()
        
        if datos_crudos:
            df = formatear_datos(datos_crudos)
            resultado = analizar_señal(df)
            
            if resultado != "ESPERAR":
                alerta = f"🚀 ¡SEÑAL DETECTADA!\n📈 Activo: {activo}\n🎯 Acción: {resultado}\n⏰ Temporalidad: 15 min"
                enviar_telegram(alerta)
                print(f"✅ Alerta enviada para {activo}")
        else:
            # Mensaje temporal mientras conectamos los datos reales
            print(f"Buscando datos de {activo}...")

if __name__ == "__main__":
    enviar_telegram("🤖 ¡Hola Martin! Tu Bot de Trading está activo y vigilando los índices de Olymp Trade.")
    while True:
        ejecutar_bot()
        time.sleep(900) # Espera 15 minutos (900 segundos)
