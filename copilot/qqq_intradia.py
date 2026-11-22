"""Day trading de QQQ con compras y cortos y costes de IBKR (D55). Velas de 1 hora de la sesión regular de Nueva York.

Solo paper trading: nada aquí se conecta a IBKR ni envía órdenes.
"""

from __future__ import annotations

import csv
import gzip
from datetime import date, datetime, time
from math import sqrt
from typing import Callable, Sequence

from copilot import cartera as ca, datos, registro, train
from copilot.intradia import Barra, sesiones
from copilot.motor import pct
from copilot.universo_eval import momentos, sharpe_deflactado

CAPITAL = 25_000.0
SPREAD_SLIP = 0.0002


def cargar(simbolo: str) -> list[Barra]:
    """Velas de 1 hora de 9:30 a 16:00 (se descarta la vela suelta de las 16:00, la subasta de cierre)."""
    with gzip.open(datos.DATOS / f"{simbolo.lower()}_yahoo_1h_730d.csv.gz", "rt", encoding="utf-8") as f:
        filas = list(csv.reader(f))[1:]
    out = [Barra(datetime.fromisoformat(r[0]), *map(float, r[1:6])) for r in filas]
    return [b for b in out if time(9, 30) <= b.hora.time() < time(16, 0)]


def coste_lado(precio: float, exposicion: float = 1.0) -> float:
    """Coste de una orden en fracción del importe: IBKR Pro escalonado + spread y slippage (D55)."""
    nocional = CAPITAL * exposicion
    acciones = nocional / precio
    comision = min(max(0.0035 * acciones, 0.35), 0.01 * nocional)
    return comision / nocional + SPREAD_SLIP


# --- Simulador de un día: señales por vela (-1, 0, 1), stop y objetivo opcionales --------------------------

def simular_dia(b: Sequence[Barra], senal: list[int], niveles: Callable | None = None) -> tuple[float, int]:
    """senal[t] = posición deseada tras el cierre de la vela t (se ejecuta en la apertura de t+1).
    niveles(t, lado, entrada) -> (stop, objetivo) o (None, None). Fuera al cierre de la última vela.
    Tras un stop u objetivo no se vuelve a entrar hasta que la señal cambie. Devuelve (rentabilidad del día, órdenes)."""
    eq, pos, entrada, stop, obj, bloqueo, ordenes = 1.0, 0, 0.0, None, None, None, 0
    n = len(b)

    def cerrar(precio):
        nonlocal eq, pos, ordenes
        eq *= 1 + pos * (precio / entrada - 1)
        eq *= 1 - coste_lado(precio)
        pos, ordenes = 0, ordenes + 1

    for t in range(n):
        if t > 0:
            deseada = senal[t - 1] if senal[t - 1] != bloqueo else 0
            if deseada != pos:
                if pos:
                    cerrar(b[t].open)
                if deseada:
                    pos, entrada, ordenes = deseada, b[t].open, ordenes + 1
                    eq *= 1 - coste_lado(entrada)
                    stop, obj = niveles(t - 1, pos, entrada) if niveles else (None, None)
            if senal[t - 1] != bloqueo:
                bloqueo = None
        if pos:
            if stop is not None and ((pos > 0 and b[t].low <= stop) or (pos < 0 and b[t].high >= stop)):
                bloqueo = pos
                cerrar(min(stop, b[t].open) if pos > 0 else max(stop, b[t].open))
            elif obj is not None and ((pos > 0 and b[t].high >= obj) or (pos < 0 and b[t].low <= obj)):
                bloqueo = pos
                cerrar(max(obj, b[t].open) if pos > 0 else min(obj, b[t].open))
        if t == n - 1 and pos:
            cerrar(b[t].close)
    return eq - 1, ordenes


# --- Indicadores continuos (causales) -----------------------------------------------------------------

def _ema(x, n):
    out, a, e = [], 2 / (n + 1), None
    for v in x:
        e = v if e is None else a * v + (1 - a) * e
        out.append(e)
    return out


def _rsi(x, n):
    out, s, b = [None], None, None
    for i in range(1, len(x)):
        g, p = max(x[i] - x[i - 1], 0), max(x[i - 1] - x[i], 0)
        s, b = (g, p) if s is None else ((s * (n - 1) + g) / n, (b * (n - 1) + p) / n)
        out.append(100.0 if b == 0 else 100 - 100 / (1 + s / b))
    return out


# --- Universo de 40 variantes (D55) ---------------------------------------------------------------------

def universo() -> list[tuple[str, str, dict]]:
    u = [("Q1", "Momentum intradía (Gao y otros 2018)", {"k": k, "h": h}) for k in (1, 2, 3) for h in (1, 2, 3)]
    u += [("Q2", "Ruptura del rango inicial (Crabel 1990)", {"r": r, "stop": s, "obj": o})
          for r in (1, 2) for s in ("otro_lado", "mitad") for o in (None, 2.0)]
    u += [("Q3", "Hueco de apertura", {"g": g, "modo": m}) for g in (0.0025, 0.005, 0.01) for m in ("seguir", "contra")]
    u += [("Q4", "Cruce de medias horarias", {"f": f, "s": s, "stop_atr": a}) for f, s in ((2, 5), (3, 7), (5, 13))
          for a in (None, 2.0)]
    u += [("Q5", "Reversión con RSI horario", {"p": p, "x": x}) for p in (2, 3, 5) for x in (10, 20, 30)]
    u += [("Q6", "Ruptura inicial a favor de la tendencia diaria", {"r": r}) for r in (1, 2)]
    assert len(u) == 40
    return u


def texto(p: dict) -> str:
    return ",".join(f"{k}={v}" for k, v in p.items())


def evaluar_regla(fam: str, p: dict, barras: list[Barra]) -> dict:
    """Rentabilidad de cada sesión (0 si no opera) para una variante, con todo calculado de forma causal."""
    ses = sesiones(barras)
    dias = sorted(ses)
    cierres = [x.close for x in barras]
    idx, i = {}, 0
    for d in dias:
        idx[d] = (i, i + len(ses[d]))
        i += len(ses[d])
    ema_f = _ema(cierres, p["f"]) if fam == "Q4" else None
    ema_s = _ema(cierres, p["s"]) if fam == "Q4" else None
    rsi = _rsi(cierres, p["p"]) if fam == "Q5" else None
    tr = [x.high - x.low for x in barras]
    atr = _ema(tr, 14)
    res = {}
    for j, d in enumerate(dias):
        b = ses[d]
        n, (a0, _) = len(b), idx[d]
        senal, niveles = [0] * n, None
        if fam == "Q1":
            k, h = p["k"], p["h"]
            if k <= n - h:
                lado = 1 if b[k - 1].close > b[0].open else -1 if b[k - 1].close < b[0].open else 0
                if lado:
                    senal[n - h - 1:n - 1] = [lado] * h
        elif fam in ("Q2", "Q6"):
            r = p["r"]
            if n > r + 1:
                alto, bajo = max(x.high for x in b[:r]), min(x.low for x in b[:r])
                dir_ok = 0
                if fam == "Q6":
                    if j < 28:
                        res[d] = (0.0, 0)
                        continue
                    previo = ses[dias[j - 1]][-1].close
                    dir_ok = 1 if previo > ses[dias[j - 28]][-1].close else -1
                lado = 0
                for t in range(r, n - 1):
                    if not lado:
                        lado = 1 if b[t].close > alto else -1 if b[t].close < bajo else 0
                        if lado and fam == "Q6" and lado != dir_ok:
                            lado = 0
                            break
                    senal[t] = lado
                medio = (alto + bajo) / 2
                otro = {1: bajo, -1: alto}
                stop_t, obj_r = p.get("stop", "otro_lado"), p.get("obj")

                def niveles(t, lado, entrada, otro=otro, medio=medio, stop_t=stop_t, obj_r=obj_r):
                    st = otro[lado] if stop_t == "otro_lado" else medio
                    r_ = (entrada - st) * lado
                    if r_ <= 0:
                        return entrada, None  # entrada ya más allá del stop: sale enseguida
                    return st, (entrada + lado * obj_r * r_) if obj_r else None
        elif fam == "Q3":
            if j == 0:
                res[d] = (0.0, 0)
                continue
            gap = b[0].open / ses[dias[j - 1]][-1].close - 1
            if abs(gap) > p["g"]:
                lado = (1 if gap > 0 else -1) * (1 if p["modo"] == "seguir" else -1)
                senal[0:n - 1] = [lado] * (n - 1)
        elif fam == "Q4":
            senal = [(1 if ema_f[a0 + t] > ema_s[a0 + t] else -1) for t in range(n)]
            senal[-1] = 0
            if p["stop_atr"]:
                def niveles(t, lado, entrada, a0=a0):
                    return entrada - lado * p["stop_atr"] * atr[a0 + t], None
        elif fam == "Q5":
            lado = 0
            for t in range(n - 1):
                v = rsi[a0 + t]
                if v is None:
                    continue
                if not lado:
                    lado = 1 if v < p["x"] else -1 if v > 100 - p["x"] else 0
                elif (lado > 0 and v > 50) or (lado < 0 and v < 50):
                    lado = 0
                senal[t] = lado
        res[d] = simular_dia(b, senal, niveles)
    return res


def metricas(rets: Sequence[float]) -> dict:
    eq, pico, dd = 1.0, 1.0, 0.0
    for v in rets:
        eq *= 1 + v
        pico = max(pico, eq)
        dd = min(dd, eq / pico - 1)
    m = sum(rets) / len(rets)
    sd = sqrt(sum((v - m) ** 2 for v in rets) / (len(rets) - 1))
    return {"rentabilidad": eq - 1, "sharpe": m / sd * sqrt(252) if sd else 0.0, "max_drawdown": dd}


# --- Registro y evaluación (D55) ---------------------------------------------------------------------------

FIN_TRAIN, INICIO_TEST, FIN_TEST = date(2026, 3, 31), date(2026, 4, 1), date(2026, 11, 20)
ARRANQUE_DIAS = 28  # Q6 necesita 28 sesiones previas: ventana común para todas
LOTES = {"TRAIN": "qqq-intradia-train-v1", "otra época": "qqq-intradia-spy-v1", "TEST": "qqq-intradia-test-v1"}
SALIDA = registro.RAIZ / "docs" / "qqq_intradia.md"
REGLA = {"Q1": "Si la rentabilidad desde la apertura hasta el cierre de la vela k es positiva, compra (si negativa, corto) "
               "las últimas h velas de la sesión.",
         "Q2": "Al primer cierre fuera del rango de las r primeras velas, compra (por arriba) o corto (por abajo). Stop en "
               "el otro lado del rango o en su mitad; objetivo opcional de 2R.",
         "Q3": "Si el hueco de apertura frente al cierre anterior supera g, se sigue (o se lleva la contraria) desde la "
               "segunda vela hasta el cierre.",
         "Q4": "Comprado si la media exponencial rápida de cierres horarios está por encima de la lenta; corto si por "
               "debajo. Stop opcional a 2 ATR horarios.",
         "Q5": "RSI horario por debajo de x: compra; por encima de 100-x: corto. Sale al cruzar 50.",
         "Q6": "Ruptura del rango de las r primeras velas solo en la dirección del cierre de ayer frente al de hace 28 sesiones."}


def registrar_ideas() -> int:
    if any(e["datos"].get("id") == "Q1" for e in registro.leer(registro.IDEAS)):
        raise SystemExit("Las ideas Q1-Q6 ya están registradas.")
    fams: dict[str, tuple[str, list[str]]] = {}
    for fam, nombre, p in universo():
        fams.setdefault(fam, (nombre, []))[1].append(texto(p))
    refs = {"Q1": ["Gao, Han, Li y Zhou (2018), Market intraday momentum, Journal of Financial Economics 129(2)"],
            "Q2": ["Crabel (1990), Day Trading with Short Term Price Patterns and Opening Range Breakout"],
            "Q6": ["Crabel (1990)", "Moskowitz, Ooi y Pedersen (2012), Time series momentum"]}
    return registro.anadir_varios(registro.IDEAS, [
        {"id": f, "nombre": n, "familia": "Day trading", "busqueda": 5, "activo": "Nasdaq-100", "par": "QQQ",
         "mercado": "NASDAQ (bolsa de EE. UU.)", "temporalidad": "1h", "lado": "compras y cortos, 1x, nada pasa la noche",
         "regla_exacta": REGLA[f], "configuraciones_permitidas": cfg, "referencias": refs.get(f, []),
         "estado": "experimental",
         "criterios_aceptacion": {"ver": "D55", "version": "intradia-ls-1",
                                  "costes": "IBKR Pro escalonado + 0,02 % por lado"}}
        for f, (n, cfg) in fams.items()])


def _diarias(barras: list[Barra]) -> dict:
    """Buy & Hold: rentabilidad de cierre a cierre de cada sesión."""
    ses = sesiones(barras)
    dias = sorted(ses)
    return {d: (ses[d][-1].close / ses[dias[i - 1]][-1].close - 1 if i else 0.0) for i, d in enumerate(dias)}


def _tramo(res: dict, d0: date, d1: date) -> tuple[list[float], int]:
    dias = [d for d in sorted(res) if d0 <= d <= d1]
    rets = [res[d][0] if isinstance(res[d], tuple) else res[d] for d in dias]
    return rets, sum(1 for d in dias if isinstance(res[d], tuple) and res[d][1])


def _r(m: dict) -> dict:
    return {k: round(v, 6) for k, v in m.items()}


def ejecutar() -> dict:
    if any(train._ya_ejecutado(l) for l in LOTES.values()):
        raise SystemExit("La búsqueda de day trading en QQQ ya se ejecutó.")
    qqq, spy = cargar("QQQ"), cargar("SPY")
    d0 = sorted(sesiones(qqq))[ARRANQUE_DIAS]
    bh_q, bh_s = _diarias(qqq), _diarias(spy)
    ventanas = {"TRAIN": (bh_q, d0, FIN_TRAIN), "otra época": (bh_s, d0, FIN_TRAIN), "TEST": (bh_q, INICIO_TEST, FIN_TEST)}
    bh = {ep: _r(metricas(_tramo(b, a, z)[0])) for ep, (b, a, z) in ventanas.items()}
    filas, srs = [], []
    for fam, nombre, p in universo():
        res_q, res_s = evaluar_regla(fam, p, qqq), evaluar_regla(fam, p, spy)
        f = {"fam": fam, "nombre": nombre, "variante": texto(p)}
        for ep, res in (("TRAIN", res_q), ("otra época", res_s), ("TEST", res_q)):
            _, a, z = ventanas[ep]
            rets, con = _tramo(res, a, z)
            f[ep] = {"m": _r(metricas(rets)), "rets": rets, "dias_con_operacion": con / len(rets)}
        mu, sd, asim, curt = momentos(f["TRAIN"]["rets"])
        f["sr"], f["T"], f["asim"], f["curt"] = (mu / sd if sd else 0.0), len(f["TRAIN"]["rets"]), asim, curt
        srs.append(f["sr"])
        filas.append(f)
    mu = sum(srs) / len(srs)
    var_sr = sum((s - mu) ** 2 for s in srs) / (len(srs) - 1)
    for f in filas:
        m, b = f["TRAIN"]["m"], bh["TRAIN"]
        f["criterios_train"] = {"rentabilidad_positiva": m["rentabilidad"] > 0,
                                "drawdown": m["max_drawdown"] > b["max_drawdown"], "sharpe": m["sharpe"] >= b["sharpe"]}
        f["dsr"] = sharpe_deflactado(f["sr"], f["T"], f["asim"], f["curt"], var_sr, len(filas))
        f["cand"] = all(f["criterios_train"].values())
        for ep in ("otra época", "TEST"):
            m, b = f[ep]["m"], bh[ep]
            f[ep]["criterios"] = {"drawdown": m["max_drawdown"] > b["max_drawdown"], "sharpe": m["sharpe"] >= b["sharpe"]}
            f[ep]["aprobada"] = all(f[ep]["criterios"].values())
    tres = [f for f in filas if f["cand"] and f["otra época"]["aprobada"] and f["TEST"]["aprobada"]]
    orden = (sorted([f for f in tres if f["dsr"] >= 0.95], key=lambda f: -f["dsr"])
             + sorted([f for f in tres if f["dsr"] < 0.95], key=lambda f: -f["dsr"]))
    elegidas = []
    for f in orden:
        if all(ca.correlacion(f["TRAIN"]["rets"], g["TRAIN"]["rets"]) <= 0.9 for g in elegidas):
            elegidas.append({**f, "significativa": f["dsr"] >= 0.95})
        if len(elegidas) == 3:
            break
    regs = []
    for f in filas:
        base = {"mercado": "QQQ", "estrategia_id": f["fam"], "variante": f["variante"]}
        regs.append({**base, "lote": LOTES["TRAIN"], "metricas": f["TRAIN"]["m"], "buy_hold": bh["TRAIN"],
                     "criterios": f["criterios_train"], "sharpe_deflactado": round(f["dsr"], 6), "N": len(filas),
                     "dias_con_operacion": round(f["TRAIN"]["dias_con_operacion"], 4), "aprobada_train": f["cand"]})
        if f["cand"]:
            for ep in ("otra época", "TEST"):
                regs.append({**base, "lote": LOTES[ep], "metricas": f[ep]["m"], "buy_hold": bh[ep],
                             "criterios": f[ep]["criterios"], "aprobada": f[ep]["aprobada"],
                             "dias_con_operacion": round(f[ep]["dias_con_operacion"], 4)})
    registro.registrar_experimentos(regs)  # todo calculado antes de escribir
    _escribir(filas, bh, tres, elegidas, d0)
    return {"candidatas": sum(f["cand"] for f in filas), "tres": len(tres),
            "dsr_max": max(f["dsr"] for f in filas),
            "elegidas": [(g["fam"], g["variante"], g["significativa"]) for g in elegidas]}


def _escribir(filas, bh, tres, elegidas, d0) -> None:
    def c(m):
        return f"{pct(m['rentabilidad'])} / {m['sharpe']:.2f} / {pct(m['max_drawdown'])}"
    l = ["# Day trading de QQQ con compras y cortos y costes de IBKR (D55, D56)", "",
         "Reglas fijadas antes de descargar los datos: D55. Velas de 1 hora de Yahoo. Todo se cierra al final de la sesión.",
         f"TRAIN {d0} a {FIN_TRAIN}; otra época = SPY en las mismas fechas; TEST {INICIO_TEST} a {FIN_TEST}.", "",
         "Columnas: rentabilidad / Sharpe anual / peor caída.", "",
         "| Buy & Hold | TRAIN (QQQ) | Otra época (SPY) | TEST (QQQ) |", "|---|---|---|---|",
         f"| | {c(bh['TRAIN'])} | {c(bh['otra época'])} | {c(bh['TEST'])} |", "",
         "## Embudo", "", f"- Universo: {len(filas)} variantes.",
         "- Cumplen las tres condiciones en TRAIN (ganan, menos caída y Sharpe >= Buy & Hold): "
         f"**{sum(f['cand'] for f in filas)}**.",
         f"- Sharpe deflactado >= 0,95 (N = {len(filas)}): **{sum(f['dsr'] >= 0.95 for f in filas)}** "
         f"(el mayor: {max(f['dsr'] for f in filas):.3f}).",
         f"- Además, criterio v2 en SPY y en TEST: **{len(tres)}**.",
         f"- Elegidas (máximo 3, correlación <= 0,9): **{len(elegidas)}**.", "",
         "## Las 40 variantes", "",
         "| Familia | Variante | TRAIN | Días con operación | Sharpe deflactado | SPY | TEST |", "|---|---|---|---|---|---|---|"]
    for f in sorted(filas, key=lambda f: -f["TRAIN"]["m"]["sharpe"]):
        l.append(f"| {f['fam']} {f['nombre']} | {f['variante']} | {c(f['TRAIN']['m'])} | "
                 f"{f['TRAIN']['dias_con_operacion']:.0%} | {f['dsr']:.3f} | "
                 f"{c(f['otra época']['m']) if f['cand'] else '-'} | {c(f['TEST']['m']) if f['cand'] else '-'} |")
    l += ["", "SPY y TEST solo se muestran para las que pasan TRAIN (las demás no se miran, para no elegir mirando TEST).", ""]
    if elegidas:
        l += ["## Elegidas", ""] + [
            f"- **{g['fam']} {g['variante']}**: TEST {c(g['TEST']['m'])}, opera el {g['TEST']['dias_con_operacion']:.0%} "
            f"de los días. {'Significativa.' if g['significativa'] else 'SIN significación estadística.'}" for g in elegidas]
    else:
        l.append("**Ninguna variante cumple el criterio en TRAIN, en SPY y en TEST.**")
    SALIDA.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
