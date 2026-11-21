"""Segunda búsqueda, Prompt 5: otra época, TEST como segunda validación, costes, superficie y regímenes (D28)."""

from __future__ import annotations

from copilot import estrategias, evaluacion_test, registro, robustez, train, train2
from copilot.costes import BINANCE_SPOT
from copilot.motor import backtest, cargar_velas, metricas, pct, recortar

LOTE_OTRA, LOTE_TEST = "busqueda2-otra-epoca-v1", "busqueda2-test-v1"
SALIDA = registro.RAIZ / "docs" / "robustez_v2.md"


def _lote(nombre):
    return [e["datos"] for e in registro.leer(registro.EXPERIMENTOS) if e["datos"].get("lote") == nombre]


def pasa_costes(f: dict) -> bool:
    """D28 regla 1: con más de una orden por semana, también debe aprobar con costes x2."""
    x2 = f["costes_multiplicados"].get("x2")
    return x2 is None or all(x2["criterios"].values())


def ejecutar() -> dict:
    if train._ya_ejecutado(LOTE_OTRA) or train._ya_ejecutado(LOTE_TEST):
        raise SystemExit("La robustez de la segunda búsqueda ya se ejecutó.")
    ideas = train2.ideas_v2()
    otra = train.evaluar(LOTE_OTRA, ideas, robustez.FICHERO, train2.aprueba_v2, 2, alinear=True)
    test = train.evaluar(LOTE_TEST, ideas, evaluacion_test.FICHERO, train2.aprueba_v2, 2, alinear=False,
                         previas=train.FICHERO)
    for f in otra + test:  # todo calculado antes de escribir
        registro.registrar_experimento(f)
    tr = {(f["estrategia_id"], f["variante"]): f for f in _lote(train2.LOTE)}
    o = {(f["estrategia_id"], f["variante"]): f for f in otra}
    t = {(f["estrategia_id"], f["variante"]): f for f in test}
    conservadas = [k for k in tr if tr[k]["aprobada_train"] and pasa_costes(tr[k])
                   and o[k]["aprobada_train"] and t[k]["aprobada_train"]]
    out = {"tr": tr, "o": o, "t": t, "conservadas": conservadas}
    _escribir(out)
    return out


def _regimenes(k) -> list[str]:
    f = estrategias.crear(*k)
    v_tr, v_o = cargar_velas(train.FICHERO), cargar_velas(robustez.FICHERO)
    v_tt = v_tr + cargar_velas(evaluacion_test.FICHERO)
    i0 = len(v_tr)
    epocas = {"TRAIN": (v_tr, backtest(v_tr, f), backtest(v_tr, estrategias.buy_hold)),
              "otra": (v_o, backtest(v_o, f), backtest(v_o, estrategias.buy_hold)),
              "TEST": (v_tt[i0:], recortar(backtest(v_tt, f), i0), recortar(backtest(v_tt, estrategias.buy_hold), i0))}
    filas = []
    for ep, (velas, r, bh) in epocas.items():
        reg = robustez.regimenes(velas)
        celdas = [f"{pct(robustez.rent_en_meses(r, m))} ({pct(robustez.rent_en_meses(bh, m))})" for m in reg.values()]
        filas.append(f"| {k[0]} {k[1]} | {ep} | " + " | ".join(celdas) + " |")
    return filas


def _escribir(out) -> None:
    tr, o, t = out["tr"], out["o"], out["t"]
    si = lambda x: "**sí**" if x else "no"
    l = ["# Robustez y segunda validación, segunda búsqueda (Prompt 5)", "",
         "Generado por `python -m copilot robustez2`. Reglas fijadas antes de ejecutar: `docs/decisiones.md`, D28.",
         "Criterio v2: drawdown menor que Buy & Hold y Sharpe igual o mayor, en la misma ventana. "
         f"Costes x1 = {BINANCE_SPOT.por_lado() * 100:.2f} % por lado.",
         "**Aviso:** TEST ya se vio en la primera búsqueda; es una segunda validación con sesgo, no una prueba limpia.", "",
         "## Las tres épocas lado a lado (todas las variantes)", "",
         "| Variante | TRAIN Sharpe (B&H) | TRAIN DD (B&H) | Costes | Otra Sharpe (B&H) | Otra DD (B&H) | TEST rent. (B&H) | TEST Sharpe (B&H) | TEST DD (B&H) | ¿Se conserva? |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for k in tr:
        a, b, c = tr[k], o[k], t[k]
        txt = lambda f, x: f"{f['metricas'][x]:.2f} ({f['buy_hold'][x]:.2f})" if x == "sharpe" else \
            f"{pct(f['metricas'][x])} ({pct(f['buy_hold'][x])})"
        etiqueta = lambda f: (" ✓" if f["aprobada_train"] else " ✗")
        l.append(f"| {k[0]} {k[1]} | {txt(a, 'sharpe')}{etiqueta(a)} | {txt(a, 'max_drawdown')} | "
                 f"{'ok' if pasa_costes(a) else '**falla x2**'} | {txt(b, 'sharpe')}{etiqueta(b)} | {txt(b, 'max_drawdown')} | "
                 f"{txt(c, 'rentabilidad')} | {txt(c, 'sharpe')}{etiqueta(c)} | {txt(c, 'max_drawdown')} | "
                 f"{si(k in out['conservadas'])} |")
    l += ["", "✓ / ✗ = aprueba o no el criterio v2 en esa época.", "", "## Superficie de parámetros: TRAIN frente a TEST", "",
          "| Estrategia | Variantes | Spearman Sharpe TRAIN-TEST | Sharpe >= B&H en TRAIN / otra / TEST |", "|---|---|---|---|"]
    for eid in sorted({k[0] for k in tr}):
        ks = [k for k in tr if k[0] == eid]
        rho = robustez.spearman([tr[k]["metricas"]["sharpe"] for k in ks], [t[k]["metricas"]["sharpe"] for k in ks])
        cuenta = " / ".join(f"{sum(d[k]['metricas']['sharpe'] >= d[k]['buy_hold']['sharpe'] for k in ks)} de {len(ks)}"
                            for d in (tr, o, t))
        l.append(f"| {eid} | {len(ks)} | {rho:.2f} | {cuenta} |")
    l += ["", "Spearman >= 0,5: orden estable; < 0: ruido. Con 2 o 3 variantes la medida es muy pobre.", ""]
    if out["conservadas"]:
        nombres = list(robustez.regimenes(cargar_velas(train.FICHERO)).keys())
        l += ["## Regímenes de mercado (variantes conservadas)", "",
              "Rentabilidad compuesta en los meses de cada régimen; entre paréntesis, Buy & Hold.", "",
              "| Variante | Época | " + " | ".join(nombres) + " |", "|---|---|" + "---|" * len(nombres)]
        for k in out["conservadas"]:
            l += _regimenes(k)
        l.append("")
    l += ["## Veredicto (regla D28.4)", "",
          ("Se conservan, como EXPERIMENTALES hasta superar el paper trading en vivo: "
           + ", ".join(f"{k[0]} {k[1]}" for k in out["conservadas"]) + "."
           if out["conservadas"] else "**Ninguna variante se conserva.**"), ""]
    SALIDA.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
