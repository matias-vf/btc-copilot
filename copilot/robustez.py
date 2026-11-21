"""Prompt 5: otra época (Bitstamp 2011-2016), regímenes, sensibilidad y veredicto (reglas en docs/decisiones.md, D9)."""

from __future__ import annotations

from copilot.motor import pct as _p

import hashlib
import subprocess
from math import log, sqrt

from copilot import datos, estrategias, registro, train
from copilot.costes import BINANCE_SPOT
from copilot.motor import Resultado, backtest, cargar_velas, metricas

LOTE = "prompt5-otra-epoca-v1"
FICHERO = datos.DATOS / "btcusd_bitstamp_1d_2011_2016.csv"
SALIDA = registro.RAIZ / "docs" / "robustez.md"


_r = train._redondear


def regimenes(velas) -> dict[str, list[str]]:
    """Meses (AAAA-MM) de cada régimen, según D9. Etiquetado a posteriori, solo para describir."""
    meses: dict[str, list] = {}
    for v in velas:
        meses.setdefault(v.fecha.strftime("%Y-%m"), []).append(v)
    ret, vol = {}, {}
    for k, vs in meses.items():
        if len(vs) < 2:
            continue
        ret[k] = vs[-1].close / vs[0].open - 1
        lr = [log(b.close / a.close) for a, b in zip(vs, vs[1:])]
        m = sum(lr) / len(lr)
        vol[k] = sqrt(sum((x - m) ** 2 for x in lr) / max(len(lr) - 1, 1)) * sqrt(365)
    mediana = sorted(vol.values())[len(vol) // 2]
    return {
        "alcista": [k for k, x in ret.items() if x > 0.10],
        "bajista": [k for k, x in ret.items() if x < -0.10],
        "lateral": [k for k, x in ret.items() if -0.10 <= x <= 0.10],
        "vol. alta": [k for k in vol if vol[k] > mediana],
        "vol. baja": [k for k in vol if vol[k] <= mediana],
    }


def rent_en_meses(r: Resultado, meses: list[str]) -> float:
    eq = [r.capital] + r.equity
    total, sel = 1.0, set(meses)
    for i, f in enumerate(r.fechas):
        if f.strftime("%Y-%m") in sel:
            total *= eq[i + 1] / eq[i]
    return total - 1


def spearman(a: list[float], b: list[float]) -> float:
    def rangos(x):
        orden = sorted(range(len(x)), key=lambda i: x[i])
        rg = [0.0] * len(x)
        i = 0
        while i < len(orden):
            j = i
            while j + 1 < len(orden) and x[orden[j + 1]] == x[orden[i]]:
                j += 1
            for k in range(i, j + 1):
                rg[orden[k]] = (i + j) / 2 + 1
            i = j + 1
        return rg
    ra, rb = rangos(a), rangos(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return cov / den if den else 0.0


def ejecutar() -> dict:
    if any(e["datos"].get("lote") == LOTE for e in registro.leer(registro.EXPERIMENTOS)):
        raise SystemExit(f"El lote {LOTE} ya se ejecutó.")
    p4 = [e["datos"] for e in registro.leer(registro.EXPERIMENTOS) if e["datos"].get("lote") == train.LOTE]
    supervivientes = sorted({f["estrategia_id"] for f in p4 if f["aprobada_train"]})
    v_otra, v_train = cargar_velas(FICHERO), cargar_velas(train.FICHERO)
    sha = hashlib.sha256(FICHERO.read_bytes()).hexdigest()
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=registro.RAIZ,
                            capture_output=True, text=True).stdout.strip()
    bh_r = {"train": backtest(v_train, estrategias.buy_hold), "otra": backtest(v_otra, estrategias.buy_hold)}
    bh = {k: metricas(r) for k, r in bh_r.items()}
    filas, res = [], {}
    for f4 in p4:
        if f4["estrategia_id"] not in supervivientes:
            continue
        fn = estrategias.crear(f4["estrategia_id"], f4["variante"])
        r1 = backtest(v_otra, fn, BINANCE_SPOT)
        m1, m3 = metricas(r1), metricas(backtest(v_otra, fn, BINANCE_SPOT.x(3)))
        fila = {"lote": LOTE, "estrategia_id": f4["estrategia_id"], "variante": f4["variante"],
                "periodo": [v_otra[0].fecha.isoformat(), v_otra[-1].fecha.isoformat()], "datos_sha256": sha,
                "codigo_commit": commit, "metricas": _r(m1), "metricas_costes_x3": _r(m3),
                "buy_hold": _r(bh["otra"]), "criterios": train.aprueba(m1, bh["otra"])}
        fila["aprueba_otra_epoca"] = all(fila["criterios"].values())
        filas.append((f4, fila))
        res[(f4["estrategia_id"], f4["variante"])] = {"otra": r1}
    for _, fila in filas:  # todo calculado antes de escribir
        registro.registrar_experimento(fila)
    informe = {"supervivientes": supervivientes, "filas": filas, "bh": bh, "bh_r": bh_r,
               "reg": {"train": regimenes(v_train), "otra": regimenes(v_otra)}, "v_train": v_train, "res": res}
    _escribir(informe)
    return informe


def veredictos(filas, bh) -> dict[str, dict]:
    out = {}
    for eid in sorted({f4["estrategia_id"] for f4, _ in filas}):
        fs = [(a, b) for a, b in filas if a["estrategia_id"] == eid]
        a = any(f4["aprobada_train"] and fo["aprueba_otra_epoca"] for f4, fo in fs)
        mitad_train = sum(f4["metricas"]["sharpe"] >= bh["train"]["sharpe"] for f4, _ in fs) >= len(fs) / 2
        mitad_otra = sum(fo["metricas"]["sharpe"] >= bh["otra"]["sharpe"] for _, fo in fs) >= len(fs) / 2
        out[eid] = {"a": a, "b_train": mitad_train, "b_otra": mitad_otra,
                    "veredicto": "CONSERVAR (provisional)" if a and mitad_train and mitad_otra else "DESCARTAR"}
    return out




def _escribir(inf) -> None:
    filas, bh, reg = inf["filas"], inf["bh"], inf["reg"]
    l = ["# Robustez y filtrado (Prompt 5)", "",
         "Generado por `python -m copilot robustez`. Reglas fijadas antes de ejecutar: `docs/decisiones.md`, D9.",
         f"TRAIN: Binance BTC/USDT {inf['v_train'][0].fecha} a {inf['v_train'][-1].fecha}. Otra época: Bitstamp BTC/USD "
         f"{filas[0][1]['periodo'][0]} a {filas[0][1]['periodo'][1]}. Costes x1 = 0,16 % por lado; x3 = 0,48 %.",
         "Cada ejecución en la otra época está anotada en `registros/experimentos.jsonl`.", "",
         "M1 no tenía ninguna variante aprobada en TRAIN: descartada sin más pruebas.", "",
         "## 1. Las dos épocas lado a lado (todas las variantes = sensibilidad de parámetros)", "",
         "| Estr. | Variante | TRAIN rent. | TRAIN Sharpe | TRAIN DD | Aprueba TRAIN | Otra rent. | Otra Sharpe | Otra DD | Otra rent. x3 | Aprueba otra |",
         "|---|---|---|---|---|---|---|---|---|---|---|",
         f"| B&H | – | {_p(bh['train']['rentabilidad'])} | {bh['train']['sharpe']:.2f} | {_p(bh['train']['max_drawdown'])} | – | "
         f"{_p(bh['otra']['rentabilidad'])} | {bh['otra']['sharpe']:.2f} | {_p(bh['otra']['max_drawdown'])} | – | – |"]
    for f4, fo in filas:
        a, b, b3 = f4["metricas"], fo["metricas"], fo["metricas_costes_x3"]
        si = lambda x: "**sí**" if x else "no"
        l.append(f"| {f4['estrategia_id']} | {f4['variante']} | {_p(a['rentabilidad'])} | {a['sharpe']:.2f} | "
                 f"{_p(a['max_drawdown'])} | {si(f4['aprobada_train'])} | {_p(b['rentabilidad'])} | {b['sharpe']:.2f} | "
                 f"{_p(b['max_drawdown'])} | {_p(b3['rentabilidad'])} | {si(fo['aprueba_otra_epoca'])} |")
    l += ["", "## 2. Regímenes de mercado (variantes aprobadas en TRAIN)", "",
          "Rentabilidad compuesta en los meses de cada régimen. Entre paréntesis, Buy & Hold en esos mismos meses.", ""]
    nombres = list(reg["train"].keys())
    l.append("| Estr. | Variante | Época | " + " | ".join(nombres) + " |")
    l.append("|---|---|---|" + "---|" * len(nombres))
    l.append("| | | | " + " | ".join(f"meses: {len(reg['train'][n])} / {len(reg['otra'][n])}" for n in nombres) + " |")
    aprobadas = [(f4, fo) for f4, fo in filas if f4["aprobada_train"]]
    for f4, fo in aprobadas:
        fn = estrategias.crear(f4["estrategia_id"], f4["variante"])
        rr = {"train": backtest(inf["v_train"], fn), "otra": inf["res"][(f4["estrategia_id"], f4["variante"])]["otra"]}
        for ep in ("train", "otra"):
            celdas = [f"{_p(rent_en_meses(rr[ep], reg[ep][n]))} ({_p(rent_en_meses(inf['bh_r'][ep], reg[ep][n]))})"
                      for n in nombres]
            l.append(f"| {f4['estrategia_id']} | {f4['variante']} | {'TRAIN' if ep == 'train' else 'otra'} | "
                     + " | ".join(celdas) + " |")
    l += ["", "## 3. Veredicto provisional (regla D9)", "",
          "(a) alguna variante aprobada en TRAIN aprueba también en la otra época; (b) al menos la mitad de las variantes "
          "con Sharpe >= Buy & Hold en cada época.", "",
          "| Estrategia | (a) | (b) TRAIN | (b) otra | Veredicto |", "|---|---|---|---|---|"]
    for eid, v in veredictos(filas, bh).items():
        si = lambda x: "sí" if x else "no"
        l.append(f"| {eid} | {si(v['a'])} | {si(v['b_train'])} | {si(v['b_otra'])} | **{v['veredicto']}** |")
    l += ["", "## 4. TRAIN frente a TEST", "",
          "Pendiente: necesita los datos de TEST, que siguen bloqueados hasta que el usuario escriba «UNLOCK».", ""]
    SALIDA.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
