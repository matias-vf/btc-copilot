# Fuentes de datos

Descarga: 2026-11-21 con `python -m copilot descargar`. APIs públicas de solo datos de mercado, sin claves ni cuentas.
El detalle por fichero (fechas, conteos, listas de días afectados y SHA-256) está en `calidad.json`.

Formato de los CSV: `fecha_utc, open, high, low, close, volumen_btc`. Una vela por día UTC (00:00 a 23:59:59).

## Temporalidad
Todas las estrategias registradas (T1, T2, B1, M1, P1) usan velas diarias. El reequilibrio semanal de P1 se calcula
a partir de las diarias. Por eso solo se descarga la temporalidad 1d. Si una estrategia futura necesita otra, se añadirá aquí.

## 1. `btcusdt_binance_1d_train.csv` (TRAIN)
- Fuente: Binance spot, par BTCUSDT, `GET https://data-api.binance.vision/api/v3/klines?interval=1d`.
- Rango: 2017-08-17 a 2022-12-31. 1963 velas = 1963 días. Sin huecos, sin duplicados, OHLC coherente, ningún día con volumen 0.
- La apertura de cada día coincide con el cierre del anterior (diferencia < 1 % en todos los días).
- Comprobación cruzada: idéntico (fecha y OHLCV) al CSV que ya tenías en `Descargas\BTCUSDT_binance_1d_TRAIN_2017-2022.csv`.
- SHA-256: `b207c011db78dc6dbc9cd8386ff44070762f84ac7d82a983af0c5e884be4c617`

**Ajuste de fechas:** el maestro pide TRAIN desde 2017. El histórico de BTCUSDT en Binance empieza el 2017-08-17, así que
TRAIN empieza ese día. Las medias largas (SMA 200, L = 365) necesitan velas previas: sus primeras señales válidas llegan
200 o 365 días después. No se rellenan con otra fuente.

**Limitaciones:**
- USDT no es exactamente USD: hay pequeñas desviaciones del dólar (por ejemplo, en mayo de 2022).
- En 2017-2018 Binance tenía menos liquidez que hoy: el slippage real pudo ser mayor que el estimado.
- El volumen es el de Binance, no el del mercado total.

**TEST bloqueado:** el código se niega a pedir, guardar o leer cualquier vela desde el 2023-01-01
(`copilot/datos.py`, `TEST_DESBLOQUEADO = False`) hasta que escribas «UNLOCK». Hay pruebas automáticas que lo comprueban.

## 2. `btcusd_bitstamp_1d_2011_2016.csv` (otra época, para el Prompt 5)
- Fuente: Bitstamp, par BTC/USD, `GET https://www.bitstamp.net/api/v2/ohlc/btcusd/?step=86400`.
- Rango: 2011-08-18 (primera vela que da la API) a 2016-12-31. 1963 velas = 1963 días. Sin huecos, sin duplicados, OHLC coherente.
- SHA-256: `b875c516c32fe719719ab7c89f1a14cf07d2a7a90c1f9866e0c676430a7de90b`

**Limitaciones (importantes):**
- Faltan 2011-01-01 a 2011-08-17: Bitstamp aún no tenía datos.
- Velas "planas" (apertura = máximo = mínimo = cierre): 56 en 2011, 4 en 2012, 3 en 2015. Son días sin operaciones
  rellenados por la API con el último precio. 33 de ellas tienen volumen 0 (30 en 2011, 3 en 2015).
- 2015-01-06 a 2015-01-08: Bitstamp suspendió la operativa tras el robo de enero de 2015.
- La apertura de un día difiere más de un 1 % del cierre anterior en 180 días (64 en 2011, 100 en 2012, 15 en 2013, 1 en 2015):
  mercado muy poco líquido. Ejecutar "en la apertura" en esos años es poco fiable; el slippage real era mucho mayor.
- Conclusión: 2011-2012 sirve para ver el comportamiento de las reglas, no para estimar con precisión una rentabilidad.

## Datos de pago
No hay. Si más adelante me dices que tienes ficheros de pago, se añadirán como fuente nueva aquí, sin reemplazar estos.
