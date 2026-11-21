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

## D21. 2026-11-21. Regla de TEST, decidida por el usuario ANTES de ver ningún resultado
Respuesta del usuario: «Mismo criterio: fuera».
- **Qué se evalúa:** las 6 variantes de las estrategias conservadas (B1: 20/10 y 55/20; T1: SMA 100, 150, 200 y cruce
  50/200), con costes x1, en TEST = 2023-01-01 a 2026-11-20. Se ejecuta el motor sobre TRAIN + TEST seguidos (las
  posiciones y los indicadores vienen de TRAIN) y se mide solo el tramo de TEST, partiendo del capital al cierre del
  2022-12-31. Buy & Hold se mide igual. Lote `test-v1` en el registro de experimentos.
- **Aprueba TEST** una variante si cumple los tres criterios de D3 frente a Buy & Hold en TEST: más rentabilidad,
  menos drawdown máximo y Sharpe igual o mayor.
- **Consecuencia:** solo las variantes que estaban en el copiloto (B1 20/10, B1 55/20, T1 SMA 100) y aprueben TEST
  siguen en el copiloto, ahora como VALIDADAS. Las que fallen salen del copiloto (no se borran del registro). Si un
  grupo (B1 o T1) se queda sin variantes, su peso pasa al otro. Si no queda ninguna, el copiloto solo dirá NO OPERAR.
- **Consistencia (D9):** Spearman entre el Sharpe de TRAIN y el de TEST de las variantes de T1 (4 variantes). B1 solo
  tiene 2 variantes, así que su "clasificación" solo indica si el orden se mantiene.
- **Información adicional:** la cartera C1 al 25 % en TEST (y si respeta el límite del 35 % de drawdown).

## D22. 2026-11-21. Resultado de TEST: ninguna estrategia del copiloto lo supera
Lote `test-v1` (experimentos 85 a 90, `docs/test.md`). Buy & Hold en TEST: +255,8 %, Sharpe 0,93, drawdown -53,0 %.
Ninguna variante supera a Buy & Hold en rentabilidad. T1 SMA 100 (+208,0 %, Sharpe 1,00, drawdown -36,8 %) y
T1 SMA 150 cumplen drawdown y Sharpe, pero no rentabilidad. B1 20/10 y B1 55/20 solo cumplen drawdown.
Consistencia D9: Spearman de T1 = 0,60 (superficie estable); el orden de B1 se mantiene, pero su Sharpe cae a la mitad.
Aplicando D21: **el copiloto se queda sin estrategias validadas y solo dice NO OPERAR** (y, si hubiera posición, VENTA
para cerrarla). Las estrategias no se borran. Las repeticiones técnicas siguen pudiendo usar las del Prompt 9.
El usuario pide entonces repetir el proceso con una búsqueda intensiva desde el Prompt 1 (ver D23).

## D23. 2026-11-21. Segunda búsqueda: decisiones del usuario antes de ver ningún resultado
Respuestas del usuario a las tres preguntas:
1. **Candidatas:** «N1, N2, N3 y N4». N1 momentum semanal (L = 1, 2, 4 semanas), N2 medias cortas (n = 5, 10, 20 días),
   N3 ruptura del rango simétrica (n = 50, 150, 200), N4 cerca del máximo de 52 semanas (x = 10 %, 20 %, EXPERIMENTAL).
   11 variantes. N5 (momentum dual con rentabilidad del efectivo) no se registra. Detalle en `docs/prompt1_v2_candidatas.md`.
2. **Protocolo:** «TEST como 2ª validación + paper». Selección en TRAIN (2017-2022), robustez en Bitstamp 2011-2016 y
   TEST 2023-2026 como segunda validación, con el aviso de que ya está visto. Las que pasen entran en el copiloto solo
   como EXPERIMENTALES hasta superar al menos un mes de paper trading en vivo.
3. **Criterio versión 2:** «Riesgo: drawdown + Sharpe». Para las estrategias nuevas basta con un drawdown máximo menor
   que el de Buy & Hold y un Sharpe igual o mayor, sin exigir más rentabilidad. Las estrategias antiguas no se
   reevalúan con este criterio. Nota de transparencia: con el criterio v2, T1 SMA 100 y T1 SMA 150 habrían aprobado
   TEST (docs/test.md); por la regla aceptada no se recuperan. Si se quisiera, sería una decisión nueva y registrada.

## D24. 2026-11-21. Prompt 2 (segunda búsqueda): N1-N4 registradas
Entradas 13 a 16 de `registros/ideas.jsonl`, con regla exacta, variantes permitidas y criterio versión 2
(`copilot/estrategias_v2.py`). 11 variantes: N1 L = 1, 2, 4 semanas; N2 n = 5, 10, 20; N3 n = 50, 150, 200;
N4 x = 10 %, 20 % (experimental). Datos: no hace falta descargar nada; las cuatro usan las velas diarias ya validadas
(N1 decide solo con el cierre del domingo, a partir de esas mismas velas). Experimentos acumulados hasta ahora: 90.

## D25. 2026-11-21. Prompt 3 (segunda búsqueda): reglas de N1-N4 en el motor
- El motor, los costes (0,16 % por lado) y la ejecución (cierre de t, apertura de t+1) no cambian (D7).
- `copilot/estrategias.py`: N1 decide solo con el cierre del domingo y mantiene la posición entre semana (el domingo de
  hace L semanas es la vela 7·L días antes); N2 usa la misma regla que T1 con medias de 5, 10 y 20 días; N3 compara con
  los cierres de las n velas previas; N4 compara con el máximo de 365 velas y no opera con menos historia.
- Pruebas: cada regla con casos a mano, N1 solo opera los lunes, y las 11 variantes pasan la comprobación de
  anticipación con datos sintéticos. Con los datos reales de TRAIN: 43 de 43 variantes registradas sin anticipación.
- Ninguna rentabilidad calculada todavía (eso es el Prompt 4).

## D26. 2026-11-21. Prompt 4 (segunda búsqueda): N1-N4 en TRAIN
Lote `busqueda2-train-v1` (experimentos 91 a 101). Con el criterio v2 aprueban 9 de 11: N1 L=2 y L=4; N2 n=5, 10 y 20;
N3 n=50; N4 x=10 % y x=20 % (experimentales). No aprueban N1 L=1 ni N3 n=150 y n=200. Ninguna alerta de "demasiado
bueno"; el diagnóstico de un día más de retraso no muestra filtración. N2 n=5 y n=10 operan más de una vez por semana
y no aprueban con costes x2 ni x3. Tabla y lectura en `docs/resultados_train_v2.md`.

## D27. 2026-11-21. Arreglos de la revisión de código (aprobados por el usuario: «si»)
1. **Ventana de comparación alineada (regla nueva, desde ahora):** cada variante se compara con Buy & Hold solo desde
   el primer día en que puede operar (tras su periodo de arranque). Antes, Buy & Hold contaba meses en los que la
   variante aún no podía operar, y eso cambiaba veredictos (N3 n=200: Sharpe 0,66 frente a 0,72 en todo TRAIN, pero
   0,70 frente a 0,47 en su ventana). Periodo de arranque (índice de la primera vela con señal posible): N1 7·L,
   N2 n-1, N3 n, N4 364. Se aplica a la segunda búsqueda en TRAIN (nuevo lote `busqueda2-train-v2`; el lote
   `busqueda2-train-v1` queda en el registro tal cual), en la otra época y donde haga falta. En TEST no cambia nada:
   ahí las estrategias llegan con la historia de TRAIN y no tienen arranque. La primera búsqueda no se reevalúa.
2. **N1 comprueba la fecha:** el domingo de hace L semanas se busca por fecha, no solo contando velas. Si falta una
   vela y la fecha no coincide, N1 no opera. En TRAIN y TEST no hay huecos, así que sus resultados no cambian.
3. **Menos código repetido:** las ejecuciones de lotes y el formato de porcentajes pasan a una sola función cada uno.

## D28. 2026-11-21. Segunda búsqueda: TRAIN con ventana alineada y reglas del Prompt 5, fijadas ANTES de ejecutarlo
**TRAIN con ventana alineada** (lote `busqueda2-train-v2`, experimentos 102 a 112): aprueban 10 de 11. Cambia N3 n=200,
que ahora aprueba (Sharpe 0,70 frente a 0,47 de Buy & Hold en su ventana). Siguen sin aprobar N1 L=1 y N3 n=150.

**Reglas del Prompt 5 (segunda búsqueda):**
1. **Costes:** una variante que da más de una orden por semana también tiene que aprobar en TRAIN con costes x2. Así
   quedan fuera N2 n=5 y N2 n=10 (con x2: Sharpe 0,44 y 0,55, por debajo de 0,73 y 0,72).
2. **Otra época:** las 11 variantes en Bitstamp 2011-2016, con ventana alineada, costes x1 (y x3 como información),
   criterio v2 contra Buy & Hold de Bitstamp en la misma ventana. Lote `busqueda2-otra-epoca-v1`.
3. **TEST (segunda validación, ya visto):** las 11 variantes, motor sobre TRAIN + TEST seguidos, medido solo en TEST
   (2023-01-01 a 2026-11-20), criterio v2. Lote `busqueda2-test-v1`.
4. **Una variante SE CONSERVA (como EXPERIMENTAL)** si aprueba el criterio v2 en TRAIN (ventana alineada), en la otra
   época y en TEST, y cumple la regla de costes.
5. **Superficie (como D9):** por estrategia, Spearman entre el Sharpe de TRAIN y el de TEST de sus variantes y
   cuántas variantes tienen Sharpe >= Buy & Hold en cada periodo. Se informa; no cambia el veredicto de la regla 4.
6. Regímenes de mercado (como D9) para las variantes conservadas, en las tres épocas.

## D29. 2026-11-21. Resultado del Prompt 5 (segunda búsqueda)
Lotes `busqueda2-otra-epoca-v1` y `busqueda2-test-v1` (experimentos 113 a 134). Aplicando D28.4, **solo se conserva
N1 L=4** (momentum de 4 semanas), como EXPERIMENTAL: aprueba el criterio v2 en TRAIN (Sharpe 1,22 frente a 0,79), en la
otra época (1,79 frente a 1,50) y en TEST (1,24 frente a 0,93; drawdown -32,5 % frente a -53,0 %). Las otras 10
fallan en TEST (o, N2 n=5 y n=10, en costes x2). Diagnósticos sin filtración; el domingo es el mejor día de la semana,
lo que indica algo de suerte (`docs/robustez_v2.md`).

## D30. 2026-11-21. Reglas de los Prompts 6 y 7 (segunda búsqueda), fijadas ANTES de ejecutar
- **Cartera (Prompt 6):** con una sola estrategia superviviente no hay nada que combinar: la "cartera" es N1 L=4 al
  100 % de su peso. La matriz de correlación se calcula solo frente a Buy & Hold.
- **Riesgo (Prompt 7):** misma regla que D13, sin apalancamiento: exposición 25 %, 50 %, 75 % o 100 % de N1 L=4.
  Admisible si el drawdown es de como mucho el 35 % en TRAIN y en la otra época; entre las admisibles, la de mayor
  Sharpe en TRAIN y, si difieren en menos de 0,05, la de menor exposición. TEST se muestra como información.
  Lote `busqueda2-riesgo-v1`. Los demás límites del copiloto (3 posiciones, pérdida máxima del 35 %, parada manual) no cambian.

## D31. 2026-11-21. Prompts 6 a 9 (segunda búsqueda): el copiloto pasa a usar N1 L=4, como EXPERIMENTAL
- **Prompt 6:** con una sola superviviente no hay cartera que combinar (correlación diaria con Buy & Hold: 0,70 a 0,75).
- **Prompt 7** (lote `busqueda2-riesgo-v1`, regla D30): exposición elegida **25 %**. Drawdown -25,8 % en TRAIN,
  -21,4 % en la otra época y -8,8 % en TEST. Las exposiciones de 50 % a 100 % superan el límite del 35 %.
- **Prompt 8:** la vigilancia (reglas v2, D17) ahora acepta las estrategias que se le pasen; por defecto sigue usando
  las de la primera búsqueda, así que D16 y D18 siguen siendo reproducibles. El copiloto la usa con N1 L=4.
- **Prompt 9:** `copilot/copiloto.py` usa `GRUPOS = {"N1": [N1 L=4]}`, exposición máxima 25 %, y marca cada señal como
  EXPERIMENTAL. N1 solo decide los domingos; la ficha da el nivel del domingo siguiente para entrar o invalidar.
  Corrección: el riesgo de N1 hasta la próxima decisión es una mala semana de TRAIN (percentil 5), porque no tiene un
  precio de salida fijo entre domingos; antes la ficha podía mostrar un 0 % engañoso.

## D32. 2026-11-21. Repetición técnica 2023-2026 y paper trading en vivo en marcha
- Repetición día a día con N1 L=4 sobre 2023-2026: paper +51,7 % (Sharpe 1,16, drawdown -9,6 %) frente a backtest
  +48,5 % (1,24, -8,8 %). Sin suspensiones ni paradas (`docs/paper_repeticion_test.md`).
- Paper trading en vivo iniciado el 2026-11-21 con 100 USD ficticios. Primer ciclo: vela del 2026-11-20, NO OPERAR.
- Funcionamiento continuo: tarea programada de Windows «BTCCopilot diario» (01:15 hora local, se recupera si el
  ordenador estaba apagado) que ejecuta `tools/diario.cmd`: ciclo, verificación de registros y commit local de
  `registros/`. Se quita con `Unregister-ScheduledTask -TaskName "BTCCopilot diario"`.
- El proyecto no se da por terminado hasta superar al menos un mes de paper trading en vivo (no antes del 2026-12-21).

## D33. 2026-11-21. Vigía horario (pedido por el usuario: «que busque oportunidades todo el día, pero que si no lo ve muy claro no es obligatorio que opere»)
- Cada hora, el vigía lee el precio público de BTC/USDT en Binance (sin claves) y anota una **OBSERVACIÓN** en
  `registros/vigia.jsonl` (solo añadir): precio, cambio en 24 h, nivel de N1 para el próximo domingo, distancia a ese
  nivel y qué decidiría N1 si el domingo cerrase al precio actual.
- **El vigía no genera señales ni órdenes.** Las operaciones siguen saliendo solo de la regla registrada de N1 L=4 con
  el cierre diario; si no hay una regla que se cumpla, NO OPERAR. Operar por oportunidades vistas entre horas exigiría
  una estrategia nueva, registrada antes de probarla y validada con todo el proceso.
- Avisos del vigía: precio a menos del 3 % del nivel de N1, o movimiento de más del 5 % en 24 h.
- Sus observaciones aparecen en el resumen diario de las 20:00.

## D34. 2026-11-21. «Si lo ve muy claro, puede operar»: se prueba N1D (N1 con revisión diaria), reglas fijadas ANTES
El usuario pidió que el copiloto pueda operar fuera del domingo cuando lo vea muy claro, y eligió «Probar N1 diaria».
"Muy claro" no puede ser una intuición: tiene que ser una regla registrada y probada.
- **N1D:** al cierre de cada día, si close_t / close_(t-28) - 1 > 0 -> comprado desde la apertura de t+1; si no,
  liquidez. Es la regla de N1 L=4 comprobada todos los días (equivale a la familia T2 con L = 28; T2 con 90, 180 y 365
  días se descartó en la primera búsqueda). Una sola variante (L = 28). Idea registrada con `busqueda: 3`.
- **Proceso, el mismo de la segunda búsqueda:** criterio v2 (menos drawdown y Sharpe >= Buy & Hold) con ventana alineada
  en TRAIN y en la otra época, TEST como segunda validación (ya visto) y regla de costes (si da más de una orden por
  semana, también debe aprobar en TRAIN con costes x2). Lotes `busqueda3-*-v1`.
- **Si aprueba todo:** entra en el copiloto como EXPERIMENTAL junto a N1 L=4, con pesos inversos a la volatilidad
  (método D11, mensual) y exposición total máxima del 25 %. Podrá operar cualquier día, siempre en paper trading.
- **Si no aprueba:** el copiloto sigue solo con N1 L=4 (domingos) y el vigía sigue sin operar.
- Aviso: en los diagnósticos de N1 (D29), decidir otros días de la semana dio un Sharpe algo menor que el domingo.

## D35. 2026-11-21. N1D entra en el copiloto (resultado de D34)
Lotes `busqueda3-*-v1` (`docs/n1d.md`). N1D aprueba el criterio v2 en TRAIN (Sharpe 1,08 frente a 0,79 en su ventana),
en la otra época (1,93 frente a 1,50) y en TEST (1,15 frente a 0,93; drawdown -36,3 % frente a -53,0 %); da como mucho
0,62 órdenes por semana, así que no necesita la prueba de costes x2. Según D34, el copiloto pasa a usar N1 L=4
(domingos) y N1D (cualquier día), con pesos inversos a la volatilidad (mensual) y exposición total máxima del 25 %,
ambas EXPERIMENTALES. El vigía horario muestra también qué haría N1D con el cierre del día. Nota: la cartera N1 + N1D
al 25 % no se ha medido como tal; las cifras de "histórico de la cartera" de la ficha siguen siendo las de N1 al 25 %.

## D36. 2026-11-21. Tercera búsqueda: 1000 estrategias (pedida por el usuario), método fijado ANTES de generar nada
Petición: «repite desde el prompt 1 subiendo el número de estrategias iniciales a 1000. Puedes escoger la temporalidad».
1. **Temporalidad elegida: velas diarias (1d)**, con reglas que deciden cada día o cada semana. Motivos: con costes de
   0,16 % por lado, las reglas intradía publicadas pierden su ventaja (por ejemplo, el efecto de 15 minutos de Shanaev
   y otros, 2023, son 0,58 pb por minuto); la evidencia publicada en BTC es sobre todo diaria y semanal; y los datos
   diarios están validados en tres épocas. Las velas horarias quedan fuera de esta búsqueda.
2. **Universo:** exactamente 1000 variantes de unas 30 familias de reglas antiguas y publicadas (medias móviles, cruces,
   momentum, filtros de Alexander, rupturas, RSI, Bollinger, reversión a corto plazo, máximos de N días, MACD, OBV,
   estocástico, ADX, Keltner, volatilidad objetivo, estacionalidad, SAR parabólico, Ichimoku, Williams %R, Darvas...).
   Parámetros en rejillas convencionales, generados por código (`copilot/universo.py`), no ajustados a los datos.
   Siguen la idea de los universos de reglas de Sullivan, Timmermann y White (1999) y Hudson y Urquhart (2021).
   N1 y N1D están dentro del universo y se vuelven a evaluar como cualquier otra.
3. **Corrección por probar muchas reglas:** en TRAIN, además del criterio v2 (menos drawdown y Sharpe >= Buy & Hold en
   la misma ventana) y la regla de costes x2, se exige un **Sharpe deflactado (Bailey y López de Prado, 2014) >= 0,95**
   con N = 1000 pruebas. Es la probabilidad de que el Sharpe verdadero sea positivo teniendo en cuenta cuántas reglas se
   han probado, la asimetría y las colas gruesas de las rentabilidades.
4. **Robustez:** las que pasen TRAIN se prueban en la otra época (Bitstamp) y en TEST (segunda validación, ya visto),
   con el criterio v2.
5. **Selección final:** como mucho 5 estrategias, elegidas por mayor Sharpe deflactado en TRAIN, saltando cualquiera
   cuya correlación diaria con una ya elegida sea mayor de 0,9.
6. **Copiloto:** las elegidas sustituyen a N1 y N1D (que, si sobreviven, seguirán), con pesos inversos a la volatilidad,
   reequilibrio mensual y exposición total máxima del 25 %, todas EXPERIMENTALES hasta superar el paper trading en vivo.
   Si no sobrevive ninguna, el copiloto sigue con N1 y N1D, con un aviso de que no superaron la corrección estadística.

## D37. 2026-11-21. Cambio pedido por el usuario antes de evaluar el universo: N1 y N1D se quedan
Petición: «no descartes la estrategia actual. Que de esta nueva búsqueda salgan algunas estrategias más para no depender
de una sola». Sustituye el punto 6 de D36:
- **N1 L=4 y N1D siguen en el copiloto pase lo que pase en la tercera búsqueda.** Si no superan la corrección por
  muchas pruebas, se dice en el informe, pero no se quitan.
- La tercera búsqueda **añade** como mucho 5 estrategias nuevas, elegidas por mayor Sharpe deflactado en TRAIN entre
  las que superen todo el proceso, saltando las que tengan una correlación diaria mayor de 0,9 con N1, N1D o con otra
  ya elegida (para que diversifiquen de verdad).
- Todas juntas en el copiloto con pesos inversos a la volatilidad, reequilibrio mensual y exposición total máxima del 25 %.
- **Ventana común:** todas las variantes del universo (y Buy & Hold) se miden desde la vela 365 de cada época, la ventana
  más larga del universo, así todas tienen el mismo número de días (necesario para el Sharpe deflactado).

## D38. 2026-11-21. Prompts 1 a 3 de la tercera búsqueda
- **Prompt 1:** universo de 1000 variantes en 31 familias publicadas (`docs/prompt1_v3_universo.md`, `copilot/universo.py`).
  Para llegar a 1000, el momentum semanal (F05) incluye también 65 y 78 semanas.
- **Prompt 2:** las 31 familias, con sus 1000 variantes y el criterio v3 (D36 y D37), están registradas en
  `registros/ideas.jsonl` (entradas 19 a 49) antes de calcular ningún resultado. No hacen falta datos nuevos: velas diarias.
- **Prompt 3:** motor de señales del universo. `backtest_rapido` da exactamente el mismo resultado que el motor normal
  (prueba automática), con la misma ejecución (cierre de t, apertura de t+1) y los mismos costes. Las 1000 variantes
  pasan la prueba de causalidad (alterar el futuro no cambia ninguna señal pasada) con los datos de TRAIN. El registro
  puede añadir muchas entradas de una vez (`anadir_varios`) conservando la cadena de hashes.

## D39. 2026-11-21. Resultado de la tercera búsqueda (1000 estrategias): ninguna supera la corrección estadística
Lotes `universo-train-v1` (1000 experimentos; las otras dos fases no tuvieron candidatas). En TRAIN (desde la vela 365),
512 de 1000 cumplen el criterio v2 y 508 también la regla de costes, pero **ninguna llega a un Sharpe deflactado de 0,95**:
el mayor es 0,499 (F12 Bollinger ruptura n=50, k=1,0; Sharpe 1,52). Un valor de 0,5 es justo lo que cabe esperar del
mejor de 1000 intentos por puro azar. N1 L=4 (0,276) y N1D (0,191) tampoco lo superan; se quedan por D37.
Lectura: con 1000 reglas parecidas, los buenos resultados históricos no se distinguen de la suerte. Las familias de
reversión (RSI, Bollinger, estocástico, Williams, Darvas) no cumplen ni el criterio v2 en TRAIN.
Nota de método: N = 1000 trata las variantes como si fueran independientes, aunque muchas están muy correlacionadas;
eso hace la corrección más dura. La regla se fijó así antes de ver resultados y se aplica tal cual (`docs/universo_resultados.md`).

## D40. 2026-11-21. Diversificar sin la corrección estadística (elegido por el usuario: «Añadir sin corrección, marcadas»)
Fijado ANTES de evaluar las candidatas en la otra época y en TEST:
- **Candidatas:** las 508 variantes que cumplen el criterio v2 y la regla de costes en TRAIN (ventana desde la vela 365).
  Se quita la exigencia del Sharpe deflactado (D36.3); el Sharpe deflactado se sigue usando solo para ordenarlas.
- **Robustez:** criterio v2 en la otra época (Bitstamp, desde la vela 365) y en TEST. Lotes `universo-otra-epoca-v2` y
  `universo-test-v2`.
- **Selección:** como mucho 5, en orden de mayor Sharpe deflactado en TRAIN, saltando las que tengan correlación diaria
  mayor de 0,9 con N1, N1D o con otra ya elegida.
- Entran en el copiloto marcadas «EXPERIMENTAL, SIN significación estadística», junto a N1 y N1D, con pesos inversos a la
  volatilidad (mensual) y exposición total máxima del 25 %. La prueba que decide es el paper trading en vivo.

## D41. 2026-11-21. Resultado de D40: cinco estrategias más en el copiloto
Lotes `universo-otra-epoca-v2` y `universo-test-v2` (`docs/universo_diversificacion.md`). De 508 candidatas, 172 cumplen
el criterio v2 en las tres épocas; se eligen 5 por Sharpe deflactado con correlación <= 0,9: U0940 (F25 momentum 28 días
y precio sobre SMA 100), U0082 (F02 cruce SMA 5/100 con banda del 1 %), U0193 (F04 momentum 35 días con umbral del 10 %),
U0190 (F04 momentum 35 días) y U0731 (F14 a menos del 10 % del máximo de 60 días). Todas son de seguimiento de
tendencia y se parecen bastante a N1 y N1D (correlación 0,80 a 0,90): diversifican poco. Entran en el copiloto
EXPERIMENTALES y SIN significación estadística; total 7 estrategias, exposición total máxima 25 %, pesos inversos a
la volatilidad (mensual). El límite de posiciones simultáneas pasa de 3 a 7 (una por estrategia).

## D42. 2026-11-21. Segundo mercado: ORO (GLD), pedido por el usuario («puedes escoger el mercado, que sea distinto a btc... repite todo el proceso»). Fijado ANTES de descargar nada
- **Mercado elegido: GLD** (SPDR Gold Shares, fondo cotizado de oro físico, NYSE Arca), velas diarias de bolsa.
  Motivos: se mueve casi sin relación con BTC (diversifica de verdad); el seguimiento de tendencia en materias primas
  está publicado (Moskowitz, Ooi y Pedersen 2012; Faber 2007); hay datos diarios desde 2004.
- **Fuente:** Yahoo Finance (gráfico diario, público, sin claves). Stooq se descartó: exige una comprobación
  anti-robots que no se debe saltar.
- **Épocas:** otra época 2004-11-18 a 2010-12-31; **TRAIN 2011-01-01 a 2018-12-31**; **TEST desde 2019-01-01,
  bloqueado en código hasta que el usuario escriba «UNLOCK»** (misma regla que para BTC). TEST del oro no se ha visto.
- **Costes por lado (estimados):** comisión 0 % (brókeres sin comisión en ETF de EE. UU.), medio spread 0,02 %,
  slippage 0,03 %: **0,05 % por lado**. La comisión anual del fondo (0,40 %) ya está descontada en su precio.
  Se supone que se pueden comprar fracciones de participación (con 100 USD ficticios). Sin apalancamiento ni cortos.
- **Calendario de bolsa:** solo hay velas los días de mercado. Se anualiza con 252 días; las reglas semanales deciden el
  último día de mercado de la semana (viernes); los huecos de más de 4 días se revisan a mano (festivos largos, cierres).
- **Proceso:** el mismo universo de 31 familias y 1000 variantes (D36), con las mismas reglas: criterio v2 (menos
  drawdown y Sharpe >= Buy & Hold de GLD en la misma ventana), costes x2 si opera más de una vez por semana, Sharpe
  deflactado >= 0,95 con N = 1000; después la otra época y TEST. Selección de hasta 5 por Sharpe deflactado con
  correlación <= 0,9 entre ellas. Si menos de 5 superan el Sharpe deflactado, se completa como en D40 (criterio v2 y
  costes en las tres épocas), marcándolas «SIN significación estadística».
- **Copiloto:** el oro tendrá su propia cuenta de paper trading de 100 USD ficticios y sus propios registros, con los
  mismos límites (exposición máxima 25 %, parada de emergencia, vigilancia). El resumen diario sumará las dos cuentas.
