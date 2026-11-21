"""Segunda búsqueda, Prompt 4: N1-N4 en TRAIN con el criterio versión 2 (D23) y la ventana alineada (D27)."""

from __future__ import annotations

from copilot import registro, train
from copilot.estrategias_v2 import CRITERIOS_V2

LOTE = "busqueda2-train-v2"  # el lote v1 (sin ventana alineada) queda en el registro
SALIDA = registro.RAIZ / "docs" / "resultados_train_v2_alineada.md"


def aprueba_v2(m: dict, bh: dict) -> dict:
    return {"drawdown": abs(m["max_drawdown"]) < abs(bh["max_drawdown"]), "sharpe": m["sharpe"] >= bh["sharpe"]}


def ideas_v2() -> list[dict]:
    return [e["datos"] for e in registro.leer(registro.IDEAS)
            if e["datos"].get("busqueda") == 2 and e["datos"]["familia"] not in ("Cartera", "Riesgo")]


def ejecutar() -> list[dict]:
    if train._ya_ejecutado(LOTE):
        raise SystemExit(f"El lote {LOTE} ya se ejecutó.")
    filas = train.evaluar(LOTE, ideas_v2(), train.FICHERO, aprueba_v2, CRITERIOS_V2["version"], alinear=True)
    train.registrar_y_tabla(filas, SALIDA, "Resultados en TRAIN, segunda búsqueda, ventana alineada (Prompt 4)",
                            "Criterio versión 2 (D23): drawdown menor que Buy & Hold y Sharpe igual o mayor. "
                            "Ventana alineada (D27): cada variante y Buy & Hold se miden desde el primer día en que "
                            "la variante puede operar.")
    return filas
