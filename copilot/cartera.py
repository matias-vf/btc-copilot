"""Prompt 6: correlaciones y cartera inversa a la volatilidad con reequilibrio mensual (reglas en D11)."""

from __future__ import annotations

import hashlib
import subprocess
from math import sqrt
from typing import Sequence

from copilot import estrategias, registro, robustez, train
from copilot.costes import BINANCE_SPOT, Costes
from copilot.motor import Resultado, backtest, cargar_velas, metricas

LOTE = "prompt6-cartera-v1"
SALIDA = registro.RAIZ / "docs" / "cartera.md"
VARIANTE = "componentes=B1(N=20,M=10|N=55,M=20)+T1(sma_n=100),ventana_vol=90,reequilibrio=mensual"
COMPONENTES = {"B1": [("B1", "N=20,M=10"), ("B1", "N=55,M=20")], "T1": [("T1", "sma_n=100")]}
VENTANA = 90


def rents(r: Resultado) -> list[float]:
    eq = [r.capital] + r.equity
    return [b / a - 1 for a, b in zip(eq, eq[1:])]


def exposiciones(r: Resultado) -> list[float]:
    """Exposición a BTC durante el día t = decisión tomada al cierre de t-1."""
    return [0.0] + r.senales[:-1]


def _std(x: Sequence[float]) -> float:
    m = sum(x) / len(x)
    return sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1))


def pesos(historia: dict[str, list[float]]) -> dict[str, float]:
    """historia: rentabilidades diarias pasadas de cada estrategia (solo hasta el cierre de hoy)."""
    n = len(historia)
    if any(len(h) < VENTANA for h in historia.values()):
        return {k: 1 / n for k in historia}
    inv = {k: (1 / s if (s := _std(h[-VENTANA:])) > 0 else 0.0) for k, h in historia.items()}
    tot = sum(inv.values())
    return {k: v / tot for k, v in inv.items()} if tot > 0 else {k: 1 / n for k in historia}


def cartera(fechas, mangas: dict[str, list[tuple[list[float], list[float]]]], costes: Costes = BINANCE_SPOT,
            capital: float = 100.0) -> tuple[Resultado, list[dict]]:
    """mangas: estrategia -> lista de (rentabilidades diarias, exposiciones) de sus variantes, a partes iguales."""
    tasa = costes.por_lado()
    sub = [(k, rr, xx, 1 / len(vs)) for k, vs in mangas.items() for rr, xx in vs]
    # Rentabilidad diaria de cada estrategia = media de sus variantes (solo para medir su volatilidad).
    r_est = {k: [sum(rr[t] for rr, _ in vs) / len(vs) for t in range(len(fechas))] for k, vs in mangas.items()}
    V, h = capital, None
    res, historial = Resultado(capital=capital), []
    for t, f in enumerate(fechas):
        if h is None or f.month != fechas[t - 1].month:
            w = pesos({k: r[:t] for k, r in r_est.items()})  # solo datos hasta el cierre de t-1
            nuevo = [w[k] * frac * V for k, _, _, frac in sub]
            if h is not None:
                delta_btc = sum((n - a) * xx[t] for n, a, (_, _, xx, _) in zip(nuevo, h, sub))
                coste = abs(delta_btc) * tasa
                res.costes_pagados += coste
                nuevo = [x * (V - coste) / V for x in nuevo]
            h = nuevo
            historial.append({"fecha": f.isoformat(), "pesos": {k: round(v, 4) for k, v in w.items()}})
        h = [x * (1 + rr[t]) for x, (_, rr, _, _) in zip(h, sub)]
        V = sum(h)
        res.fechas.append(f)
        res.equity.append(V)
        res.senales.append(0.0)
    return res, historial


def correlacion(a: list[float], b: list[float]) -> float:
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return cov / den if den else 0.0


def _epoca(velas):
    res = {f"{e} {v}": backtest(velas, estrategias.crear(e, v)) for vs in COMPONENTES.values() for e, v in vs}
    bh = backtest(velas, estrategias.buy_hold)
    mangas = {k: [(rents(res[f"{e} {v}"]), exposiciones(res[f"{e} {v}"])) for e, v in vs]
              for k, vs in COMPONENTES.items()}
    c, hist = cartera([v.fecha for v in velas], mangas)
    return res, bh, c, hist


def ejecutar() -> dict:
    if any(e["datos"].get("lote") == LOTE for e in registro.leer(registro.EXPERIMENTOS)):
        raise SystemExit(f"El lote {LOTE} ya se ejecutó.")
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=registro.RAIZ,
                            capture_output=True, text=True).stdout.strip()
    out, filas = {}, []
    for nombre, fichero in (("TRAIN", train.FICHERO), ("otra época", robustez.FICHERO)):
        velas = cargar_velas(fichero)
        res, bh, c, hist = _epoca(velas)
        mc, mb = metricas(c), metricas(bh)
        out[nombre] = {"res": res, "bh": bh, "c": c, "hist": hist, "mc": mc, "mb": mb}
        filas.append({"lote": LOTE, "estrategia_id": "C1", "variante": VARIANTE, "epoca": nombre,
                      "periodo": [velas[0].fecha.isoformat(), velas[-1].fecha.isoformat()],
                      "datos_sha256": hashlib.sha256(fichero.read_bytes()).hexdigest(), "codigo_commit": commit,
                      "metricas": train._redondear(mc), "buy_hold": train._redondear(mb),
                      "criterios": train.aprueba(mc, mb)})
    for f in filas:
        registro.registrar_experimento(f)
    _escribir(out)
    return out


def _p(x):
    return f"{x * 100:,.1f} %".replace(",", " ")


def _escribir(out) -> None:
    l = ["# Cartera combinada (Prompt 6)", "",
         "Generado por `python -m copilot cartera`. Reglas fijadas antes de ejecutar: `docs/decisiones.md`, D11.",
         "**Provisional:** B1 y T1 aún no han pasado la comprobación TRAIN frente a TEST (pendiente de «UNLOCK»).", ""]
    for ep, d in out.items():
        nombres = list(d["res"].keys()) + ["Buy & Hold"]
        series = [rents(r) for r in d["res"].values()] + [rents(d["bh"])]
        l += [f"## Correlación de rentabilidades diarias ({ep})", "",
              "| | " + " | ".join(nombres) + " |", "|---" * (len(nombres) + 1) + "|"]
        for n, a in zip(nombres, series):
            l.append(f"| {n} | " + " | ".join(f"{correlacion(a, b):.2f}" for b in series) + " |")
        l.append("")
    l += ["## Cartera frente a Buy & Hold", "",
          "| Época | | CAGR | Sharpe | Drawdown máx. | Rentabilidad total |", "|---|---|---|---|---|---|"]
    for ep, d in out.items():
        for nombre, m in (("Cartera C1", d["mc"]), ("Buy & Hold", d["mb"])):
            l.append(f"| {ep} | {nombre} | {_p(m['cagr'])} | {m['sharpe']:.2f} | {_p(m['max_drawdown'])} | "
                     f"{_p(m['rentabilidad'])} |")
        for nombre, r in d["res"].items():
            m = metricas(r)
            l.append(f"| {ep} | ({nombre} sola) | {_p(m['cagr'])} | {m['sharpe']:.2f} | {_p(m['max_drawdown'])} | "
                     f"{_p(m['rentabilidad'])} |")
    l += ["", "## Pesos de la cartera (TRAIN, cada reequilibrio mensual)", "",
          "| Mes | B1 | T1 |", "|---|---|---|"]
    for h in out["TRAIN"]["hist"]:
        l.append(f"| {h['fecha'][:7]} | {h['pesos']['B1']:.0%} | {h['pesos']['T1']:.0%} |")
    l += ["", f"Costes de reequilibrio pagados en TRAIN: {out['TRAIN']['c'].costes_pagados:.2f} USD sobre 100 USD iniciales.", ""]
    SALIDA.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
