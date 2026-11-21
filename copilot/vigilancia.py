"""Prompt 8: vigilancia diaria del deterioro de las estrategias y reglas de parada (reglas en D15)."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from math import exp, log, sqrt
from pathlib import Path
from typing import Sequence

from copilot import cartera as ca, estrategias, registro, riesgo
from copilot.costes import BINANCE_SPOT
from copilot.motor import Resultado, Vela, backtest

REGISTRO = registro.REGISTROS / "vigilancia.jsonl"
COMPONENTES = [("B1", "N=20,M=10"), ("B1", "N=55,M=20"), ("T1", "sma_n=100")]
CARTERA = "C1 al 25 %"
VENTANA_AZAR, N_AZAR = 365, 200
VENTANA_MOVIL = 180
MIN_VELAS = 400
EXPOSICION = 0.25


# --- Datos ------------------------------------------------------------------

def problemas_datos(velas: Sequence[Vela], ahora: datetime | None = None) -> list[str]:
    """Problemas que impiden generar señales hoy (D15, regla 3). Mira las dos últimas velas y la historia."""
    p = []
    if len(velas) < MIN_VELAS:
        p.append(f"solo {len(velas)} velas de historia (mínimo {MIN_VELAS})")
    if len(velas) < 2:
        return p
    a, b = velas[-2], velas[-1]
    if b.fecha == a.fecha:
        p.append(f"vela duplicada {b.fecha}")
    elif b.fecha != a.fecha + timedelta(days=1):
        p.append(f"falta al menos una vela entre {a.fecha} y {b.fecha}")
    if not (b.low <= min(b.open, b.close) and b.high >= max(b.open, b.close) and b.low > 0):
        p.append(f"OHLC incoherente el {b.fecha}")
    if a.close > 0 and abs(b.close / a.close - 1) > 0.5:
        p.append(f"el cierre se mueve {b.close / a.close - 1:+.0%} en un día")
    if a.close > 0 and abs(b.open / a.close - 1) > 0.05:
        p.append(f"la apertura se separa {b.open / a.close - 1:+.1%} del cierre anterior")
    if ahora is not None:
        cierre = datetime(b.fecha.year, b.fecha.month, b.fecha.day, tzinfo=timezone.utc) + timedelta(days=1)
        if ahora - cierre > timedelta(hours=26):
            p.append(f"datos desfasados: última vela cerrada hace {(ahora - cierre).total_seconds() / 3600:.0f} h")
    return p


# --- Referencia aleatoria ---------------------------------------------------

def mediana_azar(log_acum: list[float], ini: int, fin: int, dias: int, entradas: int, tasa: float,
                 semilla: int) -> float:
    """Mediana de N_AZAR estrategias con `entradas` tramos al azar que suman `dias` días dentro de (ini, fin].
    log_acum[t] = suma de log-rentabilidades diarias de BTC hasta t, así cada tramo cuesta O(1)."""
    rnd, W, res = random.Random(semilla), fin - ini, []
    entradas = max(1, min(entradas, dias))
    for _ in range(N_AZAR):
        cortes = sorted(rnd.sample(range(1, dias), entradas - 1)) if entradas > 1 else []
        largos = [b - a for a, b in zip([0] + cortes, cortes + [dias])]
        huecos_tot = W - dias
        hc = sorted(rnd.randint(0, huecos_tot) for _ in range(entradas))
        huecos = [hc[0]] + [b - a for a, b in zip(hc, hc[1:])]
        pos, lr = ini, 0.0
        for h, L in zip(huecos, largos):
            pos += h
            lr += log_acum[pos + L] - log_acum[pos]
            pos += L
        res.append(exp(lr) * (1 - tasa) ** (2 * entradas) - 1)
    res.sort()
    return res[len(res) // 2]


# --- Referencia de TRAIN ----------------------------------------------------

def _dd(eq: Sequence[float]) -> float:
    pico, m = eq[0], 0.0
    for x in eq:
        pico = max(pico, x)
        m = min(m, x / pico - 1)
    return m


def _percentil(x: list[float], q: float) -> float:
    s = sorted(x)
    return s[min(len(s) - 1, int(q * len(s)))]


def _vol30(velas, t) -> float:
    lr = [log(velas[i].close / velas[i - 1].close) for i in range(t - 29, t + 1)]
    m = sum(lr) / len(lr)
    return sqrt(sum((v - m) ** 2 for v in lr) / (len(lr) - 1)) * sqrt(365)


def series(velas) -> dict[str, Resultado]:
    """Resultados causales de cada componente y de la cartera al 25 %."""
    base = {f"{e} {v}": backtest(velas, estrategias.crear(e, v)) for e, v in COMPONENTES}
    mangas = {g: [(ca.rents(r), ca.exposiciones(r)) for k, r in base.items() if k.startswith(g)] for g in ("B1", "T1")}
    c, _ = ca.cartera([v.fecha for v in velas], mangas)
    base[CARTERA] = riesgo.escalar(c, velas, EXPOSICION)[0]
    return base


def referencia(velas_train) -> dict:
    s = series(velas_train)
    ref = {"peor_dd": {}, "p5_180": {}}
    for k, r in s.items():
        eq = [r.capital] + r.equity
        ref["peor_dd"][k] = _dd(eq)
        ref["p5_180"][k] = _percentil([eq[t] / eq[t - VENTANA_MOVIL] - 1 for t in range(VENTANA_MOVIL, len(eq))], 0.05)
    vols = [_vol30(velas_train, t) for t in range(30, len(velas_train))]
    ref["vol_p5"], ref["vol_p95"] = _percentil(vols, 0.05), _percentil(vols, 0.95)
    return ref


# --- Vigilancia día a día ---------------------------------------------------

def vigilar(velas, ref: dict, desde: int, hasta: int | None = None, ahora=None) -> dict:
    """Simula la vigilancia diaria desde el índice `desde`. Todo lo del día t usa solo velas hasta t."""
    hasta = len(velas) - 1 if hasta is None else hasta
    s = series(velas)
    log_acum = [0.0]
    for a, b in zip(velas, velas[1:]):
        log_acum.append(log_acum[-1] + log(b.close / a.close))
    log_acum.append(log_acum[-1])  # relleno para el índice t+1
    tasa = BINANCE_SPOT.por_lado()
    expo = {k: ca.exposiciones(r) for k, r in s.items() if k != CARTERA}
    est = {k: {"estado": "ACTIVA", "pico": None, "alerta_dd": False, "alerta_180": False, "suspension": None}
           for k in s}
    eventos, diario = [], []
    sobre_sma = None
    for t in range(desde, hasta + 1):
        f = velas[t].fecha
        hoy = []
        prob = problemas_datos(velas[: t + 1], ahora if t == hasta else None)
        if prob:
            hoy.append({"tipo": "datos", "estrategia": "todas", "motivo": "; ".join(prob)})
        v30 = _vol30(velas, t)
        if v30 > ref["vol_p95"] or v30 < ref["vol_p5"]:
            hoy.append({"tipo": "alerta", "estrategia": "mercado",
                        "motivo": f"volatilidad 30 d {v30:.0%} fuera de [{ref['vol_p5']:.0%}, {ref['vol_p95']:.0%}] de TRAIN"})
        sma200 = estrategias._sma(velas[: t + 1], 200)
        if sma200:
            ahora_sobre = velas[t].close > sma200
            if sobre_sma is not None and ahora_sobre != sobre_sma:
                hoy.append({"tipo": "alerta", "estrategia": "mercado",
                            "motivo": f"el precio cruza la SMA 200 hacia {'arriba' if ahora_sobre else 'abajo'}"})
            sobre_sma = ahora_sobre
        for k, r in s.items():
            e, eq = est[k], [r.capital] + r.equity  # eq[t+1] = capital al cierre de la vela t
            e["pico"] = max(e["pico"] or eq[t + 1], eq[t + 1])
            dd = eq[t + 1] / e["pico"] - 1
            if e["estado"] == "SUSPENDIDA":
                continue
            motivo = None
            if dd < ref["peor_dd"][k]:
                motivo = f"drawdown {dd:.1%} peor que el peor del backtest ({ref['peor_dd'][k]:.1%})"
            elif k != CARTERA and t >= VENTANA_AZAR:
                x = expo[k]
                ini = t - VENTANA_AZAR
                dias = sum(1 for i in range(ini + 1, t + 1) if x[i] > 0)
                if dias > 0:
                    entradas = sum(1 for i in range(ini + 1, t + 1) if x[i] > 0 and x[i - 1] == 0) or 1
                    rs = eq[t + 1] / eq[ini + 1] - 1
                    med = mediana_azar(log_acum, ini, t, dias, entradas, tasa, semilla=t)
                    if rs < med:
                        motivo = f"365 días: {rs:+.1%} frente a {med:+.1%} de la mediana de entradas aleatorias"
            if motivo:
                e["estado"], e["suspension"] = "SUSPENDIDA", {"fecha": f, "capital": eq[t + 1]}
                hoy.append({"tipo": "suspension", "estrategia": k, "motivo": motivo})
                if k == CARTERA:
                    hoy.append({"tipo": "parada_emergencia", "estrategia": "todas", "motivo": motivo})
                continue
            if dd < 0.75 * ref["peor_dd"][k] and not e["alerta_dd"]:
                e["alerta_dd"] = True
                hoy.append({"tipo": "alerta", "estrategia": k, "motivo": f"drawdown {dd:.1%}, más del 75 % del peor del backtest"})
            elif dd > 0.5 * ref["peor_dd"][k]:
                e["alerta_dd"] = False
            if t >= VENTANA_MOVIL:
                r180 = eq[t + 1] / eq[t + 1 - VENTANA_MOVIL] - 1
                if r180 < ref["p5_180"][k] and not e["alerta_180"]:
                    e["alerta_180"] = True
                    hoy.append({"tipo": "alerta", "estrategia": k,
                                "motivo": f"180 días: {r180:+.1%}, por debajo del percentil 5 de TRAIN ({ref['p5_180'][k]:+.1%})"})
                elif r180 >= ref["p5_180"][k]:
                    e["alerta_180"] = False
        for ev in hoy:
            ev["fecha"] = f.isoformat()
        eventos += hoy
        parada = est[CARTERA]["estado"] == "SUSPENDIDA"
        diario.append({"fecha": f.isoformat(), "datos_ok": not prob, "parada_emergencia": parada,
                       "estados": {k: est[k]["estado"] for k in s},
                       "emite_senales": {k: (not prob and not parada and est[k]["estado"] == "ACTIVA")
                                         for k in s if k != CARTERA}})
    # Resultados posteriores ("en la sombra") de cada suspensión
    for k, e in est.items():
        if e["suspension"]:
            eq_fin = ([s[k].capital] + s[k].equity)[hasta + 1]
            e["suspension"]["despues"] = eq_fin / e["suspension"]["capital"] - 1
    return {"eventos": eventos, "diario": diario, "estados": est}


def registrar(resultado: dict, ruta: Path = REGISTRO) -> None:
    """Modo en vivo: anota los eventos y el estado del último día en el registro de solo añadir."""
    for ev in resultado["eventos"]:
        registro.anadir(ruta, ev)
    registro.anadir(ruta, {"tipo": "estado_diario", **resultado["diario"][-1]})


# --- Informes -----------------------------------------------------------------

def informe_diario(dia: dict, eventos_hoy: list[dict]) -> str:
    l = [f"Estado de las estrategias, {dia['fecha']}",
         f"Datos: {'correctos' if dia['datos_ok'] else 'CON PROBLEMAS: no se generan señales'}",
         f"Parada de emergencia: {'ACTIVADA' if dia['parada_emergencia'] else 'no'}"]
    for k, st in dia["estados"].items():
        emite = dia["emite_senales"].get(k)
        l.append(f"  {k:12} {st:10} " + ("" if emite is None else ("emite señales" if emite else "sin señales")))
    for ev in eventos_hoy:
        l.append(f"  [{ev['tipo'].upper()}] {ev['estrategia']}: {ev['motivo']}")
    return "\n".join(l)


def simular_otra_epoca(salida: Path = registro.RAIZ / "docs" / "vigilancia.md") -> dict:
    from datetime import date

    from copilot import robustez, train
    from copilot.motor import cargar_velas

    ref = referencia(cargar_velas(train.FICHERO))
    v = cargar_velas(robustez.FICHERO)
    desde = next(i for i, x in enumerate(v) if x.fecha >= date(2013, 1, 1))
    r = vigilar(v, ref, desde)
    ev, diario = r["eventos"], r["diario"]
    cuenta: dict[str, int] = {}
    for e in ev:
        cuenta[e["tipo"]] = cuenta.get(e["tipo"], 0) + 1
    l = ["# Vigilancia del deterioro: simulación (Prompt 8)", "",
         "Generado por `python -m copilot vigilancia`. Reglas fijadas antes: `docs/decisiones.md`, D15.",
         f"Simulación día a día en Bitstamp {v[desde].fecha} a {v[-1].fecha}, con la referencia de TRAIN (Binance 2017-2022).",
         "Es una prueba del sistema de vigilancia; no escribe en `registros/vigilancia.jsonl` (eso solo en vivo).", "",
         "## Referencia de TRAIN", "", "| Serie | Peor drawdown | Percentil 5 de 180 días |", "|---|---|---|"]
    for k in ref["peor_dd"]:
        l.append(f"| {k} | {ref['peor_dd'][k]:.1%} | {ref['p5_180'][k]:+.1%} |")
    l += ["", f"Volatilidad de 30 días normal en TRAIN: entre {ref['vol_p5']:.0%} y {ref['vol_p95']:.0%}.", "",
          "## Resumen", "", f"- Días vigilados: {len(diario)}.",
          f"- Días sin señales por problemas de datos: {sum(1 for d in diario if not d['datos_ok'])}.",
          f"- Eventos: " + ", ".join(f"{k} {n}" for k, n in sorted(cuenta.items())) + ".", ""]
    for k in diario[0]["emite_senales"]:
        l.append(f"- {k}: emite señales {sum(1 for d in diario if d['emite_senales'][k])} de {len(diario)} días.")
    l += ["", "## Suspensiones y resultado posterior (en la sombra, hasta el final)", "",
          "| Estrategia | Fecha | Motivo | Resultado después de suspender |", "|---|---|---|---|"]
    for e in ev:
        if e["tipo"] == "suspension":
            sus = r["estados"][e["estrategia"]]["suspension"]
            l.append(f"| {e['estrategia']} | {e['fecha']} | {e['motivo']} | {sus['despues']:+.1%} |")
    l += ["", "## Primeros 40 eventos", "", "| Fecha | Tipo | Serie | Motivo |", "|---|---|---|---|"]
    for e in ev[:40]:
        l.append(f"| {e['fecha']} | {e['tipo']} | {e['estrategia']} | {e['motivo']} |")
    ult = [e for e in ev if e["fecha"] == diario[-1]["fecha"]]
    l += ["", "## Ejemplo de informe diario (último día)", "", "```", informe_diario(diario[-1], ult), "```", ""]
    salida.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
    return r
