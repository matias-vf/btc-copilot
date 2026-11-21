"""Tercera búsqueda, Prompts 4 y 5 (D36, D37): las 1000 variantes en TRAIN con Sharpe deflactado, y las supervivientes
en la otra época y en TEST. Selección final de hasta 5 que diversifiquen frente a N1 y N1D."""

from __future__ import annotations

from math import e as E_NUM, sqrt
from statistics import NormalDist

from copilot import cartera as ca, estrategias, evaluacion_test, registro, robustez, train, train2, universo as U
from copilot.costes import BINANCE_SPOT
from copilot.motor import cargar_velas, metricas, pct, recortar, requiere_costes_x2_x3

LOTES = {"TRAIN": "universo-train-v1", "otra época": "universo-otra-epoca-v1", "TEST": "universo-test-v1"}
SALIDA = registro.RAIZ / "docs" / "universo_resultados.md"
UMBRAL_DSR, N_PRUEBAS, MAX_NUEVAS, MAX_CORR = 0.95, 1000, 5, 0.9
ACTUALES = {"N1 L=4": ("N1", "L=4"), "N1D L=28": ("N1D", "L=28")}


def momentos(x: list[float]) -> tuple[float, float, float, float]:
    """media, desviación (n-1), asimetría y curtosis (no en exceso: la normal da 3)."""
    n = len(x)
    m = sum(x) / n
    d2 = sum((v - m) ** 2 for v in x) / n
    if d2 == 0:
        return m, 0.0, 0.0, 3.0
    d3 = sum((v - m) ** 3 for v in x) / n
    d4 = sum((v - m) ** 4 for v in x) / n
    return m, sqrt(d2 * n / (n - 1)), d3 / d2 ** 1.5, d4 / d2 ** 2


def sharpe_deflactado(sr: float, T: int, asim: float, curt: float, var_sr: float, N: int) -> float:
    """Bailey y López de Prado (2014). sr = Sharpe por día (sin anualizar); var_sr = varianza de los Sharpe de las N pruebas."""
    nd = NormalDist()
    g = 0.5772156649015329  # constante de Euler-Mascheroni
    sr0 = sqrt(var_sr) * ((1 - g) * nd.inv_cdf(1 - 1 / N) + g * nd.inv_cdf(1 - 1 / (N * E_NUM)))
    den = 1 - asim * sr + (curt - 1) / 4 * sr * sr
    if den <= 0:
        return 0.0
    return nd.cdf((sr - sr0) * sqrt(T - 1) / sqrt(den))


def _medir(velas, sig, i0, costes=BINANCE_SPOT):
    r = recortar(U.backtest_rapido(velas, sig, costes), i0)
    return metricas(r), ca.rents(r)


def _redondear(m):
    return train._redondear(m)


def fase_train() -> dict:
    v = cargar_velas(train.FICHERO)
    i0 = U.ARRANQUE
    bh, _ = _medir(v, [1.0] * len(v), i0)
    filas, srs = [], []
    for uid, fid, fn, ref, p in U.catalogo():
        var = U.texto_variante(p)
        sig = fn(v, **p)
        m, rets = _medir(v, sig, i0)
        mu, sd, asim, curt = momentos(rets)
        sr = mu / sd if sd else 0.0
        srs.append(sr)
        x2 = None
        if requiere_costes_x2_x3(m):
            m2, _ = _medir(v, sig, i0, BINANCE_SPOT.x(2))
            x2 = {**_redondear(m2), "criterios": train2.aprueba_v2(m2, bh)}
        filas.append({"lote": LOTES["TRAIN"], "uid": uid, "estrategia_id": fid, "variante": var,
                      "periodo": [v[i0].fecha.isoformat(), v[-1].fecha.isoformat()], "metricas": _redondear(m),
                      "buy_hold": _redondear(bh), "criterios": train2.aprueba_v2(m, bh), "costes_x2": x2,
                      "sharpe_diario": sr, "asimetria": asim, "curtosis": curt, "T": len(rets)})
    mu = sum(srs) / len(srs)
    var_sr = sum((s - mu) ** 2 for s in srs) / (len(srs) - 1)
    for f in filas:
        f["var_sharpe_pruebas"] = var_sr
        f["sharpe_deflactado"] = sharpe_deflactado(f["sharpe_diario"], f["T"], f["asimetria"], f["curtosis"],
                                                    var_sr, N_PRUEBAS)
        f["pasa_costes"] = f["costes_x2"] is None or all(f["costes_x2"]["criterios"].values())
        f["aprobada_train"] = all(f["criterios"].values()) and f["pasa_costes"] and f["sharpe_deflactado"] >= UMBRAL_DSR
    return {"filas": filas, "bh": bh, "var_sr": var_sr}


def fase_robustez(candidatas: list[dict]) -> dict:
    v_o = cargar_velas(robustez.FICHERO)
    v_tr = cargar_velas(train.FICHERO)
    v_tt = v_tr + cargar_velas(evaluacion_test.FICHERO)
    epocas = {"otra época": (v_o, U.ARRANQUE), "TEST": (v_tt, len(v_tr))}
    out = {}
    for ep, (velas, i0) in epocas.items():
        bh, _ = _medir(velas, [1.0] * len(velas), i0)
        filas = []
        for c in candidatas:
            m, _ = _medir(velas, U.senales(c["estrategia_id"], c["variante"], velas), i0)
            crit = train2.aprueba_v2(m, bh)
            filas.append({"lote": LOTES[ep], "uid": c["uid"], "estrategia_id": c["estrategia_id"],
                          "variante": c["variante"], "periodo": [velas[i0].fecha.isoformat(), velas[-1].fecha.isoformat()],
                          "metricas": _redondear(m), "buy_hold": _redondear(bh), "criterios": crit,
                          "aprobada_train": all(crit.values())})
        out[ep] = {"filas": filas, "bh": bh}
    return out


def _rets_train(k) -> list[float]:
    v = cargar_velas(train.FICHERO)
    return ca.rents(recortar(estrategias.backtest_de(k, v), U.ARRANQUE))


def seleccionar(finalistas: list[dict]) -> tuple[list[dict], list[dict]]:
    """Hasta 5 por Sharpe deflactado, saltando las que se parezcan (corr > 0,9) a N1, N1D o a otra elegida."""
    ref = {n: _rets_train(k) for n, k in ACTUALES.items()}
    elegidas, saltadas = [], []
    for f in sorted(finalistas, key=lambda x: -x["sharpe_deflactado"]):
        r = _rets_train((f["estrategia_id"], f["variante"]))
        corr = {n: ca.correlacion(r, x) for n, x in ref.items()}
        corr.update({g["uid"]: ca.correlacion(r, g["_rets"]) for g in elegidas})
        peor = max(corr.items(), key=lambda kv: kv[1])
        if peor[1] > MAX_CORR:
            saltadas.append({**f, "parecida_a": peor[0], "corr": peor[1]})
            continue
        if len(elegidas) < MAX_NUEVAS:
            elegidas.append({**f, "_rets": r, "corr_max": peor[1], "corr_con": peor[0]})
    return elegidas, saltadas


def ejecutar() -> dict:
    if any(train._ya_ejecutado(l) for l in LOTES.values()):
        raise SystemExit("La tercera búsqueda ya se evaluó.")
    tr = fase_train()
    pasan = [f for f in tr["filas"] if f["aprobada_train"]]
    rb = fase_robustez(pasan)
    o = {f["uid"]: f for f in rb["otra época"]["filas"]}
    t = {f["uid"]: f for f in rb["TEST"]["filas"]}
    finalistas = [f for f in pasan if o[f["uid"]]["aprobada_train"] and t[f["uid"]]["aprobada_train"]]
    elegidas, saltadas = seleccionar(finalistas)
    # todo calculado antes de escribir
    registro.registrar_experimentos(tr["filas"] + rb["otra época"]["filas"] + rb["TEST"]["filas"])
    out = {"tr": tr, "rb": rb, "pasan": pasan, "finalistas": finalistas, "elegidas": elegidas, "saltadas": saltadas,
           "o": o, "t": t}
    _escribir(out)
    return out


def _escribir(out) -> None:
    from collections import Counter
    tr, filas = out["tr"], out["tr"]["filas"]
    nombre = {f[0]: f[1] for f in U.FAMILIAS}
    c_v2 = Counter(f["estrategia_id"] for f in filas if all(f["criterios"].values()))
    c_cost = Counter(f["estrategia_id"] for f in filas if all(f["criterios"].values()) and f["pasa_costes"])
    c_dsr = Counter(f["estrategia_id"] for f in filas if f["aprobada_train"])
    c_tot = Counter(f["estrategia_id"] for f in filas)
    bh = tr["bh"]
    l = ["# Tercera búsqueda: 1000 estrategias (Prompts 4 y 5)", "",
         "Generado por `python -m copilot universo`. Reglas fijadas antes: `docs/decisiones.md`, D36 y D37.",
         f"TRAIN medido desde {filas[0]['periodo'][0]} (vela 365) hasta {filas[0]['periodo'][1]}, igual para las 1000 y para Buy & Hold.",
         f"Buy & Hold en esa ventana: rentabilidad {pct(bh['rentabilidad'])}, Sharpe {bh['sharpe']:.2f}, drawdown {pct(bh['max_drawdown'])}.",
         f"Sharpe deflactado con N = {N_PRUEBAS} pruebas; varianza de los Sharpe diarios entre pruebas: {tr['var_sr']:.6f}.", "",
         "## Embudo", "",
         f"- 1000 variantes probadas en TRAIN.",
         f"- Criterio v2 (menos drawdown y Sharpe >= B&H): {sum(c_v2.values())}.",
         f"- Además, regla de costes x2: {sum(c_cost.values())}.",
         f"- Además, Sharpe deflactado >= {UMBRAL_DSR}: **{len(out['pasan'])}**.",
         f"- Además, criterio v2 en la otra época y en TEST: **{len(out['finalistas'])}**.",
         f"- Elegidas (como mucho {MAX_NUEVAS}, correlación <= {MAX_CORR} con N1, N1D y entre sí): **{len(out['elegidas'])}**.", "",
         "## Por familia (TRAIN)", "", "| Familia | Nombre | Variantes | Criterio v2 | + costes | + Sharpe deflactado |",
         "|---|---|---|---|---|---|"]
    for fid, _, _, _, _ in U.FAMILIAS:
        l.append(f"| {fid} | {nombre[fid]} | {c_tot[fid]} | {c_v2[fid]} | {c_cost[fid]} | {c_dsr[fid]} |")
    top = sorted(filas, key=lambda f: -f["sharpe_deflactado"])[:20]
    l += ["", "## Las 20 con mayor Sharpe deflactado en TRAIN", "",
          "| Id | Familia | Variante | Sharpe | Drawdown | Rentabilidad | Sharpe deflactado | Aprueba TRAIN |",
          "|---|---|---|---|---|---|---|---|"]
    for f in top:
        m = f["metricas"]
        l.append(f"| {f['uid']} | {f['estrategia_id']} | {f['variante']} | {m['sharpe']:.2f} | {pct(m['max_drawdown'])} | "
                 f"{pct(m['rentabilidad'])} | {f['sharpe_deflactado']:.3f} | {'**sí**' if f['aprobada_train'] else 'no'} |")
    for nom, k in (("N1 L=4", ("F05", "semanas=4")), ("N1D L=28", ("F04", "L=28,umbral=0.0"))):
        f = next(x for x in filas if (x["estrategia_id"], x["variante"]) == k)
        l.append(f"\n{nom} dentro del universo ({f['uid']}, {k[0]} {k[1]}): Sharpe {f['metricas']['sharpe']:.2f}, "
                 f"Sharpe deflactado {f['sharpe_deflactado']:.3f} -> {'supera' if f['sharpe_deflactado'] >= UMBRAL_DSR else 'NO supera'} "
                 f"la corrección por 1000 pruebas. Se queda en el copiloto igualmente (D37).")
    if out["pasan"]:
        l += ["", "## Supervivientes de TRAIN en la otra época y en TEST", "",
              "| Id | Familia | Variante | Sharpe deflactado | Otra: Sharpe (B&H) | Otra: DD (B&H) | TEST: Sharpe (B&H) | TEST: DD (B&H) | Pasa las tres |",
              "|---|---|---|---|---|---|---|---|---|"]
        for f in sorted(out["pasan"], key=lambda x: -x["sharpe_deflactado"]):
            o, t = out["o"][f["uid"]], out["t"][f["uid"]]
            l.append(f"| {f['uid']} | {f['estrategia_id']} | {f['variante']} | {f['sharpe_deflactado']:.3f} | "
                     f"{o['metricas']['sharpe']:.2f} ({o['buy_hold']['sharpe']:.2f}) | {pct(o['metricas']['max_drawdown'])} "
                     f"({pct(o['buy_hold']['max_drawdown'])}) | {t['metricas']['sharpe']:.2f} ({t['buy_hold']['sharpe']:.2f}) | "
                     f"{pct(t['metricas']['max_drawdown'])} ({pct(t['buy_hold']['max_drawdown'])}) | "
                     f"{'**sí**' if f in out['finalistas'] else 'no'} |")
    l += ["", "## Selección final", ""]
    if out["elegidas"]:
        l += ["| Id | Familia | Nombre | Variante | Sharpe deflactado | Correlación máxima (con) |", "|---|---|---|---|---|---|"]
        l += [f"| {g['uid']} | {g['estrategia_id']} | {nombre[g['estrategia_id']]} | {g['variante']} | "
              f"{g['sharpe_deflactado']:.3f} | {g['corr_max']:.2f} ({g['corr_con']}) |" for g in out["elegidas"]]
    else:
        l.append("**Ninguna variante nueva supera todo el proceso.** El copiloto sigue con N1 y N1D (D37).")
    if out["saltadas"]:
        l += ["", "Saltadas por parecerse demasiado (correlación > 0,9): "
              + ", ".join(f"{s['uid']} ({s['estrategia_id']} {s['variante']}, {s['corr']:.2f} con {s['parecida_a']})"
                          for s in out["saltadas"][:15]) + ("..." if len(out["saltadas"]) > 15 else "") + "."]
    SALIDA.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
