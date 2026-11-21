# Paper trading: repetición 2021-2022 (Prompt 9)

Generado con `python -m copilot repeticion 2021-01-01 2022-12-31`. Registros propios en
`repeticion/2021-01-01_2022-12-31/` (los registros reales siguen vacíos). Panel: `panel.html` en esa carpeta.

**Qué es y qué no es.** Es una prueba técnica: el copiloto funciona día a día como si fuera en vivo (datos hasta ese día,
orden en la apertura siguiente, costes, vigilancia, registros), pero sobre fechas de **TRAIN**, que ya se usaron para
elegir las estrategias. No dice nada nuevo sobre si las estrategias funcionan en el futuro. El mes de paper trading
real necesita precios actuales (ver la decisión pendiente en `docs/decisiones.md`, D19).

## Comparación diaria: paper frente a backtest (cartera C1 al 25 %), mismas fechas

| | Paper | Backtest |
|---|---|---|
| Rentabilidad | +11,9 % | +9,8 % |
| CAGR | 5,8 % | 4,8 % |
| Sharpe | 0,51 | 0,47 |
| Drawdown máximo | -12,0 % | -11,7 % |
| Órdenes | 43 | – |
| Operaciones cerradas | 11 (3 positivas) | – |
| Costes pagados | 0,75 USD sobre 100 | incluidos |
| Precio simulado frente a teórico (media) | 0,060 % | – |
| Precio de la señal frente a la apertura de ejecución (media) | 0,006 % | – |

Decisiones: 22 COMPRA, 21 VENTA, 355 MANTENER, 332 NO OPERAR en 730 días. Capital final: 111,86 USD.

## Por qué no coinciden exactamente
1. **Suspensiones (la causa principal).** El backtest no tiene vigilancia; el paper sí. 457 de 2 190 días-estrategia
   (21 %) estuvieron suspendidos por la regla del azar: T1 de abril a junio de 2021 y desde noviembre de 2022; B1 55/20 de
   mayo a septiembre de 2021 y desde mayo de 2022. Las dos reactivaciones automáticas funcionaron. Aquí las
   suspensiones ayudaron un poco (+2,1 puntos), pero es suerte de este periodo: no hay que contar con ello.
2. **Inicio.** El backtest ya estaba comprado el 2021-01-01; el paper empieza en liquidez y compra en la apertura del 2021-01-02.
3. **Reequilibrios pequeños.** El paper no ejecuta cambios de exposición menores de 1 punto.
4. **Precio simulado.** Cada orden paga 0,06 % de spread y slippage sobre la apertura, igual que el modelo del backtest.

La diferencia en drawdown (-12,0 % frente a -11,7 %) y en Sharpe es pequeña: el motor de paper reproduce el backtest.
No hubo ninguna parada de emergencia ni días sin señales por datos.
