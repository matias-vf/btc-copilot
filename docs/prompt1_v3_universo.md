# Prompt 1 (tercera búsqueda): universo de 1000 estrategias

Fecha: 2026-11-21. Pedido por el usuario. Método fijado antes de generar nada: `docs/decisiones.md`, D36 y D37.
Temporalidad: **velas diarias**; las reglas deciden cada día o cada semana (motivo en D36).
Las 1000 variantes salen de `copilot/universo.py` (familias y rejillas de parámetros convencionales, sin ajustar a los datos).

## Avisos

- **No existen 1000 ideas distintas publicadas.** Son 31 familias publicadas con sus parámetros habituales. Muchas
  variantes se parecen mucho entre sí.
- **Probar 1000 reglas hace casi seguro que alguna salga bien por suerte.** Por eso se exige el Sharpe deflactado
  (D36), que corrige por el número de pruebas. Es probable que muy pocas, o ninguna, lo superen.
- TEST (2023-2026) ya se ha visto; la prueba limpia sigue siendo el paper trading en vivo.
- N1 L=4 y N1D se quedan en el copiloto pase lo que pase (D37).

## Familias

| Familia | Nombre | Tipo | Variantes | Por qué podría funcionar | Quién pierde | Publicación | Criterios (antigua y publicada / mecanismo / BTC) |
|---|---|---|---|---|---|---|---|
| F01 | Precio sobre media móvil (con banda) | Tendencia | 48 | Las tendencias persisten: el precio tarda en incorporar la información. | Quien vende en las caídas tarde o compra contra la tendencia. | Brock, Lakonishok y LeBaron (1992); Faber (2007) | ✔ / ✔ / ✔ |
| F02 | Cruce de medias móviles (con banda) | Tendencia | 96 | Cruce de una media corta sobre una larga = cambio de tendencia. | Quien sale en la primera corrección. | Brock, Lakonishok y LeBaron (1992) | ✔ / ✔ / ✔ |
| F03 | Cruce de medias exponenciales | Tendencia | 25 | Como F02, con medias que pesan más lo reciente. | Igual que F02. | Appel (1979); Murphy (1999) | ✔ / ✔ / ✔ |
| F04 | Momentum de serie temporal diario (con umbral) | Tendencia | 80 | Lo que ha subido en las últimas semanas o meses tiende a seguir (momentum). | Los que apuestan a la vuelta atrás. | Moskowitz, Ooi y Pedersen (2012); Liu y Tsyvinski (2021) | ✔ / ✔ / ✔ |
| F05 | Momentum semanal (decide el domingo) | Tendencia | 16 | Momentum semanal específico de BTC, ligado a la atención de los inversores. | Quien vende tras una buena semana. | Liu y Tsyvinski (2021) | ✔ / ✔ / ✔ |
| F06 | Regla de filtro (x % arriba entra, y % abajo sale) | Tendencia | 100 | Comprar tras una subida del x % y vender tras una caída del y %. | Quien opera contra los movimientos fuertes. | Alexander (1961); Fama y Blume (1966) | ✔ / ✔ / ✔ |
| F07 | Canal de Donchian (máximos y mínimos) | Ruptura | 40 | Romper el máximo de N días indica tendencia nueva. | Quien vende en las resistencias. | Donchian (1960); reglas de las Tortugas | ✔ / ✔ / ✔ |
| F08 | Ruptura del rango con cierres (con banda) | Ruptura | 30 | Ruptura de soporte y resistencia con cierres. | Igual que F07. | Brock, Lakonishok y LeBaron (1992); Gerritsen y otros (2020) | ✔ / ✔ / ✔ |
| F09 | Ruptura del rango con tenencia fija | Ruptura | 50 | Ruptura con salida tras un número fijo de días. | Igual que F07. | Brock, Lakonishok y LeBaron (1992) | ✔ / ✔ / ✔ |
| F10 | Reversión con RSI | Reversión | 96 | Tras caídas bruscas de corto plazo el precio suele rebotar. | Quien vende por pánico. | Wilder (1978); Connors y Alvarez (2008) | ✔ / ✔ / ✔ |
| F11 | Reversión con bandas de Bollinger | Reversión | 32 | Precio muy por debajo de su media: suele volver. | Igual que F10. | Bollinger (2001) | ✔ / ✔ / ✔ |
| F12 | Ruptura de bandas de Bollinger | Ruptura | 16 | Salir de la banda superior indica fuerza (ruptura). | Quien vende en las subidas. | Bollinger (2001) | ✔ / ✔ / ✔ |
| F13 | Reversión a corto plazo tras una caída | Reversión | 100 | Reversión de corto plazo tras una caída fuerte. | Quien vende con prisa y necesita liquidez. | Jegadeesh (1990); Lehmann (1990) | ✔ / ✔ / ✔ |
| F14 | Cerca del máximo de N días | Ruptura | 36 | Anclaje al máximo de un año: se reacciona tarde cuando el precio se acerca a él. | Quien vende cerca del máximo. | George y Hwang (2004) | ✔ / ✔ / ✔ |
| F15 | MACD | Tendencia | 12 | Cambio en la pendiente de las medias (aceleración de la tendencia). | Quien llega tarde a la tendencia. | Appel (1979) | ✔ / ✔ / ✔ |
| F16 | Volumen en balance (OBV) | Volumen | 12 | El volumen se adelanta al precio. | Quien ignora el volumen. | Granville (1963) | ✔ / ✔ / ✔ |
| F17 | Oscilador estocástico | Reversión | 24 | Cierre en la parte baja del rango reciente: rebote probable. | Quien vende en el mínimo del rango. | Lane (1984) | ✔ / ✔ / ✔ |
| F18 | ADX con DI+ > DI- | Tendencia | 16 | Solo seguir la tendencia cuando es fuerte. | Quien opera tendencias débiles. | Wilder (1978) | ✔ / ✔ / ✔ |
| F19 | Canal de Keltner (ATR) | Ruptura | 16 | Ruptura medida en múltiplos de la volatilidad. | Igual que F07. | Keltner (1960) | ✔ / ✔ / ✔ |
| F20 | Volatilidad objetivo sobre una regla base | Tamaño de posición | 36 | Reducir la exposición cuando la volatilidad sube mejora la relación riesgo-rentabilidad. | Quien mantiene el mismo tamaño con mucha volatilidad. | Moreira y Muir (2017); Harvey y otros (2018) | ✔ / ✔ / ✔ |
| F21 | Estacionalidad de calendario | Estacionalidad | 25 | Efectos de calendario (día de la semana, mes, cambio de mes). | Sin un perdedor claro: mecanismo DÉBIL en BTC. | Caporale y Plastun (2019); Baur, Cahill, Godfrey y Liu (2019) | ✔ / débil / ✔ |
| F22 | SAR parabólico | Tendencia | 12 | Stop que sigue a la tendencia y se acelera. | Quien llega tarde. | Wilder (1978) | ✔ / ✔ / ✔ |
| F23 | Ichimoku | Tendencia | 8 | Equilibrio entre medias de máximos y mínimos. | Quien opera contra la tendencia. | Hosoda (1969) | ✔ / ✔ / ✔ |
| F24 | Williams %R | Reversión | 12 | Como F17, otra medida de sobreventa. | Igual que F17. | Williams (1973) | ✔ / ✔ / ✔ |
| F25 | Momentum y media a la vez | Tendencia | 12 | Exigir momentum y precio sobre la media a la vez. | Igual que F04. | Antonacci (2014); Faber (2007) | ✔ / ✔ / ✔ |
| F26 | Ruptura con volumen alto | Ruptura | 9 | Ruptura confirmada por volumen alto. | Quien vende en rupturas con volumen. | Granville (1963); Brock y otros (1992) | ✔ / ✔ / ✔ |
| F27 | Tendencia con stop de ATR | Tendencia | 16 | Tendencia con salida por stop de volatilidad. | Quien no corta pérdidas. | Wilder (1978); LeBeau y Lucas (1992) | ✔ / ✔ / ✔ |
| F28 | Momentum solo con volatilidad baja | Tendencia | 6 | El momentum falla en los momentos de volatilidad extrema (crashes). | Quien sigue la tendencia en pánico. | Barroso y Santa-Clara (2015) | ✔ / ✔ / ✔ |
| F29 | Media adaptativa de Kaufman (KAMA) | Tendencia | 4 | Media que se adapta a lo «ruidoso» que está el mercado. | Quien opera ruido. | Kaufman (1995) | ✔ / ✔ / ✔ |
| F30 | Precio sobre media ponderada (con banda) | Tendencia | 10 | Como F01, con media ponderada. | Igual que F01. | Murphy (1999) | ✔ / ✔ / ✔ |
| F31 | Caja de Darvas | Ruptura | 5 | Romper la «caja» de los últimos días. | Igual que F07. | Darvas (1960); Cohen (2020) | ✔ / ✔ / ✔ |

## Reparto

| Tipo | Variantes |
|---|---|
| Tendencia | 461 |
| Reversión | 264 |
| Ruptura | 202 |
| Tamaño de posición | 36 |
| Estacionalidad | 25 |
| Volumen | 12 |

Total: **1000 variantes** en 31 familias.

Activo: solo BTC/USDT spot. Funcionan peor en mercados laterales (seguimiento de tendencia y rupturas) o en tendencias
largas sin rebotes (reversión). La estacionalidad (F21) se incluye para completar el universo, aunque su mecanismo en
BTC es débil.

