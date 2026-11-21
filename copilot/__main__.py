"""Uso: python -m copilot <orden>

  verificar   comprueba los registros (hash) y que no se ha perdido nada respecto al último commit
  registrar   registra las estrategias iniciales (solo la primera vez)
  descargar   descarga los datos de TRAIN (Binance) y de la otra época (Bitstamp 2011-2016)
  train       Prompt 4: ejecuta todas las variantes registradas en TRAIN (una sola vez) y las anota
  anticipacion comprueba en TRAIN que ninguna variante registrada mira el futuro (no muestra resultados)
"""

import json
import subprocess
import sys
from datetime import date, datetime, timezone

from copilot import datos, registro
from copilot.estrategias_iniciales import entradas


def verificar() -> int:
    fallos = 0
    for ruta in (registro.IDEAS, registro.EXPERIMENTOS, registro.SENALES):
        try:
            n = len(registro.leer(ruta))
        except registro.RegistroCorrupto as e:
            print(f"CORRUPTO  {e}")
            fallos += 1
            continue
        # Ancla externa: lo ya guardado en Git debe seguir siendo el principio del fichero.
        rel = ruta.relative_to(registro.RAIZ).as_posix()
        r = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=registro.RAIZ, capture_output=True)
        actual = ruta.read_bytes() if ruta.exists() else b""
        if r.returncode == 0 and not actual.startswith(r.stdout):
            print(f"ALTERADO  {rel}: ya no empieza por lo guardado en el último commit")
            fallos += 1
            continue
        print(f"OK        {rel}: {n} entradas")
    return 1 if fallos else 0


def registrar() -> int:
    if registro.leer(registro.IDEAS):
        print("El registro de ideas ya tiene entradas: no se vuelve a registrar.")
        return 1
    for e in entradas():
        registro.anadir(registro.IDEAS, e)
        print(f"Registrada {e['id']:3} ({e['estado']}): {e['nombre']}")
    return 0


FUENTES = {
    "btcusdt_binance_1d_train.csv": (datos.descargar_binance, date(2017, 8, 17), date(2022, 12, 31),
                                     "Binance spot BTCUSDT, GET https://data-api.binance.vision/api/v3/klines (interval=1d)"),
    "btcusd_bitstamp_1d_2011_2016.csv": (datos.descargar_bitstamp, date(2011, 1, 1), date(2016, 12, 31),
                                         "Bitstamp BTC/USD, GET https://www.bitstamp.net/api/v2/ohlc/btcusd/ (step=86400)"),
}


def descargar() -> int:
    informe = {}
    for nombre, (fn, ini, fin, fuente) in FUENTES.items():
        filas = fn(ini, fin)
        v = datos.validar(filas)
        sha = datos.guardar(filas, datos.DATOS / nombre)
        informe[nombre] = {"fuente": fuente, "pedido": [ini.isoformat(), fin.isoformat()],
                           "descargado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                           "sha256": sha, **v}
        print(nombre, json.dumps({k: (x if not isinstance(x, list) else len(x)) for k, x in v.items()}))
    (datos.DATOS / "calidad.json").write_text(json.dumps(informe, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


def anticipacion() -> int:
    from copilot import anticipacion as la, estrategias, motor

    velas = motor.cargar_velas()
    ideas = [e["datos"] for e in registro.leer(registro.IDEAS) if e["datos"]["estado"] != "descartada"]
    variantes = [("BH", "buy_hold")] + [(i["id"], v) for i in ideas for v in i["configuraciones_permitidas"]]
    fallos = 0
    for eid, var in variantes:
        problemas = la.comprobar(velas, lambda _d, e=eid, v=var: estrategias.crear(e, v))
        fallos += bool(problemas)
        print(f"{'OK  ' if not problemas else 'FALLO'} {eid} {var} {'; '.join(problemas)}")
    print(f"{len(variantes)} variantes comprobadas, {fallos} con anticipación")
    return 1 if fallos else 0


def train() -> int:
    from copilot import train as tr

    filas = tr.ejecutar()
    print(f"{len(filas)} variantes ejecutadas y registradas. Tabla en {tr.SALIDA.relative_to(registro.RAIZ)}")
    return 0


if __name__ == "__main__":
    ordenes = {"verificar": verificar, "registrar": registrar, "descargar": descargar,
               "anticipacion": anticipacion, "train": train}
    if len(sys.argv) != 2 or sys.argv[1] not in ordenes:
        print(__doc__)
        sys.exit(2)
    sys.exit(ordenes[sys.argv[1]]())
