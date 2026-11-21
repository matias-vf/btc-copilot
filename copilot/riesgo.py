"""Prompt 7: gestión del riesgo y tamaño de posición sobre la cartera C1 (reglas en docs/decisiones.md, D13)."""

from __future__ import annotations

from copilot.motor import pct as _p

import hashlib
import subprocess
from math import sqrt

from copilot import cartera as ca, estrategias, registro, robustez, train
from copilot.costes import BINANCE_SPOT
from copilot.estrategias import _sma
from copilot.motor import Resultado, backtest, cargar_velas, metricas

LOTE = "prompt7-riesgo-v1"
SALIDA = registro.RAIZ / "docs" / "riesgo.md"
FUNDING_DIA = 0.0003      # 0,01 % cada 8 h, tasa base de Binance (supuesto documentado en D13)
MANTENIMIENTO = 0.005     # margen de mantenimiento: liquidación si se pierde el 99,5 % del capital
DD_MAX = 0.35
EXPOSICIONES = (25, 50, 75, 100, 150, 200)
RIESGOS = (1, 2, 5)
VOL_OBJ = (30, 45)
NIVEL_SALIDA = {
    ("T1", "sma_n=100"): lambda h: _sma(h, 100),
    ("B1", "N=20,M=10"): lambda h: min(v.low for v in h[-10:]) if len(h) >= 10 else None,
    ("B1", "N=55,M=20"): lambda h: min(v.low for v in h[-20:]) if len(h) >= 20 else None,
}


def dimensionar(base, nivel, r: float):
    """En cada entrada, exposición = min(1, r / distancia al nivel de salida); se mantiene hasta salir."""
    def f(h, pos):
        if base(h, 1.0 if pos > 0 else 0.0) == 0:
            return 0.0
        if pos > 0:
            return pos
        lvl, c = nivel(h), h[-1].close
        if lvl is None or lvl >= c:
            return 0.0
        return min(1.0, r / ((c - lvl) / c))
    return f


def _serie(fechas, equity, capital, expo) -> Resultado:
    r = Resultado(capital=capital)
    r.fechas, r.equity, r.senales = list(fechas), list(equity), list(expo)
    return r


def escalar(c: Resultado, velas, k: float) -> tuple[Resultado, bool]:
    """Exposición fija k sobre la cartera. k > 1: hipotético, con funding y liquidación.
    shortcut: k constante implica reajustar a diario; ese coste de reajuste no se cobra (pequeño frente al funding)."""
    rp, x = ca.rents(c), c.senales
    E, eq, ruina = c.capital, [], False
    for t in range(len(rp)):
        if not ruina:
            if k > 1 and x[t] > 0 and t > 0:
                peor = (velas[t].low / velas[t - 1].close - 1) * k * x[t]
                if peor <= -(1 - MANTENIMIENTO):
                    ruina = True
            E = 0.0 if ruina else E * (1 + k * rp[t] - FUNDING_DIA * max(k - 1, 0) * x[t])
        eq.append(E)
    return _serie(c.fechas, eq, c.capital, [k * v for v in x]), ruina


def vol_objetivo(c: Resultado, objetivo: float, ventana: int = 60) -> Resultado:
    """Multiplicador min(1, objetivo / vol 60 d de la cartera), fijado al cierre de cada domingo."""
    rp, x, tasa = ca.rents(c), c.senales, BINANCE_SPOT.por_lado()
    E, m, eq, expo = c.capital, 1.0, [], []
    for t in range(len(rp)):
        if t > 0 and c.fechas[t - 1].weekday() == 6 and t - 1 >= ventana:
            s = ca._std(rp[t - ventana:t]) * sqrt(365)
            nuevo = 1.0 if s == 0 else min(1.0, objetivo / s)
            E -= abs(nuevo - m) * x[t] * E * tasa
            m = nuevo
        E *= 1 + m * rp[t]
        eq.append(E)
        expo.append(m * x[t])
    return _serie(c.fechas, eq, c.capital, expo)


def medir(r: Resultado, ruina: bool = False) -> dict:
    m = metricas(r)
    rp = ca.rents(r)
    meses: dict[str, float] = {}
    for f, x in zip(r.fechas, rp):
        k = f.strftime("%Y-%m")
        meses[k] = (1 + meses.get(k, 0.0)) * (1 + x) - 1
    m.update({"vol_anual": ca._std(rp) * sqrt(365), "peor_dia": min(rp), "peor_mes": min(meses.values()),
              "exposicion_media": sum(r.senales) / len(r.senales), "ruina": ruina})
    for k in ("operaciones", "ejecuciones", "ejecuciones_por_semana", "costes_pagados"):
        m.pop(k, None)
    return m


def operaciones(r: Resultado) -> list[float]:
    """Resultado de cada operación cerrada, en % del capital del componente."""
    idx = {f: i for i, f in enumerate(r.fechas)}
    out, entrada = [], None
    for e in r.ejecuciones:
        i = idx[e["fecha"]]
        if e["de"] == 0 and e["a"] > 0:
            entrada = i
        elif e["a"] == 0 and entrada is not None:
            out.append(r.equity[i] / r.equity[entrada - 1] - 1)
            entrada = None
    return out


def _epoca(velas):
    base = {k: backtest(velas, estrategias.crear(*k)) for k in NIVEL_SALIDA}
    fechas = [v.fecha for v in velas]

    def montar(res):
        mangas = {g: [(ca.rents(res[k]), ca.exposiciones(res[k])) for k in res if k[0] == g] for g in ("B1", "T1")}
        return ca.cartera(fechas, mangas)

    c, hist = montar(base)
    configs, por_op = {}, {"sin límite": {k: operaciones(r) for k, r in base.items()}}
    for k in EXPOSICIONES:
        r, ruina = escalar(c, velas, k / 100)
        configs[f"exposicion={k}%"] = medir(r, ruina)
    for rr in RIESGOS:
        res = {k: backtest(velas, dimensionar(estrategias.crear(*k), NIVEL_SALIDA[k], rr / 100)) for k in NIVEL_SALIDA}
        configs[f"riesgo_por_operacion={rr}%"] = medir(montar(res)[0])
        por_op[f"{rr} %"] = {k: operaciones(r) for k, r in res.items()}
    for v in VOL_OBJ:
        configs[f"vol_objetivo={v}%"] = medir(vol_objetivo(c, v / 100))
    return {"configs": configs, "por_op": por_op, "c": c, "hist": hist, "base": base,
            "bh": medir(backtest(velas, estrategias.buy_hold))}


def admisibles(out) -> dict[str, bool]:
    ok = {}
    for nombre in out["TRAIN"]["configs"]:
        apal = nombre.startswith("exposicion=") and int(nombre.split("=")[1].rstrip("%")) > 100
        ok[nombre] = not apal and all(
            not d["configs"][nombre]["ruina"] and d["configs"][nombre]["max_drawdown"] >= -DD_MAX for d in out.values())
    return ok


def elegir(out) -> tuple[str, bool]:
    adm, cfg = admisibles(out), out["TRAIN"]["configs"]
    cand = [n for n, v in adm.items() if v]
    if cand:
        mejor = max(cfg[n]["sharpe"] for n in cand)
        empate = [n for n in cand if mejor - cfg[n]["sharpe"] < 0.05]
        return min(empate, key=lambda n: cfg[n]["exposicion_media"]), True
    sin_apal = [n for n in cfg if not (n.startswith("exposicion=") and int(n.split("=")[1].rstrip("%")) > 100)]
    return max(sin_apal, key=lambda n: min(d["configs"][n]["max_drawdown"] for d in out.values())), False


def ejecutar() -> dict:
    if any(e["datos"].get("lote") == LOTE for e in registro.leer(registro.EXPERIMENTOS)):
        raise SystemExit(f"El lote {LOTE} ya se ejecutó.")
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=registro.RAIZ,
                            capture_output=True, text=True).stdout.strip()
    out, filas = {}, []
    for ep, fich in (("TRAIN", train.FICHERO), ("otra época", robustez.FICHERO)):
        velas = cargar_velas(fich)
        out[ep] = _epoca(velas)
        for nombre, m in out[ep]["configs"].items():
            filas.append({"lote": LOTE, "estrategia_id": "R1", "variante": nombre, "epoca": ep,
                          "periodo": [velas[0].fecha.isoformat(), velas[-1].fecha.isoformat()],
                          "datos_sha256": hashlib.sha256(fich.read_bytes()).hexdigest(), "codigo_commit": commit,
                          "metricas": train._redondear(m)})
    for f in filas:
        registro.registrar_experimento(f)
    _escribir(out)
    return out




def _escribir(out) -> None:
    adm = admisibles(out)
    eleg, ok = elegir(out)
    l = ["# Gestión del riesgo y tamaño de posición (Prompt 7)", "",
         "Generado por `python -m copilot riesgo`. Reglas fijadas antes de ejecutar: `docs/decisiones.md`, D13.",
         "Base: cartera C1 (B1 20/10 + B1 55/20 + T1 SMA 100). **Provisional** hasta TRAIN frente a TEST.",
         "150 % y 200 % son **simulaciones hipotéticas**: el copiloto no usa apalancamiento.", "",
         "## 1. Comparación de configuraciones", ""]
    for ep, d in out.items():
        l += [f"### {ep}", "",
              "| Configuración | CAGR | Sharpe | Volatilidad | Drawdown máx. | Peor día | Peor mes | Exposición media | Ruina | Admisible |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        filas = list(d["configs"].items()) + [("Buy & Hold (referencia)", d["bh"])]
        for n, m in filas:
            marca = "**ELEGIDA**" if n == eleg else ("sí" if adm.get(n) else ("–" if n not in adm else "no"))
            l.append(f"| {n} | {_p(m['cagr'])} | {m['sharpe']:.2f} | {_p(m['vol_anual'])} | {_p(m['max_drawdown'])} | "
                     f"{_p(m['peor_dia'])} | {_p(m['peor_mes'])} | {_p(m['exposicion_media'])} | "
                     f"{'SÍ' if m['ruina'] else 'no'} | {marca} |")
        l.append("")
    l += [f"Regla de elección (D13): {'configuración admisible elegida' if ok else 'NINGUNA admisible; se elige la de menor drawdown en la peor época'}: **{eleg}**.", "",
          "## 2. Riesgo por operación (en % del capital de cada componente)", "",
          "| Regla | Componente | Operaciones | Peor operación | Mediana | Pérdidas mayores que el riesgo previsto |",
          "|---|---|---|---|---|---|"]
    for ep, d in out.items():
        for regla, comp in d["por_op"].items():
            r = None if regla == "sin límite" else float(regla.split()[0]) / 100
            for (e, v), ops in comp.items():
                if not ops:
                    continue
                med = sorted(ops)[len(ops) // 2]
                exc = "–" if r is None else str(sum(1 for x in ops if x < -r))
                l.append(f"| {ep}: {regla} | {e} {v} | {len(ops)} | {_p(min(ops))} | {_p(med)} | {exc} |")
    d = out["TRAIN"]
    rs = {k: ca.rents(r) for k, r in d["base"].items()}
    xs = {k: ca.exposiciones(r) for k, r in d["base"].items()}
    n = len(next(iter(xs.values())))
    cuenta = [0, 0, 0, 0]
    for t in range(n):
        cuenta[sum(1 for x in xs.values() if x[t] > 0)] += 1
    w_b1 = sum(h["pesos"]["B1"] for h in d["hist"]) / len(d["hist"])
    w = {("B1", "N=20,M=10"): w_b1 / 2, ("B1", "N=55,M=20"): w_b1 / 2, ("T1", "sma_n=100"): 1 - w_b1}
    sigma_p = ca._std(ca.rents(d["c"]))
    dr = sum(w[k] * ca._std(rs[k]) for k in rs) / sigma_p
    l += ["", "## 3. Operaciones correlacionadas y concentración (TRAIN)", "",
          f"- Días con 0 / 1 / 2 / 3 componentes comprados: {' / '.join(f'{c / n:.0%}' for c in cuenta)}.",
          f"- Ratio de diversificación (volatilidad media ponderada de los componentes / volatilidad de la cartera): {dr:.2f}. "
          "1,00 sería ninguna diversificación.",
          f"- Peso medio de B1: {w_b1:.0%}. Dos de los tres componentes son la misma estrategia (B1).",
          "- Concentración: el 100 % del riesgo está en un solo activo (BTC). Cuando los tres componentes compran a la vez, "
          "el riesgo real es el de una sola posición grande, no el de tres pequeñas.", ""]
    SALIDA.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
