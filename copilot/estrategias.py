"""Reglas exactas de las estrategias registradas en registros/ideas.jsonl.

Cada estrategia es una función (velas hasta t, exposición vigente) -> exposición objetivo.
Sin datos suficientes para calcular un indicador, la regla devuelve 0 (no operar).
"""

from __future__ import annotations

from math import log, sqrt
from typing import Sequence

from copilot.motor import Estrategia, Vela


def _sma(h: Sequence[Vela], n: int) -> float | None:
    if len(h) < n:
        return None
    return sum(v.close for v in h[-n:]) / n


def _rsi_wilder(h: Sequence[Vela], n: int) -> float | None:
    if len(h) < n + 1:
        return None
    cambios = [b.close - a.close for a, b in zip(h, h[1:])]
    sube = sum(max(c, 0) for c in cambios[:n]) / n
    baja = sum(max(-c, 0) for c in cambios[:n]) / n
    for c in cambios[n:]:
        sube = (sube * (n - 1) + max(c, 0)) / n
        baja = (baja * (n - 1) + max(-c, 0)) / n
    if baja == 0:
        return 100.0
    return 100 - 100 / (1 + sube / baja)


def buy_hold(h, pos):
    return 1.0


def t1_sma(n: int) -> Estrategia:
    def f(h, pos):
        s = _sma(h, n)
        return 1.0 if s is not None and h[-1].close > s else 0.0
    return f


def t1_cruce(rapida: int, lenta: int) -> Estrategia:
    def f(h, pos):
        a, b = _sma(h, rapida), _sma(h, lenta)
        return 1.0 if a is not None and b is not None and a > b else 0.0
    return f


def t2_tsmom(L: int) -> Estrategia:
    def f(h, pos):
        return 1.0 if len(h) > L and h[-1].close / h[-1 - L].close - 1 > 0 else 0.0
    return f


def b1_donchian(N: int, M: int) -> Estrategia:
    def f(h, pos):
        c = h[-1].close
        if pos == 0:
            return 1.0 if len(h) > N and c > max(v.high for v in h[-N - 1:-1]) else 0.0
        return 0.0 if len(h) > M and c < min(v.low for v in h[-M - 1:-1]) else 1.0
    return f


def m1_rsi2(u: float) -> Estrategia:
    def f(h, pos):
        c = h[-1].close
        if pos == 0:
            rsi, s200 = _rsi_wilder(h, 2), _sma(h, 200)
            return 1.0 if rsi is not None and s200 is not None and rsi < u and c > s200 else 0.0
        s5 = _sma(h, 5)
        return 0.0 if s5 is not None and c > s5 else 1.0
    return f


def _vol_anual(h: Sequence[Vela], w: int) -> float | None:
    if len(h) < w + 1:
        return None
    r = [log(b.close / a.close) for a, b in zip(h[-w - 1:], h[-w:])]
    m = sum(r) / w
    return sqrt(sum((x - m) ** 2 for x in r) / (w - 1)) * sqrt(365)


def p1_vol_objetivo(base: Estrategia, sigma_obj: float, w: int) -> Estrategia:
    def f(h, pos):
        # Último domingo (weekday 6) hasta t incluido: su cierre fija la exposición de la semana.
        i = len(h) - 1
        while i >= 0 and h[i].fecha.weekday() != 6:
            i -= 1
        sigma = _vol_anual(h[: i + 1], w) if i >= 0 else None
        if sigma is None:
            return 0.0
        e = 1.0 if sigma == 0 else min(1.0, sigma_obj / sigma)
        return base(h, 1.0 if pos > 0 else 0.0) * e
    return f


def crear(estrategia_id: str, variante: str) -> Estrategia:
    """Traduce una variante registrada (texto) en su función."""
    if estrategia_id == "BH":
        return buy_hold
    if estrategia_id == "T1":
        if variante.startswith("sma_n="):
            return t1_sma(int(variante.split("=")[1]))
        rapida, lenta = variante.split("=")[1].split("/")
        return t1_cruce(int(rapida), int(lenta))
    p = dict(kv.split("=", 1) for kv in variante.split(","))
    if estrategia_id == "T2":
        return t2_tsmom(int(p["L"]))
    if estrategia_id == "B1":
        return b1_donchian(int(p["N"]), int(p["M"]))
    if estrategia_id == "M1":
        return m1_rsi2(float(p["u"]))
    if estrategia_id == "P1":
        base = buy_hold if p["base"] == "buy_hold" else crear("T1", p["base"].split(":", 1)[1])
        return p1_vol_objetivo(base, float(p["sigma_obj"].rstrip("%")) / 100, int(p["ventana"]))
    raise ValueError(f"Estrategia desconocida: {estrategia_id}")
