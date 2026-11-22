"""Comprobación de las reglas del bot de la Day Trader skill (`paper-bot`) con datos que su validador no vio (D57).

Las funciones `_ema`, `_rolling`, `breakdown_short` y `_run` copian la lógica de `paper-bot/quant/engine.py` y
`quant/generator.py` (2026-11-22); `_run` añade costes por lado, funding y la salida al final del día UTC.
"""

from __future__ import annotations

import csv
import gzip
import time
import urllib.parse
from datetime import date, datetime, timezone

from copilot import btc_intradia as bi, datos, registro, train
from copilot.universo_eval import momentos, sharpe_deflactado

FIN = date(2024, 11, 13)  # el validador de paper-bot empieza el 2024-11-14
PERP = {"BTC": date(2019, 9, 9), "ETH": date(2019, 11, 27)}
LADO, N_PRUEBAS = 0.0008, 600
REGLAS = {"BTC n=24 rr=2": ("BTC", 24, 2.0, False), "ETH n=12 rr=1.5": ("ETH", 12, 1.5, False),
          "BTC n=24 rr=2 día": ("BTC", 24, 2.0, True), "ETH n=12 rr=1.5 día": ("ETH", 12, 1.5, True)}
LOTE = "paperbot-check-v1"
SALIDA = registro.RAIZ / "docs" / "paperbot.md"


def descargar_eth() -> dict:
    """ETH spot 1h hasta el perpetuo, perpetuo 1h y funding, como `btc_intradia.descargar_todo`."""
    def ms(d):
        return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)
    inf = {}
    for nombre, url, a, b, lim in (("eth_spot_2017_2019.csv.gz", "https://data-api.binance.vision/api/v3/klines",
                                    date(2017, 8, 17), date(2019, 11, 26), 1000),
                                   ("eth_perp_2019_2024.csv.gz", "https://fapi.binance.com/fapi/v1/klines",
                                    PERP["ETH"], FIN, 1500)):
        filas = bi._bajar(url, "ETHUSDT", ms(a), ms(b) + 24 * bi.HORA_MS - 1, lim)
        with gzip.open(bi.CARPETA / nombre, "wt", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["t_utc", "open", "high", "low", "close"])
            w.writerows([[datetime.fromtimestamp(k[0] / 1000, timezone.utc).isoformat(), k[1], k[2], k[3], k[4]] for k in filas])
        inf[nombre] = bi.validar(bi.cargar(nombre))
    fund, desde, hasta = [], ms(PERP["ETH"]), ms(FIN) + 24 * bi.HORA_MS
    while desde < hasta:
        q = urllib.parse.urlencode({"symbol": "ETHUSDT", "startTime": desde, "endTime": hasta, "limit": 1000})
        lote = datos._get_json(f"https://fapi.binance.com/fapi/v1/fundingRate?{q}")
        if not lote:
            break
        fund += lote
        desde = lote[-1]["fundingTime"] + 1
        time.sleep(0.5)
    with gzip.open(bi.CARPETA / "eth_funding_2019_2024.csv.gz", "wt", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["t_utc", "tasa"])
        w.writerows([[datetime.fromtimestamp(x["fundingTime"] / 1000, timezone.utc).replace(second=0, microsecond=0).isoformat(),
                      x["fundingRate"]] for x in fund])
    inf["funding"] = len(fund)
    return inf


def _funding(nombre: str) -> dict:
    with gzip.open(bi.CARPETA / nombre, "rt", encoding="utf-8") as f:
        return {datetime.fromisoformat(r[0]).replace(minute=0): float(r[1]) for r in list(csv.reader(f))[1:]}


def velas(activo: str) -> tuple[list, dict]:
    if activo == "BTC":
        v = bi.cargar("spot_2017_2019.csv.gz") + bi.cargar("perp_2019_2026.csv.gz")
        fu = bi.funding()
    else:
        v = bi.cargar("eth_spot_2017_2019.csv.gz") + bi.cargar("eth_perp_2019_2024.csv.gz")
        fu = _funding("eth_funding_2019_2024.csv.gz")
    return [x for x in v if x.t.date() <= FIN], fu


# --- lógica de paper-bot ----------------------------------------------------------------------------------

def _ema(xs, n):
    k, out = 2 / (n + 1), []
    for x in xs:
        out.append(x if not out else x * k + out[-1] * (1 - k))
    return out


def _rolling(xs, n, fn):
    return [None if i < n else fn(xs[i - n:i]) for i in range(len(xs))]


def breakdown_short(v, n, rr):
    c = [b.close for b in v]
    e20, e50, slow = _ema(c, 20), _ema(c, 50), _ema(c, 1200)
    lo = _rolling([b.low for b in v], n, min)
    hi8 = _rolling([b.high for b in v], 8, max)
    out = [None] * len(v)
    for i in range(1200, len(v)):
        if lo[i] is not None and c[i] < lo[i] and c[i] < e20[i] < e50[i] and c[i] < slow[i]:
            stop = max(hi8[i], v[i].high)
            out[i] = (-1, stop, c[i] - rr * (stop - c[i]))
    return out


def _run(v, sigs, lado=LADO, fu=None, perp_desde=None, dia=False, max_hold=48):
    """engine.run de paper-bot + coste por lado, funding (cortos cobran la tasa) y, con dia=True, salida al cierre
    de la vela de las 23:00 UTC del día de entrada."""
    fu, trades, i, end = fu or {}, [], 0, len(v) - 1
    while i < end:
        s = sigs[i]
        if not s:
            i += 1
            continue
        side, stop, target = s
        j = i + 1
        entry = v[j].open
        if (entry - stop) * side <= 0 or (target - entry) * side <= 0:
            i += 1
            continue
        exit_px, k = None, j
        while k < len(v) and k <= j + max_hold:
            b = v[k]
            if side > 0 and b.low <= stop:
                exit_px = min(b.open, stop) if k > j else stop
            elif side < 0 and b.high >= stop:
                exit_px = max(b.open, stop) if k > j else stop
            elif side > 0 and b.high >= target:
                exit_px = max(b.open, target) if k > j else target
            elif side < 0 and b.low <= target:
                exit_px = min(b.open, target) if k > j else target
            if exit_px is not None:
                break
            if dia and (b.t.hour == 23 or k + 1 >= len(v) or v[k + 1].t.date() != v[j].t.date()):
                exit_px = b.close
                break
            k += 1
        if exit_px is None:
            k = min(k, len(v) - 1)
            exit_px = v[k].close
        cobro = 0.0
        if perp_desde:
            # funding en las horas de cobro (00, 08, 16 UTC) con la posición abierta, sin contar la apertura
            cobro = sum(fu.get(v[m].t, 0.0) for m in range(j + 1, k + 1) if v[m].t.date() >= perp_desde)
        ret = side * (exit_px / entry - 1) - 2 * lado + (-side) * cobro
        trades.append({"t": v[j].t, "ret": ret, "r": ret / (abs(entry - stop) / entry), "horas": k - j + 1})
        i = k
    return trades


def ejecutar() -> dict:
    if train._ya_ejecutado(LOTE):
        raise SystemExit("La comprobación de paper-bot ya se ejecutó.")
    cache, res = {}, {}
    for nombre, (act, n, rr, dia) in REGLAS.items():
        if act not in cache:
            cache[act] = velas(act)
        v, fu = cache[act]
        sig = breakdown_short(v, n, rr)
        tr = _run(v, sig, fu=fu, perp_desde=PERP[act], dia=dia)
        tr2 = _run(v, sig, lado=2 * LADO, fu=fu, perp_desde=PERP[act], dia=dia)
        rets = [t["ret"] for t in tr]
        mu, sd, a, c = momentos(rets) if len(rets) > 2 else (0, 0, 0, 3)
        sr = mu / sd if sd else 0.0
        media_r = sum(t["r"] for t in tr) / len(tr) if tr else 0.0
        media_r2 = sum(t["r"] for t in tr2) / len(tr2) if tr2 else 0.0
        eq = 1.0
        for x in rets:
            eq *= 1 + x
        res[nombre] = {"operaciones": len(tr), "media_r": media_r, "media_r_costes_x2": media_r2,
                       "acierto": sum(x > 0 for x in rets) / len(rets) if rets else 0.0,
                       "rentabilidad_compuesta_100pct": eq - 1, "horas_medias": sum(t["horas"] for t in tr) / len(tr) if tr else 0,
                       "desde": str(v[0].t.date()), "hasta": str(v[-1].t.date()), "_sr": sr, "_T": len(rets), "_a": a, "_c": c,
                       "por_ano": {str(y): round(sum(t["r"] for t in tr if t["t"].year == y), 2)
                                   for y in sorted({t["t"].year for t in tr})}}
    for r in res.values():
        # no tenemos los Sharpe de las 600 pruebas del validador: su varianza bajo azar es ~1/T (error del Sharpe)
        r["sharpe_deflactado"] = (sharpe_deflactado(r["_sr"], r["_T"], r["_a"], r["_c"], 1 / r["_T"], N_PRUEBAS)
                                  if r["_T"] > 2 else 0.0)
        r["criterios"] = {"30_operaciones": r["operaciones"] >= 30, "media_r_005": r["media_r"] >= 0.05,
                          "costes_x2": r["media_r_costes_x2"] > 0, "sharpe_deflactado": r["sharpe_deflactado"] >= 0.95}
        r["aprueba"] = all(r["criterios"].values())
    registro.registrar_experimentos([
        {"lote": LOTE, "estrategia_id": "PB1", "variante": k, "aprueba": r["aprueba"], "criterios": r["criterios"],
         "metricas": {x: (round(y, 6) if isinstance(y, float) else y) for x, y in r.items()
                      if not x.startswith("_") and x not in ("criterios", "aprueba")}} for k, r in res.items()])
    _escribir(res)
    return res


def registrar_idea() -> dict:
    return registro.anadir(registro.IDEAS, {
        "id": "PB1", "nombre": "Corto en ruptura del mínimo con tendencia bajista (regla de paper-bot)",
        "familia": "Ruptura", "busqueda": 6, "activo": "BTC y ETH", "par": "BTCUSDT, ETHUSDT", "mercado": "Binance",
        "temporalidad": "1h", "lado": "solo corto, 1x", "estado": "experimental",
        "regla_exacta": "Cierre horario bajo el mínimo de las n velas previas, cierre < EMA20 < EMA50 y cierre < EMA1200: "
                        "corto en la apertura siguiente; stop en el máximo de 8 velas; objetivo rr veces el riesgo; "
                        "máximo 48 velas (o cierre a las 23:00 UTC en la versión día).",
        "configuraciones_permitidas": list(REGLAS), "referencias": ["paper-bot quant/generator.py (2026-11-22)"],
        "criterios_aceptacion": {"ver": "D57", "version": "paperbot-1"}})


def _escribir(res) -> None:
    l = ["# Reglas del bot de la Day Trader skill (`paper-bot`) con datos que su validador no vio (D57, D58)", "",
         "Regla `breakdown_short` copiada del código del bot. Datos de Binance en velas de 1 hora hasta el 2024-11-13; el "
         "validador del bot empieza el 2024-11-14. Costes 0,08 % por lado + funding real.", "",
         "| Regla | Desde | Operaciones | Acierto | Media R | Media R costes x2 | Horas medias | Sharpe deflactado | Aprueba |",
         "|---|---|---|---|---|---|---|---|---|"]
    for k, r in res.items():
        l.append(f"| {k} | {r['desde']} | {r['operaciones']} | {r['acierto']:.0%} | {r['media_r']:+.3f} | "
                 f"{r['media_r_costes_x2']:+.3f} | {r['horas_medias']:.1f} | {r['sharpe_deflactado']:.3f} | "
                 f"{'sí' if r['aprueba'] else 'no'} |")
    l += ["", "## Suma de R por año", ""]
    for k, r in res.items():
        l.append(f"- {k}: " + ", ".join(f"{y}: {v:+.2f}" for y, v in r["por_ano"].items()))
    SALIDA.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")
