# Vigilancia del deterioro: simulación (Prompt 8)

Generado por `python -m copilot vigilancia`. Reglas fijadas antes: `docs/decisiones.md`, D15.
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
- Días sin señales por problemas de datos: 0.
- Eventos: alerta 446, parada_emergencia 1, suspension 4.

- B1 N=20,M=10: emite señales 1 de 1461 días.
- B1 N=55,M=20: emite señales 100 de 1461 días.
- T1 sma_n=100: emite señales 0 de 1461 días.

## Suspensiones y resultado posterior (en la sombra, hasta el final)

| Estrategia | Fecha | Motivo | Resultado después de suspender |
|---|---|---|---|
| T1 sma_n=100 | 2013-01-01 | 365 días: +66.7% frente a +67.5% de la mediana de entradas aleatorias | +8243.9% |
| B1 N=20,M=10 | 2013-01-02 | 365 días: +59.5% frente a +72.9% de la mediana de entradas aleatorias | +11543.5% |
| B1 N=55,M=20 | 2013-04-11 | drawdown -63.6% peor que el peor del backtest (-59.1%) | +1469.7% |
| C1 al 25 % | 2013-04-11 | drawdown -18.6% peor que el peor del backtest (-17.4%) | +132.0% |

## Primeros 40 eventos

| Fecha | Tipo | Serie | Motivo |
|---|---|---|---|
| 2013-01-01 | alerta | mercado | volatilidad 30 d 22% fuera de [34%, 134%] de TRAIN |
| 2013-01-01 | suspension | T1 sma_n=100 | 365 días: +66.7% frente a +67.5% de la mediana de entradas aleatorias |
| 2013-01-02 | alerta | mercado | volatilidad 30 d 22% fuera de [34%, 134%] de TRAIN |
| 2013-01-02 | suspension | B1 N=20,M=10 | 365 días: +59.5% frente a +72.9% de la mediana de entradas aleatorias |
| 2013-01-03 | alerta | mercado | volatilidad 30 d 22% fuera de [34%, 134%] de TRAIN |
| 2013-01-04 | alerta | mercado | volatilidad 30 d 14% fuera de [34%, 134%] de TRAIN |
| 2013-01-05 | alerta | mercado | volatilidad 30 d 12% fuera de [34%, 134%] de TRAIN |
| 2013-01-06 | alerta | mercado | volatilidad 30 d 12% fuera de [34%, 134%] de TRAIN |
| 2013-01-07 | alerta | mercado | volatilidad 30 d 12% fuera de [34%, 134%] de TRAIN |
| 2013-01-08 | alerta | mercado | volatilidad 30 d 15% fuera de [34%, 134%] de TRAIN |
| 2013-01-09 | alerta | mercado | volatilidad 30 d 15% fuera de [34%, 134%] de TRAIN |
| 2013-01-10 | alerta | mercado | volatilidad 30 d 18% fuera de [34%, 134%] de TRAIN |
| 2013-01-11 | alerta | mercado | volatilidad 30 d 18% fuera de [34%, 134%] de TRAIN |
| 2013-01-12 | alerta | mercado | volatilidad 30 d 18% fuera de [34%, 134%] de TRAIN |
| 2013-01-13 | alerta | mercado | volatilidad 30 d 19% fuera de [34%, 134%] de TRAIN |
| 2013-01-14 | alerta | mercado | volatilidad 30 d 22% fuera de [34%, 134%] de TRAIN |
| 2013-01-15 | alerta | mercado | volatilidad 30 d 22% fuera de [34%, 134%] de TRAIN |
| 2013-01-16 | alerta | mercado | volatilidad 30 d 23% fuera de [34%, 134%] de TRAIN |
| 2013-01-17 | alerta | mercado | volatilidad 30 d 29% fuera de [34%, 134%] de TRAIN |
| 2013-01-18 | alerta | mercado | volatilidad 30 d 29% fuera de [34%, 134%] de TRAIN |
| 2013-01-19 | alerta | mercado | volatilidad 30 d 29% fuera de [34%, 134%] de TRAIN |
| 2013-01-20 | alerta | mercado | volatilidad 30 d 29% fuera de [34%, 134%] de TRAIN |
| 2013-04-10 | alerta | mercado | volatilidad 30 d 193% fuera de [34%, 134%] de TRAIN |
| 2013-04-11 | alerta | mercado | volatilidad 30 d 311% fuera de [34%, 134%] de TRAIN |
| 2013-04-11 | suspension | B1 N=55,M=20 | drawdown -63.6% peor que el peor del backtest (-59.1%) |
| 2013-04-11 | suspension | C1 al 25 % | drawdown -18.6% peor que el peor del backtest (-17.4%) |
| 2013-04-11 | parada_emergencia | todas | drawdown -18.6% peor que el peor del backtest (-17.4%) |
| 2013-04-12 | alerta | mercado | volatilidad 30 d 323% fuera de [34%, 134%] de TRAIN |
| 2013-04-13 | alerta | mercado | volatilidad 30 d 331% fuera de [34%, 134%] de TRAIN |
| 2013-04-14 | alerta | mercado | volatilidad 30 d 331% fuera de [34%, 134%] de TRAIN |
| 2013-04-15 | alerta | mercado | volatilidad 30 d 341% fuera de [34%, 134%] de TRAIN |
| 2013-04-16 | alerta | mercado | volatilidad 30 d 342% fuera de [34%, 134%] de TRAIN |
| 2013-04-17 | alerta | mercado | volatilidad 30 d 355% fuera de [34%, 134%] de TRAIN |
| 2013-04-18 | alerta | mercado | volatilidad 30 d 356% fuera de [34%, 134%] de TRAIN |
| 2013-04-19 | alerta | mercado | volatilidad 30 d 356% fuera de [34%, 134%] de TRAIN |
| 2013-04-20 | alerta | mercado | volatilidad 30 d 355% fuera de [34%, 134%] de TRAIN |
| 2013-04-21 | alerta | mercado | volatilidad 30 d 356% fuera de [34%, 134%] de TRAIN |
| 2013-04-22 | alerta | mercado | volatilidad 30 d 354% fuera de [34%, 134%] de TRAIN |
| 2013-04-23 | alerta | mercado | volatilidad 30 d 354% fuera de [34%, 134%] de TRAIN |
| 2013-04-24 | alerta | mercado | volatilidad 30 d 354% fuera de [34%, 134%] de TRAIN |

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

## Lectura honesta: las reglas v1 funcionan, pero son demasiado duras

**Lo que funciona:**
- La vigilancia es causal (probado: alterar el futuro no cambia ninguna alerta ni suspensión del pasado).
- La regla de drawdown saltó cuando debía: el 2013-04-11, en el hundimiento del -69 %, activó la parada de emergencia.
- Las suspensiones quedan registradas con fecha y motivo, y se sigue su resultado posterior.

**Lo que no funciona bien:**
1. **"Peor que el azar" es una moneda al aire.** Comparar con la *mediana* de entradas aleatorias con los mismos días
   en el mercado hace que una estrategia con ventaja pequeña quede por debajo casi la mitad de las veces por puro ruido.
   T1 fue suspendida el primer día por 0,8 puntos (+66,7 % frente a +67,5 %) y B1 20/10 al día siguiente.
2. **Sin reactivación, una suspensión es para siempre.** En la sombra, después de suspenderse, T1 ganó un +8 244 %,
   B1 20/10 un +11 544 % y la cartera al 25 % un +132 %. Las reglas habrían apagado el copiloto justo antes de su mejor época.
3. **Las alertas de volatilidad son ruido:** 446 alertas en 4 años, porque la volatilidad de Bitstamp en 2013-2016 cae
   a menudo fuera de la banda de TRAIN. Una alerta que salta casi cada día no avisa de nada.
4. **Falta un control de datos:** los días 2015-01-06 a 2015-01-08 Bitstamp estuvo parado (velas planas, volumen 0) y la
   regla 3 no lo detectó, porque esas velas no son incoherentes. Debería exigir volumen mayor que 0.

**Por qué no lo cambio yo ahora:** las reglas se fijaron antes de ejecutar. Cambiarlas tras ver este resultado y volver a
simular sobre los mismos datos sería ajustarlas a lo ya visto. Cualquier cambio entra como versión 2 registrada, y su
prueba de verdad será el paper trading, no esta simulación.
