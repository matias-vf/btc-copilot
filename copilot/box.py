"""Box theory (D60): la caja es el máximo y el mínimo del día anterior. Compra en el 35 % inferior, corto en el 35 %
superior, stop un 10 % de la caja por fuera, objetivo la mitad (B1) o el lado opuesto (B2). Todo se cierra al final
del día. El paper en vivo usa exactamente este código sobre las velas reales. Nunca envía órdenes.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timedelta, timezone
from typing import NamedTuple

from copilot import btc_intradia as bi, datos, qqq_intradia as qi, registro, train
from copilot.universo_eval import momentos, sharpe_deflactado

ZONA, FUERA = 0.35, 0.10
VARIANTES = ("B1", "B2")
INICIO_PAPER = date(2026, 11, 23)
FIN_PAPER = date(2026, 11, 27)  # D69: sin entradas nuevas desde aquí; la regla del vídeo la sustituye
EXPOSICION = 0.25
CAPITAL = {"QQQ": 25_000.0, "BTC": 100.0}
LADO = {"QQQ": qi.coste_lado(500.0), "BTC": bi.LADO}  # QQQ: el mínimo de 0,35 USD manda a cualquier precio de 2024-2026
PAPER = registro.REGISTROS / "box" / "paper.jsonl"
SALIDA = registro.RAIZ / "docs" / "box.md"
LOTE = "box-v1"
PERIODOS = {"QQQ": {"TRAIN": (date(2024, 1, 1), qi.FIN_TRAIN), "TEST": (qi.INICIO_TEST, qi.FIN_TEST)},
            "BTC": {"TRAIN": (date(2019, 9, 9), date(2022, 12, 31)), "TEST": (date(2023, 1, 1), date(2026, 11, 20))}}


class V(NamedTuple):
    t: datetime  # inicio de la vela: hora de Nueva York (QQQ) o UTC (BTC)
    open: float
    high: float
    low: float
    close: float


def fin_dia(mercado: str, v: list[V], k: int) -> bool:
    if mercado == "BTC":
        return v[k].t.hour == 23
    return v[k].t.time() >= time(15, 30) or (k + 1 < len(v) and v[k + 1].t.date() != v[k].t.date())


def senales(v: list[V], variante: str) -> list:
    """(lado, stop, objetivo) al cierre de cada vela, con la caja del día anterior; None si no hay señal."""
    out, previo, dia, alto, bajo = [None] * len(v), None, None, None, None
    for i, b in enumerate(v):
        d = b.t.date()
        if d != dia:
            previo, dia, alto, bajo = ((alto, bajo) if dia is not None else None), d, b.high, b.low
        else:
            alto, bajo = max(alto, b.high), min(bajo, b.low)
        if not previo:
            continue
        techo, suelo = previo
        r = techo - suelo
        if r <= 0:
            continue
        c = b.close
        if suelo <= c <= suelo + ZONA * r:
            out[i] = (1, suelo - FUERA * r, suelo + r / 2 if variante == "B1" else techo)
        elif techo - ZONA * r <= c <= techo:
            out[i] = (-1, techo + FUERA * r, suelo + r / 2 if variante == "B1" else suelo)
    return out


def simular(mercado: str, v: list[V], sig: list, lado: float, fu: dict | None = None) -> list[dict]:
    """Operaciones (la última puede quedar 'abierta' si los datos acaban antes de su salida)."""
    fu, trades, i = fu or {}, [], 0
    while i < len(v) - 1:
        s = sig[i]
        if not s or fin_dia(mercado, v, i) or v[i + 1].t.date() != v[i].t.date():
            i += 1
            continue
        side, stop, obj = s
        j = i + 1
        entrada = v[j].open
        if (entrada - stop) * side <= 0 or (obj - entrada) * side <= 0:
            i += 1
            continue
        salida, motivo, k = None, None, j
        while k < len(v):
            b = v[k]
            if side > 0 and b.low <= stop or side < 0 and b.high >= stop:
                salida, motivo = (min(b.open, stop) if side > 0 else max(b.open, stop)) if k > j else stop, "stop"
            elif side > 0 and b.high >= obj or side < 0 and b.low <= obj:
                salida, motivo = (max(b.open, obj) if side > 0 else min(b.open, obj)) if k > j else obj, "objetivo"
            elif fin_dia(mercado, v, k):
                salida, motivo = b.close, "fin del día"
            if motivo:
                break
            k += 1
        t = {"entrada_t": v[j].t.isoformat(), "lado": side, "entrada": entrada, "stop": stop, "objetivo": obj}
        if not motivo:
            trades.append({**t, "abierta": True})
            break
        cobro = sum(fu.get(v[m].t, 0.0) for m in range(j + 1, k + 1))
        ret = side * (salida / entrada - 1) - 2 * lado - side * cobro
        trades.append({**t, "abierta": False, "salida_t": v[k].t.isoformat(), "salida": salida, "motivo": motivo,
                       "ret": ret, "r": ret / (abs(entrada - stop) / entrada)})
        i = k
    return trades


# --- Prueba histórica ------------------------------------------------------------------------------------

def _historico(mercado: str) -> tuple[list[V], dict]:
    if mercado == "QQQ":
        return [V(b.hora, b.open, b.high, b.low, b.close) for b in qi.cargar("QQQ")], {}
    return [V(*x) for x in bi.cargar("perp_2019_2026.csv.gz")], bi.funding()


def _medir(tr: list[dict]) -> dict:
    tr = [t for t in tr if not t["abierta"]]
    rets = [t["ret"] for t in tr]
    if len(rets) < 3:
        return {"operaciones": len(rets), "media_r": 0.0, "acierto": 0.0, "_sr": 0.0, "_T": len(rets), "_a": 0, "_c": 3}
    mu, sd, a, c = momentos(rets)
    return {"operaciones": len(rets), "media_r": sum(t["r"] for t in tr) / len(tr),
            "acierto": sum(x > 0 for x in rets) / len(rets), "_sr": mu / sd if sd else 0.0, "_T": len(rets), "_a": a, "_c": c}


def ejecutar() -> dict:
    if train._ya_ejecutado(LOTE):
        raise SystemExit("La prueba histórica de box theory ya se ejecutó.")
    res, regs = {}, []
    for mercado in ("QQQ", "BTC"):
        v, fu = _historico(mercado)
        for var in VARIANTES:
            sig = senales(v, var)
            for ep, (a, z) in PERIODOS[mercado].items():
                tramo = [t for t in simular(mercado, v, sig, LADO[mercado], fu) if a <= date.fromisoformat(t["entrada_t"][:10]) <= z]
                tramo2 = [t for t in simular(mercado, v, sig, 2 * LADO[mercado], fu) if a <= date.fromisoformat(t["entrada_t"][:10]) <= z]
                m = _medir(tramo)
                m["media_r_costes_x2"] = _medir(tramo2)["media_r"]
                m["sharpe_deflactado"] = (sharpe_deflactado(m["_sr"], m["_T"], m["_a"], m["_c"], 1 / m["_T"], 4)
                                          if m["_T"] > 2 else 0.0)
                m["criterios"] = {"30_operaciones": m["operaciones"] >= 30, "media_r_005": m["media_r"] >= 0.05,
                                  "costes_x2": m["media_r_costes_x2"] > 0, "sharpe_deflactado": m["sharpe_deflactado"] >= 0.95}
                m["aprueba"] = all(m["criterios"].values())
                m["desde"], m["hasta"] = str(a), str(z)
                res[(mercado, var, ep)] = m
                regs.append({"lote": LOTE, "estrategia_id": var, "variante": f"{mercado} {ep}", "aprueba": m["aprueba"],
                             "criterios": m["criterios"], "metricas": {k: (round(x, 6) if isinstance(x, float) else x)
                                                                      for k, x in m.items() if not k.startswith("_")
                                                                      and k not in ("criterios", "aprueba")}})
    registro.registrar_experimentos(regs)
    _escribir(res)
    return res


def _escribir(res) -> None:
    l = ["# Box theory: prueba histórica (D60, D61)", "",
         "Caja = máximo y mínimo del día anterior. Compra en el 35 % inferior, corto en el 35 % superior, stop un 10 % de la "
         "caja por fuera, objetivo la mitad (B1) o el lado opuesto (B2). Velas de 1 hora; todo cerrado al final del día. "
         "Costes: QQQ IBKR + 0,02 % por lado; BTC 0,08 % por lado + funding.", "",
         "| Mercado | Variante | Época | Operaciones | Acierto | Media R | Media R costes x2 | Sharpe deflactado | Aprueba |",
         "|---|---|---|---|---|---|---|---|---|"]
    for (mk, var, ep), m in res.items():
        l.append(f"| {mk} | {var} | {ep} {m['desde']} a {m['hasta']} | {m['operaciones']} | {m['acierto']:.0%} | "
                 f"{m['media_r']:+.3f} | {m['media_r_costes_x2']:+.3f} | {m['sharpe_deflactado']:.3f} | "
                 f"{'sí' if m['aprueba'] else 'no'} |")
    SALIDA.write_text("\n".join(l) + "\n", encoding="utf-8", newline="\n")


# --- Paper en vivo ---------------------------------------------------------------------------------------

def _velas_qqq(ahora: datetime) -> list[V]:
    b = qi_descargar_1h()
    fin = lambda x: x.hora + timedelta(minutes=30 if x.hora.time() >= time(15, 30) else 60)
    return [V(x.hora, x.open, x.high, x.low, x.close) for x in b
            if x.hora.date() >= INICIO_PAPER - timedelta(days=4) and fin(x) <= ahora.astimezone(x.hora.tzinfo)]


def qi_descargar_1h() -> list:
    from copilot.intradia import Barra
    from zoneinfo import ZoneInfo
    q = urllib.parse.urlencode({"interval": "1h", "range": "1mo", "includePrePost": "false"})
    req = urllib.request.Request(f"https://query1.finance.yahoo.com/v8/finance/chart/QQQ?{q}",
                                 headers={"User-Agent": "Mozilla/5.0 (btc-copilot-research)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode("utf-8"))["chart"]["result"][0]
    ny, k = ZoneInfo("America/New_York"), d["indicators"]["quote"][0]
    out = []
    for i, ts in enumerate(d["timestamp"]):
        vals = [k[c][i] for c in ("open", "high", "low", "close", "volume")]
        if None not in vals:
            out.append(Barra(datetime.fromtimestamp(ts, ny), *map(float, vals)))
    return [b for b in out if time(9, 30) <= b.hora.time() < time(16, 0)]


def _velas_btc(ahora: datetime) -> tuple[list[V], dict, str]:
    # Precios siempre de spot: el perpetuo (fapi) está bloqueado desde los servidores de GitHub en EE. UU. y mezclar
    # fuentes cambiaría operaciones ya registradas. Ventana desde las 00:00 UTC de hace 3 días: cajas de días completos.
    desde = int(datetime.combine(ahora.date() - timedelta(days=3), time(0), timezone.utc).timestamp() * 1000)
    q = urllib.parse.urlencode({"symbol": "BTCUSDT", "interval": "1h", "startTime": desde, "limit": 1000})
    k = datos._get_json(f"https://data-api.binance.vision/api/v3/klines?{q}")
    try:
        fq = urllib.parse.urlencode({"symbol": "BTCUSDT", "startTime": desde, "limit": 1000})
        fu = {datetime.fromtimestamp(x["fundingTime"] / 1000, timezone.utc).replace(minute=0, second=0, microsecond=0):
              float(x["fundingRate"]) for x in datos._get_json(f"https://fapi.binance.com/fapi/v1/fundingRate?{fq}")}
        fuente = "Binance spot + funding"
    except Exception:
        fu, fuente = {}, "Binance spot (sin funding)"
    v = [V(datetime.fromtimestamp(x[0] / 1000, timezone.utc), *map(float, x[1:5])) for x in k
         if x[0] / 1000 + 3600 <= ahora.timestamp()]
    return v, fu, fuente


def operaciones_vivo(mercado: str, v: list[V], fu: dict, variante: str) -> list[dict]:
    return [t for t in simular(mercado, v, senales(v, variante), LADO[mercado], fu)
            if INICIO_PAPER <= date.fromisoformat(t["entrada_t"][:10]) < FIN_PAPER]


def tick(ahora: datetime | None = None, mercados=("QQQ", "BTC")) -> int:
    """Recalcula el paper desde el 2026-11-23 con las velas cerradas y guarda solo los eventos nuevos."""
    ahora = ahora or datetime.now(timezone.utc)
    hechos = {(e["datos"]["mercado"], e["datos"]["variante"], e["datos"]["entrada_t"], e["datos"]["evento"])
              for e in registro.leer(PAPER)} if PAPER.exists() else set()
    nuevos = []
    for mk in mercados:
        try:
            v, fu, fuente = (_velas_qqq(ahora), {}, "Yahoo 1h") if mk == "QQQ" else _velas_btc(ahora)
        except Exception as e:
            print(f"box {mk}: sin datos ({type(e).__name__})")
            continue
        for var in VARIANTES:
            for t in operaciones_vivo(mk, v, fu, var):
                base = {"mercado": mk, "variante": var, "fuente": fuente, "estado": "EXPERIMENTAL"}
                eventos = {"abierta": {k: t[k] for k in ("entrada_t", "lado", "entrada", "stop", "objetivo")}}
                if not t["abierta"]:
                    eventos["cerrada"] = {k: x for k, x in t.items() if k != "abierta"}
                for e, datos_ in eventos.items():
                    if (mk, var, t["entrada_t"], e) not in hechos:
                        hechos.add((mk, var, t["entrada_t"], e))
                        nuevos.append({**base, "evento": e, **datos_})
    if nuevos:
        PAPER.parent.mkdir(parents=True, exist_ok=True)
        registro.anadir_varios(PAPER, nuevos)
    return len(nuevos)


def estado() -> dict:
    """Capital ficticio por mercado y variante (exposición 25 %) y posición abierta, desde el registro."""
    out = {(mk, var): {"capital": CAPITAL[mk], "cerradas": 0, "ganadoras": 0, "abierta": None}
           for mk in CAPITAL for var in VARIANTES}
    if not PAPER.exists():
        return out
    cerradas = set()
    for e in registro.leer(PAPER):
        d = e["datos"]
        s = out[(d["mercado"], d["variante"])]
        if d["evento"] == "cerrada":
            s["capital"] *= 1 + EXPOSICION * d["ret"]
            s["cerradas"] += 1
            s["ganadoras"] += d["ret"] > 0
            cerradas.add((d["mercado"], d["variante"], d["entrada_t"]))
            if s["abierta"] and s["abierta"]["entrada_t"] == d["entrada_t"]:
                s["abierta"] = None
        elif (d["mercado"], d["variante"], d["entrada_t"]) not in cerradas:
            s["abierta"] = d
    return out
