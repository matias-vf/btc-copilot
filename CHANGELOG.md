# Historial de cambios

## 2026-11-21. Referencia: paquete Day Trader skill
- Revisado como referencia (decisión D6). No se ejecuta ni se copia código; ninguna regla registrada cambia.

## 2026-11-21. Prompt 2: registros y datos
- Registros de solo-añadir encadenados con SHA-256: ideas, experimentos (contador acumulado) y señales.
- Registradas 5 estrategias (T1, T2, B1, P1; M1 experimental) con 31 variantes y 5 descartadas (B2, M2, M3, S1, S2).
- Criterios de aceptación v1: superar a Buy & Hold en rentabilidad, drawdown máximo y Sharpe, en TRAIN.
- Descargadas velas diarias: Binance BTCUSDT 2017-08-17 a 2022-12-31 y Bitstamp BTC/USD 2011-08-18 a 2016-12-31.
  Validadas: sin huecos ni duplicados. Limitaciones en `data/FUENTES.md`.
- Bloqueo de datos TEST (>= 2023-01-01) en código, con pruebas.
