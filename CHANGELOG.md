# Historial de cambios

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
