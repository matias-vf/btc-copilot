# Tercera búsqueda: 1000 estrategias (Prompts 4 y 5)

Generado por `python -m copilot universo`. Reglas fijadas antes: `docs/decisiones.md`, D36 y D37.
TRAIN medido desde 2018-08-17 (vela 365) hasta 2022-12-31, igual para las 1000 y para Buy & Hold.
Buy & Hold en esa ventana: rentabilidad 161.7 %, Sharpe 0.67, drawdown -76.6 %.
Sharpe deflactado con N = 1000 pruebas; varianza de los Sharpe diarios entre pruebas: 0.000597.

## Embudo

- 1000 variantes probadas en TRAIN.
- Criterio v2 (menos drawdown y Sharpe >= B&H): 512.
- Además, regla de costes x2: 508.
- Además, Sharpe deflactado >= 0.95: **0**.
- Además, criterio v2 en la otra época y en TEST: **0**.
- Elegidas (como mucho 5, correlación <= 0.9 con N1, N1D y entre sí): **0**.

## Por familia (TRAIN)

| Familia | Nombre | Variantes | Criterio v2 | + costes | + Sharpe deflactado |
|---|---|---|---|---|---|
| F01 | Precio sobre media móvil (con banda) | 48 | 41 | 41 | 0 |
| F02 | Cruce de medias móviles (con banda) | 96 | 86 | 86 | 0 |
| F03 | Cruce de medias exponenciales | 25 | 25 | 25 | 0 |
| F04 | Momentum de serie temporal diario (con umbral) | 80 | 58 | 56 | 0 |
| F05 | Momentum semanal (decide el domingo) | 16 | 14 | 14 | 0 |
| F06 | Regla de filtro (x % arriba entra, y % abajo sale) | 100 | 20 | 20 | 0 |
| F07 | Canal de Donchian (máximos y mínimos) | 40 | 33 | 33 | 0 |
| F08 | Ruptura del rango con cierres (con banda) | 30 | 19 | 19 | 0 |
| F09 | Ruptura del rango con tenencia fija | 50 | 23 | 23 | 0 |
| F10 | Reversión con RSI | 96 | 0 | 0 | 0 |
| F11 | Reversión con bandas de Bollinger | 32 | 0 | 0 | 0 |
| F12 | Ruptura de bandas de Bollinger | 16 | 15 | 15 | 0 |
| F13 | Reversión a corto plazo tras una caída | 100 | 5 | 3 | 0 |
| F14 | Cerca del máximo de N días | 36 | 28 | 28 | 0 |
| F15 | MACD | 12 | 8 | 8 | 0 |
| F16 | Volumen en balance (OBV) | 12 | 8 | 8 | 0 |
| F17 | Oscilador estocástico | 24 | 0 | 0 | 0 |
| F18 | ADX con DI+ > DI- | 16 | 16 | 16 | 0 |
| F19 | Canal de Keltner (ATR) | 16 | 15 | 15 | 0 |
| F20 | Volatilidad objetivo sobre una regla base | 36 | 30 | 30 | 0 |
| F21 | Estacionalidad de calendario | 25 | 6 | 6 | 0 |
| F22 | SAR parabólico | 12 | 10 | 10 | 0 |
| F23 | Ichimoku | 8 | 8 | 8 | 0 |
| F24 | Williams %R | 12 | 0 | 0 | 0 |
| F25 | Momentum y media a la vez | 12 | 11 | 11 | 0 |
| F26 | Ruptura con volumen alto | 9 | 9 | 9 | 0 |
| F27 | Tendencia con stop de ATR | 16 | 12 | 12 | 0 |
| F28 | Momentum solo con volatilidad baja | 6 | 3 | 3 | 0 |
| F29 | Media adaptativa de Kaufman (KAMA) | 4 | 3 | 3 | 0 |
| F30 | Precio sobre media ponderada (con banda) | 10 | 6 | 6 | 0 |
| F31 | Caja de Darvas | 5 | 0 | 0 | 0 |

## Las 20 con mayor Sharpe deflactado en TRAIN

| Id | Familia | Variante | Sharpe | Drawdown | Rentabilidad | Sharpe deflactado | Aprueba TRAIN |
|---|---|---|---|---|---|---|---|
| U0626 | F12 | n=50,k=1.0 | 1.52 | -47.0 % | 1 226.7 % | 0.499 | no |
| U0627 | F12 | n=50,k=1.5 | 1.49 | -41.4 % | 1 083.1 % | 0.472 | no |
| U0843 | F19 | n=50,k=1.5 | 1.48 | -41.6 % | 1 047.3 % | 0.468 | no |
| U0629 | F12 | n=50,k=2.5 | 1.47 | -31.1 % | 997.3 % | 0.462 | no |
| U0628 | F12 | n=50,k=2.0 | 1.46 | -38.1 % | 999.5 % | 0.453 | no |
| U0940 | F25 | L=28,n=100 | 1.46 | -44.6 % | 1 005.5 % | 0.447 | no |
| U0742 | F14 | ventana=120,x=0.05 | 1.45 | -21.6 % | 354.5 % | 0.434 | no |
| U0082 | F02 | s=5,l=100,banda=0.01 | 1.42 | -35.0 % | 1 161.7 % | 0.418 | no |
| U0789 | F16 | n=100,filtro=True | 1.41 | -43.7 % | 991.1 % | 0.405 | no |
| U0953 | F26 | N=20,k=2.0 | 1.41 | -29.6 % | 747.4 % | 0.404 | no |
| U0923 | F23 | t=10,k=30,b=60,regla=nube | 1.40 | -34.7 % | 946.1 % | 0.401 | no |
| U0031 | F01 | n=125,banda=0.0 | 1.40 | -33.6 % | 1 063.0 % | 0.398 | no |
| U0193 | F04 | L=35,umbral=0.1 | 1.37 | -42.0 % | 802.0 % | 0.377 | no |
| U0939 | F25 | L=28,n=50 | 1.37 | -47.9 % | 918.9 % | 0.374 | no |
| U0192 | F04 | L=35,umbral=0.05 | 1.37 | -50.8 % | 900.5 % | 0.371 | no |
| U0190 | F04 | L=35,umbral=0.0 | 1.36 | -46.1 % | 1 020.0 % | 0.367 | no |
| U0081 | F02 | s=5,l=100,banda=0.0 | 1.34 | -41.4 % | 973.2 % | 0.355 | no |
| U0952 | F26 | N=20,k=1.5 | 1.34 | -37.3 % | 717.8 % | 0.351 | no |
| U0030 | F01 | n=100,banda=0.02 | 1.34 | -43.1 % | 959.5 % | 0.350 | no |
| U0941 | F25 | L=28,n=200 | 1.34 | -44.7 % | 692.9 % | 0.348 | no |

N1 L=4 dentro del universo (U0253, F05 semanas=4): Sharpe 1.24, Sharpe deflactado 0.276 -> NO supera la corrección por 1000 pruebas. Se queda en el copiloto igualmente (D37).

N1D L=28 dentro del universo (U0186, F04 L=28,umbral=0.0): Sharpe 1.11, Sharpe deflactado 0.191 -> NO supera la corrección por 1000 pruebas. Se queda en el copiloto igualmente (D37).

## Selección final

**Ninguna variante nueva supera todo el proceso.** El copiloto sigue con N1 y N1D (D37).
