# Day trading de QQQ con compras y cortos y costes de IBKR (D55, D56)

Reglas fijadas antes de descargar los datos: D55. Velas de 1 hora de Yahoo. Todo se cierra al final de la sesión.
TRAIN 2024-02-06 a 2026-03-31; otra época = SPY en las mismas fechas; TEST 2026-04-01 a 2026-11-20.

Columnas: rentabilidad / Sharpe anual / peor caída.

| Buy & Hold | TRAIN (QQQ) | Otra época (SPY) | TEST (QQQ) |
|---|---|---|---|
| | 34.7 % / 0.77 / -22.9 % | 32.0 % / 0.90 / -19.0 % | 5.7 % / 0.47 / -19.7 % |

## Embudo

- Universo: 40 variantes.
- Cumplen las tres condiciones en TRAIN (ganan, menos caída y Sharpe >= Buy & Hold): **0**.
- Sharpe deflactado >= 0,95 (N = 40): **0** (el mayor: 0.097).
- Además, criterio v2 en SPY y en TEST: **0**.
- Elegidas (máximo 3, correlación <= 0,9): **0**.

## Las 40 variantes

| Familia | Variante | TRAIN | Días con operación | Sharpe deflactado | SPY | TEST |
|---|---|---|---|---|---|---|
| Q3 Hueco de apertura | g=0.01,modo=contra | 9.1 % / 0.60 / -5.1 % | 16% | 0.097 | - | - |
| Q3 Hueco de apertura | g=0.005,modo=contra | 6.7 % / 0.38 / -8.9 % | 40% | 0.061 | - | - |
| Q3 Hueco de apertura | g=0.0025,modo=contra | 4.0 % / 0.23 / -12.3 % | 64% | 0.040 | - | - |
| Q5 Reversión con RSI horario | p=3,x=20 | -6.2 % / -0.26 / -13.8 % | 82% | 0.008 | - | - |
| Q5 Reversión con RSI horario | p=5,x=10 | -2.7 % / -0.29 / -6.9 % | 13% | 0.007 | - | - |
| Q6 Ruptura inicial a favor de la tendencia diaria | r=1 | -4.2 % / -0.30 / -13.2 % | 42% | 0.008 | - | - |
| Q5 Reversión con RSI horario | p=3,x=30 | -9.4 % / -0.37 / -20.2 % | 98% | 0.005 | - | - |
| Q2 Ruptura del rango inicial (Crabel 1990) | r=1,stop=mitad,obj=2.0 | -7.1 % / -0.39 / -15.4 % | 81% | 0.006 | - | - |
| Q2 Ruptura del rango inicial (Crabel 1990) | r=1,stop=mitad,obj=None | -9.3 % / -0.50 / -15.7 % | 81% | 0.004 | - | - |
| Q2 Ruptura del rango inicial (Crabel 1990) | r=2,stop=otro_lado,obj=2.0 | -9.7 % / -0.55 / -15.1 % | 64% | 0.003 | - | - |
| Q2 Ruptura del rango inicial (Crabel 1990) | r=1,stop=otro_lado,obj=2.0 | -11.3 % / -0.59 / -17.0 % | 81% | 0.003 | - | - |
| Q2 Ruptura del rango inicial (Crabel 1990) | r=1,stop=otro_lado,obj=None | -11.4 % / -0.59 / -17.6 % | 81% | 0.003 | - | - |
| Q2 Ruptura del rango inicial (Crabel 1990) | r=2,stop=otro_lado,obj=None | -10.2 % / -0.61 / -15.1 % | 64% | 0.003 | - | - |
| Q5 Reversión con RSI horario | p=2,x=10 | -11.8 % / -0.61 / -17.3 % | 80% | 0.001 | - | - |
| Q2 Ruptura del rango inicial (Crabel 1990) | r=2,stop=mitad,obj=None | -10.1 % / -0.61 / -16.1 % | 64% | 0.002 | - | - |
| Q1 Momentum intradía (Gao y otros 2018) | k=1,h=3 | -12.5 % / -0.73 / -17.9 % | 100% | 0.001 | - | - |
| Q5 Reversión con RSI horario | p=5,x=30 | -15.6 % / -0.75 / -22.5 % | 80% | 0.001 | - | - |
| Q2 Ruptura del rango inicial (Crabel 1990) | r=2,stop=mitad,obj=2.0 | -11.5 % / -0.75 / -16.1 % | 64% | 0.001 | - | - |
| Q1 Momentum intradía (Gao y otros 2018) | k=2,h=3 | -12.9 % / -0.76 / -17.7 % | 99% | 0.001 | - | - |
| Q6 Ruptura inicial a favor de la tendencia diaria | r=2 | -8.5 % / -0.79 / -14.1 % | 34% | 0.001 | - | - |
| Q5 Reversión con RSI horario | p=2,x=30 | -19.3 % / -0.88 / -22.8 % | 100% | 0.000 | - | - |
| Q5 Reversión con RSI horario | p=5,x=20 | -14.6 % / -0.94 / -19.3 % | 46% | 0.000 | - | - |
| Q5 Reversión con RSI horario | p=2,x=20 | -20.3 % / -0.98 / -23.9 % | 99% | 0.000 | - | - |
| Q1 Momentum intradía (Gao y otros 2018) | k=2,h=2 | -12.8 % / -1.03 / -15.3 % | 100% | 0.000 | - | - |
| Q3 Hueco de apertura | g=0.01,modo=seguir | -15.8 % / -1.07 / -17.7 % | 16% | 0.000 | - | - |
| Q1 Momentum intradía (Gao y otros 2018) | k=3,h=3 | -17.5 % / -1.07 / -21.0 % | 99% | 0.000 | - | - |
| Q3 Hueco de apertura | g=0.005,modo=seguir | -23.3 % / -1.32 / -26.7 % | 40% | 0.000 | - | - |
| Q5 Reversión con RSI horario | p=3,x=10 | -19.3 % / -1.38 / -21.2 % | 41% | 0.000 | - | - |
| Q4 Cruce de medias horarias | f=5,s=13,stop_atr=None | -31.0 % / -1.44 / -34.4 % | 100% | 0.000 | - | - |
| Q1 Momentum intradía (Gao y otros 2018) | k=1,h=2 | -17.7 % / -1.47 / -19.4 % | 100% | 0.000 | - | - |
| Q3 Hueco de apertura | g=0.0025,modo=seguir | -30.0 % / -1.52 / -32.9 % | 64% | 0.000 | - | - |
| Q1 Momentum intradía (Gao y otros 2018) | k=3,h=2 | -18.8 % / -1.58 / -21.5 % | 99% | 0.000 | - | - |
| Q1 Momentum intradía (Gao y otros 2018) | k=1,h=1 | -14.2 % / -1.59 / -14.4 % | 100% | 0.000 | - | - |
| Q4 Cruce de medias horarias | f=5,s=13,stop_atr=2.0 | -33.9 % / -1.61 / -37.0 % | 100% | 0.000 | - | - |
| Q4 Cruce de medias horarias | f=2,s=5,stop_atr=None | -40.3 % / -1.63 / -43.0 % | 100% | 0.000 | - | - |
| Q4 Cruce de medias horarias | f=2,s=5,stop_atr=2.0 | -42.5 % / -1.75 / -45.0 % | 100% | 0.000 | - | - |
| Q1 Momentum intradía (Gao y otros 2018) | k=3,h=1 | -16.1 % / -1.83 / -16.2 % | 100% | 0.000 | - | - |
| Q1 Momentum intradía (Gao y otros 2018) | k=2,h=1 | -16.4 % / -1.87 / -16.5 % | 100% | 0.000 | - | - |
| Q4 Cruce de medias horarias | f=3,s=7,stop_atr=None | -44.2 % / -1.93 / -47.0 % | 100% | 0.000 | - | - |
| Q4 Cruce de medias horarias | f=3,s=7,stop_atr=2.0 | -45.4 % / -2.03 / -47.9 % | 100% | 0.000 | - | - |

SPY y TEST solo se muestran para las que pasan TRAIN (las demás no se miran, para no elegir mirando TEST).

**Ninguna variante cumple el criterio en TRAIN, en SPY y en TEST.**
