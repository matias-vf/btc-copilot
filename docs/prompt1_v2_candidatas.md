# Prompt 1 (segunda búsqueda): estrategias candidatas para BTC

Fecha: 2026-11-21. Motivo: ninguna estrategia del copiloto superó TEST (D22) y el usuario pidió repetir el proceso.
**Estado: propuesta.** Nada está registrado ni probado. Las estrategias ya probadas (T1, T2, B1, M1, P1) no se repiten.

## Aviso de método (importante)
- **TEST (2023-2026) ya está visto.** Ya sé, por ejemplo, que fue un periodo muy alcista en el que el seguimiento de
  tendencia lento ganó menos que Buy & Hold. Cualquier estrategia nueva que elija sabiendo eso estará algo sesgada,
  así que TEST ya no puede ser una prueba limpia. La única prueba limpia que queda son **datos futuros**: el paper
  trading en vivo a partir de hoy.
- **Cuantas más estrategias se prueban, más probable es que alguna "apruebe" por suerte.** Ya hay 90 experimentos en el
  registro. Una búsqueda "intensiva" debe ser amplia en ideas, pero corta en variantes.
- **El criterio de rentabilidad es muy exigente.** Una estrategia que solo puede estar comprada o en liquidez, sin
  apalancamiento, solo gana a Buy & Hold en rentabilidad si se libra de las caídas más de lo que se pierde de las
  subidas. En mercados muy alcistas eso casi nunca pasa. En TEST no lo consiguió ninguna regla probada.

## Fuentes revisadas
- Base científica (arXiv, PubMed y otras): estudios de medias móviles, rupturas, momentum y estacionalidad intradía en BTC.
- Web, con la referencia verificada: Liu y Tsyvinski (2021), *Review of Financial Studies* 34(6), 2689-2727; Detzel,
  Liu, Strauss, Zhou y Zhu (2021), *Financial Management*, doi 10.1111/fima.12310; Gerritsen, Bouri, Ramezanifar y
  Roubaud (2020), *Finance Research Letters* 34, doi 10.1016/j.frl.2019.08.011.
- Citadas de memoria (verificar antes de registrar): George y Hwang (2004), *Journal of Finance*; Antonacci (2014),
  *Dual Momentum Investing* (libro); Shanaev, Vasenin y Stepanov (2023), *Heliyon* (verificada en la base científica).

Criterios del Prompt 1: (1) antigua y publicada, (2) razón económica, (3) adecuada para BTC (incluye costes realistas).

## Seguimiento de tendencia / momentum

### N1. Momentum semanal de BTC (Liu y Tsyvinski 2021)
- **Regla:** al cierre del domingo (00:00 UTC del lunes), si la rentabilidad de las últimas L semanas es positiva,
  comprado toda la semana siguiente; si no, liquidez.
- **Por qué podría ganar:** el artículo encuentra que la rentabilidad de esta semana predice la de las 1-4 semanas
  siguientes en BTC (momentum de serie temporal a corto plazo), ligado a la atención de los inversores.
- **Quién pierde:** quien vende tras una buena semana esperando una corrección. Sigue pasando por anclaje y aversión a la pérdida.
- **Activos:** BTC y Ripple en el artículo; menos en Ethereum. Es distinta de T2 (90-365 días): horizonte de semanas.
- **Ojo:** en el artículo, incluso las peores semanas siguen teniendo rentabilidad media positiva; salir del mercado
  esas semanas puede costar rentabilidad frente a Buy & Hold.
- **Criterios:** 1 ✔ · 2 ✔ · 3 ✔ (opera como mucho una vez por semana). **Candidata.**
- **Parámetros:** L = 1, 2 o 4 semanas (3 variantes).

### N2. Medias móviles cortas (Detzel y otros 2021)
- **Regla:** al cierre diario, comprado si el cierre está por encima de su media de n días; si no, liquidez.
- **Por qué podría ganar:** el artículo argumenta que, en activos con fundamentales difíciles de valorar como BTC, los
  inversores aprenden del precio y las medias móviles cortas recogen esa información; encuentra predictibilidad en BTC.
- **Quién pierde:** quien opera contra la tendencia de corto plazo. Persiste porque el valor de BTC es incierto.
- **Activos:** BTC y acciones difíciles de valorar; peor en activos con valor fundamental claro.
- **Ojo:** con n corto opera mucho; se mostrarán costes x2 y x3.
- **Criterios:** 1 ✔ · 2 ✔ · 3 ✔ (con aviso de costes). **Candidata.**
- **Parámetros:** n = 5, 10 y 20 días (3 variantes). T1 ya probó 100-200 días.

## Rupturas

### N3. Ruptura del rango (soporte/resistencia simétrico; Brock y otros 1992, Gerritsen y otros 2020)
- **Regla:** compra si el cierre supera el máximo de los n cierres previos; vende si cae por debajo del mínimo de los n previos.
- **Por qué podría ganar:** es la regla que Gerritsen y otros encuentran mejor en BTC (más Sharpe que Buy & Hold).
- **Quién pierde:** quien vende en las resistencias. Persiste por anclaje a máximos recientes.
- **Ojo:** se parece mucho a B1 (Donchian), que no superó TEST. Usa cierres (no máximos y mínimos) y la misma n para
  entrar y salir. Aporta poca diversificación.
- **Criterios:** 1 ✔ · 2 ✔ · 3 ✔. **Candidata, con baja prioridad por parecerse a B1.**
- **Parámetros:** n = 50, 150, 200 (los del artículo; 3 variantes).

### N4. Cerca del máximo de 52 semanas (George y Hwang 2004)
- **Regla:** comprado mientras el cierre esté a menos de un x % del máximo de los últimos 365 días; si se aleja más, liquidez.
- **Por qué podría ganar:** los inversores se anclan al máximo de un año y reaccionan tarde cuando el precio se acerca a él.
- **Quién pierde:** quien vende cerca del máximo "porque ya está caro".
- **Activos:** probado en acciones; en BTC la evidencia publicada es escasa.
- **Criterios:** 1 ✔ · 2 ✔ · 3 dudosa. **Candidata EXPERIMENTAL.**
- **Parámetros:** x = 10 % y 20 % (2 variantes).

## Dimensionamiento / asignación

### N5. Momentum dual con rentabilidad del efectivo (Antonacci 2014; Moskowitz, Ooi y Pedersen 2012)
- **Regla:** comprado si la rentabilidad de 12 meses de BTC supera a la del efectivo (letras del Tesoro de EE. UU.); si no, efectivo.
- **Por qué podría ganar:** en los años con tipos altos (2023-2025, en torno al 4-5 %), estar en liquidez no es rentabilidad 0.
- **Ojo:** el proyecto supone hoy que la liquidez en USDT rinde un 0 %. Para esta estrategia habría que modelar una
  rentabilidad del efectivo, y eso **cambia una decisión tuya** (y beneficiaría también a las estrategias antiguas).
- **Criterios:** 1 ✔ · 2 ✔ · 3 depende de esa decisión. **Solo si apruebas modelar la rentabilidad del efectivo.**
- **Parámetros:** 12 meses (1 variante).

## Descartadas

| Idea | Fuente | Motivo |
|---|---|---|
| Momentum diario (1-6 días) | Liu y Tsyvinski 2021 | Operaría casi a diario: los costes (0,32 % ida y vuelta) se comerían el efecto. |
| Ciclo del halving | Divulgación; evidencia académica escasa | Solo 4 ciclos: imposible validarlo con estadística. Además, ya hemos visto el ciclo de 2024 en TEST. |
| Hora del día / sesiones | Hansen, Kim y Kimbrough 2021; Wątorek y otros 2023 | Los patrones son de volatilidad y volumen, no de rentabilidad. Exigiría velas horarias (cambia tu decisión D1). |
| Efecto "cambio de vela" de 15 minutos | Shanaev y otros 2023 | Alta frecuencia: 0,58 pb por minuto frente a un 0,10 % de comisión. Solo aparece desde 2020. |
| Lunes / fin de semana / festivos | Cohen 2020; Kunimoto y Kakamu 2021 | Igual que S1 y S2: sin mecanismo claro y con costes semanales. |
| Atención de los inversores (Google Trends) | Liu y Tsyvinski 2021 | No hay una fuente de datos gratuita y fiable dentro de la política del proyecto. |
| Volatilidad como señal | Liu y Tsyvinski 2021 | El propio artículo encuentra que la volatilidad no predice la rentabilidad de BTC. |
| Aprendizaje automático | Varios | Excluido por el maestro. |

## Resumen
- **Candidatas:** N1 (3 variantes), N2 (3), N3 (3, prioridad baja), N4 (2, experimental). Total: 11 variantes.
- **Condicional:** N5 (1), solo si se decide modelar la rentabilidad del efectivo.
