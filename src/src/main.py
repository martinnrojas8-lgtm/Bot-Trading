import time
import requests

# --- TUS DATOS DIRECTOS ---
TOKEN = "8009823136:AAFugndNO_lv00Q8t6xobWOJpkW1Z1xz9uc"
CHAT_ID = "6362924370"

# Lista de activos de Olymp Trade
ACTIVOS = [
    "Asia Composite Index", "BrasIndex", "Cafeina Index", 
    "Compound Index", "Crypto Composite Index", 
    "Europe Composite Index", "LATAM Index"
]

def enviar_telegram(mensaje):
    """Envía la alerta directamente a tu Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Error de conexión: {e}")

def analizar_señal_simulada(activo):
    """
    Esta función es el puente. Por ahora imprime que está vigilando.
    En el siguiente paso conectaremos los precios en tiempo real.
    """
    return "ESPERAR"

def ejecutar_bot():
    print(f"--- {time.strftime('%H:%M:%S')} | Vigilando índices de Olymp Trade ---")
    
    for activo in ACTIVOS:
        # Por ahora el bot recorre la lista y verifica que todo esté OK
        resultado = analizar_señal_simulada(activo)
        
        if resultado != "ESPERAR":
            alerta = f"🚀 ¡SEÑAL DETECTADA!\n📈 Activo: {activo}\n🎯 Acción: {resultado}\n⏰ Temporalidad: 15 min"
            enviar_telegram(alerta)

if __name__ == "__main__":
    print("Iniciando conexión con Telegram...")
    enviar_telegram("🤖 ¡Hola Martin! El Bot ya tiene tu ID y Token. Está listo para vigilar Olymp Trade.")
    
    while True:
        ejecutar_bot()
        # Espera 15 minutos para la siguiente vela
        print("Dormido 15 min hasta la próxima revisión...")
        time.sleep(900)
