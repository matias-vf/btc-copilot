# Decisiones

Solo se añaden decisiones nuevas al final; las anteriores no se editan.

## D1. 2026-11-21. Mercado y ejecución
BTC/USDT spot de Binance, solo comprado o liquidez. Señal con el cierre de la vela diaria (00:00 UTC), ejecución en la
apertura de la vela siguiente. Los cortos con perpetuos quedan para una variante posterior registrada.

## D2. 2026-11-21. Ventanas de datos
- TRAIN: 2017-08-17 a 2022-12-31. El maestro dice "desde 2017"; Binance empieza el 2017-08-17.
- TEST: desde 2023-01-01. Bloqueado en código hasta «UNLOCK».
- Otra época (Prompt 5): Bitstamp BTC/USD 2011-08-18 a 2016-12-31 (la API no tiene datos antes de 2011-08-18).
- Pendiente para el Prompt 3: la señal del 2022-12-31 se ejecutaría en la apertura del 2023-01-01, que es TEST. El motor
  deberá cerrar o valorar las posiciones con el último cierre de TRAIN, sin leer la vela del 2023-01-01.

## D3. 2026-11-21. Criterios de aceptación (versión 1), fijados antes de ver resultados
En TRAIN, neto de costes, la estrategia debe cumplir las tres:
1. Rentabilidad total > Buy & Hold de BTC.
2. |Drawdown máximo| < |drawdown máximo de Buy & Hold|.
3. Sharpe >= Sharpe de Buy & Hold (rentabilidades diarias, 365 días al año, tipo libre de riesgo 0). Criterio
   secundario elegido por el usuario.
Si opera más de una vez por semana se muestran también resultados con costes x2 y x3.

## D4. 2026-11-21. Registros de solo-añadir
JSON Lines con cadena de hashes SHA-256 (`copilot/registro.py`). Ancla externa: Git. `registrar_experimento` rechaza
estrategias no registradas o descartadas, y variantes que no estén en `configuraciones_permitidas`.

## D5. 2026-11-21. Recuento de variantes registradas
T1: 4 · T2: 3 · B1: 2 · M1: 2 (experimental) · P1: 20 (5 bases x 2 sigma objetivo x 2 ventanas). Total: 31.
Cuantas más variantes se prueban, más probable es que alguna "gane" por azar; el contador lo deja a la vista.

## D6. 2026-11-21. Paquete «Day Trader skill» como referencia
El usuario pidió usarlo. Está hecho para acciones de EE. UU. en intradía (horario NYSE, velas de 1 y 5 minutos de Yahoo),
así que no se ejecuta sobre BTC: solo se toman ideas, adaptadas a BTC diario. No cambia D1 a D5.

| Herramienta | Idea que se toma | Dónde entra |
|---|---|---|
| trader-risk | Una puerta PASS/BLOCK con el motivo, antes de cada operación simulada. Salir nunca se bloquea. | Prompt 8 (paper trading): bloquear si la estrategia no está validada, la señal ha caducado, los datos están desfasados o la exposición supera 1. |
| trader-exit | Escribir las condiciones de invalidación ANTES de la entrada. | Prompt 7.3: cada señal guarda su invalidación (la regla de salida registrada) y su riesgo estimado. |
| trader-timemachine | Simular muchos caminos con los propios datos y contar cada vez que la regla se activó en el pasado. | Prompt 5 y 7.4: resultado histórico por señal. Una simulación nueva es un experimento: se registra antes. |
| trader-budget | Tamaño de posición según la pérdida máxima por operación. | No se adopta: cambiaría las reglas registradas. Solo podría entrar como variante nueva registrada. |
| trader-broker | Envío de órdenes a un broker. | **No se adopta. Nunca.** El copiloto no envía órdenes reales. |
| trader-scanner, trader-news, trader-entry, trader-alerts, trader-analyst, trader-pelosi | Acciones de EE. UU. | No aplican a BTC. |

## D7. 2026-11-21. Motor de backtesting (Prompt 3)
- **Causalidad impuesta por el motor:** la estrategia solo recibe una copia de las velas hasta t. La decisión del cierre
  de t se ejecuta en la apertura de t+1. La última vela de TRAIN (2022-12-31) no genera ninguna orden, así que nunca se
  necesita la vela del 2023-01-01 (resuelve lo pendiente de D2).
- **Final del periodo:** la posición abierta se valora como si se vendiera al último cierre, restando el coste de salida.
  Igual para Buy & Hold y para todas las estrategias.
- **Compras:** el coste sale del efectivo; nunca hay efectivo negativo (sin apalancamiento oculto).
- **Solo se opera cuando cambia la decisión.** Si la exposición se desvía por el movimiento del precio, no se reajusta
  cada día (P1 reajusta solo los lunes, como está registrado).
- **Métricas:** rentabilidad total, CAGR (365 días), Sharpe con rentabilidades diarias del capital (365, tipo libre de
  riesgo 0, incluye los días en liquidez), drawdown máximo, operaciones (entradas desde liquidez) y ejecuciones (todas
  las órdenes, incluidos los reajustes de P1).
- **Datos insuficientes:** si un indicador no se puede calcular todavía (por ejemplo, SMA 200 en los primeros 199 días),
  la regla devuelve "no operar". Esos días cuentan en el periodo.
- **Comprobación de anticipación:** `copilot/anticipacion.py`. En cuatro cortes se alteran al azar todas las velas
  posteriores y se reconstruye la estrategia con esos datos alterados; las señales y el capital hasta el corte deben
  ser idénticos. Una estrategia tramposa de prueba es detectada. Ejecutada en TRAIN: 32 de 32 variantes sin anticipación.
- **Regla permanente de resultados extraordinarios:** `motor.alertas()` marca Sharpe > 2, CAGR más de 50 puntos por
  encima de Buy & Hold, o drawdown menor del 15 % con operaciones. Un resultado marcado se trata primero como posible
  error: se repite la comprobación de anticipación y se revisa el código antes de enseñarlo, y se muestra con el aviso.

## D8. 2026-11-21. Ejecución en TRAIN (Prompt 4)
Lote `prompt4-train-v1`: 31 variantes ejecutadas una sola vez y anotadas en `registros/experimentos.jsonl` (contador 1 a 31),
con el SHA-256 de los datos y el commit del código. La orden `train` se niega a repetir el mismo lote: repetirlo sería un
experimento nuevo con otro nombre. Aprueban los tres criterios en TRAIN 10 variantes: T1 SMA 100, T2 L=365, B1 20/10,
B1 55/20 y 6 de P1 (todas sobre T1 SMA 100 o SMA 150). Los criterios se evalúan con costes x1, como se fijó en D3.
Tabla y comprobaciones en `docs/resultados_train.md`.

## D9. 2026-11-21. Reglas del Prompt 5, fijadas ANTES de ejecutar nada en la otra época
**Qué se prueba.** Las estrategias con al menos una variante aprobada en TRAIN: T1, T2, B1 y P1. Se prueban TODAS sus
variantes (29), no solo las aprobadas. M1 no tiene ninguna variante aprobada: se descarta sin más pruebas.

**Otra época.** Bitstamp BTC/USD, 2011-08-18 a 2016-12-31, mismo motor. Costes x1 (modelo Binance) y x3 (0,48 % por lado,
cerca de las comisiones reales de Bitstamp en esos años). Cada ejecución se anota en el registro de experimentos
(lote `prompt5-otra-epoca-v1`). Criterios: los mismos tres de D3, contra Buy & Hold de Bitstamp en esa época, con costes x1.

**Regímenes de mercado** (solo para describir, se etiquetan a posteriori por meses naturales, en cada época):
- Alcista: el mes BTC sube más de un 10 %. Bajista: baja más de un 10 %. Lateral: entre -10 % y +10 %.
- Volatilidad alta / baja: volatilidad diaria anualizada del mes por encima / por debajo de la mediana de los meses de esa época.
- En cada régimen se muestra la rentabilidad compuesta de la estrategia y la de Buy & Hold en esos mismos meses.

**Sensibilidad.** Se enseña la tabla completa de variantes en las dos épocas.

**Veredicto por estrategia (provisional hasta TRAIN frente a TEST):**
- CONSERVAR si (a) al menos una variante aprobada en TRAIN también aprueba los tres criterios en la otra época, y
  (b) en cada época, al menos la mitad de sus variantes tienen Sharpe >= Sharpe de Buy & Hold (la superficie no es un
  pico aislado).
- Si no, DESCARTAR.

**TRAIN frente a TEST.** Necesita los datos de TEST. Se hará solo cuando el usuario escriba «UNLOCK». Medida: correlación
de rangos de Spearman entre el Sharpe de las variantes en TRAIN y en TEST, por estrategia. Superficie estable si es
>= 0,5; ruido si es < 0. Entre medias, dudosa.

## D10. 2026-11-21. Resultado del Prompt 5 (provisional)
Lote `prompt5-otra-epoca-v1`: 29 variantes de T1, T2, B1 y P1 en Bitstamp 2011-2016, anotadas en el registro (contador 32 a 60).
Aplicando D9 sin cambios: CONSERVAR (provisional) B1 y T1; DESCARTAR P1, T2 y M1. Seis alertas de "demasiado bueno"
revisadas sin indicios de filtración (`docs/robustez.md`, sección 5). La consistencia TRAIN frente a TEST queda pendiente
de «UNLOCK»; el veredicto de B1 y T1 no es definitivo hasta entonces.

## D11. 2026-11-21. Reglas del Prompt 6 (cartera), fijadas ANTES de ejecutar
El usuario decidió pasar al Prompt 6 sin abrir TEST. La cartera usa las estrategias conservadas provisionalmente
(B1 y T1), así que también es **provisional**.

**Componentes:** las variantes que aprobaron en TRAIN y en la otra época, sin elegir "la mejor":
- B1: Donchian 20/10 y Donchian 55/20, a partes iguales dentro del peso de B1.
- T1: SMA 100.

**Pesos:** inversos a la volatilidad, por estrategia (B1 y T1). Volatilidad = desviación típica de las rentabilidades
diarias de los últimos 90 días de cada estrategia (B1 = media diaria de sus dos variantes), calculada con el cierre del
último día del mes. Peso_i = (1/vol_i) / suma(1/vol). Con menos de 90 días de historia: pesos iguales.
Si una estrategia ha estado en liquidez los 90 días (vol = 0), su peso se reparte entre las demás; si todas, pesos iguales.
**Reequilibrio mensual** al cierre del último día del mes; sin ajustes por predicciones ni opiniones.
**Costes del reequilibrio:** solo la parte que cambia la exposición neta a BTC, al mismo 0,16 % por lado. Los costes de
cada estrategia ya están dentro de su propio resultado.

**Comparación:** CAGR, Sharpe y drawdown máximo frente a Buy & Hold en TRAIN y, como información, en la otra época.
Se registra como idea nueva C1 y cada ejecución como experimento (lote `prompt6-cartera-v1`).

## D12. 2026-11-21. Resultado del Prompt 6 (provisional)
Lote `prompt6-cartera-v1`: cartera C1 ejecutada en TRAIN y en la otra época (experimentos 61 y 62). Mejora a Buy & Hold en
CAGR, Sharpe y drawdown en las dos épocas, pero diversifica poco (correlaciones 0,78-0,89). Sigue siendo provisional
hasta TRAIN frente a TEST. Informe en `docs/cartera.md`.

## D13. 2026-11-21. Cambio de guion y reglas del Prompt 7 (riesgo), fijadas ANTES de ejecutar
El usuario envió nuevos Prompts 7 (riesgo y tamaño de posición), 8 (deterioro y reglas de parada) y 9 (copiloto).
Sustituyen a las Partes 7-9 del maestro y se harán en ese orden. El copiloto (antes "Parte 7") pasa al Prompt 9.

**Base:** la cartera C1 (D11) y sus componentes B1 20/10, B1 55/20 y T1 SMA 100. Se simula en TRAIN y en la otra época.
Se registra como idea R1 y cada simulación como experimento (lote `prompt7-riesgo-v1`).

**Configuraciones (11):**
1. Exposición fija de la cartera: 25 %, 50 %, 75 %, 100 %, y **hipotéticas** 150 % y 200 % (apalancadas).
   Apalancamiento: se paga funding de 0,01 % cada 8 horas (0,03 % al día, la tasa base de Binance) sobre la parte
   prestada, en los días con posición. Liquidación (el capital pasa a 0) si la caída desde el cierre anterior hasta el
   mínimo del día, multiplicada por el apalancamiento, llega al 99,5 %.
2. Riesgo por operación: en cada entrada, exposición del componente = min(1, r / d), con d = distancia desde el cierre
   hasta el nivel de salida de la propia regla (T1: SMA 100; B1: mínimo de las M últimas velas). r = 1 %, 2 %, 5 %.
   La exposición se mantiene hasta la salida.
3. Volatilidad objetivo de la cartera: exposición = min(1, objetivo / volatilidad de la cartera en 60 días), fijada cada
   domingo al cierre. Objetivo = 30 % y 45 % anual.

**Se mide:** CAGR, Sharpe, volatilidad anual, drawdown máximo, peor día, peor mes, exposición media, si se arruina, y por
operación: pérdida peor y cuántas pérdidas superan el riesgo previsto (por huecos, porque se sale en la apertura siguiente).
También el efecto de las operaciones correlacionadas (días con 0, 1, 2 o 3 componentes comprados y ratio de
diversificación) y la concentración (un solo activo; peso de B1).

**Límites fijados ahora (antes de ver resultados):**
- Exposición mínima 0 % y máxima 100 %. **Sin apalancamiento**, pase lo que pase en las simulaciones (D1).
- Pérdida máxima tolerada de la cartera: drawdown del 35 %.
- Como máximo 3 posiciones abiertas a la vez (una por componente), todas en BTC.

**Regla de elección:** son admisibles las configuraciones sin apalancamiento, sin ruina y con drawdown máximo de como
mucho el 35 % en las DOS épocas. Entre ellas, la de mayor Sharpe en TRAIN; si dos difieren en menos de 0,05, la de menor
exposición media. Si ninguna es admisible, la de menor drawdown en la peor época, y se dice que el 35 % no es alcanzable.

## D14. 2026-11-21. Resultado del Prompt 7 (provisional)
Lote `prompt7-riesgo-v1`: 11 configuraciones x 2 épocas (experimentos 63 a 84). Elegida por la regla de D13: exposición
fija del 25 % de C1. Apalancamiento: arruina en la otra época (2013-04-10, -69 % en un día); confirmado que no se usa.
La regla de riesgo por operación no controla a T1. La volatilidad objetivo del 30 % se queda fuera por 0,8 puntos de
drawdown en TRAIN; no se reajusta a posteriori. Límites del copiloto en `docs/riesgo.md`, sección 5.
Corrección técnica: las métricas ya no dividen por cero cuando el capital llega a 0 (ruina); no cambia ningún resultado anterior.

## D15. 2026-11-21. Reglas del Prompt 8 (deterioro y parada), fijadas ANTES de poner nada en marcha
**Qué se vigila cada día:** los tres componentes (B1 20/10, B1 55/20, T1 SMA 100) y la cartera C1 al 25 % de exposición.
**Referencia histórica:** solo TRAIN (backtest). Nunca se recalcula con datos nuevos.

**Reglas de SUSPENSIÓN (paran las señales nuevas):**
1. *Peor que el azar:* rentabilidad de los últimos 365 días por debajo de la mediana de 200 estrategias de entradas
   aleatorias con los mismos días en el mercado, el mismo número de entradas y los mismos costes (0,16 % por lado), en
   esos mismos 365 días. Si la estrategia no estuvo en el mercado ningún día de la ventana, no se compara.
2. *Drawdown:* drawdown desde el inicio de la vigilancia peor que el peor drawdown del backtest en TRAIN (B1 20/10
   -54,3 %, B1 55/20 -59,1 %, T1 -64,5 %). Para la cartera al 25 % (-17,4 %): se suspenden TODAS las señales (parada de emergencia).
3. *Datos:* no se generan señales ese día si falta una vela, hay duplicados, OHLC incoherente, la última vela tiene
   más de 26 horas, el cierre se mueve más de un 50 % en un día o la apertura se separa más de un 5 % del cierre anterior.
   Tampoco con menos de 400 velas de historia (indicadores y ventana de 365 días).

**ALERTAS (avisan, no paran):**
- Drawdown peor que el 75 % del peor del backtest.
- Rentabilidad de los últimos 180 días por debajo del percentil 5 de las rentabilidades de 180 días en TRAIN.
- Volatilidad de 30 días por encima del percentil 95 o por debajo del percentil 5 de TRAIN (cambio de mercado).
- Precio que cruza la SMA 200 (cambio de tendencia general).

**Después de una suspensión:** la estrategia no se borra. Se sigue calculando su resultado hipotético ("en la sombra")
para registrar qué habría pasado. No hay reactivación automática: solo con aprobación explícita del usuario, anotada en
el registro. Todo (alertas, suspensiones, reactivaciones, estado diario) va a `registros/vigilancia.jsonl`, de solo añadir.

**Prueba antes de usarlo en vivo:** se simula la vigilancia día a día en la otra época (Bitstamp 2013-2016), con la
referencia de TRAIN. Es una prueba del sistema de vigilancia, no de una estrategia nueva: no se anota como experimento.

## D16. 2026-11-21. Resultado del Prompt 8 (reglas de vigilancia v1)
Simulación en Bitstamp 2013-2016: la regla de drawdown funciona (parada de emergencia el 2013-04-11), pero la regla
"peor que la mediana aleatoria" suspende por ruido el primer día y, sin reactivación, deja el copiloto apagado mientras
las estrategias suspendidas ganan miles de por cien en la sombra. Falta exigir volumen > 0 en los datos. Las reglas v1
no se tocan; queda pendiente que el usuario decida una versión 2 antes del Prompt 9. Informe en `docs/vigilancia.md`.

## D17. 2026-11-21. Reglas de vigilancia versión 2 (aprobadas por el usuario: «Sí, registra la v2»)
La v1 (D15) no se borra: su código sigue disponible (`version="v1"`) y su resultado queda en `docs/vigilancia.md`.
Cambios de la v2 (lo demás, igual que en la v1):
1. **Azar:** se suspende solo si la rentabilidad de 365 días queda por debajo del **percentil 25** de las 200 estrategias
   aleatorias durante **30 días seguidos**.
2. **Reactivación automática** (solo de las suspensiones por azar): cuando la rentabilidad de 365 días está por encima de
   la **mediana** aleatoria durante 30 días seguidos. Se anota en el registro como evento "reactivacion".
3. **Drawdown:** sin cambios. La reactivación tras una suspensión por drawdown o una parada de emergencia solo con
   aprobación explícita del usuario.
4. **Volatilidad:** la alerta salta solo cuando la volatilidad de 30 días entra o sale de la banda normal de TRAIN.
5. **Datos:** además, no se generan señales si la última vela tiene volumen 0.
Aviso: la v2 se diseñó después de ver la simulación v1 en Bitstamp 2013-2016, así que volver a simularla en esos mismos
datos es una prueba débil. Su prueba de verdad será el paper trading.

## D18. 2026-11-21. Resultado de la vigilancia v2
Simulación en Bitstamp 2013-2016 (`docs/vigilancia_v2.md`): ninguna suspensión por azar; 4 suspensiones por drawdown el
2013-04-11/15, que solo se reactivan con aprobación del usuario; 3 días sin señales por volumen 0 (parón de Bitstamp en
enero de 2015); 53 alertas frente a 446 en la v1. La v2 queda como versión por defecto. La v1 se puede reproducir
(`version="v1"`) y tiene una prueba automática que lo comprueba.

## D19. 2026-11-21. Copiloto y paper trading (Prompt 9)
- Copiloto integrado (`copilot/copiloto.py`, `copilot/paper.py`, `copilot/panel.py`): estrategias B1 20/10, B1 55/20 y
  T1 SMA 100, pesos C1, exposición máxima 25 %, vigilancia v2, parada manual y automática, registros de solo añadir.
- Suspensión = sin entradas nuevas; las salidas siempre se permiten. Parada = se cierra todo. Datos malos = ningún cambio.
- Reequilibrios menores de 1 punto de exposición no se ejecutan (evita órdenes mínimas).
- Repetición técnica 2021-2022 sobre TRAIN: paper +11,9 % frente a backtest +9,8 %; diferencias explicadas en
  `docs/paper_repeticion.md`. Es una prueba del sistema, no de las estrategias.
- **Pendiente del usuario:** el modo en vivo y el mes de paper trading real necesitan precios posteriores al 01/01/2023,
  que son TEST. `python -m copilot hoy` y `en-marcha` se niegan a funcionar hasta que el usuario decida.
- El proyecto no se considera terminado hasta superar el mes de paper trading real.

## D20. 2026-11-21. TEST desbloqueado por el usuario
El usuario escribió exactamente «UNLOCK». Se cambia `TEST_DESBLOQUEADO = True` en `copilot/datos.py`. A partir de aquí,
los datos desde el 2023-01-01 se pueden descargar y leer. Todas las reglas (estrategias, criterios D3, robustez D9,
cartera D11, riesgo D13, vigilancia D17) quedaron fijadas antes de este momento y no se cambian a la vista de TEST.
Las pruebas del bloqueo siguen comprobando la lógica forzando el bloqueo dentro de la prueba.
