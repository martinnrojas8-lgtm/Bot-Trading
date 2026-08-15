import asyncio
import websockets
import json
import logging
from datetime import datetime
from collections import deque
import os

# ============================================================
#  CONFIGURACIÓN - ¡CAMBIÁ ESTO!
# ============================================================
API_TOKEN = os.environ.get("API_TOKEN", "TU_TOKEN_AQUI")  # ← PON TU TOKEN
SYMBOLS = ["R_100", "R_75"]  # Índices sintéticos de Deriv
TRADE_AMOUNT = 10  # USD por operación (empezá con poco)
CONTRACT_DURATION = 1  # 1 minuto
EMA_SHORT = 9
EMA_MEDIUM = 20
EMA_LONG = 50
MIN_VELAS_SEPARADAS = 15  # minutos sin cruces
DERIV_WS = "wss://ws.binaryws.com/websockets/v3?app_id=1089"

# ============================================================
#  LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot_log.txt", encoding="utf-8")
    ]
)
log = logging.getLogger(__name__)

# ============================================================
#  CÁLCULO DE EMA
# ============================================================
def calcular_ema(precios: list, periodo: int) -> list:
    """Calcula EMA de forma eficiente"""
    if len(precios) < periodo:
        return []
    k = 2 / (periodo + 1)
    ema = [sum(precios[:periodo]) / periodo]
    for precio in precios[periodo:]:
        ema.append(precio * k + ema[-1] * (1 - k))
    return ema

# ============================================================
#  DETECCIÓN DE SEÑAL - ESTRATEGIA DEFINITIVA
# ============================================================
def detectar_senal(velas: list) -> str | None:
    """
    Estrategia de retroceso con EMAs:
    1. EMAs ordenadas (9 > 20 > 50 o viceversa)
    2. Sin cruces en últimos 15 minutos
    3. Vela de retroceso toca EMA9 (cierre NO traspasa)
    4. Vela de confirmación en dirección de la tendencia
    """
    if len(velas) < EMA_LONG + 5:
        return None
    
    # Obtener precios de cierre
    cierres = [v["close"] for v in velas]
    
    # Calcular EMAs
    ema9_series = calcular_ema(cierres, EMA_SHORT)
    ema20_series = calcular_ema(cierres, EMA_MEDIUM)
    ema50_series = calcular_ema(cierres, EMA_LONG)
    
    if len(ema9_series) < MIN_VELAS_SEPARADAS + 2:
        return None
    
    # EMAs actuales y previas
    ema9 = ema9_series[-1]
    ema20 = ema20_series[-1]
    ema50 = ema50_series[-1]
    
    # 1. VERIFICAR ORDEN Y SEPARACIÓN DE EMAs
    orden_alcista = ema9 > ema20 > ema50
    orden_bajista = ema9 < ema20 < ema50
    
    if not orden_alcista and not orden_bajista:
        log.debug("❌ EMAs desordenadas o cruzadas")
        return None
    
    # 2. VERIFICAR QUE NO HAYA CRUCES EN ÚLTIMOS 15 MINUTOS
    ema9_ultimas = ema9_series[-MIN_VELAS_SEPARADAS:]
    ema20_ultimas = ema20_series[-MIN_VELAS_SEPARADAS:]
    ema50_ultimas = ema50_series[-MIN_VELAS_SEPARADAS:]
    
    if orden_alcista:
        # Verificar que ninguna EMA se cruce en el período
        for i in range(len(ema9_ultimas) - 1):
            if not (ema9_ultimas[i] > ema20_ultimas[i] > ema50_ultimas[i]):
                log.debug("❌ Cruce detectado en últimos 15 min")
                return None
    else:  # bajista
        for i in range(len(ema9_ultimas) - 1):
            if not (ema9_ultimas[i] < ema20_ultimas[i] < ema50_ultimas[i]):
                log.debug("❌ Cruce detectado en últimos 15 min")
                return None
    
    # 3. ANALIZAR RETROCESO + CONFIRMACIÓN (últimas 2 velas)
    vela_retroceso = velas[-2]
    vela_confirmacion = velas[-1]
    
    # Obtener EMA9 de la vela de retroceso
    ema9_retroceso = ema9_series[-2]
    
    if orden_alcista:
        # RETROCESO BAJISTA (vela roja) que toca EMA9
        es_retroceso = (
            vela_retroceso["close"] < vela_retroceso["open"] and  # vela bajista
            vela_retroceso["low"] <= ema9_retroceso and  # toca EMA9 (mecha)
            vela_retroceso["close"] > ema9_retroceso  # cierre NO traspasa EMA9
        )
        
        # CONFIRMACIÓN ALCISTA (vela verde) que cierra por encima del retroceso
        es_confirmacion = (
            vela_confirmacion["close"] > vela_confirmacion["open"] and  # vela alcista
            vela_confirmacion["close"] > vela_retroceso["close"]  # cierra sobre retroceso
        )
        
        if es_retroceso and es_confirmacion:
            log.info(f"🎯 SEÑAL CALL detectada!")
            log.info(f"   Retroceso: {vela_retroceso['close']:.5f} | EMA9: {ema9_retroceso:.5f}")
            log.info(f"   Confirmación: {vela_confirmacion['close']:.5f} > {vela_retroceso['close']:.5f}")
            return "CALL"
    
    else:  # orden_bajista
        # RETROCESO ALCISTA (vela verde) que toca EMA9
        es_retroceso = (
            vela_retroceso["close"] > vela_retroceso["open"] and  # vela alcista
            vela_retroceso["high"] >= ema9_retroceso and  # toca EMA9 (mecha)
            vela_retroceso["close"] < ema9_retroceso  # cierre NO traspasa EMA9
        )
        
        # CONFIRMACIÓN BAJISTA (vela roja) que cierra por debajo del retroceso
        es_confirmacion = (
            vela_confirmacion["close"] < vela_confirmacion["open"] and  # vela bajista
            vela_confirmacion["close"] < vela_retroceso["close"]  # cierra bajo retroceso
        )
        
        if es_retroceso and es_confirmacion:
            log.info(f"🎯 SEÑAL PUT detectada!")
            log.info(f"   Retroceso: {vela_retroceso['close']:.5f} | EMA9: {ema9_retroceso:.5f}")
            log.info(f"   Confirmación: {vela_confirmacion['close']:.5f} < {vela_retroceso['close']:.5f}")
            return "PUT"
    
    return None

# ============================================================
#  CLASE PRINCIPAL DEL BOT
# ============================================================
class DerivBot:
    def __init__(self):
        self.ws = None
        self.velas = {sym: deque(maxlen=200) for sym in SYMBOLS}
        self.operaciones_abiertas = set()
        self.stats = {"ganadas": 0, "perdidas": 0, "total": 0, "profit": 0}
        self.ultima_operacion = {}  # para evitar duplicados
        self.conectado = False

    async def conectar(self):
        """Conexión principal con reconexión automática"""
        log.info("=" * 55)
        log.info("  BOT DE RETROCESO CON EMAS")
        log.info(f"  Activos: {', '.join(SYMBOLS)}")
        log.info(f"  Monto: ${TRADE_AMOUNT} | Duración: {CONTRACT_DURATION}min")
        log.info("=" * 55)
        
        while True:
            try:
                async with websockets.connect(DERIV_WS) as ws:
                    self.ws = ws
                    self.conectado = True
                    await self.autenticar()
                    await self.suscribir_velas()
                    await self.escuchar()
            except Exception as e:
                log.error(f"❌ Conexión perdida: {e} — reconectando en 5s...")
                self.conectado = False
                await asyncio.sleep(5)

    async def enviar(self, datos: dict):
        """Envía mensaje al WebSocket"""
        await self.ws.send(json.dumps(datos))

    async def autenticar(self):
        """Autenticación con API token"""
        await self.enviar({"authorize": API_TOKEN})
        resp = json.loads(await self.ws.recv())
        
        if "error" in resp:
            log.error(f"❌ Error de autenticación: {resp['error']['message']}")
            raise Exception("Token inválido")
        
        balance = resp["authorize"]["balance"]
        currency = resp["authorize"]["currency"]
        log.info(f"✅ Autenticado | Balance: {balance} {currency}")

    async def suscribir_velas(self):
        """Suscripción a velas de 1 minuto"""
        for symbol in SYMBOLS:
            # Obtener historial
            await self.enviar({
                "ticks_history": symbol,
                "granularity": 60,  # 1 minuto
                "count": 200,
                "end": "latest",
                "style": "candles"
            })
            
            resp = json.loads(await self.ws.recv())
            if "candles" in resp:
                await self.procesar_historial(resp)
            
            # Suscribirse a actualizaciones en tiempo real
            await self.enviar({
                "subscribe": 1,
                "ticks": symbol
            })
            log.info(f"📊 Suscrito a {symbol} (1min)")

    async def escuchar(self):
        """Escucha mensajes del WebSocket"""
        async for mensaje in self.ws:
            try:
                datos = json.loads(mensaje)
                
                # Ping automático
                if datos.get("msg_type") == "ping":
                    await self.enviar({"pong": datos.get("ping")})
                    continue
                
                # Procesar según tipo
                msg_type = datos.get("msg_type")
                if msg_type == "candles":
                    await self.procesar_historial(datos)
                elif msg_type == "ohlc":
                    await self.procesar_vela_nueva(datos)
                elif msg_type == "buy":
                    self.procesar_compra(datos)
                elif msg_type == "proposal_open_contract":
                    await self.procesar_resultado(datos)
                elif "error" in datos:
                    log.error(f"API Error: {datos['error'].get('message', 'Desconocido')}")
            except json.JSONDecodeError:
                log.error(f"JSON inválido: {mensaje[:100]}")
            except Exception as e:
                log.error(f"Error en escuchar: {e}")

    async def procesar_historial(self, datos: dict):
        """Procesa historial de velas"""
        symbol = datos["echo_req"]["ticks_history"]
        velas_raw = datos.get("candles", [])
        
        for v in velas_raw:
            self.velas[symbol].append({
                "open": float(v["open"]),
                "high": float(v["high"]),
                "low": float(v["low"]),
                "close": float(v["close"]),
                "epoch": v["epoch"]
            })
        
        log.info(f"📥 {symbol}: {len(self.velas[symbol])} velas cargadas")

    async def procesar_vela_nueva(self, datos: dict):
        """Procesa nueva vela (1 minuto)"""
        ohlc = datos.get("ohlc", {})
        symbol = ohlc.get("symbol")
        
        if not symbol or symbol not in SYMBOLS:
            return
        
        vela = {
            "open": float(ohlc["open"]),
            "high": float(ohlc["high"]),
            "low": float(ohlc["low"]),
            "close": float(ohlc["close"]),
            "epoch": ohlc["epoch"]
        }
        
        # Actualizar o agregar vela
        if self.velas[symbol] and self.velas[symbol][-1]["epoch"] == vela["epoch"]:
            self.velas[symbol][-1] = vela  # actualizar vela en curso
        else:
            self.velas[symbol].append(vela)  # nueva vela cerrada
            await self.analizar(symbol)

    async def analizar(self, symbol: str):
        """Analiza señal y ejecuta operación"""
        # Evitar operaciones duplicadas
        if symbol in self.operaciones_abiertas:
            return
        
        # Evitar operar en la misma vela de confirmación
        if symbol in self.ultima_operacion:
            tiempo_ultima = self.ultima_operacion[symbol]
            if (datetime.now() - tiempo_ultima).seconds < 30:
                return
        
        velas = list(self.velas[symbol])
        senal = detectar_senal(velas)
        
        if senal:
            log.info(f"🚀 EJECUTANDO {senal} en {symbol}")
            await self.operar(symbol, senal)
            self.ultima_operacion[symbol] = datetime.now()

    async def operar(self, symbol: str, direccion: str):
        """Ejecuta la operación en Deriv"""
        contract_type = "CALL" if direccion == "CALL" else "PUT"
        self.operaciones_abiertas.add(symbol)
        
        await self.enviar({
            "buy": 1,
            "price": TRADE_AMOUNT,
            "parameters": {
                "contract_type": contract_type,
                "symbol": symbol,
                "duration": CONTRACT_DURATION,
                "duration_unit": "m",
                "basis": "stake",
                "currency": "USD",
            },
            "subscribe": 1
        })
        
        log.info(f"📤 Orden enviada: {symbol} | {contract_type} | ${TRADE_AMOUNT}")

    def procesar_compra(self, datos: dict):
        """Procesa confirmación de compra"""
        if "error" in datos:
            symbol = datos.get("echo_req", {}).get("parameters", {}).get("symbol", "?")
            log.error(f"❌ Error al comprar {symbol}: {datos['error']['message']}")
            self.operaciones_abiertas.discard(symbol)
            return
        
        compra = datos.get("buy", {})
        log.info(f"✅ Contrato abierto | ID: {compra.get('contract_id')}")

    async def procesar_resultado(self, datos: dict):
        """Procesa resultado de la operación"""
        contrato = datos.get("proposal_open_contract", {})
        if not contrato.get("is_expired") and not contrato.get("is_sold"):
            return
        
        symbol = contrato.get("underlying")
        profit = float(contrato.get("profit", 0))
        
        # Actualizar estadísticas
        self.stats["total"] += 1
        self.stats["profit"] += profit
        
        if profit > 0:
            self.stats["ganadas"] += 1
            resultado = "✅ GANADA"
        else:
            self.stats["perdidas"] += 1
            resultado = "❌ PERDIDA"
        
        winrate = (self.stats["ganadas"] / self.stats["total"] * 100) if self.stats["total"] > 0 else 0
        
        log.info(f"{'='*50}")
        log.info(f"  {resultado}")
        log.info(f"  Activo: {symbol}")
        log.info(f"  P&L: {'+' if profit > 0 else ''}{profit:.2f} USD")
        log.info(f"  Balance: {self.stats['profit']:.2f} USD")
        log.info(f"  Stats: {self.stats['ganadas']}W / {self.stats['perdidas']}L | {winrate:.1f}%")
        log.info(f"{'='*50}")
        
        self.operaciones_abiertas.discard(symbol)

# ============================================================
#  EJECUCIÓN
# ============================================================
if __name__ == "__main__":
    bot = DerivBot()
    asyncio.run(bot.conectar())
