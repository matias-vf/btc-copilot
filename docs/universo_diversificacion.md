# Tercera búsqueda: estrategias añadidas para diversificar (D40)

Generado por `python -m copilot diversificar`. Regla elegida por el usuario y fijada antes de evaluar: D40.
**Ninguna de estas estrategias supera la corrección por 1000 pruebas (Sharpe deflactado).** Son EXPERIMENTALES y
SIN significación estadística; la prueba que decide es el paper trading en vivo.

## Embudo

- Candidatas (criterio v2 + costes en TRAIN): 508.
- Aprueban también la otra época: 422.
- Aprueban también TEST: 191.
- Aprueban las tres: **172**.
- Elegidas (máximo 5, correlación <= 0.9 con N1, N1D y entre sí): **5**.

## Elegidas

| Id | Familia | Nombre | Variante | TRAIN Sharpe (DD) | Otra época Sharpe (DD) | TEST Sharpe (DD) | TEST rent. (B&H) | Sharpe deflactado | Correlación máx. (con) |
|---|---|---|---|---|---|---|---|---|---|
| U0940 | F25 | Momentum y media a la vez | L=28,n=100 | 1.46 (-44.6 %) | 1.74 (-70.3 %) | 1.43 (-22.2 %) | 374.1 % (255.8 %) | 0.447 | 0.89 (N1D L=28) |
| U0082 | F02 | Cruce de medias móviles (con banda) | s=5,l=100,banda=0.01 | 1.42 (-35.0 %) | 1.71 (-70.3 %) | 1.01 (-32.2 %) | 218.1 % (255.8 %) | 0.418 | 0.90 (U0940) |
| U0193 | F04 | Momentum de serie temporal diario (con umbral) | L=35,umbral=0.1 | 1.37 (-42.0 %) | 1.58 (-70.3 %) | 1.17 (-22.1 %) | 195.0 % (255.8 %) | 0.377 | 0.88 (U0940) |
| U0190 | F04 | Momentum de serie temporal diario (con umbral) | L=35,umbral=0.0 | 1.36 (-46.1 %) | 1.96 (-70.3 %) | 1.17 (-32.7 %) | 274.5 % (255.8 %) | 0.367 | 0.88 (N1D L=28) |
| U0731 | F14 | Cerca del máximo de N días | ventana=60,x=0.1 | 1.33 (-46.0 %) | 2.38 (-34.0 %) | 0.95 (-47.8 %) | 176.7 % (255.8 %) | 0.344 | 0.80 (U0940) |

Buy & Hold: otra época Sharpe 1.54, DD -84.9 %; TEST Sharpe 0.93, DD -53.0 %.

Finalistas saltadas por parecerse demasiado a N1, N1D o a otra elegida: 106.

Familias de las finalistas: F04 Momentum de serie temporal diario (con umbral) (26), F01 Precio sobre media móvil (con banda) (23), F02 Cruce de medias móviles (con banda) (23), F20 Volatilidad objetivo sobre una regla base (22), F03 Cruce de medias exponenciales (16), F25 Momentum y media a la vez (7), F15 MACD (6), F27 Tendencia con stop de ATR (6), F30 Precio sobre media ponderada (con banda) (6), F05 Momentum semanal (decide el domingo) (5), F19 Canal de Keltner (ATR) (5), F12 Ruptura de bandas de Bollinger (4), F16 Volumen en balance (OBV) (4), F23 Ichimoku (4), F09 Ruptura del rango con tenencia fija (3), F06 Regla de filtro (x % arriba entra, y % abajo sale) (2), F07 Canal de Donchian (máximos y mínimos) (2), F08 Ruptura del rango con cierres (con banda) (2), F18 ADX con DI+ > DI- (2), F28 Momentum solo con volatilidad baja (2), F14 Cerca del máximo de N días (1), F22 SAR parabólico (1).

