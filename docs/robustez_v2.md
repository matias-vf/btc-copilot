# Robustez y segunda validación, segunda búsqueda (Prompt 5)

Generado por `python -m copilot robustez2`. Reglas fijadas antes de ejecutar: `docs/decisiones.md`, D28.
Criterio v2: drawdown menor que Buy & Hold y Sharpe igual o mayor, en la misma ventana. Costes x1 = 0.16 % por lado.
**Aviso:** TEST ya se vio en la primera búsqueda; es una segunda validación con sesgo, no una prueba limpia.

## Las tres épocas lado a lado (todas las variantes)

| Variante | TRAIN Sharpe (B&H) | TRAIN DD (B&H) | Costes | Otra Sharpe (B&H) | Otra DD (B&H) | TEST rent. (B&H) | TEST Sharpe (B&H) | TEST DD (B&H) | ¿Se conserva? |
|---|---|---|---|---|---|---|---|---|---|
| N1 L=1 | 0.57 (0.72) ✗ | -80.9 % (-83.2 %) | ok | 1.38 (1.36) ✓ | -79.6 % (-84.9 %) | 103.7 % (255.8 %) | 0.75 (0.93) ✗ | -30.2 % (-53.0 %) | no |
| N1 L=2 | 1.12 (0.70) ✓ | -62.3 % (-83.2 %) | ok | 1.92 (1.40) ✓ | -77.9 % (-84.9 %) | 72.4 % (255.8 %) | 0.60 (0.93) ✗ | -39.2 % (-53.0 %) | no |
| N1 L=4 | 1.22 (0.79) ✓ | -73.0 % (-83.2 %) | ok | 1.79 (1.50) ✓ | -70.3 % (-84.9 %) | 312.4 % (255.8 %) | 1.24 (0.93) ✓ | -32.5 % (-53.0 %) | **sí** |
| N2 n=5 | 0.73 (0.73) ✓ | -70.2 % (-83.2 %) | **falla x2** | 1.80 (1.33) ✓ | -70.7 % (-84.9 %) | 10.6 % (255.8 %) | 0.24 (0.93) ✗ | -57.4 % (-53.0 %) | no |
| N2 n=10 | 0.74 (0.72) ✓ | -72.8 % (-83.2 %) | **falla x2** | 1.91 (1.36) ✓ | -70.1 % (-84.9 %) | 75.2 % (255.8 %) | 0.61 (0.93) ✗ | -37.6 % (-53.0 %) | no |
| N2 n=20 | 0.98 (0.72) ✓ | -68.3 % (-83.2 %) | ok | 1.88 (1.41) ✓ | -72.3 % (-84.9 %) | 106.5 % (255.8 %) | 0.73 (0.93) ✗ | -33.8 % (-53.0 %) | no |
| N3 n=50 | 0.92 (0.72) ✓ | -73.2 % (-83.2 %) | ok | 1.75 (1.53) ✓ | -70.3 % (-84.9 %) | 155.9 % (255.8 %) | 0.89 (0.93) ✗ | -39.4 % (-53.0 %) | no |
| N3 n=150 | 0.36 (0.44) ✗ | -75.8 % (-76.6 %) | ok | 1.63 (1.56) ✓ | -75.1 % (-84.9 %) | 57.4 % (255.8 %) | 0.50 (0.93) ✗ | -54.5 % (-53.0 %) | no |
| N3 n=200 | 0.70 (0.47) ✓ | -53.1 % (-76.6 %) | ok | 1.68 (1.69) ✗ | -71.0 % (-84.9 %) | 153.8 % (255.8 %) | 0.80 (0.93) ✗ | -49.9 % (-53.0 %) | no |
| N4 x=10% | 1.10 (0.67) ✓ | -24.9 % (-76.6 %) | ok | 1.87 (1.54) ✓ | -40.6 % (-84.9 %) | 52.5 % (255.8 %) | 0.55 (0.93) ✗ | -43.5 % (-53.0 %) | no |
| N4 x=20% | 0.89 (0.67) ✓ | -40.5 % (-76.6 %) | ok | 1.99 (1.54) ✓ | -55.4 % (-84.9 %) | 90.5 % (255.8 %) | 0.66 (0.93) ✗ | -39.2 % (-53.0 %) | no |

✓ / ✗ = aprueba o no el criterio v2 en esa época.

## Superficie de parámetros: TRAIN frente a TEST

| Estrategia | Variantes | Spearman Sharpe TRAIN-TEST | Sharpe >= B&H en TRAIN / otra / TEST |
|---|---|---|---|
| N1 | 3 | 0.50 | 2 de 3 / 3 de 3 / 1 de 3 |
| N2 | 3 | 1.00 | 3 de 3 / 3 de 3 / 0 de 3 |
| N3 | 3 | 1.00 | 2 de 3 / 2 de 3 / 0 de 3 |
| N4 | 2 | -1.00 | 2 de 2 / 2 de 2 / 0 de 2 |

Spearman >= 0,5: orden estable; < 0: ruido. Con 2 o 3 variantes la medida es muy pobre.

## Regímenes de mercado (variantes conservadas)

Rentabilidad compuesta en los meses de cada régimen; entre paréntesis, Buy & Hold.

| Variante | Época | alcista | bajista | lateral | vol. alta | vol. baja |
|---|---|---|---|---|---|---|
| N1 L=4 | TRAIN | 13 028.2 % (52 442.6 %) | -72.7 % (-98.4 %) | -56.8 % (-55.0 %) | 772.6 % (65.5 %) | 77.2 % (132.6 %) |
| N1 L=4 | otra | 166 094.3 % (494 379.0 %) | -69.6 % (-98.3 %) | -44.6 % (-1.3 %) | 2 540.6 % (396.3 %) | 961.7 % (1 537.6 %) |
| N1 L=4 | TEST | 580.5 % (1 292.5 %) | -17.3 % (-76.3 %) | -26.7 % (8.0 %) | 185.2 % (104.5 %) | 44.6 % (74.0 %) |

## Veredicto (regla D28.4)

Se conservan, como EXPERIMENTALES hasta superar el paper trading en vivo: N1 L=4.

## Diagnósticos de N1 L=4 en TEST (no son variantes nuevas; no entran en el registro)
Una sola variante de 11 supera las tres épocas. Para comprobar que no es casualidad del calendario o un error:

| Prueba | Sharpe | Drawdown máx. |
|---|---|---|
| Buy & Hold | 0,93 | -53,0 % |
| N1 L=4 tal cual (decide el domingo) | 1,24 | -32,5 % |
| Con un día más de retraso | 1,03 | -41,8 % |
| Con costes x2 | 1,18 | -32,9 % |
| Decidiendo el lunes / martes / miércoles | 0,95 / 0,92 / 1,01 | -34,0 % / -32,5 % / -38,0 % |
| Decidiendo el jueves / viernes / sábado | 1,12 / 1,13 / 0,96 | -36,3 % / -26,7 % / -32,6 % |

**Lectura honesta:**
- No hay indicios de filtración: el retraso extra la empeora un poco, pero no la hunde.
- El domingo resulta ser el mejor día de la semana; con otros días el Sharpe baja a 0,92-1,13. Parte del 1,24 es suerte.
  Aun así, con cualquier día la caída máxima es mucho menor que la de Buy & Hold, y con 6 de 7 días el Sharpe es igual o mayor.
- Es 1 de 11 variantes, elegida sabiendo cómo fue TEST: puede ser suerte. Por eso queda EXPERIMENTAL hasta el paper trading en vivo.
- En TEST pierde mucho menos en meses bajistas (-17 % frente a -76 %), pero también pierde en meses laterales (-27 % frente a +8 %).
