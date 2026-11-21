"""Motor de backtesting causal, en velas diarias.

Reglas que el propio motor impone:
- La estrategia solo recibe las velas hasta t incluida (una copia recortada): no puede ver t+1.
- La decisión tomada con el cierre de t se ejecuta en la apertura de t+1.
- La última vela no genera ninguna orden (su ejecución caería fuera de los datos, en TEST).
- La posición abierta al final se valora como si se vendiera al último cierre, restando el coste de salida.
- Exposición entre 0 (liquidez) y 1 (todo en BTC). Sin apalancamiento ni cortos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from math import sqrt
from pathlib import Path
from typing import Callable, NamedTuple, Sequence

from copilot import datos
from copilot.costes import BINANCE_SPOT, Costes


class Vela(NamedTuple):
    fecha: date
    open: float
    high: float
    low: float
    close: float
    volumen: float


# (velas hasta t incluida, exposición objetivo vigente) -> nueva exposición objetivo en [0, 1]
Estrategia = Callable[[Sequence[Vela], float], float]


def cargar_velas(ruta: Path = datos.DATOS / "btcusdt_binance_1d_train.csv") -> list[Vela]:
    return [Vela(date.fromisoformat(f[0]), *map(float, f[1:6])) for f in datos.cargar(ruta)]


@dataclass
class Resultado:
    capital: float
    fechas: list[date] = field(default_factory=list)
    equity: list[float] = field(default_factory=list)     # valor al cierre de cada vela
    senales: list[float] = field(default_factory=list)    # decisión tomada al cierre de cada vela
    ejecuciones: list[dict] = field(default_factory=list)
    costes_pagados: float = 0.0


def backtest(velas: Sequence[Vela], estrategia: Estrategia, costes: Costes = BINANCE_SPOT,
             capital: float = 100.0) -> Resultado:
    r = Resultado(capital=capital)
    tasa = costes.por_lado()
    efectivo, unidades, objetivo, pendiente = capital, 0.0, 0.0, None
    ultima = len(velas) - 1
    for t, v in enumerate(velas):
        if pendiente is not None and pendiente != objetivo:
            valor = efectivo + unidades * v.open
            actual = unidades * v.open
            deseado = pendiente * valor
            if deseado > actual:  # compra: el coste sale del efectivo, nunca queda en negativo
                nocional = (deseado - actual) / (1 + tasa)
                delta = nocional / v.open
            else:
                nocional = actual - deseado
                delta = -nocional / v.open
            coste = nocional * tasa
            efectivo -= delta * v.open + coste
            unidades += delta
            r.costes_pagados += coste
            r.ejecuciones.append({"fecha": v.fecha, "precio": v.open, "de": objetivo, "a": pendiente,
                                  "nocional": nocional, "coste": coste})
            objetivo = pendiente
        pendiente = None
        valor = efectivo + unidades * v.close
        if t == ultima:
            valor -= unidades * v.close * tasa  # valoración de liquidación
        r.fechas.append(v.fecha)
        r.equity.append(valor)
        if t < ultima:
            nuevo = float(estrategia(velas[: t + 1], objetivo))
            if not 0.0 <= nuevo <= 1.0:
                raise ValueError(f"{v.fecha}: exposición {nuevo} fuera de [0, 1]")
            pendiente = nuevo
            r.senales.append(nuevo)
        else:
            r.senales.append(objetivo)
    return r


def metricas(r: Resultado) -> dict:
    eq = [r.capital] + r.equity
    rets = [b / a - 1 for a, b in zip(eq, eq[1:])]
    media = sum(rets) / len(rets)
    var = sum((x - media) ** 2 for x in rets) / (len(rets) - 1) if len(rets) > 1 else 0.0
    sharpe = media / sqrt(var) * sqrt(365) if var > 0 else 0.0
    pico, mdd = eq[0], 0.0
    for x in eq:
        pico = max(pico, x)
        mdd = min(mdd, x / pico - 1)
    dias = len(r.equity)
    entradas = sum(1 for e in r.ejecuciones if e["de"] == 0 and e["a"] > 0)
    return {
        "rentabilidad": eq[-1] / r.capital - 1,
        "cagr": (eq[-1] / r.capital) ** (365 / dias) - 1,
        "sharpe": sharpe,
        "max_drawdown": mdd,
        "operaciones": entradas,
        "ejecuciones": len(r.ejecuciones),
        "ejecuciones_por_semana": len(r.ejecuciones) / (dias / 7),
        "costes_pagados": r.costes_pagados,
        "dias": dias,
    }


def requiere_costes_x2_x3(m: dict) -> bool:
    return m["ejecuciones_por_semana"] > 1


def alertas(m: dict, bh: dict) -> list[str]:
    """Señales de 'demasiado bueno'. Si hay alguna, se trata como posible error antes de enseñarlo."""
    a = []
    if m["sharpe"] > 2.0:
        a.append(f"Sharpe {m['sharpe']:.2f} > 2: muy raro en BTC diario")
    if m["cagr"] > bh["cagr"] + 0.5:
        a.append(f"CAGR {m['cagr']:.0%} supera a Buy & Hold en más de 50 puntos al año")
    if m["operaciones"] > 0 and m["max_drawdown"] > -0.15:
        a.append(f"Drawdown máximo {m['max_drawdown']:.0%}: demasiado pequeño para BTC 2017-2022")
    return a
