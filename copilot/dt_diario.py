"""Day trading de apertura a cierre con velas diarias desde 2000 en acciones de EE. UU. (D67).

Solo investigación con datos históricos: nada aquí se conecta a un broker ni envía órdenes. Usa numpy (solo en el PC).
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime
from itertools import product

import warnings

import numpy as np

from copilot import registro, train
from copilot.dt100k import coste, medir
from copilot.retroceso import _psr
from copilot.universo_eval import sharpe_deflactado

DATOS = registro.RAIZ / "data" / "acciones_1d_max.json.gz"
DIR = registro.REGISTROS / "dt_diario"
TRAIN_CSV = DIR / "train.csv.gz"
SALIDA = registro.RAIZ / "docs" / "dt_diario.md"
ID, VARIANTE = "DTD", "DTD-v1"
LOTES = {"TRAIN": "dtd-train-v1", "VALIDACION": "dtd-validacion-v1", "TEST": "dtd-test-v1"}
INICIO, FIN_TRAIN, FIN_VALID = date(2000, 1, 3), date(2012, 12, 31), date(2018, 12, 31)
ARRANQUE, N_VALID, N_TEST = 25, 200, 5
MIN_OPS = {"TRAIN": 500, "VALIDACION": 200, "TEST": 200}

FAMILIAS = {
    "HUECO": (0.25, 0.5, 1.0, 1.5, 2.0), "AYER": (0.5, 1.0, 1.5, 2.0, 3.0), "CAJA": (0.1, 0.25, 0.35),
    "IBS": (0.1, 0.2, 0.3), "RSI2": (5.0, 10.0, 20.0), "SEMANA": (1.0, 1.5, 2.0, 3.0), "RUPTURA20": (0.0, 0.25),
    "RANK_HUECO": (0.05, 0.1, 0.2), "RANK_AYER": (0.05, 0.1, 0.2), "DIA_SEMANA": (0, 1, 2, 3, 4),
    "CAMBIO_MES": ("inicio", "fin"), "HUECO_SPY": (0.25, 0.5, 1.0),
}
MODOS, LADOS = ("seguir", "contraria"), ("compras", "cortos", "ambos")
MERCADOS, VOLS, VOLUMENES = ("-", "a favor", "en contra"), ("-", "baja", "alta"), ("-", ">1.5", "<0.8")
STOPS, OBJETIVOS = (0.5, 1.0, 0.0), (1.0, 2.0, 0.0)


def todas() -> list[tuple]:
    return [(f, p, *resto) for f, ps in FAMILIAS.items() for p in ps
            for resto in product(MODOS, LADOS, MERCADOS, VOLS, VOLUMENES, STOPS, OBJETIVOS)]


def texto(r: tuple) -> str:
    f, p, modo, lado, mk, vo, vl, st, ob = r
    return (f"{f} p={p} {modo} {lado} spy={mk} vol={vo} volumen_ayer={vl} stop={'%gATR' % st if st else 'no'} "
            f"obj={'%gR' % ob if ob else 'no'}")


def preparar() -> dict:
    with gzip.open(DATOS, "rt", encoding="utf-8") as f:
        crudo = json.load(f)
    ses = {s: {datetime.fromisoformat(r[0]).date(): r[1:6] for r in filas} for s, filas in crudo.items()}
    dias = sorted(d for d in ses["SPY"] if d >= INICIO)
    simb = sorted(s for s in ses if s != "SPY" and ses[s])
    A = np.full((len(simb) + 1, len(dias), 5), np.nan)
    pos = {d: j for j, d in enumerate(dias)}
    for i, s in enumerate(simb + ["SPY"]):
        for d, v in ses[s].items():
            if d in pos:
                A[i, pos[d]] = v
    A[(A[:, :, :4] <= 0).any(axis=2)] = np.nan
    return {"A": A, "dias": dias, "simb": simb}


def _antes(x, n=1):
    y = np.full_like(x, np.nan)
    y[:, n:] = x[:, :-n]
    return y


def _ventana(x, n, fn):
    warnings.filterwarnings("ignore", category=RuntimeWarning)  # ventanas vacías -> NaN, es lo esperado
    y = np.full_like(x, np.nan)
    for d in range(n, x.shape[1]):
        y[:, d] = fn(x[:, d - n:d], axis=1)
    return y


def rasgos(A: np.ndarray, dias: list[date]) -> dict:
    """Todo lo que una regla puede mirar a la apertura: días anteriores y la apertura de hoy."""
    with np.errstate(all="ignore"):
        O, H, L, C, V = (A[:, :, k] for k in range(5))
        PC, PH, PL = _antes(C), _antes(H), _antes(L)  # ayer
        TR = np.fmax(H - L, np.fmax(abs(H - PC), abs(L - PC)))
        ATR = _ventana(TR, 14, np.nanmean)
        atrp = ATR / PC
        dif = np.diff(C, axis=1, prepend=np.nan)
        up = dn = np.zeros(C.shape[0])
        rsi = np.full_like(C, np.nan)
        for d in range(1, C.shape[1] - 1):
            x = dif[:, d]
            up = np.where(np.isnan(x), up, (up + np.where(x > 0, x, 0)) / 2)
            dn = np.where(np.isnan(x), dn, (dn + np.where(x < 0, -x, 0)) / 2)
            rsi[:, d + 1] = np.where(up + dn > 0, 100 * up / (up + dn), 50.0)
        terc = np.full_like(atrp, np.nan)
        lo, hi = np.nanpercentile(atrp[:-1], 33.333, axis=0), np.nanpercentile(atrp[:-1], 66.667, axis=0)
        terc[:-1] = np.where(atrp[:-1] <= lo, 0, np.where(atrp[:-1] >= hi, 2, 1))
        terc[np.isnan(atrp)] = np.nan
        mes = np.array([d.month for d in dias])
        primero = np.r_[True, mes[1:] != mes[:-1]]
        ultimo = np.r_[mes[:-1] != mes[1:], True]
        inicio = primero | np.r_[False, primero[:-1]] | np.r_[False, False, primero[:-2]]  # 3 primeras sesiones
        fin = ultimo | np.r_[ultimo[1:], False]  # 2 últimas (el calendario de sesiones se conoce de antemano)
        F = {"O": O[:-1], "H": H[:-1], "L": L[:-1], "C": C[:-1], "PC": PC[:-1], "ATR": ATR[:-1], "atrp": atrp[:-1],
             "R1": (PC / _antes(C, 2))[:-1] - 1, "R5": (PC / _antes(C, 6))[:-1] - 1,
             "caja": ((O - PL) / (PH - PL))[:-1], "IBS": (_antes((C - L) / (H - L)))[:-1], "RSI": rsi[:-1],
             "H20": _ventana(H, 20, np.nanmax)[:-1],
             "L20": _ventana(L, 20, np.nanmin)[:-1], "VREL": (_antes(V) / _ventana(V, 20, np.nanmean))[:-1],
             "terc": terc[:-1], "sO": O[-1], "sPC": PC[-1], "sATRP": atrp[-1],
             "dow": np.array([d.weekday() for d in dias]), "inicio_mes": inicio, "fin_mes": fin}
    return F


def senal(F: dict, f: str, p) -> np.ndarray:
    with np.errstate(all="ignore"):
        O, PC, atrp = F["O"], F["PC"], F["atrp"]
        S, D = O.shape

        def umbral(x):
            return np.sign(x) * (abs(x) > p)

        def ranking(x):
            ok = ~np.isnan(x)
            orden = np.argsort(np.argsort(np.where(ok, x, np.inf), axis=0), axis=0)
            q = (orden + 0.5) / np.maximum(ok.sum(axis=0), 1)
            return np.where(ok & (q >= 1 - p), 1.0, np.where(ok & (q <= p), -1.0, 0.0))
        hueco = O / PC - 1
        if f == "HUECO":
            s = umbral(hueco / atrp)
        elif f == "AYER":
            s = umbral(F["R1"] / atrp)
        elif f == "CAJA":
            s = np.where(F["caja"] > 1 - p, 1.0, np.where(F["caja"] < p, -1.0, 0.0))
        elif f == "IBS":
            s = np.where(F["IBS"] > 1 - p, 1.0, np.where(F["IBS"] < p, -1.0, 0.0))
        elif f == "RSI2":
            s = np.where(F["RSI"] > 100 - p, 1.0, np.where(F["RSI"] < p, -1.0, 0.0))
        elif f == "SEMANA":
            s = umbral(F["R5"] / (atrp * np.sqrt(5)))
        elif f == "RUPTURA20":  # H20/L20 de los 20 días ANTERIORES (la ventana acaba ayer)
            s = np.where(O > F["H20"] + p * F["ATR"], 1.0, np.where(O < F["L20"] - p * F["ATR"], -1.0, 0.0))
        elif f == "RANK_HUECO":
            s = ranking(hueco)
        elif f == "RANK_AYER":
            s = ranking(F["R1"])
        elif f == "DIA_SEMANA":
            s = np.broadcast_to((F["dow"] == p).astype(float), (S, D))
        elif f == "CAMBIO_MES":
            s = np.broadcast_to(F["inicio_mes" if p == "inicio" else "fin_mes"].astype(float), (S, D))
        elif f == "HUECO_SPY":
            g = (F["sO"] / F["sPC"] - 1) / F["sATRP"]
            s = np.broadcast_to(np.sign(g) * (abs(g) > p), (S, D))
        else:
            raise ValueError(f)
    return np.nan_to_num(np.asarray(s, dtype=float))


def operaciones(F: dict, r: tuple) -> dict:
    f, p, modo, lado, mk, vo, vl, st, ob = r
    s = senal(F, f, p) * (1 if modo == "seguir" else -1)
    if lado != "ambos":
        s = np.where(s * (1 if lado == "compras" else -1) > 0, s, 0.0)
    with np.errstate(all="ignore"):
        if mk != "-":
            m = np.sign(F["sO"] / F["sPC"] - 1)[None, :]
            s = np.where(m == s * (1 if mk == "a favor" else -1), s, 0.0)
        if vo != "-":
            s = np.where(F["terc"] == (0 if vo == "baja" else 2), s, 0.0)
        if vl != "-":
            s = np.where(F["VREL"] > 1.5 if vl == ">1.5" else F["VREL"] < 0.8, s, 0.0)
        ok = np.isfinite(F["O"]) & np.isfinite(F["C"]) & np.isfinite(F["atrp"]) & (F["atrp"] > 0)
        ok[:, :ARRANQUE] = False
    si, di = np.nonzero((s != 0) & ok)
    lado_, ent = s[si, di], F["O"][si, di]
    Hh, Ll, sal = F["H"][si, di], F["L"][si, di], F["C"][si, di].copy()
    R = (st if st else 1.0) * F["atrp"][si, di]
    larga = lado_ > 0
    hecho = np.zeros(len(ent), bool)
    if st:
        stop = ent * (1 - lado_ * R)
        t = np.where(larga, Ll <= stop, Hh >= stop)
        sal[t], hecho = stop[t], t
    if ob:
        obj = ent * (1 + lado_ * ob * R)
        t = ~hecho & np.where(larga, Hh >= obj, Ll <= obj)
        sal[t] = obj[t]
    return {"d": di, "bruto": lado_ * (sal / ent - 1), "coste": coste(ent) + coste(sal), "R": R}


def tramos(dias: list[date]) -> dict:
    b = next(i for i, x in enumerate(dias) if x > FIN_TRAIN)
    c = next(i for i, x in enumerate(dias) if x > FIN_VALID)
    return {"TRAIN": (ARRANQUE, b), "VALIDACION": (b, c), "TEST": (c, len(dias))}


def _criterios(m: dict, tramo: str) -> dict:
    return {f"{MIN_OPS[tramo]}_operaciones": m["operaciones"] >= MIN_OPS[tramo], "media_r_005": m["media_r"] >= 0.05,
            "costes_x2": m["media_r_x2"] > 0, "sharpe_deflactado": m["dsr"] >= 0.95}


def _dsr(ms: list[dict]) -> None:
    n = len(ms)
    var = float(np.var([m["sr"] for m in ms], ddof=1)) if n > 1 else 0.0
    for m in ms:
        m["dsr"] = (sharpe_deflactado(m["sr"], m["T"], m["asim"], m["curt"], var, n) if n > 1
                    else _psr(m["sr"], m["T"], m["asim"], m["curt"]))


_F: dict = {}


def _iniciar():
    z = preparar()
    _F.update(rasgos(z["A"], z["dias"]))
    _F["_tr"] = tramos(z["dias"])
    _F["_reglas"] = todas()


def _train_lote(idx: list[int]) -> list[dict]:
    a, b = _F["_tr"]["TRAIN"]
    out = []
    for i in idx:
        m = medir(operaciones(_F, _F["_reglas"][i]), a, b)
        m.pop("diaria", None)
        out.append({"i": i, **m})
    return out


def ejecutar(trabajadores: int = 8) -> dict:
    if any(train._ya_ejecutado(l) for l in LOTES.values()):
        raise SystemExit("La búsqueda DTD ya se ejecutó.")
    reglas = todas()
    z = preparar()
    F = rasgos(z["A"], z["dias"])
    tr = tramos(z["dias"])
    DIR.mkdir(parents=True, exist_ok=True)
    if not any(e["datos"].get("id") == ID for e in registro.leer(registro.IDEAS)):
        registro.anadir(registro.IDEAS, {
            "id": ID, "nombre": f"{len(reglas)} reglas de day trading de apertura a cierre (velas diarias)",
            "familia": "Day trading", "busqueda": 7, "activo": f"{len(z['simb'])} acciones de EE. UU.", "par": "acciones",
            "mercado": "NYSE y NASDAQ", "temporalidad": "1d (apertura a cierre)", "lado": "compras, cortos o ambos; 1x",
            "regla_exacta": "Ver D67. Todas las combinaciones de dt_diario.todas(), sin sorteo.",
            "configuraciones_permitidas": [VARIANTE], "estado": "experimental",
            "criterios_aceptacion": {"ver": "D67", "version": "dtd-1"}})
    a, b = tr["TRAIN"]
    filas = []
    lotes = [list(range(k, min(k + 300, len(reglas)))) for k in range(0, len(reglas), 300)]
    with ProcessPoolExecutor(trabajadores, initializer=_iniciar) as ex:
        for k, parte in enumerate(ex.map(_train_lote, lotes)):
            filas += parte
            if k % 20 == 0:
                print(f"TRAIN {len(filas)} / {len(reglas)}", flush=True)
    _dsr(filas)
    for f in filas:
        f["cand"] = f["operaciones"] >= MIN_OPS["TRAIN"] and f["media_r"] >= 0.05 and f["media_r_x2"] > 0 and f["sr"] > 0
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["n", "regla", "operaciones", "media_r", "media_r_costes_x2", "sharpe_diario", "acierto",
                f"sharpe_deflactado_N{len(reglas)}", "candidata"])
    for f in filas:
        w.writerow([f["i"] + 1, texto(reglas[f["i"]]), f["operaciones"], f"{f['media_r']:.5f}", f"{f['media_r_x2']:.5f}",
                    f"{f['sr']:.5f}", f"{f['acierto']:.4f}", f"{f['dsr']:.5f}", int(f["cand"])])
    cuerpo = buf.getvalue().encode("utf-8")
    TRAIN_CSV.write_bytes(gzip.compress(cuerpo, mtime=0))
    cands = sorted((f for f in filas if f["cand"]), key=lambda f: (-f["dsr"], -f["sr"]))
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
    _dsr([g["V"] for g in elegidas])
    for g in elegidas:
        g["crit_v"] = _criterios(g["V"], "VALIDACION")
        g["pasa_v"] = all(g["crit_v"].values())
    finalistas = []
    a0, b0 = tr["TRAIN"][0], tr["VALIDACION"][1]
    for g in sorted((g for g in elegidas if g["pasa_v"]), key=lambda g: -g["V"]["dsr"]):
        dia = medir(g["op"], a0, b0)["diaria"]
        if all(abs(np.corrcoef(dia, h["dia2"])[0, 1]) <= 0.9 for h in finalistas):
            finalistas.append({**g, "dia2": dia})
        if len(finalistas) == N_TEST:
            break
    a, b = tr["TEST"]
    mid = (a + b) // 2
    for g in finalistas:
        g["T"] = medir(g["op"], a, b)
        g["T"]["mitades"] = (medir(g["op"], a, mid)["rent_media"], medir(g["op"], mid, b)["rent_media"])
    _dsr([g["T"] for g in finalistas])
    for g in finalistas:
        g["crit_t"] = {**_criterios(g["T"], "TEST"), "dos_mitades": min(g["T"]["mitades"]) > 0}
        g["aprueba"] = all(g["crit_t"].values())

    def limpio(m):
        return {k: (round(v, 6) if isinstance(v, float) else v) for k, v in m.items() if k != "diaria"}
    base = {"estrategia_id": ID, "variante": VARIANTE, "mercado": f"{len(z['simb'])} acciones de EE. UU."}
    regs = [{**base, "lote": LOTES["TRAIN"], "reglas": len(reglas),
             "sha256_resultados_train": hashlib.sha256(cuerpo).hexdigest(), "candidatas": len(cands),
             "dsr_max": round(max(f["dsr"] for f in filas), 6)}]
    regs += [{**base, "lote": LOTES["VALIDACION"], "regla": texto(reglas[g["i"]]),
              "train": limpio({k: g[k] for k in ("operaciones", "media_r", "media_r_x2", "sr", "dsr")}),
              "metricas": limpio(g["V"]), "criterios": g["crit_v"], "aprobada": g["pasa_v"], "N": len(elegidas)}
             for g in elegidas]
    regs += [{**base, "lote": LOTES["TEST"], "regla": texto(reglas[g["i"]]), "metricas": limpio(g["T"]),
              "criterios": g["crit_t"], "aprobada": g["aprueba"], "N": len(finalistas)} for g in finalistas]
    registro.registrar_experimentos(regs)
    resumen = {"tramos": {k: [str(z["dias"][v[0]]), str(z["dias"][v[1] - 1])] for k, v in tr.items()},
               "acciones": len(z["simb"]), "dias": len(z["dias"]), "reglas": len(reglas),
               "candidatas_train": len(cands), "dsr_train_095": sum(f["dsr"] >= 0.95 for f in filas),
               "a_validacion": len(elegidas), "pasan_validacion": sum(g["pasa_v"] for g in elegidas),
               "finalistas": len(finalistas), "aprueban_test": sum(g["aprueba"] for g in finalistas)}
    _escribir(resumen, filas, reglas, elegidas, finalistas)
    return resumen


def _escribir(res, filas, reglas, elegidas, finalistas) -> None:
    t = res["tramos"]
    l = ["# Day trading de apertura a cierre con velas diarias desde 2000 (D67)", "",
         f"{res['acciones']} acciones, {res['dias']} sesiones. TRAIN {t['TRAIN'][0]} a {t['TRAIN'][1]}; VALIDACIÓN "
         f"{t['VALIDACION'][0]} a {t['VALIDACION'][1]}; TEST {t['TEST'][0]} a {t['TEST'][1]}. Entra a la apertura y "
         "sale el mismo día. Costes de IBKR con 5.000 USD por operación + 0,02 % por lado.", "",
         "| Paso | Reglas |", "|---|---|", f"| Probadas en TRAIN | {res['reglas']} |",
         f"| Candidatas en TRAIN (>= 500 operaciones, >= +0,05 R, costes x2 > 0) | {res['candidatas_train']} |",
         f"| Con Sharpe deflactado >= 0,95 en TRAIN (N = {res['reglas']}) | {res['dsr_train_095']} |",
         f"| A VALIDACIÓN | {res['a_validacion']} |", f"| Pasan VALIDACIÓN | {res['pasan_validacion']} |",
         f"| Finalistas al TEST | {res['finalistas']} |", f"| Aprueban el TEST | {res['aprueban_test']} |", "",
         "## Las 15 mejores de TRAIN", "",
         "| Qué hace | Operaciones | Media R | Costes x2 | Acierto | Sharpe defl. |", "|---|---|---|---|---|---|"]
    for f in sorted((f for f in filas if f["cand"]), key=lambda f: -f["dsr"])[:15]:
        l.append(f"| {texto(reglas[f['i']])} | {f['operaciones']} | {f['media_r']:+.3f} | {f['media_r_x2']:+.3f} | "
                 f"{f['acierto']:.0%} | {f['dsr']:.3f} |")
    l += ["", "## VALIDACIÓN: las 15 mejores", "",
          "| Qué hace | Operaciones | Media R | Costes x2 | Sharpe defl. | Pasa |", "|---|---|---|---|---|---|"]
    for g in sorted(elegidas, key=lambda g: -g["V"]["dsr"])[:15]:
        v = g["V"]
        l.append(f"| {texto(reglas[g['i']])} | {v['operaciones']} | {v['media_r']:+.3f} | {v['media_r_x2']:+.3f} | "
                 f"{v['dsr']:.3f} | {'sí' if g['pasa_v'] else 'no'} |")
    l += ["", "## TEST", ""]
    if not finalistas:
        l.append("Ninguna regla pasó la VALIDACIÓN: el TEST no se ha mirado.")
    else:
        l += ["| Qué hace | Operaciones | Media R | Costes x2 | Sharpe defl. | Mitades (media por operación) | Aprueba |",
              "|---|---|---|---|---|---|---|"]
        for g in finalistas:
            m = g["T"]
            l.append(f"| {texto(reglas[g['i']])} | {m['operaciones']} | {m['media_r']:+.3f} | {m['media_r_x2']:+.3f} | "
                     f"{m['dsr']:.3f} | {m['mitades'][0]:+.4%} / {m['mitades'][1]:+.4%} | "
                     f"{'sí' if g['aprueba'] else 'no'} |")
    SALIDA.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
