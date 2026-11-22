# Historial de cambios

## 2026-11-22. Day trading de QQQ con compras y cortos (IBKR)
- Velas de 1 hora de QQQ y SPY (Yahoo, 730 días). Motor horario con cortos, stops, objetivos, cierre al final de la
  sesión y costes de IBKR Pro escalonado (D55). Comando `python -m copilot qqq-daytrading`.
- 40 variantes (Q1-Q6): ninguna aprueba TRAIN; no se añade cuenta de paper (D56). Informe en `docs/qqq_intradia.md`.

## 2026-11-21. Nasdaq (QQQ): diario e intradía
- Datos diarios de QQQ 1999-2026 (Yahoo) y 60 días de velas de 5 minutos.
- Intradía: ruptura del rango de apertura de 5 minutos (Zarattini y Aziz 2023), solo compra, en paper cada 5 minutos (D48, D49).
- Diario: ninguna regla de los otros copilotos funciona en QQQ; búsqueda propia con 2 reglas sin significación (D50).
- Copilotos y cuentas de paper: BTC, oro, Nasdaq diario y Nasdaq intradía. Las tareas pueden despertar el ordenador.

## 2026-11-21. Copiloto del oro en marcha
- Búsqueda propia en el oro con el universo de 1000: 4 reglas sin significación estadística (D45, D46).
- El copiloto admite un segundo mercado (`python -m copilot hoy oro`): cuenta de paper propia, datos de Yahoo,
  calendario de bolsa en la vigilancia, costes del oro. Primer ciclo en vivo el 2026-11-21.
- La tarea diaria y el resumen de las 20:00 incluyen el oro.

## 2026-11-21. Tercera búsqueda (1000 estrategias) y oro
- 1000 variantes en 31 familias: ninguna supera el Sharpe deflactado (D39); se añaden 5 marcadas sin significación (D40, D41).
- Copiloto de BTC con 7 estrategias EXPERIMENTALES (N1, N1D y 5 del universo).
- Segundo mercado oro (GLD): datos de Yahoo, TEST desbloqueado por el usuario (D43). Las reglas del copiloto no funcionan
  en el oro (D44): el oro queda sin copiloto.

## 2026-11-21. Vigía horario y resumen diario
- Vigía cada hora (D33): observa el precio y anota qué haría N1 el domingo; no genera señales ni órdenes.
- Orden `resumen` (solo lectura) y resumen diario a las 20:00 en la app de Claude.
- `verificar` comprueba también los registros del paper trading, la vigilancia y el vigía.

## 2026-11-21. Segunda búsqueda completa y paper trading en vivo
- Revisión de código: N1 por fecha, ventana alineada con Buy & Hold, ejecución de lotes y formato unificados (D27).
- TRAIN alineado: 10 de 11 aprueban; Prompt 5: solo N1 L=4 sobrevive (D28, D29); exposición 25 % (D30, D31).
- Copiloto con N1 L=4 como EXPERIMENTAL; recupera días perdidos y valida la historia descargada.
- Repetición 2023-2026: paper reproduce el backtest (D32). Paper trading en vivo desde el 2026-11-21, tarea diaria.

## 2026-11-21. Segunda búsqueda, Prompt 4: N1-N4 en TRAIN
- Orden `python -m copilot train2`: 11 variantes ejecutadas y registradas con el criterio v2.
- Aprueban 9 de 11 en TRAIN; N2 n=5 y n=10 son frágiles a los costes (D26, `docs/resultados_train_v2.md`).

## 2026-11-21. Segunda búsqueda, Prompt 3: reglas de N1-N4
- Reglas exactas de N1-N4 en `copilot/estrategias.py`, con pruebas propias. Motor y costes sin cambios.
- Comprobación de anticipación: 43 de 43 variantes registradas sin anticipación en TRAIN (D25).

## 2026-11-21. Segunda búsqueda, Prompt 2: registro de N1-N4
- N1 momentum semanal, N2 media móvil corta, N3 ruptura del rango y N4 cerca del máximo de 52 semanas (experimental),
  11 variantes, registradas con el criterio versión 2 antes de probarlas (D24).

## 2026-11-21. Segunda búsqueda de estrategias: Prompt 1 v2
- Búsqueda en la literatura con referencias verificadas; 4 candidatas (11 variantes) y 8 ideas descartadas.
- Decisiones del usuario (D23): N1-N4, TEST como segunda validación + paper trading, criterio v2 (drawdown + Sharpe).

## 2026-11-21. TEST desbloqueado y evaluado
- «UNLOCK» del usuario (D20). Datos de TEST 2023-01-01 a 2026-11-20 descargados y validados.
- Regla de TEST elegida por el usuario antes de ver resultados (D21). Orden `python -m copilot test`.
- Ninguna estrategia del copiloto supera a Buy & Hold en rentabilidad en TEST (D22): el copiloto queda en NO OPERAR.

## 2026-11-21. Prompt 9: copiloto y paper trading
- Ciclo diario: datos, orden pendiente en la apertura, valoración, límite de pérdidas, vigilancia v2, señal y seguimiento.
- Ficha de señal COMPRA/VENTA/MANTENER/NO OPERAR con precio, estrategias, justificación, riesgo, invalidación,
  histórico, estado de validación, sesión de Nueva York y contexto de mercado.
- Paper trading con 100 USD ficticios, costes, límite del 25 %, 3 posiciones, pérdida máxima del 35 %, kill switch.
- Órdenes nuevas: `senal`, `hoy`, `en-marcha`, `repeticion`, `parar`, `reanudar`. Panel HTML local.
- Lectura visual de capturas (pantalla compartida) que nunca cambia la decisión.
- Repetición técnica 2021-2022 (`docs/paper_repeticion.md`). Modo en vivo bloqueado hasta decidir sobre TEST (D19).

## 2026-11-21. Vigilancia v2 (aprobada por el usuario)
- Reglas v2 (D17): azar por debajo del percentil 25 durante 30 días; reactivación automática solo de esas suspensiones;
  alertas de volatilidad solo al entrar o salir de la banda; sin señales con velas de volumen 0.
- La v1 sigue disponible y reproducible. Simulación v2 en `docs/vigilancia_v2.md` (D18).

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
