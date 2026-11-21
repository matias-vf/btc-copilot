"""Oro (GLD), D43: las reglas del copiloto de BTC, tal cual, en las tres épocas del oro. No se elige nada con estos datos."""

from __future__ import annotations

from datetime import date

from copilot import cartera as ca, datos, estrategias, registro, train, train2, universo as U
from copilot.costes import Costes
from copilot.motor import Vela, metricas, pct, recortar, requiere_costes_x2_x3
from copilot.universo_eval import momentos, sharpe_deflactado

COSTES = Costes(comision=0.0, medio_spread=0.0002, slippage=0.0003)  # 0,05 % por lado (D42)
DIAS = 252
LOTE = "oro-v1"
SALIDA = registro.RAIZ / "docs" / "oro.md"
REGLAS = {"N1D L=28": ("N1D", "L=28"), "U0940": ("F25", "L=28,n=100"), "U0082": ("F02", "s=5,l=100,banda=0.01"),
          "U0193": ("F04", "L=35,umbral=0.1"), "U0190": ("F04", "L=35,umbral=0.0"), "U0731": ("F14", "ventana=60,x=0.1")}
FICHEROS = {"otra época": "gld_yahoo_1d_otra_epoca_2004_2010.csv", "TRAIN": "gld_yahoo_1d_train_2011_2018.csv",
            "TEST": "gld_yahoo_1d_test_2019_2026.csv"}


def velas(nombre: str) -> list[Vela]:
    return [Vela(date.fromisoformat(f[0]), *map(float, f[1:6])) for f in datos.cargar_oro(datos.DATOS / nombre)]


def _medir(k, v, i0, costes=COSTES):
    r = recortar(estrategias.backtest_de(k, v, costes), i0)
    return metricas(r, DIAS), ca.rents(r)


def ejecutar() -> dict:
    if train._ya_ejecutado(LOTE):
        raise SystemExit(f"El lote {LOTE} ya se ejecutó.")
    v_o, v_tr, v_te = (velas(FICHEROS[e]) for e in ("otra época", "TRAIN", "TEST"))
    v_tt = v_tr + v_te
    epocas = {"otra época": (v_o, U.ARRANQUE), "TRAIN": (v_tr, U.ARRANQUE), "TEST": (v_tt, len(v_tr))}
    bh = {e: _medir(("BH", "buy_hold"), v, i0)[0] for e, (v, i0) in epocas.items()}
    filas, res = [], {}
    for nombre, k in REGLAS.items():
        res[nombre] = {}
        for e, (v, i0) in epocas.items():
            m, _ = _medir(k, v, i0)
            crit = train2.aprueba_v2(m, bh[e])
            x2 = None
            if e == "TRAIN" and requiere_costes_x2_x3(m):
                m2, _ = _medir(k, v, i0, COSTES.x(2))
                x2 = {**train._redondear(m2), "criterios": train2.aprueba_v2(m2, bh[e])}
            res[nombre][e] = {"m": m, "crit": crit, "x2": x2}
            filas.append({"lote": LOTE, "mercado": "GLD", "estrategia_id": k[0], "variante": k[1], "regla": nombre,
                          "epoca": e, "periodo": [v[i0].fecha.isoformat(), v[-1].fecha.isoformat()],
                          "metricas": train._redondear(m), "buy_hold": train._redondear(bh[e]), "criterios": crit,
                          "costes_x2": x2})
    # Sharpe deflactado en 2011-2026 con N = número de reglas probadas
    srs = {}
    for nombre, k in REGLAS.items():
        _, rets = _medir(k, v_tt, U.ARRANQUE)
        mu, sd, asim, curt = momentos(rets)
        srs[nombre] = (mu / sd if sd else 0.0, len(rets), asim, curt)
    media = sum(s[0] for s in srs.values()) / len(srs)
    var_sr = sum((s[0] - media) ** 2 for s in srs.values()) / (len(srs) - 1)
    aprobadas = []
    for nombre in REGLAS:
        sr, T, a, c = srs[nombre]
        res[nombre]["dsr"] = sharpe_deflactado(sr, T, a, c, var_sr, len(REGLAS))
        x2 = res[nombre]["TRAIN"]["x2"]
        res[nombre]["aprueba"] = (all(all(res[nombre][e]["crit"].values()) for e in epocas)
                                  and (x2 is None or all(x2["criterios"].values())) and res[nombre]["dsr"] >= 0.95)
        if res[nombre]["aprueba"]:
            aprobadas.append(nombre)
    for f in filas:
        f["sharpe_deflactado_2011_2026"] = res[f["regla"]]["dsr"]
        f["aprueba_oro"] = res[f["regla"]]["aprueba"]
    registro.registrar_experimentos(filas)  # todo calculado antes de escribir
    _escribir(res, bh, aprobadas)
    return {"res": res, "aprobadas": aprobadas, "bh": bh}


def _escribir(res, bh, aprobadas) -> None:
    l = ["# Oro (GLD): las reglas del copiloto, sin elegir nada (D43)", "",
         "Generado por `python -m copilot oro`. Ninguna regla se eligió mirando el oro: toda su historia es fuera de muestra.",
         f"Costes {COSTES.por_lado() * 100:.2f} % por lado. Sharpe anualizado con {DIAS} días. Ventanas desde la vela 365 "
         "(TEST, desde 2019 con la historia anterior delante). N1 no se aplica (decide en domingo).", "",
         "| Regla | Época | Rentabilidad (B&H) | Sharpe (B&H) | Drawdown (B&H) | Órdenes/semana | Criterio v2 |",
         "|---|---|---|---|---|---|---|"]
    for nombre, d in res.items():
        for e in ("otra época", "TRAIN", "TEST"):
            m, b, c = d[e]["m"], bh[e], d[e]["crit"]
            l.append(f"| {nombre} | {e} | {pct(m['rentabilidad'])} ({pct(b['rentabilidad'])}) | {m['sharpe']:.2f} "
                     f"({b['sharpe']:.2f}) | {pct(m['max_drawdown'])} ({pct(b['max_drawdown'])}) | "
                     f"{m['ejecuciones_por_semana']:.2f} | {'sí' if all(c.values()) else 'no'} |")
    l += ["", "| Regla | Sharpe deflactado 2011-2026 (N = 6) | Costes x2 en TRAIN | Aprueba |", "|---|---|---|---|"]
    for nombre, d in res.items():
        x2 = d["TRAIN"]["x2"]
        l.append(f"| {nombre} | {d['dsr']:.3f} | {'no hace falta' if x2 is None else ('ok' if all(x2['criterios'].values()) else 'falla')} | "
                 f"{'**sí**' if d['aprueba'] else 'no'} |")
    l += ["", ("Aprueban y forman el copiloto del oro: " + ", ".join(aprobadas) + "." if aprobadas
               else "**Ninguna regla aprueba en el oro.** El oro queda sin copiloto."), ""]
    SALIDA.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
