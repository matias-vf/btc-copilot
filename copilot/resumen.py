"""Resumen diario del paper trading en vivo, solo leyendo los registros (sin red, sin escribir nada)."""

from __future__ import annotations

from datetime import date

from copilot import copiloto as cp, paper, registro
from copilot.motor import pct


def texto(rutas: dict = cp.RUTAS_VIVO) -> str:
    cuenta, ent = paper.cargar(rutas["paper"])
    sen = [e["datos"] for e in registro.leer(rutas["senales"]) if e["datos"]["tipo"] == "senal"]
    vig = [e["datos"] for e in registro.leer(rutas["vigilancia"])]
    if not sen or not cuenta.valoraciones:
        return "El paper trading en vivo aún no tiene ningún día registrado."
    s, v = sen[-1], cuenta.valoraciones[-1]
    inicio = next(d["fecha"] for d in ent if d["tipo"] == "inicio")
    dias = (date.fromisoformat(v["fecha"]) - date.fromisoformat(inicio)).days + 1
    errores = [d for d in ent if d["tipo"] == "error"]
    parada = paper.parada_manual_activa(ent)
    eventos = [d for d in vig if d.get("tipo") in ("alerta", "suspension", "reactivacion", "parada_emergencia", "datos")
               and d.get("fecha") == s["vela"]]
    cerradas = cuenta.operaciones_cerradas
    l = [f"Día {dias} de paper trading (desde el {inicio}; el mes mínimo termina el 2026-12-21).",
         f"Última vela procesada: {s['vela']} (UTC). Precio BTC: {s['precio_referencia']:,.2f} USDT.",
         f"Decisión: {s['decision']}. Exposición a BTC: {pct(s['exposicion_objetivo'])} (máximo 25 %).",
         "Por qué: " + " ".join(s["justificacion"]),
         f"Capital ficticio: {v['valor']:.2f} USD ({v['valor'] - cuenta.capital_inicial:+.2f} USD, "
         f"{pct(v['valor'] / cuenta.capital_inicial - 1)}). Drawdown máximo: {pct(cuenta.drawdown())}.",
         f"Operaciones cerradas: {len(cerradas)} ({sum(o['resultado_usdt'] > 0 for o in cerradas)} positivas)"
         f"{'; hay una abierta' if cuenta.abierta else ''}. Órdenes simuladas: {len(cuenta.ejecuciones)}. "
         f"Costes: {cuenta.costes:.2f} USD."]
    l += [f"Para operar haría falta: {x}" for x in s.get("condiciones_para_operar", [])]
    l += [f"Se invalida si: {x}" for x in s.get("invalidacion", [])]
    l += [f"Vigilancia: {e['tipo']} - {e['estrategia']}: {e['motivo']}" for e in eventos]
    l += [f"Aviso: {a}" for a in s.get("avisos", [])]
    if parada:
        l.append(f"PARADA ACTIVA desde {parada.get('fecha')}: {parada.get('motivo')}")
    if errores:
        l.append(f"Errores de funcionamiento registrados: {len(errores)} (último: {errores[-1].get('error')})")
    if date.today().toordinal() - date.fromisoformat(s["vela"]).toordinal() > 2:
        l.append("ATENCIÓN: la última vela procesada tiene más de 2 días; puede que la tarea diaria no se esté ejecutando.")
    return "\n".join(l)
