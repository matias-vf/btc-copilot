"""Uso: python -m copilot <orden>

  verificar   comprueba los registros (hash) y que no se ha perdido nada respecto al último commit
  registrar   registra las estrategias iniciales (solo la primera vez)
  descargar   descarga los datos de TRAIN (Binance) y de la otra época (Bitstamp 2011-2016)
  train       Prompt 4: ejecuta todas las variantes registradas en TRAIN (una sola vez) y las anota
  robustez    Prompt 5: otra época (Bitstamp), regímenes, sensibilidad y veredicto (una sola vez)
  cartera     Prompt 6: correlaciones y cartera inversa a la volatilidad (una sola vez)
  riesgo      Prompt 7: simulaciones de exposición, riesgo por operación y volatilidad (una sola vez)
  vigilancia  Prompt 8: simula la vigilancia diaria del deterioro en la otra época
  senal AAAA-MM-DD   ficha del copiloto para una fecha de TRAIN (no escribe en ningún registro)
  train2      segunda búsqueda, Prompt 4: N1-N4 en TRAIN (una sola vez)
  robustez2   segunda búsqueda, Prompt 5: otra época y TEST (una sola vez)
  riesgo2     segunda búsqueda, Prompts 6 y 7: cartera y exposición (una sola vez)
  test        evaluación final en TEST (regla D21, una sola vez)
  n1d         evalúa N1 con revisión diaria (D34, una sola vez)
  vigia       observación horaria del mercado (no opera; D33)
  resumen     resumen del paper trading en vivo (solo lee los registros)
  hoy         un ciclo en vivo con datos de hoy (bloqueado mientras TEST siga cerrado)
  en-marcha   funcionamiento continuo en vivo, un ciclo al día (bloqueado mientras TEST siga cerrado)
  repeticion AAAA-MM-DD AAAA-MM-DD   paper trading día a día sobre fechas de TRAIN, con registros propios
  parar "motivo"     parada de emergencia manual (kill switch) del paper trading en vivo
  reanudar "motivo"  reanuda tras una parada (solo tú puedes hacerlo)
  anticipacion comprueba en TRAIN que ninguna variante registrada mira el futuro (no muestra resultados)
"""

import json
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

from copilot import datos, registro
from copilot.estrategias_iniciales import entradas


def verificar() -> int:
    fallos = 0
    vivos = [registro.REGISTROS / n for n in ("paper.jsonl", "vigilancia.jsonl", "vigia.jsonl")]
    for ruta in (registro.IDEAS, registro.EXPERIMENTOS, registro.SENALES, *[r for r in vivos if r.exists()]):
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
    ideas = [e["datos"] for e in registro.leer(registro.IDEAS)
             if e["datos"]["estado"] != "descartada" and e["datos"]["familia"] not in ("Cartera", "Riesgo")]
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


def robustez() -> int:
    from copilot import robustez as rb

    inf = rb.ejecutar()
    print(f"{len(inf['filas'])} variantes ejecutadas en la otra época y registradas. Informe en docs/robustez.md")
    return 0


def cartera() -> int:
    from copilot import cartera as ca

    ca.ejecutar()
    print("Cartera ejecutada en TRAIN y en la otra época y registrada. Informe en docs/cartera.md")
    return 0


def riesgo() -> int:
    from copilot import riesgo as rg

    rg.ejecutar()
    print("Simulaciones de riesgo ejecutadas y registradas. Informe en docs/riesgo.md")
    return 0


def vigilancia() -> int:
    from copilot import vigilancia as vg

    vg.simular_otra_epoca("v2")
    print("Simulación de vigilancia (reglas v2) hecha. Informe en docs/vigilancia_v2.md")
    return 0


def senal(fecha: str) -> int:
    from datetime import date
    from copilot import copiloto as cp, vigilancia as vg

    velas = [v for v in motor_velas() if v.fecha <= date.fromisoformat(fecha)]
    f = velas[-1].fecha
    ahora = datetime(f.year, f.month, f.day, tzinfo=timezone.utc) + timedelta(days=1, minutes=5)
    print(cp.ficha(cp.decidir(velas, {}, 0.0, None, vg.problemas_datos(velas, ahora), None, ahora)))
    print("(Ficha sin historial de paper: supone que hoy no hay posiciones abiertas.)")
    return 0


def motor_velas():
    from copilot import motor
    return motor.cargar_velas()


def train2() -> int:
    from copilot import train2 as t2

    filas = t2.ejecutar()
    print(f"{len(filas)} variantes de la segunda búsqueda ejecutadas y registradas. Tabla en {t2.SALIDA.relative_to(registro.RAIZ)}")
    return 0


def robustez2() -> int:
    from copilot import robustez2 as rb

    out = rb.ejecutar()
    print(f"Robustez de la segunda búsqueda registrada. Se conservan: {len(out['conservadas'])}. Informe en docs/robustez_v2.md")
    return 0


def riesgo2() -> int:
    from copilot import riesgo2 as rg

    out = rg.ejecutar()
    print(f"Riesgo de la segunda búsqueda registrado. Exposición elegida: {out['elegida']} %. Informe en docs/riesgo_v2.md")
    return 0


def n1d() -> int:
    from copilot import busqueda3

    out = busqueda3.ejecutar()
    print(f"N1D evaluada y registrada. {'Aprueba' if out['aprueba'] else 'No aprueba'}. Informe en docs/n1d.md")
    return 0


def vigia() -> int:
    from copilot import vigia as vg

    print(vg.texto(vg.ejecutar()))
    return 0


def resumen() -> int:
    from copilot import resumen as rs

    print(rs.texto())
    return 0


def test() -> int:
    from copilot import evaluacion_test as et

    et.ejecutar()
    print("Evaluación en TEST hecha y registrada. Informe en docs/test.md")
    return 0


def hoy() -> int:
    from copilot import copiloto as cp
    try:
        velas = cp.velas_en_vivo()
        senales = cp.poner_al_dia(velas=velas)
        if not senales:
            print("Nada nuevo: la última vela cerrada ya tiene su señal.")
        for s in senales:
            print(cp.ficha(s))
        if senales:
            from copilot import panel
            panel.generar(cp.comparar(cp.RUTAS_VIVO, velas), registro.REGISTROS / "panel_vivo.html",
                          "Copiloto BTC: paper trading en vivo")
            print("Panel actualizado: registros/panel_vivo.html")
    except datos.DatosTestBloqueados as e:
        print(f"BLOQUEADO: {e}\nLos precios de hoy son posteriores al 01/01/2023 (TEST). "
              "El modo en vivo necesita tu decisión sobre esos datos (docs/decisiones.md).")
        return 1
    return 0


def en_marcha() -> int:
    from copilot import copiloto as cp
    try:
        cp.en_marcha()
    except datos.DatosTestBloqueados as e:
        print(f"BLOQUEADO: {e}")
        return 1
    return 0


def repeticion(desde: str, hasta: str) -> int:
    from datetime import date
    from copilot import copiloto as cp, panel

    carpeta = registro.RAIZ / "repeticion" / f"{desde}_{hasta}"
    cp.repeticion(date.fromisoformat(desde), date.fromisoformat(hasta), carpeta)
    cmp = cp.comparar(carpeta)
    panel.generar(cmp, carpeta / "panel.html", f"Copiloto BTC: repetición {desde} a {hasta}")
    print(cp.ficha(cmp["senales"][-1]))
    print(f"\nRepetición guardada en {carpeta.relative_to(registro.RAIZ)}; panel en panel.html")
    return 0


def _parada(tipo: str, motivo: str) -> int:
    from copilot import copiloto as cp
    registro.anadir(cp.RUTAS_VIVO["paper"], {"tipo": tipo, "fecha": datetime.now(timezone.utc).date().isoformat(),
                                             "motivo": motivo, "por": "usuario"})
    print(f"{tipo} registrada: {motivo}")
    return 0


if __name__ == "__main__":
    con_args = {"senal": senal, "repeticion": repeticion,
                "parar": lambda m: _parada("parada_manual", m), "reanudar": lambda m: _parada("reanudacion", m)}
    if len(sys.argv) >= 3 and sys.argv[1] in con_args:
        sys.exit(con_args[sys.argv[1]](*sys.argv[2:]))
    ordenes = {"n1d": n1d, "vigia": vigia, "resumen": resumen, "train2": train2, "robustez2": robustez2, "riesgo2": riesgo2, "test": test, "hoy": hoy, "en-marcha": en_marcha, "verificar": verificar, "registrar": registrar, "descargar": descargar,
               "anticipacion": anticipacion, "train": train,
               "robustez": robustez, "cartera": cartera,
               "riesgo": riesgo, "vigilancia": vigilancia}
    if len(sys.argv) != 2 or sys.argv[1] not in ordenes:
        print(__doc__)
        sys.exit(2)
    sys.exit(ordenes[sys.argv[1]]())
