# Cartera y riesgo, segunda búsqueda (Prompts 6 y 7)

Generado por `python -m copilot riesgo2`. Reglas fijadas antes de ejecutar: `docs/decisiones.md`, D30.
Única estrategia superviviente: N1 L=4 (EXPERIMENTAL). Sin apalancamiento.

## Prompt 6: cartera

Con una sola estrategia no hay combinación posible: la cartera es N1 L=4 con todo su peso.

| Época | Correlación diaria con Buy & Hold |
|---|---|
| TRAIN | 0.70 |
| otra época | 0.75 |
| TEST | 0.73 |

## Prompt 7: exposición

### TRAIN

| Exposición | CAGR | Sharpe | Volatilidad | Drawdown máx. | Peor día | Peor mes | Exposición media | Admisible |
|---|---|---|---|---|---|---|---|---|
| 25 % | 16.7 % | 1.21 | 13.6 % | -25.8 % | -3.5 % | -7.9 % | 12.6 % | **ELEGIDA** |
| 50 % | 33.8 % | 1.21 | 27.2 % | -46.0 % | -7.1 % | -15.3 % | 25.3 % | no |
| 75 % | 50.6 % | 1.21 | 40.8 % | -61.4 % | -10.6 % | -22.4 % | 37.9 % | no |
| 100 % | 66.4 % | 1.21 | 54.4 % | -73.0 % | -14.1 % | -29.1 % | 50.6 % | no |
| Buy & Hold | 28.5 % | 0.72 | 78.0 % | -83.2 % | -39.5 % | -37.3 % | 100 % | – |

### otra época

| Exposición | CAGR | Sharpe | Volatilidad | Drawdown máx. | Peor día | Peor mes | Exposición media | Admisible |
|---|---|---|---|---|---|---|---|---|
| 25 % | 37.3 % | 1.78 | 18.9 % | -21.4 % | -12.1 % | -10.9 % | 14.3 % | **ELEGIDA** |
| 50 % | 82.0 % | 1.78 | 37.7 % | -40.4 % | -24.3 % | -22.4 % | 28.5 % | no |
| 75 % | 132.3 % | 1.78 | 56.6 % | -56.7 % | -36.4 % | -34.1 % | 42.8 % | no |
| 100 % | 185.2 % | 1.78 | 75.4 % | -70.3 % | -48.5 % | -45.4 % | 57.0 % | no |
| Buy & Hold | 126.5 % | 1.33 | 100.1 % | -84.9 % | -48.5 % | -39.7 % | 100 % | – |

### TEST

| Exposición | CAGR | Sharpe | Volatilidad | Drawdown máx. | Peor día | Peor mes | Exposición media | Admisible |
|---|---|---|---|---|---|---|---|---|
| 25 % | 10.7 % | 1.24 | 8.5 % | -8.8 % | -2.1 % | -2.2 % | 14.3 % | **ELEGIDA** |
| 50 % | 21.7 % | 1.24 | 16.9 % | -17.1 % | -4.2 % | -4.4 % | 28.6 % | no |
| 75 % | 32.8 % | 1.24 | 25.4 % | -25.1 % | -6.3 % | -6.8 % | 42.9 % | no |
| 100 % | 43.9 % | 1.24 | 33.8 % | -32.5 % | -8.4 % | -9.3 % | 57.3 % | no |
| Buy & Hold | 38.6 % | 0.93 | 46.3 % | -53.0 % | -14.0 % | -24.1 % | 100 % | – |

Regla D30: exposición elegida **25 %**.

Con la misma estrategia, subir la exposición multiplica ganancias y pérdidas por igual: el Sharpe no cambia.
La regla elige la menor exposición que cumple el límite del 35 % de drawdown en TRAIN y en la otra época.

