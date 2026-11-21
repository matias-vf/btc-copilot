# Costes de operativa (BTC/USDT spot, Binance)

Consultado el 2026-11-21. El código está en `copilot/costes.py`.

| Concepto | Valor por lado | Fuente / razonamiento |
|---|---|---|
| Comisión | 0,100 % | Página oficial de comisiones de Binance (binance.com/en/fee/trading): usuario normal (menos de 1 M USD al mes), 0,100 % maker y 0,100 % taker. Con BNB sería 0,075 %, pero **no se asume** tener BNB. Para 2017-2022 se asume la misma tarifa base de usuario normal. |
| Medio spread | 0,01 % | **Estimación**, no medida. Hoy el spread de BTCUSDT en Binance suele ser de un tick (0,01 USDT, una fracción minúscula del precio). Se usa un valor mucho mayor porque en 2017-2018 el libro era más fino y la apertura de las 00:00 UTC puede ser más agitada. |
| Slippage | 0,05 % | **Estimación**, no medida: orden a mercado al inicio de la vela diaria. Para 100 USD de capital simulado es conservador; para importes grandes no lo sería. |
| Funding | 0 | No aplica: solo spot, sin perpetuos ni préstamo. Cuando se registre la variante con perpetuos (cortos) habrá que añadir el funding real cada 8 horas. |
| Conversión | 0 | No aplica: la cuenta simulada está en USDT. La diferencia USDT/USD no se modela (ver `data/FUENTES.md`). |
| **Total** | **0,16 % por lado (0,32 % ida y vuelta)** | |

## Spot frente a futuros
Spot: se compra BTC de verdad, sin apalancamiento ni funding, solo comisión + spread + slippage.
Perpetuos: comisiones más bajas (0,02 % maker / 0,05 % taker según Binance) pero con funding, riesgo de liquidación y
precio de marca distinto del spot. Este proyecto usa solo spot hasta que se registre una variante de perpetuos.

## Otros exchanges
Los costes de BTC no son iguales en todas partes. Si se usa otra fuente (por ejemplo, Bitstamp en el Prompt 5), sus
resultados se calculan con este mismo modelo para comparar reglas, y se avisa de que las comisiones reales de Bitstamp
en 2011-2016 eran más altas (del orden de 0,25 % a 0,5 %).

## Costes x2 y x3
Si una variante ejecuta más de una orden por semana de media (`ejecuciones_por_semana > 1`), sus resultados se
muestran también con todos los costes multiplicados por 2 y por 3 (`Costes.x(2)`, `Costes.x(3)`).
