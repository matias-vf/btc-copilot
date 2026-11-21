"""Comprobación automática de anticipación (look-ahead).

Para varios cortes t se alteran al azar todas las velas desde t+1. Si la estrategia o el
motor fueran causales, las señales y el capital hasta t no cambian. Si cambian, alguien
está mirando el futuro.
"""

from __future__ import annotations

import random
from typing import Callable, Sequence

from copilot.costes import BINANCE_SPOT, Costes
from copilot.motor import Estrategia, Vela, backtest

# Recibe TODAS las velas con las que se va a probar y devuelve la estrategia. Así, si una
# estrategia se construye precalculando algo sobre la serie completa, la alteración la alcanza.
Fabrica = Callable[[Sequence[Vela]], Estrategia]


def _alterar(velas: Sequence[Vela], semilla: int) -> list[Vela]:
    rnd = random.Random(semilla)
    out = []
    for v in velas:
        k = rnd.uniform(0.5, 1.5)
        out.append(v._replace(open=v.open * k, high=v.high * k * 1.05, low=v.low * k * 0.95,
                              close=v.close * k, volumen=v.volumen * rnd.uniform(0.1, 3)))
    return out


def comprobar(velas: Sequence[Vela], fabrica: Fabrica, costes: Costes = BINANCE_SPOT,
              cortes: Sequence[int] | None = None, semilla: int = 7) -> list[str]:
    """Devuelve la lista de problemas encontrados (vacía = sin anticipación detectada)."""
    n = len(velas)
    cortes = cortes or [n // 4, n // 2, (3 * n) // 4, n - 2]
    base = backtest(velas, fabrica(velas), costes)
    problemas = []
    for t in cortes:
        alterado = list(velas[: t + 1]) + _alterar(velas[t + 1:], semilla + t)
        r = backtest(alterado, fabrica(alterado), costes)
        if r.senales[: t + 1] != base.senales[: t + 1]:
            problemas.append(f"corte {velas[t].fecha}: la señal cambia al alterar el futuro")
        if r.equity[: t + 1] != base.equity[: t + 1]:
            problemas.append(f"corte {velas[t].fecha}: el capital cambia al alterar el futuro")
    return problemas
