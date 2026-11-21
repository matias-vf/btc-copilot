"""Descarga y validación de velas diarias de BTC desde APIs públicas (sin claves).

Solo lectura de datos de mercado: ninguna función de este módulo envía órdenes.
TEST (desde 2023-01-01) está bloqueado: no se puede pedir ni guardar una vela de TEST
hasta que el usuario escriba «UNLOCK» y se cambie este código en un paso registrado.
"""

from __future__ import annotations

import csv
import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "data"

INICIO_TEST = date(2023, 1, 1)
TEST_DESBLOQUEADO = True  # «UNLOCK» recibido del usuario el 2026-11-21 (D20)

COLUMNAS = ["fecha_utc", "open", "high", "low", "close", "volumen_btc"]
DIA_MS = 86_400_000


class DatosTestBloqueados(Exception):
    pass


def _ms(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)


def _fecha(ms: int) -> date:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date()


def comprobar_no_test(fin: date) -> None:
    if fin >= INICIO_TEST and not TEST_DESBLOQUEADO:
        raise DatosTestBloqueados(f"{fin} pertenece a TEST (>= {INICIO_TEST}). Bloqueado hasta «UNLOCK».")


def _get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "btc-copilot-research/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def descargar_binance(inicio: date, fin: date) -> list[list]:
    """Velas 1d BTCUSDT spot. Endpoint público de solo datos de mercado de Binance."""
    comprobar_no_test(fin)
    filas, desde = [], _ms(inicio)
    hasta = _ms(fin) + DIA_MS - 1
    while desde <= hasta:
        q = urllib.parse.urlencode(
            {"symbol": "BTCUSDT", "interval": "1d", "startTime": desde, "endTime": hasta, "limit": 1000}
        )
        lote = _get_json(f"https://data-api.binance.vision/api/v3/klines?{q}")
        if not lote:
            break
        for k in lote:
            filas.append([_fecha(k[0]).isoformat(), k[1], k[2], k[3], k[4], k[5]])
        desde = lote[-1][0] + DIA_MS
        time.sleep(1)
    return filas


def descargar_bitstamp(inicio: date, fin: date) -> list[list]:
    """Velas 1d BTC/USD de Bitstamp (API pública v2)."""
    comprobar_no_test(fin)
    filas, desde = [], _ms(inicio) // 1000
    hasta = (_ms(fin) + DIA_MS) // 1000 - 1
    while desde <= hasta:
        # Sin "end": con start+end la API devuelve las ÚLTIMAS 1000 velas del rango, no las primeras.
        q = urllib.parse.urlencode({"step": 86400, "limit": 1000, "start": desde})
        lote = _get_json(f"https://www.bitstamp.net/api/v2/ohlc/btcusd/?{q}")["data"]["ohlc"]
        lote = [k for k in lote if desde <= int(k["timestamp"]) <= hasta]
        if not lote:
            break
        for k in lote:
            ts = int(k["timestamp"]) * 1000
            filas.append([_fecha(ts).isoformat(), k["open"], k["high"], k["low"], k["close"], k["volume"]])
        desde = int(lote[-1]["timestamp"]) + 86400
        time.sleep(1)
    return filas


def validar(filas: list[list]) -> dict:
    """Huecos, duplicados, OHLC incoherentes y días sin volumen."""
    fechas = [date.fromisoformat(f[0]) for f in filas]
    vistas, duplicados = set(), []
    for d in fechas:
        if d in vistas:
            duplicados.append(d.isoformat())
        vistas.add(d)
    huecos, d = [], min(fechas)
    while d <= max(fechas):
        if d not in vistas:
            huecos.append(d.isoformat())
        d += timedelta(days=1)
    incoherentes, sin_volumen = [], []
    for f in filas:
        o, h, l, c, v = map(float, f[1:6])
        if not (l <= min(o, c) and h >= max(o, c) and l > 0):
            incoherentes.append(f[0])
        if v == 0:
            sin_volumen.append(f[0])
    return {
        "primera": min(fechas).isoformat(),
        "ultima": max(fechas).isoformat(),
        "velas": len(filas),
        "dias_esperados": (max(fechas) - min(fechas)).days + 1,
        "duplicados": duplicados,
        "huecos": huecos,
        "ohlc_incoherentes": incoherentes,
        "dias_volumen_cero": sin_volumen,
        "ordenadas": fechas == sorted(fechas),
    }


def guardar(filas: list[list], ruta: Path) -> str:
    """Escribe el CSV y devuelve su SHA-256."""
    ultima = max(date.fromisoformat(f[0]) for f in filas)
    comprobar_no_test(ultima)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(COLUMNAS)
        w.writerows(filas)
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def cargar(ruta: Path) -> list[list]:
    """Lee un CSV guardado. Rechaza cualquier vela de TEST mientras siga bloqueado."""
    with Path(ruta).open(encoding="utf-8") as f:
        filas = list(csv.reader(f))[1:]
    if filas:
        comprobar_no_test(max(date.fromisoformat(r[0]) for r in filas))
    return filas
