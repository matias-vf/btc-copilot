# Reglas del bot de la Day Trader skill (`paper-bot`) con datos que su validador no vio (D57, D58)

Regla `breakdown_short` copiada del código del bot. Datos de Binance en velas de 1 hora hasta el 2024-11-13; el validador del bot empieza el 2024-11-14. Costes 0,08 % por lado + funding real.

| Regla | Desde | Operaciones | Acierto | Media R | Media R costes x2 | Horas medias | Sharpe deflactado | Aprueba |
|---|---|---|---|---|---|---|---|---|
| BTC n=24 rr=2 | 2017-08-17 | 380 | 43% | -0.012 | -0.073 | 31.9 | 0.004 | no |
| ETH n=12 rr=1.5 | 2017-08-17 | 512 | 45% | +0.004 | -0.052 | 27.1 | 0.000 | no |
| BTC n=24 rr=2 día | 2017-08-17 | 517 | 39% | -0.072 | -0.133 | 11.1 | 0.000 | no |
| ETH n=12 rr=1.5 día | 2017-08-17 | 731 | 42% | -0.042 | -0.101 | 10.3 | 0.000 | no |

## Suma de R por año

- BTC n=24 rr=2: 2017: -2.03, 2018: +25.48, 2019: -5.54, 2020: -6.66, 2021: -3.76, 2022: -5.89, 2023: -10.37, 2024: +4.37
- ETH n=12 rr=1.5: 2017: -3.70, 2018: +24.66, 2019: -7.71, 2020: -10.48, 2021: -2.36, 2022: +3.99, 2023: +0.21, 2024: -2.67
- BTC n=24 rr=2 día: 2017: -0.99, 2018: +5.59, 2019: -15.04, 2020: -4.45, 2021: -5.24, 2022: -12.85, 2023: -7.00, 2024: +2.97
- ETH n=12 rr=1.5 día: 2017: +0.25, 2018: +13.65, 2019: -10.11, 2020: -7.40, 2021: -6.63, 2022: -1.24, 2023: -14.01, 2024: -5.13
