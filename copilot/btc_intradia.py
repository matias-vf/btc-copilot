"""Day trading en BTC con compras y cortos (D54): datos de 1 hora, universo de reglas intradía, motor y evaluación.

Solo análisis y paper trading: perpetuo de Binance simulado, sin claves ni órdenes reales.
"""

from __future__ import annotations

import csv
import gzip
import time
import urllib.parse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import NamedTuple

from copilot import datos

CARPETA = datos.DATOS / "btc_1h"
LADO = 0.0008  # 0,05 % comisión taker + 0,01 % medio spread + 0,02 % slippage, por lado (D54)
HORA_MS = 3_600_000


class H(NamedTuple):
    t: datetime  # inicio de la vela (UTC)
    open: float
    high: float
    low: float
    close: float


def _bajar(url_base: str, simbolo: str, desde: int, hasta: int, limite: int) -> list[list]:
    filas = []
    while desde <= hasta:
        q = urllib.parse.urlencode({"symbol": simbolo, "interval": "1h", "startTime": desde, "endTime": hasta, "limit": limite})
        lote = datos._get_json(f"{url_base}?{q}")
        if not lote:
            break
        filas += lote
        desde = lote[-1][0] + HORA_MS
        time.sleep(0.5)
    return filas


def descargar_todo() -> dict:
    """Spot 1h (otra época), perpetuo 1h (TRAIN + TEST) y funding. Guarda CSV comprimidos y devuelve un informe."""
    def ms(d):
        return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)
    CARPETA.mkdir(parents=True, exist_ok=True)
    inf = {}
    trozos = {"spot_2017_2019.csv.gz": ("https://data-api.binance.vision/api/v3/klines", date(2017, 8, 17), date(2019, 9, 8), 1000),
              "perp_2019_2026.csv.gz": ("https://fapi.binance.com/fapi/v1/klines", date(2019, 9, 9), date(2026, 11, 20), 1500)}
    for nombre, (url, a, b, lim) in trozos.items():
        filas = _bajar(url, "BTCUSDT", ms(a), ms(b) + 24 * HORA_MS - 1, lim)
        with gzip.open(CARPETA / nombre, "wt", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["t_utc", "open", "high", "low", "close"])
            w.writerows([[datetime.fromtimestamp(k[0] / 1000, timezone.utc).isoformat(), k[1], k[2], k[3], k[4]] for k in filas])
        inf[nombre] = validar(cargar(nombre))
    fund, desde, hasta = [], ms(date(2019, 9, 9)), ms(date(2026, 11, 21))
    while desde < hasta:
        q = urllib.parse.urlencode({"symbol": "BTCUSDT", "startTime": desde, "endTime": hasta, "limit": 1000})
        lote = datos._get_json(f"https://fapi.binance.com/fapi/v1/fundingRate?{q}")
        if not lote:
            break
        fund += lote
        desde = lote[-1]["fundingTime"] + 1
        time.sleep(0.5)
    with gzip.open(CARPETA / "funding_2019_2026.csv.gz", "wt", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["t_utc", "tasa"])
        w.writerows([[datetime.fromtimestamp(x["fundingTime"] / 1000, timezone.utc).replace(second=0, microsecond=0).isoformat(),
                      x["fundingRate"]] for x in fund])
    inf["funding"] = {"cobros": len(fund), "primero": fund[0]["fundingTime"] if fund else None}
    return inf


def cargar(nombre: str) -> list[H]:
    with gzip.open(CARPETA / nombre, "rt", encoding="utf-8") as f:
        return [H(datetime.fromisoformat(r[0]), *map(float, r[1:5])) for r in list(csv.reader(f))[1:]]


def funding() -> dict[datetime, float]:
    with gzip.open(CARPETA / "funding_2019_2026.csv.gz", "rt", encoding="utf-8") as f:
        return {datetime.fromisoformat(r[0]).replace(minute=0): float(r[1]) for r in list(csv.reader(f))[1:]}


def validar(v: list[H]) -> dict:
    huecos = [(a.t.isoformat(), b.t.isoformat()) for a, b in zip(v, v[1:]) if b.t - a.t != timedelta(hours=1)]
    dup = len(v) - len({x.t for x in v})
    malas = sum(1 for x in v if not (x.low <= min(x.open, x.close) and x.high >= max(x.open, x.close)))
    return {"velas": len(v), "desde": v[0].t.isoformat(), "hasta": v[-1].t.isoformat(), "huecos": len(huecos),
            "ejemplos_huecos": huecos[:5], "duplicados": dup, "ohlc_incoherentes": malas}
