# Decisiones

Solo se añaden decisiones nuevas al final; las anteriores no se editan.

## D1. 2026-11-21. Mercado y ejecución
BTC/USDT spot de Binance, solo comprado o liquidez. Señal con el cierre de la vela diaria (00:00 UTC), ejecución en la
apertura de la vela siguiente. Los cortos con perpetuos quedan para una variante posterior registrada.

## D2. 2026-11-21. Ventanas de datos
- TRAIN: 2017-08-17 a 2022-12-31. El maestro dice "desde 2017"; Binance empieza el 2017-08-17.
- TEST: desde 2023-01-01. Bloqueado en código hasta «UNLOCK».
- Otra época (Prompt 5): Bitstamp BTC/USD 2011-08-18 a 2016-12-31 (la API no tiene datos antes de 2011-08-18).
- Pendiente para el Prompt 3: la señal del 2022-12-31 se ejecutaría en la apertura del 2023-01-01, que es TEST. El motor
  deberá cerrar o valorar las posiciones con el último cierre de TRAIN, sin leer la vela del 2023-01-01.

## D3. 2026-11-21. Criterios de aceptación (versión 1), fijados antes de ver resultados
En TRAIN, neto de costes, la estrategia debe cumplir las tres:
1. Rentabilidad total > Buy & Hold de BTC.
2. |Drawdown máximo| < |drawdown máximo de Buy & Hold|.
3. Sharpe >= Sharpe de Buy & Hold (rentabilidades diarias, 365 días al año, tipo libre de riesgo 0). Criterio
   secundario elegido por el usuario.
Si opera más de una vez por semana se muestran también resultados con costes x2 y x3.

## D4. 2026-11-21. Registros de solo-añadir
JSON Lines con cadena de hashes SHA-256 (`copilot/registro.py`). Ancla externa: Git. `registrar_experimento` rechaza
estrategias no registradas o descartadas, y variantes que no estén en `configuraciones_permitidas`.

## D5. 2026-11-21. Recuento de variantes registradas
T1: 4 · T2: 3 · B1: 2 · M1: 2 (experimental) · P1: 20 (5 bases x 2 sigma objetivo x 2 ventanas). Total: 31.
Cuantas más variantes se prueban, más probable es que alguna "gane" por azar; el contador lo deja a la vista.

## D6. 2026-11-21. Paquete «Day Trader skill» como referencia
El usuario pidió usarlo. Está hecho para acciones de EE. UU. en intradía (horario NYSE, velas de 1 y 5 minutos de Yahoo),
así que no se ejecuta sobre BTC: solo se toman ideas, adaptadas a BTC diario. No cambia D1 a D5.

| Herramienta | Idea que se toma | Dónde entra |
|---|---|---|
| trader-risk | Una puerta PASS/BLOCK con el motivo, antes de cada operación simulada. Salir nunca se bloquea. | Prompt 8 (paper trading): bloquear si la estrategia no está validada, la señal ha caducado, los datos están desfasados o la exposición supera 1. |
| trader-exit | Escribir las condiciones de invalidación ANTES de la entrada. | Prompt 7.3: cada señal guarda su invalidación (la regla de salida registrada) y su riesgo estimado. |
| trader-timemachine | Simular muchos caminos con los propios datos y contar cada vez que la regla se activó en el pasado. | Prompt 5 y 7.4: resultado histórico por señal. Una simulación nueva es un experimento: se registra antes. |
| trader-budget | Tamaño de posición según la pérdida máxima por operación. | No se adopta: cambiaría las reglas registradas. Solo podría entrar como variante nueva registrada. |
| trader-broker | Envío de órdenes a un broker. | **No se adopta. Nunca.** El copiloto no envía órdenes reales. |
| trader-scanner, trader-news, trader-entry, trader-alerts, trader-analyst, trader-pelosi | Acciones de EE. UU. | No aplican a BTC. |

## D7. 2026-11-21. Motor de backtesting (Prompt 3)
- **Causalidad impuesta por el motor:** la estrategia solo recibe una copia de las velas hasta t. La decisión del cierre
  de t se ejecuta en la apertura de t+1. La última vela de TRAIN (2022-12-31) no genera ninguna orden, así que nunca se
  necesita la vela del 2023-01-01 (resuelve lo pendiente de D2).
- **Final del periodo:** la posición abierta se valora como si se vendiera al último cierre, restando el coste de salida.
  Igual para Buy & Hold y para todas las estrategias.
- **Compras:** el coste sale del efectivo; nunca hay efectivo negativo (sin apalancamiento oculto).
- **Solo se opera cuando cambia la decisión.** Si la exposición se desvía por el movimiento del precio, no se reajusta
  cada día (P1 reajusta solo los lunes, como está registrado).
- **Métricas:** rentabilidad total, CAGR (365 días), Sharpe con rentabilidades diarias del capital (365, tipo libre de
  riesgo 0, incluye los días en liquidez), drawdown máximo, operaciones (entradas desde liquidez) y ejecuciones (todas
  las órdenes, incluidos los reajustes de P1).
- **Datos insuficientes:** si un indicador no se puede calcular todavía (por ejemplo, SMA 200 en los primeros 199 días),
  la regla devuelve "no operar". Esos días cuentan en el periodo.
- **Comprobación de anticipación:** `copilot/anticipacion.py`. En cuatro cortes se alteran al azar todas las velas
  posteriores y se reconstruye la estrategia con esos datos alterados; las señales y el capital hasta el corte deben
  ser idénticos. Una estrategia tramposa de prueba es detectada. Ejecutada en TRAIN: 32 de 32 variantes sin anticipación.
- **Regla permanente de resultados extraordinarios:** `motor.alertas()` marca Sharpe > 2, CAGR más de 50 puntos por
  encima de Buy & Hold, o drawdown menor del 15 % con operaciones. Un resultado marcado se trata primero como posible
  error: se repite la comprobación de anticipación y se revisa el código antes de enseñarlo, y se muestra con el aviso.

## D8. 2026-11-21. Ejecución en TRAIN (Prompt 4)
Lote `prompt4-train-v1`: 31 variantes ejecutadas una sola vez y anotadas en `registros/experimentos.jsonl` (contador 1 a 31),
con el SHA-256 de los datos y el commit del código. La orden `train` se niega a repetir el mismo lote: repetirlo sería un
experimento nuevo con otro nombre. Aprueban los tres criterios en TRAIN 10 variantes: T1 SMA 100, T2 L=365, B1 20/10,
B1 55/20 y 6 de P1 (todas sobre T1 SMA 100 o SMA 150). Los criterios se evalúan con costes x1, como se fijó en D3.
Tabla y comprobaciones en `docs/resultados_train.md`.
