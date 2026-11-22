"""Intradía en QQQ (D48): ruptura del rango de apertura de 5 minutos (Zarattini y Aziz, 2023), solo compra.

Solo análisis y paper trading. Cada decisión usa únicamente velas de 5 minutos ya cerradas.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timedelta, timezone
from math import sqrt
from typing import NamedTuple, Sequence
from zoneinfo import ZoneInfo

from copilot import paper, registro
from copilot.costes import Costes

NY = ZoneInfo("America/New_York")
COSTES = Costes(comision=0.0, medio_spread=0.0002, slippage=0.0003)  # 0,05 % por lado (D42)
EXPOSICION_MAX, RIESGO, OBJETIVO_R = 0.25, 0.01, 10.0
APERTURA, CIERRE = time(9, 30), time(16, 0)
CARPETA = registro.REGISTROS / "nasdaq_intradia"
RUTAS = {"senales": CARPETA / "senales.jsonl", "paper": CARPETA / "paper.jsonl"}


class Barra(NamedTuple):
    hora: datetime  # inicio de la vela, hora de Nueva York
    open: float
    high: float
    low: float
    close: float
    volumen: float


def descargar(rango: str = "60d", simbolo: str = "QQQ") -> list[Barra]:
    """Velas de 5 minutos del horario normal de bolsa (Yahoo Finance, público, sin claves)."""
    q = urllib.parse.urlencode({"interval": "5m", "range": rango, "includePrePost": "false"})
    req = urllib.request.Request(f"https://query1.finance.yahoo.com/v8/finance/chart/{simbolo}?{q}",
                                 headers={"User-Agent": "Mozilla/5.0 (btc-copilot-research)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode("utf-8"))["chart"]["result"][0]
    qd, out = d["indicators"]["quote"][0], []
    for i, ts in enumerate(d.get("timestamp", [])):
        vals = [qd[k][i] for k in ("open", "high", "low", "close", "volume")]
        if all(v is not None for v in vals):
            h = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(NY)
            if APERTURA <= h.time() < CIERRE:
                out.append(Barra(h, *map(float, vals)))
    return out


def sesiones(barras: Sequence[Barra]) -> dict[date, list[Barra]]:
    out: dict[date, list[Barra]] = {}
    for b in sorted(barras, key=lambda b: b.hora):
        out.setdefault(b.hora.date(), []).append(b)
    return out


def eventos_del_dia(barras: Sequence[Barra]) -> list[dict]:
    """Lo que la regla hace con las velas CERRADAS de un día: [] o [entrada] o [entrada, salida]."""
    if len(barras) < 2 or barras[0].hora.time() != APERTURA:
        return []
    b0, b1 = barras[0], barras[1]
    if not b0.close > b0.open:  # primera vela bajista o plana: no se opera
        return []
    entrada, stop = b1.open, b0.low
    r = entrada - stop
    if r <= 0:
        return []
    objetivo = entrada + OBJETIVO_R * r
    expo = min(EXPOSICION_MAX, RIESGO / (r / entrada))
    ev = [{"tipo": "entrada", "hora": b1.hora.isoformat(), "precio": entrada, "exposicion": expo, "stop": stop,
           "objetivo": objetivo, "rango": [b0.low, b0.high]}]
    for b in barras[1:]:
        if b.low <= stop:  # el stop tiene prioridad (conservador); si abre por debajo, sale a la apertura
            ev.append({"tipo": "salida", "hora": b.hora.isoformat(), "precio": min(stop, b.open), "motivo": "stop"})
            return ev
        if b.high >= objetivo:
            ev.append({"tipo": "salida", "hora": b.hora.isoformat(), "precio": max(objetivo, b.open), "motivo": "objetivo"})
            return ev
    ultima = barras[-1]
    if (ultima.hora + timedelta(minutes=5)).time() >= CIERRE:  # la sesión terminó: cierre del día
        ev.append({"tipo": "salida", "hora": ultima.hora.isoformat(), "precio": ultima.close, "motivo": "cierre"})
    return ev


def resultado_dia(ev: list[dict], costes: Costes = COSTES) -> float:
    """Cambio del capital ese día (0 si no se opera)."""
    if len(ev) < 2:
        return 0.0
    c = costes.por_lado()
    e, s = ev[0], ev[1]
    return e["exposicion"] * (s["precio"] * (1 - c) / (e["precio"] * (1 + c)) - 1)


def evaluar(barras: Sequence[Barra]) -> dict:
    ses = sesiones(barras)
    dias = sorted(ses)
    rets = [resultado_dia(eventos_del_dia(ses[d])) for d in dias]
    cierres = [ses[d][-1].close for d in dias]
    bh = [b / a - 1 for a, b in zip(cierres, cierres[1:])]

    def met(x):
        eq, pico, dd = 1.0, 1.0, 0.0
        for v in x:
            eq *= 1 + v
            pico = max(pico, eq)
            dd = min(dd, eq / pico - 1)
        m = sum(x) / len(x)
        sd = sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1)) if len(x) > 1 else 0.0
        return {"rentabilidad": eq - 1, "sharpe": m / sd * sqrt(252) if sd else 0.0, "max_drawdown": dd}
    ops = [eventos_del_dia(ses[d]) for d in dias]
    return {"dias": len(dias), "desde": dias[0].isoformat(), "hasta": dias[-1].isoformat(),
            "operaciones": sum(1 for e in ops if len(e) == 2), "ganadoras": sum(1 for r in rets if r > 0),
            "salidas": {m: sum(1 for e in ops if len(e) == 2 and e[1]["motivo"] == m) for m in ("stop", "objetivo", "cierre")},
            "estrategia": met(rets[1:]), "buy_hold": met(bh)}  # mismos días que Buy & Hold (desde el segundo)


# --- Paper trading en vivo ----------------------------------------------------------------------------

def ciclo(barras_hoy: Sequence[Barra], ahora: datetime, rutas: dict = RUTAS) -> list[dict]:
    """Añade al paper los eventos de hoy que aún no estén registrados. Solo usa velas cerradas (fin <= ahora)."""
    cerradas = [b for b in barras_hoy if b.hora + timedelta(minutes=5) <= ahora.astimezone(NY)]
    cuenta, ent = paper.cargar(rutas["paper"])
    if not ent:
        registro.anadir(rutas["paper"], {"tipo": "inicio", "fecha": ahora.date().isoformat(), "capital": paper.CAPITAL_INICIAL})
        cuenta, ent = paper.cargar(rutas["paper"])
    if paper.parada_manual_activa(ent) or not cerradas:
        return []
    hoy = cerradas[0].hora.date().isoformat()
    hechos = {(d["hora"], d["tipo_evento"]) for d in ent if d.get("tipo") == "ejecucion" and d.get("hora")}
    nuevos = []
    for ev in eventos_del_dia(cerradas):
        if (ev["hora"], ev["tipo"]) in hechos:
            continue
        objetivo = ev["exposicion"] if ev["tipo"] == "entrada" else 0.0
        e = paper.simular_ejecucion(cuenta, objetivo, ev["precio"], hoy, COSTES)
        if e is None:
            continue
        e.update(tipo="ejecucion", tipo_evento=ev["tipo"], hora=ev["hora"], motivo=ev.get("motivo"))
        registro.anadir(rutas["paper"], e)
        cuenta.aplicar(e)
        just = ([f"Primera vela de 5 min alcista ({ev['rango'][0]:,.2f}-{ev['rango'][1]:,.2f}): compra en la apertura de la "
                 f"segunda; stop {ev['stop']:,.2f}, objetivo {ev['objetivo']:,.2f} (10R)."] if ev["tipo"] == "entrada" else
                [f"Salida por {ev['motivo']} a {ev['precio']:,.2f}."])
        s = {"tipo": "senal", "vela": hoy, "hora": ev["hora"], "activo": "QQQ (Nasdaq-100)", "par": "QQQ, velas de 5 min",
             "decision": "COMPRA" if ev["tipo"] == "entrada" else "VENTA", "precio_referencia": ev["precio"],
             "exposicion_objetivo": objetivo, "justificacion": just,
             "invalidacion": [f"Se invalida si toca {ev['stop']:,.2f} (stop) en cualquier vela de 5 min."] if ev["tipo"] == "entrada" else [],
             "avisos": [], "posiciones": {"I01": 1.0 if objetivo else 0.0},
             "estado_validacion": "EXPERIMENTAL: probada solo con 60 días de datos (D48). No es una estrategia validada."}
        registro.anadir(rutas["senales"], s)
        nuevos.append(s)
    ultima = cerradas[-1]
    if (ultima.hora + timedelta(minutes=5)).time() >= CIERRE and not any(
            d.get("tipo") == "valoracion" and d["fecha"] == hoy for d in ent):
        registro.anadir(rutas["paper"], {"tipo": "valoracion", "fecha": hoy, "precio": ultima.close,
                                         "valor": cuenta.valor(ultima.close), "exposicion": cuenta.exposicion(ultima.close)})
    return nuevos


def en_horario(ahora: datetime) -> bool:
    ny = ahora.astimezone(NY)
    return ny.weekday() < 5 and time(9, 35) <= ny.time() <= time(16, 10)


# --- I02: flujo de la Day Trader skill en acciones (D52) ------------------------------------------------

NO_ENTRADAS_DESPUES, FUERA = time(15, 30), time(15, 50)  # la vela de las 15:50 cierra a las 15:55 (flat_by)


def senal_skill(barras: Sequence[Barra]) -> int | None:
    """Índice de la primera vela que CIERRA sobre el máximo del rango 9:30-9:45 (o None)."""
    if len(barras) < 4 or [b.hora.time() for b in barras[:3]] != [time(9, 30), time(9, 35), time(9, 40)]:
        return None
    alto = max(b.high for b in barras[:3])
    for j in range(3, len(barras)):
        if (barras[j].hora + timedelta(minutes=5)).time() > NO_ENTRADAS_DESPUES:
            return None
        if barras[j].close > alto:
            return j
    return None


def operar_skill(barras: Sequence[Barra], j: int) -> list[dict]:
    """Entrada en la apertura de la vela j+1; stop or-mid; objetivo 2R; fuera con la vela de las 15:50."""
    if j + 1 >= len(barras):
        return []
    alto, bajo = max(b.high for b in barras[:3]), min(b.low for b in barras[:3])
    stop, entrada = (alto + bajo) / 2, barras[j + 1].open
    r = entrada - stop
    if r <= 0:
        return []
    objetivo = entrada + 2 * r
    ev = [{"tipo": "entrada", "hora": barras[j + 1].hora.isoformat(), "precio": entrada, "stop": stop,
           "objetivo": objetivo, "exposicion": min(EXPOSICION_MAX, RIESGO / (r / entrada))}]
    for b in barras[j + 1:]:
        if b.low <= stop:
            ev.append({"tipo": "salida", "hora": b.hora.isoformat(), "precio": min(stop, b.open), "motivo": "stop"})
            return ev
        if b.high >= objetivo:
            ev.append({"tipo": "salida", "hora": b.hora.isoformat(), "precio": max(objetivo, b.open), "motivo": "objetivo"})
            return ev
        if b.hora.time() >= FUERA:
            ev.append({"tipo": "salida", "hora": b.hora.isoformat(), "precio": b.close, "motivo": "15:55"})
            return ev
    return ev


def elegir_skill(dia: dict[str, Sequence[Barra]]) -> tuple[str, int] | None:
    """La acción que da señal antes; empate: la más negociada hasta esa vela (precio x volumen)."""
    mejores = []
    for s, barras in dia.items():
        j = senal_skill(barras)
        if j is not None:
            mejores.append((barras[j].hora, -sum(b.close * b.volumen for b in barras[: j + 1]), s, j))
    return (min(mejores)[2], min(mejores)[3]) if mejores else None
