"""Descarga velas (por defecto 1 hora, 730 días; o `1d max`) de Yahoo para el universo de 234 acciones + SPY (D65). Solo datos públicos."""

import gzip
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parents[1]
NY = ZoneInfo("America/New_York")
EPOCA = datetime(1970, 1, 1, tzinfo=timezone.utc)  # fromtimestamp falla antes de 1970 en Windows
INTERVALO, RANGO = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("1h", "730d")
SALIDA = RAIZ / "data" / f"acciones_{INTERVALO}_{RANGO}.json.gz"


def bajar(s: str) -> list:
    # con range=max Yahoo devuelve velas mensuales: para "max" se piden fechas (desde 2000)
    fechas = ({"period1": 946684800, "period2": int(time.time())} if RANGO == "max" else {"range": RANGO})
    q = urllib.parse.urlencode({"interval": INTERVALO, **fechas, "includePrePost": "false"})
    for intento in range(4):
        try:
            req = urllib.request.Request(f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?{q}",
                                         headers={"User-Agent": "Mozilla/5.0 (btc-copilot-research)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read().decode("utf-8"))["chart"]["result"][0]
            qd, out = d["indicators"]["quote"][0], []
            for i, ts in enumerate(d.get("timestamp", [])):
                v = [qd[k][i] for k in ("open", "high", "low", "close", "volume")]
                if all(x is not None for x in v):
                    out.append([(EPOCA + timedelta(seconds=ts)).astimezone(NY).isoformat(), *v])
            return out
        except Exception as e:  # noqa: BLE001
            print(s, "reintento", intento, e, file=sys.stderr)
            time.sleep(5 * (intento + 1))
    return []


if __name__ == "__main__":
    simbolos = [l.strip() for l in (RAIZ / "data" / "universo_skill_234.txt").read_text().split() if l.strip()] + ["SPY"]
    datos = {}
    for s in simbolos:
        datos[s] = bajar(s)
        print(s, len(datos[s]), flush=True)
        time.sleep(0.4)
    with gzip.open(SALIDA, "wt", encoding="utf-8") as f:
        json.dump(datos, f)
    print("vacios:", [s for s, v in datos.items() if not v])
