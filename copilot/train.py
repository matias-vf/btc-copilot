"""Prompt 4: ejecuta todas las variantes registradas en TRAIN y anota cada una en experimentos.jsonl."""

from __future__ import annotations

import hashlib
import subprocess

from copilot import datos, estrategias, registro
from copilot.costes import BINANCE_SPOT
from copilot.estrategias_iniciales import CRITERIOS
from copilot.motor import alertas, backtest, cargar_velas, metricas, requiere_costes_x2_x3

LOTE = "prompt4-train-v1"
FICHERO = datos.DATOS / "btcusdt_binance_1d_train.csv"
SALIDA = registro.RAIZ / "docs" / "resultados_train.md"


def _redondear(m: dict) -> dict:
    return {k: (round(v, 6) if isinstance(v, float) else v) for k, v in m.items()}


def aprueba(m: dict, bh: dict) -> dict:
    return {
        "rentabilidad": m["rentabilidad"] > bh["rentabilidad"],
        "drawdown": abs(m["max_drawdown"]) < abs(bh["max_drawdown"]),
        "sharpe": m["sharpe"] >= bh["sharpe"],
    }


def ejecutar() -> list[dict]:
    if any(e["datos"].get("lote") == LOTE for e in registro.leer(registro.EXPERIMENTOS)):
        raise SystemExit(f"El lote {LOTE} ya se ejecutó: repetirlo sería un experimento nuevo con otro nombre.")
    velas = cargar_velas(FICHERO)
    sha = hashlib.sha256(FICHERO.read_bytes()).hexdigest()
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=registro.RAIZ,
                            capture_output=True, text=True).stdout.strip()
    bh = metricas(backtest(velas, estrategias.buy_hold, BINANCE_SPOT))
    ideas = [e["datos"] for e in registro.leer(registro.IDEAS) if e["datos"]["estado"] != "descartada"]
    filas = []
    for idea in ideas:
        for var in idea["configuraciones_permitidas"]:
            f = estrategias.crear(idea["id"], var)
            m = metricas(backtest(velas, f, BINANCE_SPOT))
            extra = {}
            if requiere_costes_x2_x3(m):
                for k in (2, 3):
                    extra[f"x{k}"] = _redondear(metricas(backtest(velas, f, BINANCE_SPOT.x(k))))
            fila = {
                "lote": LOTE, "estrategia_id": idea["id"], "variante": var, "estado_idea": idea["estado"],
                "periodo": [velas[0].fecha.isoformat(), velas[-1].fecha.isoformat()],
                "datos_sha256": sha, "codigo_commit": commit, "costes_por_lado": BINANCE_SPOT.por_lado(),
                "criterios_version": CRITERIOS["version"],
                "metricas": _redondear(m), "costes_multiplicados": extra,
                "buy_hold": _redondear(bh), "criterios": aprueba(m, bh), "alertas": alertas(m, bh),
            }
            fila["aprobada_train"] = all(fila["criterios"].values())
            filas.append(fila)
    # Se calcula todo antes de escribir: si algo falla a medias, el registro no queda con un lote incompleto.
    for fila in filas:
        registro.registrar_experimento(fila)
    _escribir_tabla(filas, bh)
    return filas


def _pct(x: float) -> str:
    return f"{x * 100:,.1f} %".replace(",", " ")


def _escribir_tabla(filas: list[dict], bh: dict) -> None:
    variantes = {}
    for f in filas:
        variantes[f["estrategia_id"]] = variantes.get(f["estrategia_id"], 0) + 1
    l = [
        "# Resultados en TRAIN (Prompt 4)", "",
        f"Generado por `python -m copilot train` (lote `{LOTE}`). Periodo {filas[0]['periodo'][0]} a "
        f"{filas[0]['periodo'][1]}, BTC/USDT Binance spot, velas diarias, costes {_pct(BINANCE_SPOT.por_lado())} por lado.",
        "Cada fila está anotada en `registros/experimentos.jsonl`. Rentabilidades históricas: no predicen el futuro.", "",
        "| Estrategia | Variantes probadas | Variante | Operaciones | Rentabilidad | Sharpe | Drawdown máx. | Supera B&H (rent. / DD / Sharpe) | Avisos |",
        "|---|---|---|---|---|---|---|---|---|",
        f"| **Buy & Hold** | – | – | 1 | {_pct(bh['rentabilidad'])} | {bh['sharpe']:.2f} | {_pct(bh['max_drawdown'])} | referencia | |",
    ]
    for f in filas:
        m, c = f["metricas"], f["criterios"]
        marca = " / ".join("sí" if c[k] else "no" for k in ("rentabilidad", "drawdown", "sharpe"))
        if f["aprobada_train"]:
            marca = f"**{marca} → APRUEBA**"
        avisos = list(f["alertas"])
        if f["estado_idea"] == "experimental":
            avisos.append("EXPERIMENTAL")
        for k, mk in f["costes_multiplicados"].items():
            avisos.append(f"costes {k}: {_pct(mk['rentabilidad'])}, Sharpe {mk['sharpe']:.2f}")
        l.append(f"| {f['estrategia_id']} | {variantes[f['estrategia_id']]} | {f['variante']} | {m['operaciones']} | "
                 f"{_pct(m['rentabilidad'])} | {m['sharpe']:.2f} | {_pct(m['max_drawdown'])} | {marca} | "
                 f"{'; '.join(avisos)} |")
    l += ["", f"Total de variantes probadas (contador acumulado): {len(filas)}."]
    SALIDA.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
