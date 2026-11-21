"""Evaluación final en TEST (Prompt 5, parte 3, y regla D21). Una sola vez."""

from __future__ import annotations

from copilot.motor import pct as _p

import hashlib
import subprocess
from datetime import date

from copilot import datos, estrategias, registro, robustez, train, vigilancia as vg
from copilot.motor import backtest, cargar_velas, metricas, recortar

LOTE = "test-v1"
FICHERO = datos.DATOS / "btcusdt_binance_1d_test.csv"
SALIDA = registro.RAIZ / "docs" / "test.md"
VARIANTES = [("B1", "N=20,M=10"), ("B1", "N=55,M=20"), ("T1", "sma_n=100"), ("T1", "sma_n=150"),
             ("T1", "sma_n=200"), ("T1", "cruce_sma=50/200")]
EN_COPILOTO = {("B1", "N=20,M=10"), ("B1", "N=55,M=20"), ("T1", "sma_n=100")}
INICIO = date(2023, 1, 1)


tramo = recortar  # nombre usado en este módulo


def ejecutar() -> dict:
    if any(e["datos"].get("lote") == LOTE for e in registro.leer(registro.EXPERIMENTOS)):
        raise SystemExit(f"El lote {LOTE} ya se ejecutó.")
    velas = cargar_velas(train.FICHERO) + cargar_velas(FICHERO)
    i0 = next(i for i, v in enumerate(velas) if v.fecha >= INICIO)
    sha = hashlib.sha256(FICHERO.read_bytes()).hexdigest()
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=registro.RAIZ,
                            capture_output=True, text=True).stdout.strip()
    bh = metricas(tramo(backtest(velas, estrategias.buy_hold), i0))
    p4 = {(e["datos"]["estrategia_id"], e["datos"]["variante"]): e["datos"]["metricas"]
          for e in registro.leer(registro.EXPERIMENTOS) if e["datos"].get("lote") == train.LOTE}
    filas = []
    for k in VARIANTES:
        m = metricas(tramo(backtest(velas, estrategias.crear(*k)), i0))
        crit = train.aprueba(m, bh)
        filas.append({"lote": LOTE, "estrategia_id": k[0], "variante": k[1],
                      "periodo": [velas[i0].fecha.isoformat(), velas[-1].fecha.isoformat()], "datos_sha256": sha,
                      "codigo_commit": commit, "metricas": train._redondear(m), "buy_hold": train._redondear(bh),
                      "criterios": crit, "aprueba_test": all(crit.values()), "en_copiloto": k in EN_COPILOTO,
                      "sharpe_train": p4[k]["sharpe"]})
    c25 = vg.series(velas)[vg.CARTERA]
    mc = metricas(tramo(c25, i0))
    for f in filas:
        registro.registrar_experimento(f)
    out = {"filas": filas, "bh": bh, "c25": mc, "desde": velas[i0].fecha, "hasta": velas[-1].fecha}
    _escribir(out)
    return out




def _escribir(o) -> None:
    from copilot.robustez import spearman

    bh, filas = o["bh"], o["filas"]
    t1 = [f for f in filas if f["estrategia_id"] == "T1"]
    rho = spearman([f["sharpe_train"] for f in t1], [f["metricas"]["sharpe"] for f in t1])
    b1 = [f for f in filas if f["estrategia_id"] == "B1"]
    orden_b1 = ((b1[0]["sharpe_train"] > b1[1]["sharpe_train"]) == (b1[0]["metricas"]["sharpe"] > b1[1]["metricas"]["sharpe"]))
    sup = "estable" if rho >= 0.5 else ("ruido" if rho < 0 else "dudosa")
    quedan = [f for f in filas if f["en_copiloto"] and f["aprueba_test"]]
    l = ["# Evaluación en TEST", "",
         f"Generado por `python -m copilot test`. Regla decidida antes de ver resultados: `docs/decisiones.md`, D21.",
         f"TEST: BTC/USDT Binance {o['desde']} a {o['hasta']}, costes 0,16 % por lado. Cada fila está en el registro (lote `{LOTE}`).",
         "", "## Resultados", "",
         "| Estrategia | Variante | En el copiloto | Operaciones | Rentabilidad | Sharpe | Drawdown máx. | Supera B&H (rent. / DD / Sharpe) | Aprueba TEST |",
         "|---|---|---|---|---|---|---|---|---|",
         f"| **Buy & Hold** | – | – | – | {_p(bh['rentabilidad'])} | {bh['sharpe']:.2f} | {_p(bh['max_drawdown'])} | referencia | – |"]
    for f in filas:
        m, c = f["metricas"], f["criterios"]
        si = " / ".join("sí" if c[x] else "no" for x in ("rentabilidad", "drawdown", "sharpe"))
        l.append(f"| {f['estrategia_id']} | {f['variante']} | {'sí' if f['en_copiloto'] else 'no'} | {m['operaciones']} | "
                 f"{_p(m['rentabilidad'])} | {m['sharpe']:.2f} | {_p(m['max_drawdown'])} | {si} | "
                 f"{'**SÍ**' if f['aprueba_test'] else 'no'} |")
    l += ["", "## Consistencia TRAIN frente a TEST (D9)", "",
          "| Variante | Sharpe TRAIN | Sharpe TEST |", "|---|---|---|"]
    l += [f"| {f['estrategia_id']} {f['variante']} | {f['sharpe_train']:.2f} | {f['metricas']['sharpe']:.2f} |" for f in filas]
    l += ["", f"- T1: Spearman = {rho:.2f} -> superficie **{sup}** (estable >= 0,5; ruido < 0).",
          f"- B1: el orden entre 20/10 y 55/20 {'se mantiene' if orden_b1 else 'se invierte'} (con 2 variantes no hay más que medir).",
          "", "## Cartera C1 al 25 % en TEST (informativo)", "",
          f"Rentabilidad {_p(o['c25']['rentabilidad'])}, CAGR {_p(o['c25']['cagr'])}, Sharpe {o['c25']['sharpe']:.2f}, "
          f"drawdown {_p(o['c25']['max_drawdown'])} (límite del 35 %: {'respetado' if o['c25']['max_drawdown'] >= -0.35 else 'SUPERADO'}). "
          f"Buy & Hold: CAGR {_p(bh['cagr'])}.", "",
          "## Consecuencia para el copiloto (D21)", "",
          ("Siguen, ahora VALIDADAS: " + ", ".join(f"{f['estrategia_id']} {f['variante']}" for f in quedan) + "."
           if quedan else "**Ninguna variante del copiloto aprueba TEST.** El copiloto solo dirá NO OPERAR."), ""]
    SALIDA.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
