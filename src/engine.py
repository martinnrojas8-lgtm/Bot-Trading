import pandas as pd
import pandas_ta as ta

def analizar_señal(datos_velas):
    # Convertimos los datos a un formato que el bot entienda
    df = pd.DataFrame(datos_velas)
    
    # Calculamos las EMAs de 9 y 21
    df['ema9'] = ta.ema(df['close'], length=9)
    df['ema21'] = ta.ema(df['close'], length=21)
    
    # Obtenemos la última vela cerrada y la actual
    ultima = df.iloc[-1]
    
    # DETERMINACIÓN DE TENDENCIA
    tendencia_alcista = ultima['ema9'] > ultima['ema21']
    tendencia_bajista = ultima['ema9'] < ultima['ema21']
    
    # LÓGICA DE RETROCESO Y CONFIRMACIÓN
    # En tendencia alcista: el precio baja a tocar la EMA21 y cierra arriba
    if tendencia_alcista and (ultima['low'] <= ultima['ema21'] < ultima['close']):
        return "COMPRA"
    
    # En tendencia bajista: el precio sube a tocar la EMA21 y cierra abajo
    if tendencia_bajista and (ultima['high'] >= ultima['ema21'] > ultima['close']):
        return "VENTA"
        
    return "ESPERAR"
