"""Segunda búsqueda, Prompt 4: ejecuta N1-N4 en TRAIN con el criterio versión 2 (D23) y anota cada variante."""

from __future__ import annotations

import hashlib
import subprocess

from copilot import estrategias, registro, train
from copilot.costes import BINANCE_SPOT
from copilot.estrategias_v2 import CRITERIOS_V2
from copilot.motor import alertas, backtest, cargar_velas, metricas, requiere_costes_x2_x3

LOTE = "busqueda2-train-v1"
SALIDA = registro.RAIZ / "docs" / "resultados_train_v2.md"


def aprueba_v2(m: dict, bh: dict) -> dict:
    return {"drawdown": abs(m["max_drawdown"]) < abs(bh["max_drawdown"]), "sharpe": m["sharpe"] >= bh["sharpe"]}


def ejecutar() -> list[dict]:
    if any(e["datos"].get("lote") == LOTE for e in registro.leer(registro.EXPERIMENTOS)):
        raise SystemExit(f"El lote {LOTE} ya se ejecutó.")
    velas = cargar_velas(train.FICHERO)
    sha = hashlib.sha256(train.FICHERO.read_bytes()).hexdigest()
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=registro.RAIZ,
                            capture_output=True, text=True).stdout.strip()
    bh = metricas(backtest(velas, estrategias.buy_hold, BINANCE_SPOT))
    ideas = [e["datos"] for e in registro.leer(registro.IDEAS) if e["datos"].get("busqueda") == 2]
    filas = []
    for idea in ideas:
        for var in idea["configuraciones_permitidas"]:
            f = estrategias.crear(idea["id"], var)
            m = metricas(backtest(velas, f, BINANCE_SPOT))
            extra = {}
            if requiere_costes_x2_x3(m):
                for k in (2, 3):
                    mk = metricas(backtest(velas, f, BINANCE_SPOT.x(k)))
                    extra[f"x{k}"] = {**train._redondear(mk), "criterios": aprueba_v2(mk, bh)}
            crit = aprueba_v2(m, bh)
            filas.append({"lote": LOTE, "estrategia_id": idea["id"], "variante": var, "estado_idea": idea["estado"],
                          "periodo": [velas[0].fecha.isoformat(), velas[-1].fecha.isoformat()], "datos_sha256": sha,
                          "codigo_commit": commit, "costes_por_lado": BINANCE_SPOT.por_lado(),
                          "criterios_version": CRITERIOS_V2["version"], "metricas": train._redondear(m),
                          "costes_multiplicados": extra, "buy_hold": train._redondear(bh), "criterios": crit,
                          "alertas": alertas(m, bh), "aprobada_train": all(crit.values())})
    for f in filas:  # todo calculado antes de escribir
        registro.registrar_experimento(f)
    _escribir(filas, bh)
    return filas


def _p(x):
    return f"{x * 100:,.1f} %".replace(",", " ")


def _escribir(filas, bh) -> None:
    n = {}
    for f in filas:
        n[f["estrategia_id"]] = n.get(f["estrategia_id"], 0) + 1
    l = ["# Resultados en TRAIN, segunda búsqueda (Prompt 4)", "",
         f"Generado por `python -m copilot train2` (lote `{LOTE}`). TRAIN {filas[0]['periodo'][0]} a {filas[0]['periodo'][1]}, "
         f"BTC/USDT Binance spot, costes {BINANCE_SPOT.por_lado() * 100:.2f} % por lado.",
         "Criterio versión 2 (D23): drawdown máximo menor que Buy & Hold y Sharpe igual o mayor. No exige más rentabilidad.",
         "Cada fila está en `registros/experimentos.jsonl`. Rentabilidades históricas: no predicen el futuro.", "",
         "| Estrategia | Variantes | Variante | Operaciones | Órdenes/semana | Rentabilidad | Sharpe | Drawdown máx. | Supera B&H (DD / Sharpe) | Avisos |",
         "|---|---|---|---|---|---|---|---|---|---|",
         f"| **Buy & Hold** | – | – | 1 | – | {_p(bh['rentabilidad'])} | {bh['sharpe']:.2f} | {_p(bh['max_drawdown'])} | referencia | |"]
    for f in filas:
        m, c = f["metricas"], f["criterios"]
        marca = " / ".join("sí" if c[k] else "no" for k in ("drawdown", "sharpe"))
        if f["aprobada_train"]:
            marca = f"**{marca} → APRUEBA**"
        av = list(f["alertas"]) + (["EXPERIMENTAL"] if f["estado_idea"] == "experimental" else [])
        for k, mk in f["costes_multiplicados"].items():
            av.append(f"costes {k}: {_p(mk['rentabilidad'])}, Sharpe {mk['sharpe']:.2f}, "
                      f"{'aprueba' if all(mk['criterios'].values()) else 'NO aprueba'}")
        l.append(f"| {f['estrategia_id']} | {n[f['estrategia_id']]} | {f['variante']} | {m['operaciones']} | "
                 f"{m['ejecuciones_por_semana']:.2f} | {_p(m['rentabilidad'])} | {m['sharpe']:.2f} | "
                 f"{_p(m['max_drawdown'])} | {marca} | {'; '.join(av)} |")
    total = len([e for e in registro.leer(registro.EXPERIMENTOS)])
    l += ["", f"Variantes de esta búsqueda: {len(filas)}. Experimentos acumulados en el registro: {total}."]
    SALIDA.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
