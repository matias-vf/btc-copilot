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

**TEST (antes bloqueado, abierto el 2026-11-21 con «UNLOCK»):** el código se negaba a pedir, guardar o leer cualquier vela desde el 2023-01-01
(`copilot/datos.py`, `TEST_DESBLOQUEADO = False`) hasta que escribas «UNLOCK». Hay pruebas automáticas que lo comprueban.

## 1b. `btcusdt_binance_1d_test.csv` (TEST, descargado tras «UNLOCK», D20)
- Fuente: la misma que TRAIN. Descargado el 2026-11-21.
- Rango: 2023-01-01 a 2026-11-20 (última vela cerrada). 1420 velas = 1420 días. Sin huecos, sin duplicados, OHLC
  coherente, ningún día con volumen 0. Ninguna apertura se separa más de un 1 % del cierre anterior.
- Continuidad con TRAIN: último cierre de TRAIN 16 542,40; primera apertura de TEST 16 541,77.
- SHA-256: `6530a851b2b8576e77bf16fe6fd84479da6976dccd9388f7f9637c9a8afa5bcb`

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

## 3. Oro: GLD (SPDR Gold Shares), segundo mercado (D42)
- Fuente: Yahoo Finance, gráfico diario público (`query1.finance.yahoo.com/v8/finance/chart/GLD`, interval=1d), sin claves.
  Precios sin ajustar (GLD no reparte dividendos). Fecha = día de mercado en Nueva York. Descargado el 2026-11-21.
- `gld_yahoo_1d_otra_epoca_2004_2010.csv`: 2004-11-18 (primer día de cotización de GLD) a 2010-12-31, 1541 velas.
  SHA-256 `1c571e1486020a1e09f4c3127df28481bbba0a70be199c80848367bddcfc653a`
- `gld_yahoo_1d_train_2011_2018.csv`: 2011-01-03 a 2018-12-31, 2012 velas. SHA-256 `c8cd5f4809e97d620cf213177f49d8c96a38c876edf4f033be706548b8340ac7`
- Calidad: sin duplicados, OHLC coherente, ningún día con volumen 0, ninguna vela en fin de semana. Solo hay velas los
  días de mercado (por eso "faltan" fines de semana y festivos). Huecos de más de 4 días: 2006-12-29 a 2007-01-03
  (bolsa cerrada el 2 de enero de 2007 por el funeral del presidente Ford) y 2012-10-26 a 2012-10-31 (huracán Sandy).
  Son cierres reales del mercado, no datos perdidos.
- **TEST del oro (desde 2019-01-01): NO descargado.** El código se niega a pedirlo, guardarlo o leerlo
  (`TEST_ORO_DESBLOQUEADO = False`) hasta que el usuario escriba «UNLOCK».
- Limitaciones: Yahoo es una fuente gratuita y no oficial; sus datos pueden tener errores puntuales. GLD cotiza solo en
  horario de bolsa de EE. UU.; entre el cierre y la apertura puede haber saltos de precio.

## 4. QQQ y SPY, velas de 1 hora (day trading, D55)
- Fuente: Yahoo Finance, gráfico público (`query1.finance.yahoo.com/v8/finance/chart/{QQQ,SPY}`, interval=1h,
  range=730d, includePrePost=false), sin claves. Descargado el 2026-11-22. Hora convertida a Nueva York.
- `qqq_yahoo_1h_730d.csv.gz`: 5092 velas, 2023-12-26 a 2026-11-20, 730 sesiones. SHA-256
  `be1eb91485d8635c253681643b0d6a689bec048e2dc5cfb3a62eb481fe1a93e1`
- `spy_yahoo_1h_730d.csv.gz`: misma estructura. SHA-256 `4ad0b899d8fd46b55b9cd5cfe2893063b051bf6753594d6a615925cdb917fd1e`
- Las velas empiezan a las :30; la de las 15:30 dura media hora. Los días de cierre anticipado tienen 4 velas. Se
  descarta la vela suelta de las 16:00 (subasta de cierre) si aparece.

## 5. 234 acciones + SPY, velas de 1 hora (búsqueda de 100.000 reglas, D65)
- Fuente: Yahoo Finance, gráfico público (`query1.finance.yahoo.com/v8/finance/chart/{símbolo}`, interval=1h,
  range=730d, includePrePost=false), sin claves. Descargado el 2026-11-25 con `tools/descargar_acciones_1h.py`.
- `acciones_1h_730d.json.gz` (no se sube a git por tamaño): 2023-12-29 a 2026-11-25, 723 sesiones completas de SPY.
  SHA-256 `ab5b96f4d697b36d5a7945b10cb6fe229ff32dc10f25b285c1fdcbcfc90aaca4`. Sin datos: RDDT (error 422 de Yahoo) y SQ (ya no cotiza con ese símbolo).
  Quedan 230 acciones con más de 300 sesiones. Faltan el 0,04 % de las velas.

## 6. 234 acciones + SPY, velas diarias desde 2000 (day trading de apertura a cierre, D67)
- Fuente: Yahoo Finance, gráfico público, interval=1d, period1=2000-01-01 hasta hoy (con range=max Yahoo da velas
  mensuales). Descargado el 2026-11-25 con `tools/descargar_acciones_1h.py 1d max`.
- `acciones_1d_max.json.gz` (no se sube a git): 6.766 sesiones de SPY, 2000-01-03 a 2026-11-25. SHA-256 `b35818f63d23fda9063bf8bb87e2ef761960af3699cdb8a93e7797b5473b9170`.
  Sin datos: SQ. Las empresas que salieron a bolsa después de 2000 solo tienen datos desde entonces.
