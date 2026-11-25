"""Estrategia del vídeo «1 BOX Trading Strategy» (D63): ruptura del rango de los primeros 15 minutos y entrada en el
retroceso al borde roto. Velas de 5 minutos, compras y cortos, todo cerrado a las 15:55. Solo prueba histórica.
"""

from __future__ import annotations

import csv
import gzip
import json
from datetime import datetime, time
from math import sqrt
from statistics import NormalDist

from copilot import datos, qqq_intradia as qi, registro, train
from copilot.intradia import Barra, sesiones
from copilot.universo_eval import momentos

LOTE = "video-retroceso-v1"
SALIDA = registro.RAIZ / "docs" / "video_retroceso.md"
FIN_RANGO, SIN_ENTRADAS, ULTIMA = time(9, 45), time(15, 30), time(15, 50)


def operar_dia(b: list[Barra], lado_coste=qi.coste_lado) -> dict | None:
    """Una sesión de velas de 5 minutos -> la operación del día o None."""
    rango = [x for x in b if x.hora.time() < FIN_RANGO]
    if len(rango) < 3:
        return None
    alto, bajo = max(x.high for x in rango), min(x.low for x in rango)
    medio = (alto + bajo) / 2
    resto = [x for x in b if x.hora.time() >= FIN_RANGO]
    lado, i = 0, 0
    while i < len(resto) and not lado:  # 1) primera ruptura con cierre fuera
        c = resto[i].close
        lado = 1 if c > alto else -1 if c < bajo else 0
        i += 1
    if not lado:
        return None
    borde = alto if lado > 0 else bajo
    entrada = None
    for j in range(i, len(resto)):  # 2) retroceso al borde
        x = resto[j]
        if x.hora.time() >= SIN_ENTRADAS:
            return None
        if (lado > 0 and x.low <= borde) or (lado < 0 and x.high >= borde):
            entrada = min(x.open, borde) if lado > 0 else max(x.open, borde)
            break
        if (lado > 0 and x.close < bajo) or (lado < 0 and x.close > alto):
            return None  # ruptura fallida antes del retroceso
    if entrada is None:
        return None
    riesgo = (entrada - medio) * lado
    if riesgo <= 0:
        return None  # ya abrió más allá del stop
    objetivo = entrada + lado * 2 * riesgo
    salida, motivo = None, None
    for x in resto[j:]:  # 3) gestión; en la vela de entrada solo cuenta lo que pasa en el borde o más allá
        if (lado > 0 and x.low <= medio) or (lado < 0 and x.high >= medio):
            salida, motivo = (min(x.open, medio) if lado > 0 else max(x.open, medio)) if x is not resto[j] else medio, "stop"
        elif x is not resto[j] and ((lado > 0 and x.high >= objetivo) or (lado < 0 and x.low <= objetivo)):
            # en la vela de entrada no se cuenta el objetivo: su máximo pudo ser anterior al retroceso
            salida, motivo = (max(x.open, objetivo) if lado > 0 else min(x.open, objetivo)), "objetivo"
        elif x.hora.time() >= ULTIMA:
            salida, motivo = x.close, "cierre"
        if motivo:
            break
    if not motivo:
        salida, motivo = resto[-1].close, "cierre"
    bruto = lado * (salida / entrada - 1)
    coste = lado_coste(entrada) + lado_coste(salida)
    return {"fecha": str(b[0].hora.date()), "lado": lado, "entrada": entrada, "salida": salida, "motivo": motivo,
            "bruto": bruto, "coste": coste, "riesgo": riesgo / entrada}


def _psr(sr: float, T: int, asim: float, curt: float) -> float:
    """Sharpe deflactado con N = 1: el umbral es Sharpe 0 (Bailey y López de Prado, sin corrección por pruebas)."""
    den = 1 - asim * sr + (curt - 1) / 4 * sr * sr
    return NormalDist().cdf(sr * sqrt(T - 1) / sqrt(den)) if den > 0 else 0.0


def _medir(ops: list[dict], x_costes: float = 1.0) -> dict:
    rets = [o["bruto"] - x_costes * o["coste"] for o in ops]
    rs = [r / o["riesgo"] for r, o in zip(rets, ops)]
    if len(rets) < 3:
        return {"operaciones": len(rets), "media_r": sum(rs) / len(rs) if rs else 0.0, "acierto": 0.0, "dsr": 0.0}
    mu, sd, a, c = momentos(rets)
    sr = mu / sd if sd else 0.0
    return {"operaciones": len(rets), "media_r": sum(rs) / len(rs), "acierto": sum(r > 0 for r in rets) / len(rets),
            "dsr": _psr(sr, len(rets), a, c),
            "media_r_sin_costes": sum(o["bruto"] / o["riesgo"] for o in ops) / len(ops)}


def _cargar_csv(nombre: str) -> list[Barra]:
    with open(datos.DATOS / nombre, encoding="utf-8") as f:
        return [Barra(datetime.fromisoformat(r[0]), *map(float, r[1:6])) for r in list(csv.reader(f))[1:]]


def _acciones() -> dict[str, list[Barra]]:
    with gzip.open(datos.DATOS / "acciones_5m_60d_hasta_2026-11-20.json.gz", "rt", encoding="utf-8") as f:
        return {s: [Barra(datetime.fromisoformat(r[0]), *map(float, r[1:6])) for r in filas]
                for s, filas in json.load(f).items()}


def ejecutar() -> dict:
    if train._ya_ejecutado(LOTE):
        raise SystemExit("La prueba de la estrategia del vídeo ya se ejecutó.")
    conjuntos = {"QQQ": {"QQQ": _cargar_csv("qqq_yahoo_5m_60d_hasta_2026-11-20.csv")},
                 "SPY": {"SPY": _cargar_csv("spy_yahoo_5m_60d_hasta_2026-11-24.csv")},
                 "233 acciones": _acciones()}
    res, regs = {}, []
    for nombre, series in conjuntos.items():
        ops, dias = [], 0
        for b in series.values():
            for dia in sesiones(b).values():
                dias += 1
                if len(dia) >= 70:  # sesiones completas (78 velas); fuera los días a medias y de cierre anticipado
                    o = operar_dia(dia)
                    if o:
                        ops.append(o)
        m = _medir(ops)
        m["media_r_costes_x2"] = _medir(ops, 2.0)["media_r"]
        m["dias"] = dias
        m["por_motivo"] = {k: sum(o["motivo"] == k for o in ops) for k in ("objetivo", "stop", "cierre")}
        m["criterios"] = {"30_operaciones": m["operaciones"] >= 30, "media_r_005": m["media_r"] >= 0.05,
                          "costes_x2": m["media_r_costes_x2"] > 0, "sharpe_deflactado": m["dsr"] >= 0.95}
        m["aprueba"] = all(m["criterios"].values())
        res[nombre] = m
        regs.append({"lote": LOTE, "estrategia_id": "V1", "variante": nombre, "aprueba": m["aprueba"],
                     "criterios": m["criterios"],
                     "metricas": {k: (round(v, 6) if isinstance(v, float) else v) for k, v in m.items()
                                  if k not in ("criterios", "aprueba")}})
    registro.registrar_experimentos(regs)
    l = ["# Estrategia del vídeo «1 BOX Trading Strategy»: prueba (D63, D64)", "",
         "Rango de los primeros 15 minutos, primera ruptura con cierre fuera, entrada en el retroceso al borde, stop en la "
         "mitad del rango, objetivo 2R, fuera a las 15:55. Velas de 5 minutos de Yahoo de los últimos 60 días. Costes IBKR.", "",
         "| Mercado | Días | Operaciones | Acierto | Media R sin costes | Media R con costes | Media R costes x2 | "
         "Objetivo / stop / cierre | Sharpe deflactado | Aprueba |", "|---|---|---|---|---|---|---|---|---|---|"]
    for k, m in res.items():
        pm = m["por_motivo"]
        l.append(f"| {k} | {m['dias']} | {m['operaciones']} | {m['acierto']:.0%} | {m.get('media_r_sin_costes', 0):+.3f} | "
                 f"{m['media_r']:+.3f} | {m['media_r_costes_x2']:+.3f} | {pm['objetivo']} / {pm['stop']} / {pm['cierre']} | "
                 f"{m['dsr']:.3f} | {'sí' if m['aprueba'] else 'no'} |")
    SALIDA.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
    return res
