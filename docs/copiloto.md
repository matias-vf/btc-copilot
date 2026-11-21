# El copiloto (Prompt 9)

Solo analiza y simula. No hay ningún cliente de exchange en el código, ni claves, ni forma de enviar una orden real.

## Qué hace cada día (justo después del cierre de la vela diaria, 00:05 UTC)
1. **Datos:** comprueba que las velas están completas, al día, sin duplicados, coherentes y con volumen. Si no, no da señales.
2. **Orden de ayer:** si ayer hubo COMPRA o VENTA, la simula en la apertura de hoy con comisión (0,10 %), medio spread
   (0,01 %) y slippage (0,05 %). Funding: no aplica (spot, sin apalancamiento).
3. **Valoración:** valora la cuenta de 100 USD ficticios al cierre. Si pierde más de un 35 % desde su máximo, parada de emergencia.
4. **Vigilancia (reglas v2):** estado de cada estrategia (activa o suspendida), alertas y parada de emergencia si la
   cartera supera su peor drawdown del backtest.
5. **Señal:** ejecuta las reglas registradas de B1 20/10, B1 55/20 y T1 SMA 100, las combina con los pesos inversos a la
   volatilidad de la cartera C1 y aplica el límite del 25 % de exposición. Resultado: **COMPRA, VENTA, MANTENER o NO OPERAR**.
6. **Seguimiento:** 1, 7 y 30 días después de cada COMPRA o VENTA anota cómo evolucionó el precio y el resultado hipotético neto de costes.

## Cómo resuelve señales contradictorias
No hay contradicciones sin resolver: cada estrategia vota 0 (liquidez) o 1 (comprada) y la decisión es la suma ponderada.
Si B1 sale y T1 entra el mismo día, solo se ejecuta la diferencia neta. La ficha explica qué hizo cada estrategia.

## Límites de seguridad
| Límite | Valor |
|---|---|
| Exposición máxima a BTC | 25 % del capital |
| Posiciones simultáneas | 3 como máximo (una por estrategia) |
| Pérdida máxima de la cuenta | 35 % desde su máximo: parada de emergencia |
| Parada manual (kill switch) | `python -m copilot parar "motivo"`; se cierra todo en la siguiente apertura |
| Reanudar | solo tú: `python -m copilot reanudar "motivo"` |
| Estrategia suspendida | sin entradas nuevas; las salidas siempre se permiten |
| Datos con problemas | ningún cambio ese día; una orden pendiente se cancela |

## Registros (solo añadir, con hash encadenado)
- `registros/senales.jsonl`: cada señal diaria completa y su seguimiento.
- `registros/paper.jsonl`: inicio, órdenes simuladas, valoraciones diarias, paradas, reanudaciones y errores.
- `registros/vigilancia.jsonl`: alertas, suspensiones, reactivaciones y estado diario.
La cuenta se reconstruye siempre desde su registro, así que cada cifra se puede comprobar.

## Funcionamiento continuo
`python -m copilot en-marcha` ejecuta un ciclo al día mientras el ordenador esté encendido. Un error se anota en el
registro y se reintenta a los 10 minutos. **Hoy está bloqueado:** los precios actuales son posteriores al 01/01/2023 (TEST).

## Lo que no hace
- No da un porcentaje de confianza: no hay datos para calibrarlo como probabilidad.
- No usa funding, open interest, liquidaciones, noticias ni otros activos (no hay fuentes verificables y gratuitas conectadas).
- No ve la pantalla por sí solo: ver `docs/pantalla_compartida.md`.
