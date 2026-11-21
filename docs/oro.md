# Oro (GLD): las reglas del copiloto, sin elegir nada (D43)

Generado por `python -m copilot oro`. Ninguna regla se eligió mirando el oro: toda su historia es fuera de muestra.
Costes 0.05 % por lado. Sharpe anualizado con 252 días. Ventanas desde la vela 365 (TEST, desde 2019 con la historia anterior delante). N1 no se aplica (decide en domingo).

| Regla | Época | Rentabilidad (B&H) | Sharpe (B&H) | Drawdown (B&H) | Órdenes/semana | Criterio v2 |
|---|---|---|---|---|---|---|
| N1D L=28 | otra época | 6.8 % (108.3 %) | 0.17 (0.80) | -36.2 % (-29.4 %) | 0.56 | no |
| N1D L=28 | TRAIN | -17.0 % (-22.9 %) | -0.26 (-0.19) | -31.6 % (-42.1 %) | 0.66 | no |
| N1D L=28 | TEST | 135.5 % (166.2 %) | 0.82 (0.78) | -20.5 % (-34.9 %) | 0.52 | sí |
| U0940 | otra época | 8.6 % (108.3 %) | 0.19 (0.80) | -29.7 % (-29.4 %) | 0.55 | no |
| U0940 | TRAIN | -16.5 % (-22.9 %) | -0.32 (-0.19) | -24.9 % (-42.1 %) | 0.55 | no |
| U0940 | TEST | 115.3 % (166.2 %) | 0.76 (0.78) | -25.3 % (-34.9 %) | 0.49 | no |
| U0082 | otra época | 35.3 % (108.3 %) | 0.45 (0.80) | -24.8 % (-29.4 %) | 0.13 | no |
| U0082 | TRAIN | -22.9 % (-22.9 %) | -0.40 (-0.19) | -34.7 % (-42.1 %) | 0.10 | no |
| U0082 | TEST | 115.5 % (166.2 %) | 0.71 (0.78) | -31.3 % (-34.9 %) | 0.08 | no |
| U0193 | otra época | -5.8 % (108.3 %) | -0.07 (0.80) | -17.1 % (-29.4 %) | 0.39 | no |
| U0193 | TRAIN | 1.2 % (-22.9 %) | 0.07 (-0.19) | -4.1 % (-42.1 %) | 0.10 | sí |
| U0193 | TEST | 8.2 % (166.2 %) | 0.16 (0.78) | -16.4 % (-34.9 %) | 0.30 | no |
| U0190 | otra época | 44.3 % (108.3 %) | 0.54 (0.80) | -29.9 % (-29.4 %) | 0.51 | no |
| U0190 | TRAIN | -13.1 % (-22.9 %) | -0.20 (-0.19) | -23.5 % (-42.1 %) | 0.49 | no |
| U0190 | TEST | 98.9 % (166.2 %) | 0.68 (0.78) | -18.9 % (-34.9 %) | 0.50 | no |
| U0731 | otra época | 25.2 % (108.3 %) | 0.36 (0.80) | -30.0 % (-29.4 %) | 0.32 | no |
| U0731 | TRAIN | -32.9 % (-22.9 %) | -0.41 (-0.19) | -48.9 % (-42.1 %) | 0.25 | no |
| U0731 | TEST | 164.8 % (166.2 %) | 0.85 (0.78) | -24.9 % (-34.9 %) | 0.12 | sí |

| Regla | Sharpe deflactado 2011-2026 (N = 6) | Costes x2 en TRAIN | Aprueba |
|---|---|---|---|
| N1D L=28 | 0.863 | no hace falta | no |
| U0940 | 0.840 | no hace falta | no |
| U0082 | 0.769 | no hace falta | no |
| U0193 | 0.472 | no hace falta | no |
| U0190 | 0.804 | no hace falta | no |
| U0731 | 0.777 | no hace falta | no |

**Ninguna regla aprueba en el oro.** El oro queda sin copiloto.

