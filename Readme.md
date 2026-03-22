# Bot de Trading — Deriv V25/V50
## Estrategia: EMA 9 + EMA 21 | Fixed Time 15 minutos

---

## ¿Qué hace el bot?
- Monitorea **Volatility 25 (V25)** y **Volatility 50 (V50)** simultáneamente
- Calcula EMA 9 y EMA 21 en tiempo real sobre velas de 15 minutos
- Detecta retrocesos que no rompen las EMAs + vela de continuación
- Opera automáticamente $100 USD por señal
- Registra cada operación con motivo de entrada y resultado

---

## Configuración inicial

### 1. Insertar tu API Token
Abrí `bot.py` y en la línea 8 reemplazá:
```
API_TOKEN = "TU_TOKEN_AQUI"
```
por tu token real de Deriv.

### 2. Correr localmente (opcional, para probar)
```bash
pip install -r requirements.txt
python bot.py
```

---

## Deploy en Railway (corre 24/7 en la nube)

### Paso 1 — Subir a GitHub
1. Creá un repositorio **privado** en github.com
2. Subí los 3 archivos: `bot.py`, `requirements.txt`, `railway.toml`

### Paso 2 — Crear proyecto en Railway
1. Entrá a [railway.app](https://railway.app)
2. Iniciá sesión con tu cuenta de GitHub
3. Clic en **"New Project"**
4. Elegí **"Deploy from GitHub repo"**
5. Seleccioná el repositorio del bot

### Paso 3 — Agregar el token como variable de entorno
En Railway, en tu proyecto:
1. Clic en **"Variables"**
2. Agregá: `API_TOKEN` = tu token de Deriv

Luego en `bot.py` cambiá la línea 8 a:
```python
import os
API_TOKEN = os.environ.get("API_TOKEN")
```

### Paso 4 — Deploy
Railway despliega automáticamente. En la pestaña **"Logs"** vas a ver el bot corriendo en tiempo real.

---

## Leer los logs

Cada entrada se ve así:
```
2026-03-22 14:30:00 | INFO | 🎯 SEÑAL en 1HZ25V
2026-03-22 14:30:00 | INFO |    Dirección : CALL (ALCISTA)
2026-03-22 14:30:00 | INFO |    EMA9      : 1234.56789
2026-03-22 14:30:00 | INFO |    EMA21     : 1230.12345
2026-03-22 14:30:00 | INFO |    Precio    : 1235.00000
2026-03-22 14:45:00 | INFO | =============================================
2026-03-22 14:45:00 | INFO |   RESULTADO: ✅ GANADA
2026-03-22 14:45:00 | INFO |   Activo   : 1HZ25V
2026-03-22 14:45:00 | INFO |   P&L      : +87.50 USD
2026-03-22 14:45:00 | INFO |   Stats    : 3W / 1L | Winrate: 75.0%
```

---

## Ajustes rápidos en bot.py

| Variable | Línea | Descripción |
|---|---|---|
| `TRADE_AMOUNT` | 10 | Monto por operación (default: $100) |
| `CONTRACT_DURATION` | 11 | Duración en minutos (default: 15) |
| `EMA_SHORT` | 12 | EMA rápida (default: 9) |
| `EMA_LONG` | 13 | EMA lenta (default: 21) |
