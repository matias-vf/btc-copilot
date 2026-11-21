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
| Prompt 5: robustez y filtrado | Pendiente |

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
  __main__.py               órdenes: verificar, registrar, descargar, anticipacion
registros/
  ideas.jsonl               registro de estrategias (una por línea)
  experimentos.jsonl        cada variante probada, con contador acumulado
  senales.jsonl             señales del copiloto (vacío por ahora)
data/
  *.csv                     velas diarias
  FUENTES.md                procedencia, calidad y limitaciones
  calidad.json              informe automático de huecos y duplicados
docs/decisiones.md          decisiones tomadas y por qué
docs/costes.md              costes de operativa y de dónde salen
docs/resultados_train.md    tabla de resultados en TRAIN
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
6. (Opcional) Para volver a descargar los datos:
   ```powershell
   python -m copilot descargar
   ```
