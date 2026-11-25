"""Búsqueda de 100.000 estrategias de day trading en acciones de EE. UU. (D65). Velas de 1 hora, nada pasa la noche.

Solo investigación con datos históricos: nada aquí se conecta a un broker ni envía órdenes. Usa numpy (solo en el PC).
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import random
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime, time
from math import sqrt
from pathlib import Path

import numpy as np

from copilot import registro, train
from copilot.retroceso import _psr
from copilot.universo_eval import sharpe_deflactado

DATOS = registro.RAIZ / "data" / "acciones_1h_730d.json.gz"
CACHE = registro.RAIZ / "logs" / "dt100k_cache.npz"
DIR = registro.REGISTROS / "dt100k"
REGLAS, TRAIN_CSV = DIR / "reglas.txt.gz", DIR / "train.csv.gz"
SALIDA = registro.RAIZ / "docs" / "dt100k.md"
ID, VARIANTE = "DT100K", "DT100K-v1"
LOTES = {"TRAIN": "dt100k-train-v1", "VALIDACION": "dt100k-validacion-v1", "TEST": "dt100k-test-v1"}
HORAS = [time(9, 30), time(10, 30), time(11, 30), time(12, 30), time(13, 30), time(14, 30), time(15, 30)]
ARRANQUE = 25
FIN_TRAIN, FIN_VALID = date(2025, 6, 30), date(2026, 1, 31)
SEMILLA, N_REGLAS, N_VALID, N_TEST = 20261125, 100_000, 200, 5
NOCIONAL, SLIP = 5_000.0, 0.0002

# --- Datos -------------------------------------------------------------------------------------------------


def preparar() -> dict:
    """Matrices (acciones, días, 7 velas) de las sesiones completas de SPY; NaN donde falta una sesión."""
    if CACHE.exists():
        z = np.load(CACHE, allow_pickle=False)
        return {k: z[k] for k in z.files}
    with gzip.open(DATOS, "rt", encoding="utf-8") as f:
        crudo = json.load(f)
    ses = {}
    for s, filas in crudo.items():
        d: dict = {}
        for r in filas:
            t = datetime.fromisoformat(r[0])
            if t.time() in HORAS:
                d.setdefault(t.date(), {})[HORAS.index(t.time())] = r[1:6]
        ses[s] = {k: [v[i] for i in range(7)] for k, v in d.items() if len(v) == 7}
    dias = sorted(ses["SPY"])
    simb = sorted(s for s in ses if s != "SPY" and len(ses[s]) > 300)
    A = np.full((len(simb) + 1, len(dias), 7, 5), np.nan)
    for i, s in enumerate(simb + ["SPY"]):
        for j, d in enumerate(dias):
            if d in ses[s]:
                A[i, j] = ses[s][d]
    out = {"A": A, "dias": np.array([d.toordinal() for d in dias]), "simb": np.array(simb)}
    CACHE.parent.mkdir(exist_ok=True)
    np.savez(CACHE, **out)
    return out


def _desplazar(x, n=1):
    y = np.full_like(x, np.nan)
    y[:, n:] = x[:, :-n]
    return y


def _media_movil(x, n):
    """Media de los n días ANTERIORES (sin el de hoy), ignorando huecos."""
    y = np.full_like(x, np.nan)
    for d in range(n, x.shape[1]):
        y[:, d] = np.nanmean(x[:, d - n:d], axis=1) if x.ndim == 2 else np.nanmean(x[:, d - n:d], axis=1)
    return y


def rasgos(A: np.ndarray) -> dict:
    """Todo lo que una regla puede mirar. Los rasgos diarios solo usan días anteriores."""
    with np.errstate(all="ignore"):
        O, H, L, C, V = (A[:-1, :, :, k] for k in range(5))
        sO, sC = A[-1, :, :, 0], A[-1, :, :, 3]
        PC = _desplazar(C[:, :, 6])
        dH, dL = H.max(axis=2), L.min(axis=2)
        TR = np.fmax(dH - dL, np.fmax(abs(dH - PC), abs(dL - PC)))
        ATR = _media_movil(TR, 14)
        cierres = C[:, :, 6]
        R1 = PC / _desplazar(cierres, 2) - 1
        R5 = PC / _desplazar(cierres, 6) - 1
        H20 = np.full_like(PC, np.nan)
        L20 = np.full_like(PC, np.nan)
        for d in range(20, PC.shape[1]):
            H20[:, d] = np.nanmax(dH[:, d - 20:d], axis=1)
            L20[:, d] = np.nanmin(dL[:, d - 20:d], axis=1)
        # RSI(2) de Wilder con los cierres diarios hasta ayer
        dif = np.diff(cierres, axis=1, prepend=np.nan)
        up, dn = np.zeros_like(PC[:, 0]), np.zeros_like(PC[:, 0])
        rsi = np.full_like(PC, np.nan)
        for d in range(1, PC.shape[1]):
            x = dif[:, d]
            u, w = np.where(x > 0, x, 0.0), np.where(x < 0, -x, 0.0)
            up = np.where(np.isnan(x), up, (up + u) / 2)
            dn = np.where(np.isnan(x), dn, (dn + w) / 2)
            if d + 1 < PC.shape[1]:
                rsi[:, d + 1] = np.where(up + dn > 0, 100 * up / (up + dn), 50.0)
        CV = np.cumsum(V, axis=2)
        CVM = np.stack([_media_movil(CV[:, :, k], 20) for k in range(7)], axis=2)
        TP = (H + L + C) / 3
        VW = np.cumsum(TP * V, axis=2) / CV
        sPC = np.concatenate([[np.nan], sC[:-1, 6]])
        atrp = ATR / PC
        terc = np.full_like(atrp, np.nan)
        lo, hi = np.nanpercentile(atrp, 33.333, axis=0), np.nanpercentile(atrp, 66.667, axis=0)
        terc = np.where(atrp <= lo, 0, np.where(atrp >= hi, 2, 1)).astype(float)
        terc[np.isnan(atrp)] = np.nan
    return {"O": O, "H": H, "L": L, "C": C, "PC": PC, "ATR": ATR, "atrp": atrp, "PH": _desplazar(dH),
            "PL": _desplazar(dL), "R1": R1, "R5": R5, "H20": H20, "L20": L20, "RSI": rsi, "RVOL": CV / CVM, "VW": VW,
            "sO": sO, "sC": sC, "sPC": sPC, "terc": terc}


# --- Las reglas --------------------------------------------------------------------------------------------

FAMILIAS = {  # familia: (entradas permitidas, valores del parámetro)
    "HUECO": ((-1, 0, 1), (0.25, 0.5, 1.0, 1.5, 2.0)),
    "IMPULSO": ((0, 1, 2, 3, 4), (0.25, 0.5, 0.75, 1.0, 1.5)),
    "RUPTURA1": ((1, 2, 3, 4), (0.0, 0.1, 0.25)),
    "AYER": ((-1, 0), (0.5, 1.0, 1.5, 2.0, 3.0)),
    "VS_SPY": ((0, 1, 2, 3, 4), (0.25, 0.5, 1.0, 1.5)),
    "VWAP": ((0, 1, 2, 3, 4), (0.1, 0.25, 0.5, 1.0)),
    "RANKING": ((-1, 0, 1, 2, 3), (0.05, 0.1, 0.2)),
    "CAJA": ((-1, 0, 1), (0.1, 0.25, 0.35)),
    "RSI2": ((-1, 0, 1), (5.0, 10.0, 20.0)),
    "SEMANA": ((-1, 0), (1.0, 1.5, 2.0, 3.0)),
    "RUPTURA20": ((-1, 0, 1, 2), (0.0, 0.25)),
    "HUECO_VELA": ((0,), (0.25, 0.5, 1.0, 1.5)),
}
MODOS, LADOS = ("seguir", "contraria"), ("compras", "cortos", "ambos")
RVOLS, MERCADOS, VOLS = ("-", ">1.5", ">2.5", "<0.8"), ("-", "a favor", "en contra"), ("-", "baja", "alta")
STOPS, OBJETIVOS, TIEMPOS = (0.25, 0.5, 1.0), (1.0, 2.0, 3.0, 0.0), (1, 2, 0)


def todas() -> list[tuple]:
    out = []
    for fam, (entradas, params) in FAMILIAS.items():
        for e in entradas:
            for p in params:
                for modo in MODOS:
                    for lado in LADOS:
                        for rv in (RVOLS if e >= 0 else ("-",)):
                            for mk in MERCADOS:
                                for vo in VOLS:
                                    for st in STOPS:
                                        for ob in OBJETIVOS:
                                            for ti in TIEMPOS:
                                                out.append((fam, e, p, modo, lado, rv, mk, vo, st, ob, ti))
    return out


def texto(r: tuple) -> str:
    fam, e, p, modo, lado, rv, mk, vo, st, ob, ti = r
    ent = "apertura" if e < 0 else HORAS[e].strftime("cierre %H:%M")
    return (f"{fam} p={p} {modo} {lado} entrada={ent} rvol={rv} spy={mk} vol={vo} stop={st}ATR "
            f"obj={'%gR' % ob if ob else 'no'} salida={'%d velas' % ti if ti else 'cierre'}")


def elegir() -> list[tuple]:
    return random.Random(SEMILLA).sample(todas(), N_REGLAS)


def senal(F: dict, fam: str, e: int, p: float) -> np.ndarray:
    """-1, 0 o 1 por (acción, día), con datos conocidos al entrar (apertura si e = -1, cierre de la vela e si no)."""
    with np.errstate(all="ignore"):
        O0, PC, atrp = F["O"][:, :, 0], F["PC"], F["atrp"]
        P = O0 if e < 0 else F["C"][:, :, e]
        def umbral(x):
            return np.sign(x) * (abs(x) > p)
        if fam == "HUECO":
            s = umbral((O0 / PC - 1) / atrp)
        elif fam == "IMPULSO":
            s = umbral((P / O0 - 1) / atrp)
        elif fam == "RUPTURA1":
            H0, L0 = F["H"][:, :, 0], F["L"][:, :, 0]
            s = np.where(P > H0 + p * F["ATR"], 1.0, np.where(P < L0 - p * F["ATR"], -1.0, 0.0))
        elif fam == "AYER":
            s = umbral(F["R1"] / atrp)
        elif fam == "VS_SPY":
            s = umbral((P / O0 - F["sC"][None, :, e] / F["sO"][None, :, 0]) / atrp)
        elif fam == "VWAP":
            s = umbral((P / F["VW"][:, :, e] - 1) / atrp)
        elif fam == "RANKING":
            x = P / PC - 1
            ok = ~np.isnan(x)
            orden = np.argsort(np.argsort(np.where(ok, x, np.inf), axis=0), axis=0)
            n = ok.sum(axis=0)
            q = (orden + 0.5) / np.maximum(n, 1)
            s = np.where(ok & (q >= 1 - p), 1.0, np.where(ok & (q <= p), -1.0, 0.0))
        elif fam == "CAJA":
            pos = (P - F["PL"]) / (F["PH"] - F["PL"])
            s = np.where(pos > 1 - p, 1.0, np.where(pos < p, -1.0, 0.0))
        elif fam == "RSI2":
            s = np.where(F["RSI"] > 100 - p, 1.0, np.where(F["RSI"] < p, -1.0, 0.0))
        elif fam == "SEMANA":
            s = umbral(F["R5"] / (atrp * sqrt(5)))
        elif fam == "RUPTURA20":
            s = np.where(P > F["H20"] + p * F["ATR"], 1.0, np.where(P < F["L20"] - p * F["ATR"], -1.0, 0.0))
        elif fam == "HUECO_VELA":
            g = (O0 / PC - 1) / atrp
            s = np.where((abs(g) > p) & (np.sign(F["C"][:, :, 0] - O0) == np.sign(g)), np.sign(g), 0.0)
        else:
            raise ValueError(fam)
    return np.nan_to_num(s)


def coste(p: np.ndarray) -> np.ndarray:
    """Fracción por lado: IBKR Pro escalonado con 5.000 USD por operación + spread y deslizamiento (D65)."""
    acciones = NOCIONAL / p
    return np.minimum(np.maximum(0.0035 * acciones, 0.35), 0.01 * NOCIONAL) / NOCIONAL + SLIP


def operaciones(F: dict, r: tuple) -> dict:
    """Simula una regla en todos los días: índice de día, rentabilidad bruta, coste y R de cada operación."""
    fam, e, p, modo, lado, rv, mk, vo, st, ob, ti = r
    s = senal(F, fam, e, p) * (1 if modo == "seguir" else -1)
    if lado == "compras":
        s = np.where(s > 0, s, 0.0)
    elif lado == "cortos":
        s = np.where(s < 0, s, 0.0)
    with np.errstate(all="ignore"):
        if rv != "-":
            x = F["RVOL"][:, :, e]
            s = np.where({">1.5": x > 1.5, ">2.5": x > 2.5, "<0.8": x < 0.8}[rv], s, 0.0)
        if mk != "-":
            m = (F["sO"][:, 0] if e < 0 else F["sC"][:, e]) / F["sPC"] - 1
            s = np.where(np.sign(m)[None, :] == s * (1 if mk == "a favor" else -1), s, 0.0)
        if vo != "-":
            s = np.where(F["terc"] == (0 if vo == "baja" else 2), s, 0.0)
        P = F["O"][:, :, 0] if e < 0 else F["C"][:, :, e]
        ok = np.isfinite(P) & np.isfinite(F["atrp"]) & (F["atrp"] > 0)
        ok[:, :ARRANQUE] = False
        si, di = np.nonzero((s != 0) & ok)
    lado_ = s[si, di]
    ent = P[si, di]
    R = st * F["atrp"][si, di]
    stop = ent * (1 - lado_ * R)
    obj = ent * (1 + lado_ * ob * R) if ob else np.full_like(ent, np.nan)
    j0 = 0 if e < 0 else e + 1
    ult = 6 if not ti else min(e + ti, 6)
    sal = np.full_like(ent, np.nan)
    abierta = np.ones_like(ent, dtype=bool)
    if j0 > 6:  # sin velas tras la entrada: no hay operación
        return {"d": di[:0], "bruto": ent[:0], "coste": ent[:0], "R": ent[:0]}
    for j in range(j0, ult + 1):
        Oj, Hj, Lj = F["O"][si, di, j], F["H"][si, di, j], F["L"][si, di, j]
        larga = lado_ > 0
        tS = abierta & np.where(larga, Lj <= stop, Hj >= stop)
        sal[tS] = np.where(larga, np.minimum(Oj, stop), np.maximum(Oj, stop))[tS]
        abierta &= ~tS
        if ob:
            tO = abierta & np.where(larga, Hj >= obj, Lj <= obj)
            sal[tO] = np.where(larga, np.maximum(Oj, obj), np.minimum(Oj, obj))[tO]
            abierta &= ~tO
    sal[abierta] = F["C"][si, di, ult][abierta]
    bruto = lado_ * (sal / ent - 1)
    return {"d": di, "bruto": bruto, "coste": coste(ent) + coste(sal), "R": R}


def medir(op: dict, d0: int, d1: int, x_costes: float = 1.0) -> dict:
    """Métricas en los días [d0, d1): operaciones, media en R, Sharpe diario de la cartera (días sin operar = 0)."""
    m = (op["d"] >= d0) & (op["d"] < d1)
    n = int(m.sum())
    T = d1 - d0
    if n < 3:
        return {"operaciones": n, "media_r": 0.0, "media_r_x2": 0.0, "sr": 0.0, "T": T, "asim": 0.0, "curt": 3.0,
                "acierto": 0.0, "dias_con_op": 0, "rent_media": 0.0}
    neto = op["bruto"][m] - x_costes * op["coste"][m]
    dd = op["d"][m] - d0
    cnt = np.bincount(dd, minlength=T)
    diaria = np.bincount(dd, weights=neto, minlength=T) / np.maximum(cnt, 1)
    mu, sd = diaria.mean(), diaria.std(ddof=1)
    c = diaria - mu
    m2 = (c ** 2).mean()
    asim = float((c ** 3).mean() / m2 ** 1.5) if m2 > 0 else 0.0
    curt = float((c ** 4).mean() / m2 ** 2) if m2 > 0 else 3.0
    return {"operaciones": n, "media_r": float((neto / op["R"][m]).mean()),
            "media_r_x2": float(((op["bruto"][m] - 2 * op["coste"][m]) / op["R"][m]).mean()),
            "sr": float(mu / sd) if sd > 0 else 0.0, "T": T, "asim": asim, "curt": curt,
            "acierto": float((neto > 0).mean()), "dias_con_op": int((cnt > 0).sum()), "rent_media": float(neto.mean()),
            "diaria": diaria}


# --- El embudo ---------------------------------------------------------------------------------------------

_F: dict = {}


def _iniciar():
    global _F
    z = preparar()
    _F = rasgos(z["A"])
    _F["tramos"] = tramos(z["dias"])


def tramos(dias: np.ndarray) -> dict:
    d = [date.fromordinal(int(x)) for x in dias]
    a = ARRANQUE
    b = next(i for i, x in enumerate(d) if x > FIN_TRAIN)
    c = next(i for i, x in enumerate(d) if x > FIN_VALID)
    return {"TRAIN": (a, b), "VALIDACION": (b, c), "TEST": (c, len(d))}


def _train_lote(lote: list[tuple[int, tuple]]) -> list[tuple]:
    a, b = _F["tramos"]["TRAIN"]
    out = []
    for i, r in lote:
        m = medir(operaciones(_F, r), a, b)
        out.append((i, m["operaciones"], m["dias_con_op"], m["media_r"], m["media_r_x2"], m["sr"], m["asim"],
                    m["curt"], m["acierto"], m["T"]))
    return out


def _huella(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def registrar_idea(reglas: list[tuple]) -> str:
    DIR.mkdir(parents=True, exist_ok=True)
    cuerpo = "\n".join(f"S{i + 1:06d}\t{texto(r)}" for i, r in enumerate(reglas)).encode("utf-8") + b"\n"
    REGLAS.write_bytes(gzip.compress(cuerpo, mtime=0))
    h = _huella(cuerpo)
    if not any(e["datos"].get("id") == ID for e in registro.leer(registro.IDEAS)):
        registro.anadir(registro.IDEAS, {
            "id": ID, "nombre": "100.000 reglas de day trading en acciones de EE. UU.", "familia": "Day trading",
            "busqueda": 6, "activo": "234 acciones de EE. UU.", "par": "acciones", "mercado": "NYSE y NASDAQ",
            "temporalidad": "1h", "lado": "compras, cortos o ambos; 1x; nada pasa la noche",
            "regla_exacta": "Ver D65. Lista completa en registros/dt100k/reglas.txt.gz (S000001 a S100000).",
            "configuraciones_permitidas": [VARIANTE], "sha256_reglas": h, "semilla": SEMILLA,
            "combinaciones_validas": len(todas()), "estado": "experimental",
            "criterios_aceptacion": {"ver": "D65", "version": "dt100k-1"}})
    return h


def ejecutar(trabajadores: int = 8) -> dict:
    if any(train._ya_ejecutado(l) for l in LOTES.values()):
        raise SystemExit("La búsqueda DT100K ya se ejecutó.")
    reglas = elegir()
    huella = registrar_idea(reglas)
    z = preparar()
    tr = tramos(z["dias"])
    # 1) TRAIN: las 100.000
    lotes = [list(enumerate(reglas))[k:k + 500] for k in range(0, N_REGLAS, 500)]
    res = [None] * N_REGLAS
    with ProcessPoolExecutor(trabajadores, initializer=_iniciar) as ex:
        for k, parte in enumerate(ex.map(_train_lote, lotes)):
            for fila in parte:
                res[fila[0]] = fila
            if k % 20 == 0:
                print(f"TRAIN {min((k + 1) * 500, N_REGLAS)} / {N_REGLAS}", flush=True)
    srs = np.array([f[5] for f in res])
    var_sr = float(srs.var(ddof=1))
    filas = []
    for f in res:
        i, n, dco, mr, mr2, sr, asim, curt, aci, T = f
        dsr = sharpe_deflactado(sr, T, asim, curt, var_sr, N_REGLAS)
        cand = n >= 200 and mr >= 0.05 and mr2 > 0 and sr > 0
        filas.append({"i": i, "n": n, "dias": dco, "media_r": mr, "media_r_x2": mr2, "sr": sr, "acierto": aci,
                      "dsr": dsr, "cand": cand})
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["regla", "operaciones", "dias_con_op", "media_r", "media_r_costes_x2", "sharpe_diario", "acierto",
                "sharpe_deflactado_N100000", "candidata"])
    for f in filas:
        w.writerow([f"S{f['i'] + 1:06d}", f["n"], f["dias"], f"{f['media_r']:.5f}", f"{f['media_r_x2']:.5f}",
                    f"{f['sr']:.5f}", f"{f['acierto']:.4f}", f"{f['dsr']:.5f}", int(f["cand"])])
    cuerpo = buf.getvalue().encode("utf-8")
    TRAIN_CSV.write_bytes(gzip.compress(cuerpo, mtime=0))
    cands = sorted((f for f in filas if f["cand"]), key=lambda f: (-f["dsr"], -f["sr"]))
    # 2) A VALIDACIÓN: las 200 mejores sin parecidas al 90 %
    F = rasgos(z["A"])
    a, b = tr["TRAIN"]
    elegidas = []
    for f in cands:
        op = operaciones(F, reglas[f["i"]])
        dia = medir(op, a, b)["diaria"]
        if all(abs(np.corrcoef(dia, g["dia"])[0, 1]) <= 0.9 for g in elegidas):
            elegidas.append({**f, "op": op, "dia": dia})
        if len(elegidas) == N_VALID:
            break
    a, b = tr["VALIDACION"]
    for g in elegidas:
        g["V"] = medir(g["op"], a, b)
    nv = len(elegidas)
    var_v = float(np.var([g["V"]["sr"] for g in elegidas], ddof=1)) if nv > 1 else 0.0
    for g in elegidas:
        v = g["V"]
        v["dsr"] = (sharpe_deflactado(v["sr"], v["T"], v["asim"], v["curt"], var_v, nv) if nv > 1
                    else _psr(v["sr"], v["T"], v["asim"], v["curt"]))
        g["crit_v"] = {"60_operaciones": v["operaciones"] >= 60, "media_r_005": v["media_r"] >= 0.05,
                       "costes_x2": v["media_r_x2"] > 0, "sharpe_deflactado": v["dsr"] >= 0.95}
        g["pasa_v"] = all(g["crit_v"].values())
    # 3) TEST: hasta 5 finalistas, una sola vez
    a0, b0 = tr["TRAIN"][0], tr["VALIDACION"][1]
    finalistas = []
    for g in sorted((g for g in elegidas if g["pasa_v"]), key=lambda g: -g["V"]["dsr"]):
        dia = medir(g["op"], a0, b0)["diaria"]
        if all(abs(np.corrcoef(dia, h["dia2"])[0, 1]) <= 0.9 for h in finalistas):
            finalistas.append({**g, "dia2": dia})
        if len(finalistas) == N_TEST:
            break
    a, b = tr["TEST"]
    mid = (a + b) // 2
    nf = len(finalistas)
    for g in finalistas:
        t = medir(g["op"], a, b)
        g["T"] = t
        var_t = float(np.var([medir(h["op"], a, b)["sr"] for h in finalistas], ddof=1)) if nf > 1 else 0.0
        t["dsr"] = (sharpe_deflactado(t["sr"], t["T"], t["asim"], t["curt"], var_t, nf) if nf > 1
                    else _psr(t["sr"], t["T"], t["asim"], t["curt"]))
        h1, h2 = medir(g["op"], a, mid), medir(g["op"], mid, b)
        t["mitades"] = (h1["rent_media"], h2["rent_media"])
        g["crit_t"] = {"60_operaciones": t["operaciones"] >= 60, "media_r_005": t["media_r"] >= 0.05,
                       "costes_x2": t["media_r_x2"] > 0, "sharpe_deflactado": t["dsr"] >= 0.95,
                       "dos_mitades": h1["rent_media"] > 0 and h2["rent_media"] > 0}
        g["aprueba"] = all(g["crit_t"].values())
    # registro: resumen de TRAIN + las 200 de VALIDACIÓN + las finalistas
    def limpio(m):
        return {k: (round(v, 6) if isinstance(v, float) else v) for k, v in m.items() if k not in ("diaria",)}
    base = {"estrategia_id": ID, "variante": VARIANTE, "mercado": "234 acciones de EE. UU."}
    regs = [{**base, "lote": LOTES["TRAIN"], "reglas": N_REGLAS, "sha256_reglas": huella,
             "sha256_resultados_train": _huella(cuerpo), "candidatas": len(cands),
             "dsr_max_N100000": round(max(f["dsr"] for f in filas), 6), "var_sr": var_sr}]
    for g in elegidas:
        regs.append({**base, "lote": LOTES["VALIDACION"], "regla": f"S{g['i'] + 1:06d}", "texto": texto(reglas[g["i"]]),
                     "train": {"operaciones": g["n"], "media_r": round(g["media_r"], 6), "sr": round(g["sr"], 6),
                               "dsr_N100000": round(g["dsr"], 6)},
                     "metricas": limpio(g["V"]), "criterios": g["crit_v"], "aprobada": g["pasa_v"], "N": nv})
    for g in finalistas:
        regs.append({**base, "lote": LOTES["TEST"], "regla": f"S{g['i'] + 1:06d}", "texto": texto(reglas[g["i"]]),
                     "metricas": limpio(g["T"]), "criterios": g["crit_t"], "aprobada": g["aprueba"], "N": nf})
    registro.registrar_experimentos(regs)
    resumen = {"tramos": {k: [str(date.fromordinal(int(z["dias"][x]))) for x in (v[0], v[1] - 1)]
                          for k, v in tr.items()},
               "acciones": len(z["simb"]), "dias": len(z["dias"]), "candidatas_train": len(cands),
               "a_validacion": nv, "pasan_validacion": sum(g["pasa_v"] for g in elegidas), "finalistas": nf,
               "aprueban_test": sum(g["aprueba"] for g in finalistas)}
    _escribir(resumen, filas, reglas, elegidas, finalistas)
    return resumen


def _escribir(resumen, filas, reglas, elegidas, finalistas) -> None:
    t = resumen["tramos"]
    l = ["# Búsqueda de 100.000 estrategias de day trading en acciones de EE. UU. (D65)", "",
         f"Velas de 1 hora de Yahoo, {resumen['acciones']} acciones, {resumen['dias']} sesiones completas. "
         f"TRAIN {t['TRAIN'][0]} a {t['TRAIN'][1]}; VALIDACIÓN {t['VALIDACION'][0]} a {t['VALIDACION'][1]}; "
         f"TEST {t['TEST'][0]} a {t['TEST'][1]}. Costes de IBKR con 5.000 USD por operación + 0,02 % por lado.", "",
         "## El embudo", "",
         "| Paso | Reglas |", "|---|---|",
         f"| Probadas en TRAIN | {N_REGLAS:,} |".replace(",", "."),
         f"| Candidatas en TRAIN (>= 200 operaciones, >= +0,05 R, costes x2 > 0) | {resumen['candidatas_train']} |",
         f"| Con Sharpe deflactado >= 0,95 en TRAIN (N = 100.000) | {sum(f['dsr'] >= 0.95 for f in filas)} |",
         f"| A VALIDACIÓN (las mejores, sin parecidas) | {resumen['a_validacion']} |",
         f"| Pasan VALIDACIÓN | {resumen['pasan_validacion']} |",
         f"| Finalistas al TEST | {resumen['finalistas']} |",
         f"| Aprueban el TEST | {resumen['aprueban_test']} |", "",
         "## Las 15 mejores de TRAIN", "",
         "| Regla | Qué hace | Operaciones | Media R | Costes x2 | Acierto | Sharpe defl. (N = 100.000) |",
         "|---|---|---|---|---|---|---|"]
    for f in sorted((f for f in filas if f["cand"]), key=lambda f: -f["dsr"])[:15]:
        l.append(f"| S{f['i'] + 1:06d} | {texto(reglas[f['i']])} | {f['n']} | {f['media_r']:+.3f} | "
                 f"{f['media_r_x2']:+.3f} | {f['acierto']:.0%} | {f['dsr']:.3f} |")
    l += ["", "## VALIDACIÓN: las 15 mejores de las que llegaron", "",
          "| Regla | Qué hace | Operaciones | Media R | Costes x2 | Sharpe defl. | Pasa |", "|---|---|---|---|---|---|---|"]
    for g in sorted(elegidas, key=lambda g: -g["V"]["dsr"])[:15]:
        v = g["V"]
        l.append(f"| S{g['i'] + 1:06d} | {texto(reglas[g['i']])} | {v['operaciones']} | {v['media_r']:+.3f} | "
                 f"{v['media_r_x2']:+.3f} | {v['dsr']:.3f} | {'sí' if g['pasa_v'] else 'no'} |")
    l += ["", "## TEST", ""]
    if not finalistas:
        l.append("Ninguna regla pasó la VALIDACIÓN: no hay nada que mirar en el TEST.")
    else:
        l += ["| Regla | Qué hace | Operaciones | Media R | Costes x2 | Sharpe defl. | Mitades | Aprueba |",
              "|---|---|---|---|---|---|---|---|"]
        for g in finalistas:
            t_ = g["T"]
            l.append(f"| S{g['i'] + 1:06d} | {texto(reglas[g['i']])} | {t_['operaciones']} | {t_['media_r']:+.3f} | "
                     f"{t_['media_r_x2']:+.3f} | {t_['dsr']:.3f} | {t_['mitades'][0]:+.4%} / {t_['mitades'][1]:+.4%} | "
                     f"{'sí' if g['aprueba'] else 'no'} |")
    SALIDA.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
