# Copiloto de trading de Bitcoin (BTC)

## Qué es
Un programa en Python, en tu ordenador, que investiga estrategias sencillas y publicadas para BTC/USDT (Binance spot),
las prueba con datos históricos y, más adelante, genera señales COMPRA / VENTA / NO OPERAR y las prueba en
**paper trading** (dinero ficticio).

**No ejecuta operaciones reales, no se conecta a ninguna cuenta y no usa claves privadas. Nunca.**
Solo descarga precios públicos.

## Estado
| Paso | Estado |
|---|---|
| Prompt 1: estrategias candidatas | Hecho (fuera de este repositorio) |
| Prompt 2: registros y datos | Hecho |
| Prompt 3: motor de backtesting | Hecho |
| Prompt 4: ejecutar estrategias en TRAIN | Hecho (`docs/resultados_train.md`) |
| Prompt 5: robustez y filtrado | Hecho; TEST evaluado: ninguna estrategia lo supera (`docs/test.md`) |
| Prompt 6: cartera combinada | Hecho, provisional (`docs/cartera.md`) |
| Prompt 7: riesgo y tamaño de posición | Hecho, provisional (`docs/riesgo.md`) |
| Prompt 8: deterioro y reglas de parada | Hecho, reglas v2 (`docs/vigilancia_v2.md`; la v1 en `docs/vigilancia.md`) |
| Prompt 9: copiloto y paper trading | Construido; sin estrategias validadas, solo dice NO OPERAR |
| Segunda búsqueda: Prompt 1 (candidatas) | Hecho (`docs/prompt1_v2_candidatas.md`) |
| Segunda búsqueda: Prompt 2 (registro) | Hecho: N1-N4 registradas |
| Segunda búsqueda: Prompt 3 (reglas en el motor) | Hecho |
| Segunda búsqueda: Prompt 4 (ejecutar en TRAIN) | Hecho (`docs/resultados_train_v2.md`) |
| Segunda búsqueda: Prompt 5 (robustez y TEST) | Hecho: solo se conserva N1 L=4, EXPERIMENTAL (`docs/robustez_v2.md`) |
| Segunda búsqueda: Prompts 6-7 (cartera y riesgo) | Hecho: N1 L=4 al 25 % de exposición (`docs/riesgo_v2.md`) |
| Segunda búsqueda: Prompts 8-9 (vigilancia y copiloto) | Hecho: el copiloto usa N1 L=4 |
| Tercera búsqueda (1000 estrategias) | Hecho: ninguna supera la corrección; 5 añadidas sin significación (`docs/universo_resultados.md`, `docs/universo_diversificacion.md`) |
| Segundo mercado: oro (GLD) | Hecho: ninguna regla del copiloto funciona en el oro (`docs/oro.md`) |
| **Paper trading en vivo** | **En marcha desde el 2026-11-21** (mínimo un mes: hasta el 2026-12-21 como pronto) |

## Estructura
```
copilot/
  registro.py               registros de solo-añadir, encadenados con hash SHA-256
  datos.py                  descarga y validación de velas; bloqueo de TEST
  estrategias_iniciales.py  estrategias del Prompt 1 tal y como se registraron
  costes.py                 comisiones, spread y slippage de Binance spot
  motor.py                  backtest causal y métricas
  estrategias.py            reglas exactas de cada estrategia
  anticipacion.py           comprobación automática de que nada mira el futuro
  train.py                  Prompt 4: ejecuta y registra todas las variantes en TRAIN
  robustez.py               Prompt 5: otra época, regímenes, sensibilidad y veredicto
  cartera.py                Prompt 6: correlaciones y cartera inversa a la volatilidad
  riesgo.py                 Prompt 7: exposición, riesgo por operación y volatilidad objetivo
  vigilancia.py             Prompt 8: vigilancia diaria del deterioro y reglas de parada
  copiloto.py               Prompt 9: ciclo diario, señales, ficha, lectura visual, modo en vivo
  paper.py                  Prompt 9: cuenta simulada de 100 USD con costes y límites
  panel.py                  Prompt 9: panel HTML local
  __main__.py               órdenes: verificar, registrar, descargar, anticipacion
registros/
  ideas.jsonl               registro de estrategias (una por línea)
  experimentos.jsonl        cada variante probada, con contador acumulado
  senales.jsonl             señales del copiloto (vacío por ahora)
  vigilancia.jsonl          alertas, suspensiones y estado diario en vivo (vacío por ahora)
data/
  *.csv                     velas diarias
  FUENTES.md                procedencia, calidad y limitaciones
  calidad.json              informe automático de huecos y duplicados
docs/decisiones.md          decisiones tomadas y por qué
docs/costes.md              costes de operativa y de dónde salen
docs/resultados_train.md    tabla de resultados en TRAIN
docs/robustez.md            Prompt 5: las dos épocas lado a lado
docs/cartera.md             Prompt 6: cartera frente a Buy & Hold
docs/riesgo.md              Prompt 7: comparación de configuraciones de riesgo y límites
docs/vigilancia.md          Prompt 8: simulación de la vigilancia con las reglas v1
docs/vigilancia_v2.md       Prompt 8: simulación con las reglas v2 (las vigentes)
docs/copiloto.md            Prompt 9: cómo funciona el copiloto y sus límites
docs/pantalla_compartida.md Prompt 9: cómo analizar un gráfico con Claude
docs/paper_repeticion.md    Prompt 9: repetición 2021-2022, paper frente a backtest
docs/test.md                evaluación final en TEST (2023-2026)
docs/prompt1_v2_candidatas.md  segunda búsqueda: estrategias candidatas
docs/resultados_train_v2.md segunda búsqueda: resultados en TRAIN
repeticion/                 registros y panel de cada repetición
tests/                      pruebas automáticas
```

## Cómo se garantiza que los registros solo crecen
- El código solo sabe **añadir** líneas al final; no existe ninguna función para editar o borrar.
- Cada línea lleva el hash de la anterior. Si alguien cambia, borra o reordena una línea, el hash deja de cuadrar
  y el programa se niega a seguir.
- Borrar las últimas líneas no rompe la cadena; por eso `verificar` compara además con la última versión guardada en Git.

## Instalación (una sola vez)
Ya tienes instalado lo necesario: **Python 3.12** (el lenguaje en el que está hecho el programa) y **Git** (guarda el
historial de cambios). Este paso no usa librerías extra.

## El copiloto en vivo (lo único que tienes que saber)
- Cada día a las **01:15 (hora de Madrid)** Windows ejecuta solo el copiloto (tarea programada «BTCCopilot diario»).
  Si el ordenador estaba apagado, se ejecuta al encenderlo y recupera los días que falten.
- Estrategia: **N1 L=4** (momentum de 4 semanas, EXPERIMENTAL). Solo decide los domingos. Como mucho el 25 % del
  capital ficticio (100 USD) en BTC. **No se envía ninguna orden real.**
- **Oro (GLD):** segundo copiloto con su propia cuenta de 100 USD ficticios (registros en `registros\oro\`, panel en
  `registros\oro\panel_vivo.html`). Se ejecuta en la misma tarea diaria. Sus 4 reglas son EXPERIMENTALES y SIN
  significación estadística (`docs/oro_universo.md`).
- **Nasdaq (QQQ):** copiloto diario (2 reglas, `registros\nasdaq\`) e intradía cada 5 minutos en horario de bolsa
  (ruptura del rango de apertura, `registros\nasdaq_intradia\`, tarea «BTCCopilot intradia»). Todo EXPERIMENTAL.
- **Vigía cada hora** (tarea «BTCCopilot vigia»): mira el precio y anota qué haría N1 si el domingo cerrase así.
  Solo observa: **no opera**. Las operaciones salen únicamente de la regla de N1; si no se cumple, NO OPERAR.
- **Resumen a las 20:00** en la app de Claude (tarea programada «Resumen diario del copiloto BTC»), con el vigía incluido.
- Para ver cómo va: abre con doble clic `registros\panel_vivo.html`.
- Para ver la señal de hoy en la terminal: `python -m copilot hoy` (pasos abajo).
- Parada de emergencia del paper trading: `python -m copilot parar "motivo"`; para volver: `python -m copilot reanudar "motivo"`.
- Para quitar la tarea programada, en PowerShell:
  ```powershell
  Unregister-ScheduledTask -TaskName "BTCCopilot diario" -Confirm:$false
  ```
  ```powershell
  Unregister-ScheduledTask -TaskName "BTCCopilot vigia" -Confirm:$false
  ```

## Cómo se ejecuta
1. Pulsa la tecla Windows, escribe `PowerShell` y pulsa Intro.
2. Copia esta línea, pégala y pulsa Intro (te lleva a la carpeta del proyecto):
   ```powershell
   cd $HOME\Documents\BTCCopilot
   ```
3. Para comprobar que los registros están intactos:
   ```powershell
   python -m copilot verificar
   ```
   Cada línea debe empezar por `OK`.
4. Para pasar las pruebas automáticas:
   ```powershell
   python -m unittest -v
   ```
   Al final debe decir `OK`.
5. Para comprobar que ninguna estrategia mira el futuro (tarda menos de un minuto):
   ```powershell
   python -m copilot anticipacion
   ```
   La última línea debe decir `0 con anticipación`.
6. Para ver la ficha del copiloto en una fecha de TRAIN (por ejemplo, el 31/12/2022):
   ```powershell
   python -m copilot senal 2022-12-31
   ```
7. Para ver el panel de la repetición, abre en el navegador el archivo
   `repeticion\2021-01-01_2022-12-31\panel.html` (doble clic desde el Explorador de archivos).
8. Parada de emergencia del paper trading en vivo (y para reanudar):
   ```powershell
   python -m copilot parar "motivo"
   ```
   ```powershell
   python -m copilot reanudar "motivo"
   ```
9. (Opcional) Para volver a descargar los datos:
   ```powershell
   python -m copilot descargar
   ```
