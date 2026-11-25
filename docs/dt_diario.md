# Day trading de apertura a cierre con velas diarias desde 2000 (D67)

233 acciones, 6766 sesiones. TRAIN 2000-02-08 a 2012-12-31; VALIDACIÓN 2013-01-02 a 2018-12-31; TEST 2019-01-02 a 2026-11-25. Entra a la apertura y sale el mismo día. Costes de IBKR con 5.000 USD por operación + 0,02 % por lado.

| Paso | Reglas |
|---|---|
| Probadas en TRAIN | 59778 |
| Candidatas en TRAIN (>= 500 operaciones, >= +0,05 R, costes x2 > 0) | 826 |
| Con Sharpe deflactado >= 0,95 en TRAIN (N = 59778) | 0 |
| A VALIDACIÓN | 200 |
| Pasan VALIDACIÓN | 0 |
| Finalistas al TEST | 0 |
| Aprueban el TEST | 0 |

## Las 15 mejores de TRAIN

| Qué hace | Operaciones | Media R | Costes x2 | Acierto | Sharpe defl. |
|---|---|---|---|---|---|
| RANK_HUECO p=0.05 contraria ambos spy=- vol=- volumen_ayer=- stop=0.5ATR obj=no | 43531 | +0.081 | +0.003 | 47% | 0.000 |
| RANK_HUECO p=0.05 contraria ambos spy=a favor vol=- volumen_ayer=<0.8 stop=no obj=1R | 6941 | +0.067 | +0.026 | 55% | 0.000 |
| RANK_HUECO p=0.05 contraria ambos spy=a favor vol=- volumen_ayer=<0.8 stop=0.5ATR obj=2R | 6941 | +0.125 | +0.042 | 51% | 0.000 |
| RANK_HUECO p=0.05 contraria ambos spy=a favor vol=- volumen_ayer=<0.8 stop=1ATR obj=1R | 6941 | +0.061 | +0.020 | 55% | 0.000 |
| RANK_HUECO p=0.1 contraria ambos spy=- vol=baja volumen_ayer=- stop=no obj=1R | 18363 | +0.052 | +0.015 | 54% | 0.000 |
| RANK_HUECO p=0.1 contraria ambos spy=- vol=baja volumen_ayer=- stop=0.5ATR obj=no | 18363 | +0.099 | +0.026 | 48% | 0.000 |
| RANK_HUECO p=0.05 contraria ambos spy=a favor vol=- volumen_ayer=<0.8 stop=no obj=2R | 6941 | +0.067 | +0.026 | 55% | 0.000 |
| RANK_HUECO p=0.05 contraria ambos spy=a favor vol=- volumen_ayer=<0.8 stop=no obj=no | 6941 | +0.067 | +0.026 | 55% | 0.000 |
| HUECO p=0.25 contraria compras spy=a favor vol=- volumen_ayer=<0.8 stop=0.5ATR obj=2R | 3960 | +0.084 | +0.003 | 49% | 0.000 |
| HUECO p=0.25 contraria compras spy=a favor vol=- volumen_ayer=<0.8 stop=0.5ATR obj=no | 3960 | +0.092 | +0.011 | 49% | 0.000 |
| HUECO p=0.25 contraria compras spy=a favor vol=baja volumen_ayer=- stop=0.5ATR obj=no | 5760 | +0.078 | +0.002 | 48% | 0.000 |
| HUECO p=0.25 contraria compras spy=a favor vol=baja volumen_ayer=<0.8 stop=0.5ATR obj=2R | 1675 | +0.099 | +0.023 | 51% | 0.000 |
| HUECO p=0.25 contraria compras spy=a favor vol=baja volumen_ayer=<0.8 stop=0.5ATR obj=no | 1675 | +0.109 | +0.034 | 50% | 0.000 |
| HUECO p=0.25 contraria compras spy=a favor vol=baja volumen_ayer=<0.8 stop=1ATR obj=2R | 1675 | +0.052 | +0.014 | 54% | 0.000 |
| HUECO p=0.25 contraria compras spy=a favor vol=baja volumen_ayer=<0.8 stop=1ATR obj=no | 1675 | +0.051 | +0.014 | 54% | 0.000 |

## VALIDACIÓN: las 15 mejores

| Qué hace | Operaciones | Media R | Costes x2 | Sharpe defl. | Pasa |
|---|---|---|---|---|---|
| RANK_HUECO p=0.05 contraria ambos spy=- vol=- volumen_ayer=- stop=0.5ATR obj=no | 25907 | +0.043 | -0.025 | 0.996 | no |
| RANK_HUECO p=0.05 contraria ambos spy=- vol=- volumen_ayer=<0.8 stop=0.5ATR obj=no | 8225 | +0.070 | +0.004 | 0.704 | no |
| RANK_HUECO p=0.05 contraria ambos spy=a favor vol=- volumen_ayer=<0.8 stop=0.5ATR obj=2R | 4108 | +0.073 | +0.005 | 0.457 | no |
| RANK_HUECO p=0.05 contraria ambos spy=a favor vol=- volumen_ayer=- stop=0.5ATR obj=no | 12704 | +0.052 | -0.017 | 0.385 | no |
| RANK_HUECO p=0.05 contraria compras spy=- vol=- volumen_ayer=<0.8 stop=no obj=no | 4207 | +0.060 | +0.028 | 0.352 | no |
| HUECO p=1.0 contraria ambos spy=- vol=- volumen_ayer=<0.8 stop=1ATR obj=2R | 1310 | +0.060 | +0.018 | 0.260 | no |
| RANK_HUECO p=0.05 contraria ambos spy=a favor vol=- volumen_ayer=<0.8 stop=no obj=1R | 4108 | +0.033 | -0.001 | 0.234 | no |
| RANK_HUECO p=0.05 contraria compras spy=- vol=- volumen_ayer=- stop=no obj=2R | 12951 | +0.023 | -0.011 | 0.224 | no |
| HUECO p=0.5 contraria ambos spy=a favor vol=- volumen_ayer=<0.8 stop=0.5ATR obj=no | 1275 | +0.113 | +0.032 | 0.202 | no |
| RANK_HUECO p=0.05 contraria compras spy=a favor vol=- volumen_ayer=<0.8 stop=no obj=1R | 2328 | +0.051 | +0.019 | 0.187 | no |
| HUECO p=0.5 contraria ambos spy=a favor vol=- volumen_ayer=<0.8 stop=no obj=2R | 1275 | +0.034 | -0.006 | 0.144 | no |
| RANK_HUECO p=0.05 contraria compras spy=- vol=- volumen_ayer=<0.8 stop=0.5ATR obj=no | 4207 | +0.112 | +0.047 | 0.116 | no |
| AYER p=2.0 seguir ambos spy=- vol=baja volumen_ayer=>1.5 stop=no obj=1R | 640 | +0.044 | +0.003 | 0.079 | no |
| HUECO p=1.0 contraria compras spy=- vol=- volumen_ayer=<0.8 stop=1ATR obj=2R | 692 | +0.115 | +0.074 | 0.070 | no |
| HUECO p=0.25 contraria compras spy=a favor vol=- volumen_ayer=<0.8 stop=0.5ATR obj=2R | 1867 | +0.048 | -0.030 | 0.068 | no |

## TEST

Ninguna regla pasó la VALIDACIÓN: el TEST no se ha mirado.
