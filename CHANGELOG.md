# Historial de cambios

## 2026-11-21. Prompt 8: deterioro de estrategias y reglas de parada (v1)
- Reglas fijadas antes de ejecutar (D15). Módulo `copilot/vigilancia.py` y orden `python -m copilot vigilancia`.
- Controles diarios: datos, drawdown frente al backtest, referencia de entradas aleatorias, rentabilidad móvil, volatilidad y SMA 200.
- Registro de solo añadir `registros/vigilancia.jsonl` para el modo en vivo; estrategias suspendidas seguidas "en la sombra".
- Simulación en Bitstamp 2013-2016: reglas v1 demasiado duras (D16). Pendiente decidir la versión 2.

## 2026-11-21. Prompt 7: gestión del riesgo y tamaño de posición
- Nuevos Prompts 7, 8 y 9 del usuario sustituyen a las Partes 7-9 del maestro (D13).
- Reglas fijadas antes de ejecutar (D13); idea R1 registrada; orden `python -m copilot riesgo`.
- 11 configuraciones (exposición 25-200 %, riesgo por operación 1/2/5 %, volatilidad objetivo 30/45 %) en dos épocas.
- Elegida: exposición del 25 % (drawdown -17 % en TRAIN, -21 % en la otra época). El apalancamiento se arruina en 2013.
- Corregida la división por cero de las métricas con capital 0.

## 2026-11-21. Prompt 6: cartera combinada (provisional)
- Reglas fijadas antes de ejecutar (D11) y cartera registrada como idea C1.
- Orden `python -m copilot cartera`: correlaciones, pesos inversos a la volatilidad (90 días), reequilibrio mensual.
- TRAIN: CAGR 54,9 %, Sharpe 1,16, drawdown -56,5 % frente a 28,5 %, 0,72 y -83,2 % de Buy & Hold (`docs/cartera.md`).
- Las estrategias de cada ejecución ya no recorren las ideas de la familia "Cartera".

## 2026-11-21. Prompt 5: robustez y filtrado (parcial)
- Reglas de robustez fijadas antes de ejecutar (D9). Orden `python -m copilot robustez`.
- 29 variantes probadas en Bitstamp 2011-2016 (x1 y x3), regímenes de mercado y sensibilidad completa (`docs/robustez.md`).
- Veredicto provisional: conservar B1 y T1; descartar P1, T2 y M1. TRAIN frente a TEST pendiente de «UNLOCK».

## 2026-11-21. Prompt 4: ejecución en TRAIN
- Orden `python -m copilot train`: ejecuta las 31 variantes registradas y anota cada una en el registro de experimentos.
- 10 variantes superan a Buy & Hold en rentabilidad, drawdown y Sharpe en TRAIN. Ninguna dispara las alertas de "demasiado bueno".
- Tabla y diagnósticos de filtración en `docs/resultados_train.md`.

## 2026-11-21. Prompt 3: motor de backtesting
- Modelo de costes Binance spot: 0,10 % comisión + 0,01 % medio spread + 0,05 % slippage por lado; multiplicador x2/x3 (`docs/costes.md`).
- Motor causal: decisión al cierre de t, ejecución en la apertura de t+1; sin órdenes en la última vela; valoración final de liquidación.
- Reglas exactas de T1, T2, B1, M1 y P1 (31 variantes) y Buy & Hold.
- Comprobación automática de anticipación; pasada en TRAIN por las 32 variantes. Alertas de resultados demasiado buenos.

## 2026-11-21. Referencia: paquete Day Trader skill
- Revisado como referencia (decisión D6). No se ejecuta ni se copia código; ninguna regla registrada cambia.

## 2026-11-21. Prompt 2: registros y datos
- Registros de solo-añadir encadenados con SHA-256: ideas, experimentos (contador acumulado) y señales.
- Registradas 5 estrategias (T1, T2, B1, P1; M1 experimental) con 31 variantes y 5 descartadas (B2, M2, M3, S1, S2).
- Criterios de aceptación v1: superar a Buy & Hold en rentabilidad, drawdown máximo y Sharpe, en TRAIN.
- Descargadas velas diarias: Binance BTCUSDT 2017-08-17 a 2022-12-31 y Bitstamp BTC/USD 2011-08-18 a 2016-12-31.
  Validadas: sin huecos ni duplicados. Limitaciones en `data/FUENTES.md`.
- Bloqueo de datos TEST (>= 2023-01-01) en código, con pruebas.
