"""Vigía horario (D33): observa el mercado y anota qué haría N1 L=4 si el domingo cerrase así. NO opera ni da señales."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from copilot import copiloto as cp, datos, registro
from copilot.motor import Vela, pct

REGISTRO = registro.REGISTROS / "vigia.jsonl"
CERCA = 0.03       # aviso si el precio está a menos de un 3 % del nivel de N1
MOVIMIENTO = 0.05  # aviso si el precio se mueve más de un 5 % en 24 h


def ticker_24h() -> dict:
    """Precio público de BTCUSDT y su cambio en 24 h (datos de mercado de Binance, sin claves)."""
    d = datos._get_json("https://data-api.binance.vision/api/v3/ticker/24hr?symbol=BTCUSDT")
    return {"precio": float(d["lastPrice"]), "cambio_24h": float(d["priceChangePercent"]) / 100,
            "maximo_24h": float(d["highPrice"]), "minimo_24h": float(d["lowPrice"])}


def velas_recientes() -> list[Vela]:
    ayer = datetime.now(timezone.utc).date() - timedelta(days=1)
    return [Vela(date.fromisoformat(f[0]), *map(float, f[1:6])) for f in datos.descargar_binance(ayer - timedelta(days=60), ayer)]


def observar(velas: list[Vela], t: dict, ahora: datetime, posicion: float) -> dict:
    """velas: velas diarias cerradas hasta ayer. t: ticker. posicion: posición actual de N1 (0 o 1)."""
    hoy = ahora.date()
    domingo = hoy + timedelta(days=(6 - hoy.weekday()) % 7)  # el domingo cuya vela decide (puede ser hoy)
    base = domingo - timedelta(days=28)
    nivel = next((v.close for v in velas if v.fecha == base), None)
    p = t["precio"]
    obs = {"tipo": "observacion", "fecha_hora_utc": ahora.isoformat(timespec="minutes"), "precio": p,
           "cambio_24h": t["cambio_24h"], "domingo_decision": domingo.isoformat(), "nivel_n1": nivel,
           "posicion_n1": posicion, "avisos": [],
           "nota": "OBSERVACIÓN del vigía: no es una señal ni una orden. Solo decide la regla de N1 con el cierre del domingo."}
    if nivel is None:
        obs["avisos"].append("No se pudo calcular el nivel de N1 (falta la vela de referencia).")
        return obs
    d = p / nivel - 1
    obs["distancia_al_nivel"] = d
    arriba = p > nivel
    if posicion > 0:
        obs["si_cerrase_asi"] = "MANTENER (seguiría comprado)" if arriba else "VENTA (saldría a liquidez)"
    else:
        obs["si_cerrase_asi"] = "COMPRA (entraría)" if arriba else "NO OPERAR (seguiría en liquidez)"
    if abs(d) < CERCA:
        obs["avisos"].append(f"Precio a {pct(d)} del nivel de N1 ({nivel:,.2f}): el domingo {domingo} puede cambiar la decisión.")
    if abs(t["cambio_24h"]) > MOVIMIENTO:
        obs["avisos"].append(f"Movimiento fuerte: {pct(t['cambio_24h'])} en 24 horas.")
    return obs


def ejecutar() -> dict:
    sen = [e["datos"] for e in registro.leer(cp.RUTAS_VIVO["senales"]) if e["datos"]["tipo"] == "senal"]
    posicion = sen[-1]["posiciones"].get("N1 L=4", 0.0) if sen else 0.0
    obs = observar(velas_recientes(), ticker_24h(), datetime.now(timezone.utc), posicion)
    registro.anadir(REGISTRO, obs)
    return obs


def texto(o: dict) -> str:
    l = [f"Vigía {o['fecha_hora_utc']} UTC: BTC {o['precio']:,.2f} USDT ({pct(o['cambio_24h'])} en 24 h)."]
    if o.get("nivel_n1"):
        l.append(f"Nivel de N1 para el domingo {o['domingo_decision']}: {o['nivel_n1']:,.2f} ({pct(o['distancia_al_nivel'])}). "
                 f"Si cerrase así: {o['si_cerrase_asi']}.")
    l += [f"Aviso: {a}" for a in o["avisos"]]
    l.append(o["nota"])
    return "\n".join(l)
