"""Segunda búsqueda, Prompts 6 y 7: cartera (una sola estrategia) y exposición de N1 L=4 (reglas D30)."""

from __future__ import annotations

from copilot import cartera as ca, estrategias, evaluacion_test, registro, riesgo, robustez, train
from copilot.estrategias_iniciales import COMUN
from copilot.motor import backtest, cargar_velas, pct, recortar

LOTE = "busqueda2-riesgo-v1"
SALIDA = registro.RAIZ / "docs" / "riesgo_v2.md"
COMPONENTE = ("N1", "L=4")
EXPOSICIONES = (25, 50, 75, 100)
DD_MAX = 0.35


def registrar_idea() -> None:
    if any(e["datos"]["id"] == "R2" for e in registro.leer(registro.IDEAS)):
        return
    registro.anadir(registro.IDEAS, {
        **COMUN, "id": "R2", "nombre": "Exposición fija sobre N1 L=4", "familia": "Riesgo", "estado": "registrada",
        "busqueda": 2, "regla_exacta": "Exposición = k x posición de N1 L=4 (0 o 1), sin apalancamiento. Ver D30.",
        "configuraciones_permitidas": [f"exposicion={k}%" for k in EXPOSICIONES]})


def _epocas() -> dict:
    """Resultado de N1 L=4 (con senales = exposición diaria) y de Buy & Hold en cada época."""
    f = estrategias.crear(*COMPONENTE)
    v_tr, v_o = cargar_velas(train.FICHERO), cargar_velas(robustez.FICHERO)
    v_tt = v_tr + cargar_velas(evaluacion_test.FICHERO)
    out = {}
    for ep, velas, i0 in (("TRAIN", v_tr, 0), ("otra época", v_o, 0), ("TEST", v_tt, len(v_tr))):
        r, bh = backtest(velas, f), backtest(velas, estrategias.buy_hold)
        x = ca.exposiciones(r)
        if i0:
            r, bh, x = recortar(r, i0), recortar(bh, i0), x[i0:]
        r.senales = x
        out[ep] = {"r": r, "bh": bh, "velas": velas[i0:]}
    return out


def ejecutar() -> dict:
    if train._ya_ejecutado(LOTE):
        raise SystemExit(f"El lote {LOTE} ya se ejecutó.")
    registrar_idea()
    ep = _epocas()
    res, filas = {}, []
    for nombre, d in ep.items():
        res[nombre] = {"bh": riesgo.medir(d["bh"]),
                       "corr": ca.correlacion(ca.rents(d["r"]), ca.rents(d["bh"]))}
        for k in EXPOSICIONES:
            r, ruina = riesgo.escalar(d["r"], d["velas"], k / 100)
            m = riesgo.medir(r, ruina)
            res[nombre][k] = m
            filas.append({"lote": LOTE, "estrategia_id": "R2", "variante": f"exposicion={k}%", "epoca": nombre,
                          "componente": list(COMPONENTE), "metricas": train._redondear(m)})
    adm = {k: all(res[e][k]["max_drawdown"] >= -DD_MAX and not res[e][k]["ruina"] for e in ("TRAIN", "otra época"))
           for k in EXPOSICIONES}
    cand = [k for k in EXPOSICIONES if adm[k]]
    if cand:
        mejor = max(res["TRAIN"][k]["sharpe"] for k in cand)
        elegida = min(k for k in cand if mejor - res["TRAIN"][k]["sharpe"] < 0.05)
    else:
        elegida = max(EXPOSICIONES, key=lambda k: min(res[e][k]["max_drawdown"] for e in ("TRAIN", "otra época")))
    for f in filas:  # todo calculado antes de escribir
        registro.registrar_experimento(f)
    _escribir(res, adm, elegida, bool(cand))
    return {"res": res, "elegida": elegida, "admisibles": adm}


def _escribir(res, adm, elegida, hay) -> None:
    l = ["# Cartera y riesgo, segunda búsqueda (Prompts 6 y 7)", "",
         "Generado por `python -m copilot riesgo2`. Reglas fijadas antes de ejecutar: `docs/decisiones.md`, D30.",
         f"Única estrategia superviviente: N1 L=4 (EXPERIMENTAL). Sin apalancamiento.", "",
         "## Prompt 6: cartera", "",
         "Con una sola estrategia no hay combinación posible: la cartera es N1 L=4 con todo su peso.", "",
         "| Época | Correlación diaria con Buy & Hold |", "|---|---|"]
    l += [f"| {e} | {d['corr']:.2f} |" for e, d in res.items()]
    l += ["", "## Prompt 7: exposición", ""]
    for e, d in res.items():
        l += [f"### {e}", "", "| Exposición | CAGR | Sharpe | Volatilidad | Drawdown máx. | Peor día | Peor mes | Exposición media | Admisible |",
              "|---|---|---|---|---|---|---|---|---|"]
        for k in EXPOSICIONES:
            m = d[k]
            marca = "**ELEGIDA**" if k == elegida else ("sí" if adm[k] else "no")
            l.append(f"| {k} % | {pct(m['cagr'])} | {m['sharpe']:.2f} | {pct(m['vol_anual'])} | {pct(m['max_drawdown'])} | "
                     f"{pct(m['peor_dia'])} | {pct(m['peor_mes'])} | {pct(m['exposicion_media'])} | {marca} |")
        b = d["bh"]
        l += [f"| Buy & Hold | {pct(b['cagr'])} | {b['sharpe']:.2f} | {pct(b['vol_anual'])} | {pct(b['max_drawdown'])} | "
              f"{pct(b['peor_dia'])} | {pct(b['peor_mes'])} | 100 % | – |", ""]
    l += [("Regla D30: " + (f"exposición elegida **{elegida} %**." if hay else
                           f"ninguna exposición es admisible; se elige la de menor drawdown en la peor época: {elegida} %.")),
          "", "Con la misma estrategia, subir la exposición multiplica ganancias y pérdidas por igual: el Sharpe no cambia.",
          "La regla elige la menor exposición que cumple el límite del 35 % de drawdown en TRAIN y en la otra época.", ""]
    SALIDA.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
