# N1D: N1 con revisión diaria (D34)

Generado por `python -m copilot n1d`. Reglas fijadas antes de ejecutar: `docs/decisiones.md`, D34.
Criterio v2: drawdown menor que Buy & Hold y Sharpe igual o mayor, en la misma ventana.

| Época | Operaciones | Órdenes/semana | Rentabilidad (B&H) | Sharpe (B&H) | Drawdown máx. (B&H) | Aprueba |
|---|---|---|---|---|---|---|
| TRAIN | 77 | 0.56 | 922.2 % (417.9 %) | 1.08 (0.79) | -76.3 % (-83.2 %) | **sí** |
| otra época | 70 | 0.50 | 42 512.4 % (18 706.1 %) | 1.93 (1.50) | -70.3 % (-84.9 %) | **sí** |
| TEST | 63 | 0.62 | 265.3 % (255.8 %) | 1.15 (0.93) | -36.3 % (-53.0 %) | **sí** |

Costes x2 en TRAIN: no hace falta (como mucho una orden por semana).

## Veredicto (D34)

**N1D aprueba todo**: entra en el copiloto como EXPERIMENTAL junto a N1 L=4 y podrá operar cualquier día (paper trading).

