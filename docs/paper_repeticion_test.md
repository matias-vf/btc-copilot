# Paper trading: repetición 2023-2026 con N1 L=4 (segunda búsqueda)

Generado con `python -m copilot repeticion 2023-01-01 2026-11-20`. Registros propios y panel en
`repeticion/2023-01-01_2026-11-20/`. Es una prueba técnica: el copiloto funciona día a día como en vivo (datos solo
hasta ese día, orden en la apertura siguiente, costes, vigilancia v2, límite del 25 %), sobre el periodo TEST, que ya
está visto. No sustituye al mes de paper trading en vivo.

| | Paper | Backtest (N1 L=4 al 25 %) |
|---|---|---|
| Rentabilidad | +51,7 % | +48,5 % |
| CAGR | 11,3 % | 10,7 % |
| Sharpe | 1,16 | 1,24 |
| Drawdown máximo | -9,6 % | -8,8 % |
| Órdenes | 50 | – |
| Operaciones cerradas | 25 (11 positivas) | – |
| Costes pagados | 2,90 USD sobre 100 | incluidos |
| Precio simulado frente a teórico (media) | 0,060 % | – |
| Precio de la señal frente a la apertura de ejecución | 0,0001 % | – |

Decisiones en 1 420 días: 25 COMPRA, 25 VENTA, 787 MANTENER y 583 NO OPERAR. Ninguna suspensión ni parada de emergencia.

**Por qué no coinciden del todo:** el paper empieza en liquidez y espera al primer domingo para decidir; no ejecuta
cambios de exposición menores de 1 punto; y su valor real cambia un poco por el redondeo de las órdenes. Las
diferencias son pequeñas (Sharpe 1,16 frente a 1,24): el motor de paper reproduce el backtest.
