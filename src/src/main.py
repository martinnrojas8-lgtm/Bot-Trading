from connection import BrokerConnection, formatear_datos
from engine import analizar_señal
import time

# Lista de activos que me pasaste en la foto
ACTIVOS = [
    "Asia Composite Index", 
    "BrasIndex", 
    "Cafeina Index", 
    "Commodity Composite Index", 
    "Europe Composite Index", 
    "LATAM Index"
]

def ejecutar_bot():
    print("--- Bot de Trading EMA 9/21 (15 min) Iniciado ---")
    
    for activo in ACTIVOS:
        # 1. Intentamos conectar y obtener datos
        conexion = BrokerConnection(activo)
        datos_crudos = conexion.obtener_velas()
        
        if datos_crudos:
            # 2. Formateamos los datos
            df = formatear_datos(datos_crudos)
            
            # 3. Analizamos con la estrategia
            resultado = analizar_señal(df)
            
            print(f"Activo: {activo} | Estado: {resultado}")
        else:
            # Por ahora imprimimos esto mientras terminamos de conectar Olymp
            print(f"Activo: {activo} | Esperando datos reales de la plataforma...")

if __name__ == "__main__":
    # El bot correrá este ciclo
    while True:
        ejecutar_bot()
        # Esperamos 15 minutos para la siguiente vela (900 segundos)
        print("Dormido hasta la próxima vela de 15 min...")
        time.sleep(900)
