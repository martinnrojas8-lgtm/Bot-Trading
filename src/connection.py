import pandas as pd

class BrokerConnection:
    def __init__(self, activo):
        self.activo = activo

    def obtener_velas(self, temporalidad="15m", cantidad=100):
        """
        Esta función pedirá los datos al broker.
        Por ahora, prepararemos el terreno para recibir 
        los datos de Olymp Trade.
        """
        # Aquí es donde el bot se conectará a la plataforma
        # Para el test, este espacio devolverá datos vacíos o simulados
        print(f"Conectando con Olymp Trade para obtener {self.activo}...")
        
        # En el futuro, aquí usaremos un 'scrapper' o una API
        return None 

def formatear_datos(raw_data):
    """
    Toma los datos crudos del broker y los pone en el 
    formato que el 'engine' necesita (Open, High, Low, Close).
    """
    df = pd.DataFrame(raw_data)
    # Aseguramos que los precios sean números decimales
    df['close'] = pd.to_numeric(df['close'])
    return df
