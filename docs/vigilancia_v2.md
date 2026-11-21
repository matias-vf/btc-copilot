# Vigilancia del deterioro: simulación, reglas v2 (Prompt 8)

Generado por `python -m copilot vigilancia`. Reglas: `docs/decisiones.md`, D15 + D17.
Simulación día a día en Bitstamp 2013-01-01 a 2016-12-31, con la referencia de TRAIN (Binance 2017-2022).
Es una prueba del sistema de vigilancia; no escribe en `registros/vigilancia.jsonl` (eso solo en vivo).

## Referencia de TRAIN

| Serie | Peor drawdown | Percentil 5 de 180 días |
|---|---|---|
| B1 N=20,M=10 | -54.3% | -26.7% |
| B1 N=55,M=20 | -59.1% | -21.3% |
| T1 sma_n=100 | -64.5% | -27.6% |
| C1 al 25 % | -17.4% | -5.7% |

Volatilidad de 30 días normal en TRAIN: entre 34% y 134%.

## Resumen

- Días vigilados: 1461.
- Días sin señales por problemas de datos: 3.
- Eventos: alerta 53, datos 3, parada_emergencia 1, suspension 4.

- B1 N=20,M=10: emite señales 100 de 1461 días.
- B1 N=55,M=20: emite señales 100 de 1461 días.
- T1 sma_n=100: emite señales 100 de 1461 días.

## Suspensiones y resultado mientras estuvo suspendida (en la sombra)

| Estrategia | Desde | Hasta | Motivo | Resultado durante la suspensión |
|---|---|---|---|---|
| B1 N=20,M=10 | 2013-04-11 | sigue suspendida | drawdown -63.6% peor que el peor del backtest (-54.3%) | +1727.5% |
| B1 N=55,M=20 | 2013-04-11 | sigue suspendida | drawdown -63.6% peor que el peor del backtest (-59.1%) | +1469.7% |
| T1 sma_n=100 | 2013-04-15 | sigue suspendida | drawdown -67.7% peor que el peor del backtest (-64.5%) | +1390.6% |
| C1 al 25 % | 2013-04-11 | sigue suspendida | drawdown -18.6% peor que el peor del backtest (-17.4%) | +132.0% |

## Eventos (sin las alertas de mercado)

| Fecha | Tipo | Serie | Motivo |
|---|---|---|---|
| 2013-04-11 | suspension | B1 N=20,M=10 | drawdown -63.6% peor que el peor del backtest (-54.3%) |
| 2013-04-11 | suspension | B1 N=55,M=20 | drawdown -63.6% peor que el peor del backtest (-59.1%) |
| 2013-04-11 | alerta | T1 sma_n=100 | drawdown -63.6%, más del 75 % del peor del backtest |
| 2013-04-11 | suspension | C1 al 25 % | drawdown -18.6% peor que el peor del backtest (-17.4%) |
| 2013-04-11 | parada_emergencia | todas | drawdown -18.6% peor que el peor del backtest (-17.4%) |
| 2013-04-15 | suspension | T1 sma_n=100 | drawdown -67.7% peor que el peor del backtest (-64.5%) |
| 2015-01-06 | datos | todas | volumen 0 el 2015-01-06 (mercado parado o vela de relleno) |
| 2015-01-07 | datos | todas | volumen 0 el 2015-01-07 (mercado parado o vela de relleno) |
| 2015-01-08 | datos | todas | volumen 0 el 2015-01-08 (mercado parado o vela de relleno) |

## Ejemplo de informe diario (último día)

```
Estado de las estrategias, 2016-12-31
Datos: correctos
Parada de emergencia: ACTIVADA
  B1 N=20,M=10 SUSPENDIDA sin señales
  B1 N=55,M=20 SUSPENDIDA sin señales
  T1 sma_n=100 SUSPENDIDA sin señales
  C1 al 25 %   SUSPENDIDA 
```

## Lectura (v2 frente a v1)

| | v1 | v2 |
|---|---|---|
| Suspensiones por "peor que el azar" | 2 (el primer y el segundo día, por ruido) | 0 |
| Suspensiones por drawdown | 2 | 4 (las tres estrategias y la cartera, en el hundimiento de abril de 2013) |
| Alertas | 446 | 53 |
| Días sin señales por datos | 0 (no vio el parón de Bitstamp) | 3 (2015-01-06 a 2015-01-08, volumen 0) |
| Días con señales posibles | 0 a 100 según la estrategia | 100 en las tres |

- **La regla del azar ya no dispara por ruido.** En esta época ninguna estrategia pasó 30 días seguidos por debajo del
  percentil 25 aleatorio. Por eso aquí la reactivación automática no llegó a usarse.
- **La parada por drawdown hace su trabajo, pero deja todo apagado.** El 2013-04-11 (caída del -69 % en un día) las tres
  estrategias superaron su peor drawdown de TRAIN y la cartera al 25 % también (-18,6 % frente a -17,4 %). Como se
  acordó, solo se reactivan con tu aprobación. Sin esa aprobación, el copiloto habría estado parado de abril de 2013 a
  diciembre de 2016, y las estrategias habrían ganado entre un +1 391 % y un +1 728 % en la sombra.
- **Qué significa en la práctica:** tras una parada de emergencia, la decisión de volver es tuya. El informe diario
  te enseñará el resultado en la sombra para que decidas con datos.
- Recordatorio: la v2 se diseñó tras ver la v1 en estos mismos datos. La prueba de verdad será el paper trading.
