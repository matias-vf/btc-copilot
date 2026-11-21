"""N1D (D34): N1 con revisión diaria. TRAIN, otra época y TEST con el criterio v2. Una sola vez."""

from __future__ import annotations

from copilot import evaluacion_test, registro, robustez, robustez2, train, train2
from copilot.motor import pct

LOTES = {"TRAIN": "busqueda3-train-v1", "otra época": "busqueda3-otra-epoca-v1", "TEST": "busqueda3-test-v1"}
SALIDA = registro.RAIZ / "docs" / "n1d.md"


def idea() -> dict:
    return next(e["datos"] for e in registro.leer(registro.IDEAS) if e["datos"]["id"] == "N1D")


def ejecutar() -> dict:
    if any(train._ya_ejecutado(l) for l in LOTES.values()):
        raise SystemExit("N1D ya se evaluó.")
    i = [idea()]
    r = {"TRAIN": train.evaluar(LOTES["TRAIN"], i, train.FICHERO, train2.aprueba_v2, 2, alinear=True)[0],
         "otra época": train.evaluar(LOTES["otra época"], i, robustez.FICHERO, train2.aprueba_v2, 2, alinear=True)[0],
         "TEST": train.evaluar(LOTES["TEST"], i, evaluacion_test.FICHERO, train2.aprueba_v2, 2, alinear=False,
                               previas=train.FICHERO)[0]}
    for f in r.values():  # todo calculado antes de escribir
        registro.registrar_experimento(f)
    costes = robustez2.pasa_costes(r["TRAIN"])
    aprueba = costes and all(f["aprobada_train"] for f in r.values())
    l = ["# N1D: N1 con revisión diaria (D34)", "",
         "Generado por `python -m copilot n1d`. Reglas fijadas antes de ejecutar: `docs/decisiones.md`, D34.",
         "Criterio v2: drawdown menor que Buy & Hold y Sharpe igual o mayor, en la misma ventana.", "",
         "| Época | Operaciones | Órdenes/semana | Rentabilidad (B&H) | Sharpe (B&H) | Drawdown máx. (B&H) | Aprueba |",
         "|---|---|---|---|---|---|---|"]
    for ep, f in r.items():
        m, b = f["metricas"], f["buy_hold"]
        l.append(f"| {ep} | {m['operaciones']} | {m['ejecuciones_por_semana']:.2f} | {pct(m['rentabilidad'])} "
                 f"({pct(b['rentabilidad'])}) | {m['sharpe']:.2f} ({b['sharpe']:.2f}) | {pct(m['max_drawdown'])} "
                 f"({pct(b['max_drawdown'])}) | {'**sí**' if f['aprobada_train'] else 'no'} |")
    x2 = r["TRAIN"]["costes_multiplicados"].get("x2")
    l += ["", "Costes x2 en TRAIN: " + ("no hace falta (como mucho una orden por semana)." if x2 is None else
          f"Sharpe {x2['sharpe']:.2f}, drawdown {pct(x2['max_drawdown'])}: {'aprueba' if costes else 'NO aprueba'}."),
          "", "## Veredicto (D34)", "",
          ("**N1D aprueba todo**: entra en el copiloto como EXPERIMENTAL junto a N1 L=4 y podrá operar cualquier día "
           "(paper trading)." if aprueba else
           "**N1D no aprueba.** El copiloto sigue solo con N1 L=4 (decide los domingos) y el vigía sigue sin operar."), ""]
    SALIDA.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
    return {"r": r, "aprueba": aprueba, "costes": costes}
