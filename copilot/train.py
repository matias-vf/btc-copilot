"""Ejecución de lotes de variantes registradas (Prompt 4 de cada búsqueda). Cada variante se anota en experimentos.jsonl."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Callable

from copilot import datos, estrategias, registro
from copilot.costes import BINANCE_SPOT
from copilot.estrategias_iniciales import CRITERIOS
from copilot.motor import alertas, backtest, cargar_velas, metricas, pct, recortar, requiere_costes_x2_x3

LOTE = "prompt4-train-v1"
FICHERO = datos.DATOS / "btcusdt_binance_1d_train.csv"
SALIDA = registro.RAIZ / "docs" / "resultados_train.md"


def _redondear(m: dict) -> dict:
    return {k: (round(v, 6) if isinstance(v, float) else v) for k, v in m.items()}


def aprueba(m: dict, bh: dict) -> dict:
    """Criterio versión 1 (D3)."""
    return {
        "rentabilidad": m["rentabilidad"] > bh["rentabilidad"],
        "drawdown": abs(m["max_drawdown"]) < abs(bh["max_drawdown"]),
        "sharpe": m["sharpe"] >= bh["sharpe"],
    }


def _ya_ejecutado(lote: str) -> bool:
    return any(e["datos"].get("lote") == lote for e in registro.leer(registro.EXPERIMENTOS))


def evaluar(lote: str, ideas: list[dict], fichero: Path, aprueba_fn: Callable, criterios_version: int,
            alinear: bool) -> list[dict]:
    """Ejecuta todas las variantes de `ideas` sobre `fichero` y devuelve las filas (sin registrarlas).
    alinear=True (D27): estrategia y Buy & Hold se miden solo desde el primer día en que la variante puede operar."""
    velas = cargar_velas(fichero)
    sha = hashlib.sha256(fichero.read_bytes()).hexdigest()
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=registro.RAIZ,
                            capture_output=True, text=True).stdout.strip()
    r_bh = backtest(velas, estrategias.buy_hold, BINANCE_SPOT)
    filas = []
    for idea in ideas:
        for var in idea["configuraciones_permitidas"]:
            f = estrategias.crear(idea["id"], var)
            i0 = estrategias.calentamiento(idea["id"], var) + 1 if alinear else 0
            med = (lambda r: metricas(recortar(r, i0))) if i0 else metricas
            m, bh = med(backtest(velas, f, BINANCE_SPOT)), med(r_bh)
            extra = {}
            if requiere_costes_x2_x3(m):
                for k in (2, 3):
                    mk = med(backtest(velas, f, BINANCE_SPOT.x(k)))
                    extra[f"x{k}"] = {**_redondear(mk), "criterios": aprueba_fn(mk, bh)}
            crit = aprueba_fn(m, bh)
            filas.append({"lote": lote, "estrategia_id": idea["id"], "variante": var, "estado_idea": idea["estado"],
                          "periodo": [velas[i0].fecha.isoformat(), velas[-1].fecha.isoformat()],
                          "ventana_alineada": alinear, "datos_sha256": sha, "codigo_commit": commit,
                          "costes_por_lado": BINANCE_SPOT.por_lado(), "criterios_version": criterios_version,
                          "metricas": _redondear(m), "costes_multiplicados": extra, "buy_hold": _redondear(bh),
                          "criterios": crit, "alertas": alertas(m, bh), "aprobada_train": all(crit.values())})
    return filas


def registrar_y_tabla(filas: list[dict], salida: Path, titulo: str, nota: str) -> None:
    """Todo se calcula antes de escribir: si algo falla a medias, el registro no queda con un lote incompleto."""
    for f in filas:
        registro.registrar_experimento(f)
    n: dict[str, int] = {}
    for f in filas:
        n[f["estrategia_id"]] = n.get(f["estrategia_id"], 0) + 1
    claves = list(filas[0]["criterios"])
    l = [f"# {titulo}", "", f"Lote `{filas[0]['lote']}`. BTC/USDT Binance spot, velas diarias, costes "
         f"{BINANCE_SPOT.por_lado() * 100:.2f} % por lado. {nota}",
         "Cada fila está en `registros/experimentos.jsonl`. Rentabilidades históricas: no predicen el futuro.", "",
         f"| Estrategia | Variantes | Variante | Desde | Operaciones | Órdenes/semana | Rentabilidad | Sharpe | Drawdown máx. "
         f"| B&H en la misma ventana (rent. / Sharpe / DD) | Supera B&H ({' / '.join(claves)}) | Avisos |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for f in filas:
        m, b, c = f["metricas"], f["buy_hold"], f["criterios"]
        marca = " / ".join("sí" if c[k] else "no" for k in claves)
        if f["aprobada_train"]:
            marca = f"**{marca} → APRUEBA**"
        av = list(f["alertas"]) + (["EXPERIMENTAL"] if f["estado_idea"] == "experimental" else [])
        for k, mk in f["costes_multiplicados"].items():
            av.append(f"costes {k}: {pct(mk['rentabilidad'])}, Sharpe {mk['sharpe']:.2f}, "
                      f"{'aprueba' if all(mk['criterios'].values()) else 'NO aprueba'}")
        l.append(f"| {f['estrategia_id']} | {n[f['estrategia_id']]} | {f['variante']} | {f['periodo'][0]} | "
                 f"{m['operaciones']} | {m['ejecuciones_por_semana']:.2f} | {pct(m['rentabilidad'])} | {m['sharpe']:.2f} | "
                 f"{pct(m['max_drawdown'])} | {pct(b['rentabilidad'])} / {b['sharpe']:.2f} / {pct(b['max_drawdown'])} | "
                 f"{marca} | {'; '.join(av)} |")
    total = len(registro.leer(registro.EXPERIMENTOS))
    l += ["", f"Variantes de este lote: {len(filas)}. Experimentos acumulados en el registro: {total}."]
    salida.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")


def ejecutar() -> list[dict]:
    """Primera búsqueda (lote ya ejecutado el 2026-11-21; se niega a repetirlo)."""
    if _ya_ejecutado(LOTE):
        raise SystemExit(f"El lote {LOTE} ya se ejecutó: repetirlo sería un experimento nuevo con otro nombre.")
    ideas = [e["datos"] for e in registro.leer(registro.IDEAS) if e["datos"]["estado"] != "descartada"
             and e["datos"].get("busqueda", 1) == 1 and e["datos"]["familia"] not in ("Cartera", "Riesgo")]
    filas = evaluar(LOTE, ideas, FICHERO, aprueba, CRITERIOS["version"], alinear=False)
    registrar_y_tabla(filas, SALIDA, "Resultados en TRAIN (Prompt 4)", "Criterio versión 1 (D3).")
    return filas
