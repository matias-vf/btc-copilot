"""Prompt 9: copiloto de BTC. Integra las estrategias conservadas, la gestión del riesgo (D14), la vigilancia (D17)
y el paper trading. Solo analiza y simula: no hay ningún cliente de exchange ni forma de enviar órdenes reales.
"""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from copilot import cartera as ca, datos, estrategias, paper, registro, riesgo, riesgo2, train, train2, vigilancia as vg
from copilot.costes import BINANCE_SPOT
from copilot.motor import Resultado, Vela, backtest, cargar_velas, metricas

def domingo_siguiente(f: date) -> date:
    """Próximo domingo en que N1 decide (si hoy es domingo, la decisión de hoy ya está tomada: el siguiente)."""
    return f + timedelta(days=7 if f.weekday() == 6 else 6 - f.weekday())


def nivel_n1(h, L: int = 4):
    """Cierre con el que N1 comparará el próximo domingo (el de 7·L días antes). None si falta esa vela."""
    base = domingo_siguiente(h[-1].fecha) - timedelta(days=7 * L)
    i = len(h) - 1 - (h[-1].fecha - base).days
    return h[i].close if 0 <= i < len(h) and h[i].fecha == base else None


# D31: estrategias del copiloto tras la segunda búsqueda. La primera búsqueda (B1, T1) no superó TEST (D22).
GRUPOS = {"N1": [("N1", "L=4")]}
NIVEL_SALIDA = {**riesgo.NIVEL_SALIDA, ("N1", "L=4"): nivel_n1}
ENTRADA = {("T1", "sma_n=100"): lambda h: estrategias._sma(h, 100),
           ("B1", "N=20,M=10"): lambda h: max(v.high for v in h[-20:]) if len(h) >= 20 else None,
           ("B1", "N=55,M=20"): lambda h: max(v.high for v in h[-55:]) if len(h) >= 55 else None,
           ("N1", "L=4"): nivel_n1}
ESTADO_VALIDACION = ("EXPERIMENTAL: N1 L=4 aprobó el criterio v2 en TRAIN (2017-2022), en otra época (Bitstamp "
                     "2011-2016) y en TEST (2023-2026, ya visto antes de elegirla). Debe superar al menos un mes de paper "
                     "trading en vivo. No es una estrategia plenamente validada.")
VALIDADAS: set = {("N1", "L=4")}
TEST_FICHERO = datos.DATOS / "btcusdt_binance_1d_test.csv"
MIN_CAMBIO = 0.01  # reequilibrios menores de 1 punto de exposición no se ejecutan
NY = ZoneInfo("America/New_York")
RUTAS_VIVO = {"senales": registro.SENALES, "paper": registro.REGISTROS / "paper.jsonl", "vigilancia": vg.REGISTRO}


def _nombre(k) -> str:
    return f"{k[0]} {k[1]}"


@lru_cache(maxsize=1)
def referencia_train() -> dict:
    """Todo lo que el copiloto sabe del pasado sale de TRAIN y del registro de experimentos."""
    velas = cargar_velas(train.FICHERO)
    exps = [e["datos"] for e in registro.leer(registro.EXPERIMENTOS)]
    hist = {}
    for g in GRUPOS.values():
        for k in g:
            m = next(e["metricas"] for e in exps if e.get("lote") in (train.LOTE, train2.LOTE)
                     and e["estrategia_id"] == k[0] and e["variante"] == k[1])
            ops = riesgo.operaciones(backtest(velas, estrategias.crear(*k)))
            ganadoras = sorted(x for x in ops if x > 0)
            semanas = sorted(velas[t].close / velas[t - 7].close - 1 for t in range(7, len(velas)))
            hist[k] = {"p5_semana": semanas[len(semanas) // 20],
                       "rentabilidad": m["rentabilidad"], "sharpe": m["sharpe"], "max_drawdown": m["max_drawdown"],
                       "operaciones": m["operaciones"], "peor_operacion": min(ops),
                       "mediana_ganadora": ganadoras[len(ganadoras) // 2] if ganadoras else 0.0,
                       "aciertos": len(ganadoras) / len(ops) if ops else 0.0}
    c25 = next(e["metricas"] for e in exps if e.get("lote") == riesgo2.LOTE and e["variante"] == "exposicion=25%"
               and e["epoca"] == "TRAIN")
    return {"vig": vg.referencia(velas, GRUPOS), "hist": hist, "c25": c25}


# --- Contexto: sesiones y mercado -------------------------------------------------

def sesion(ahora: datetime) -> dict:
    ny = ahora.astimezone(NY)
    h = ny.hour + ny.minute / 60
    activas = [n for n, (a, b) in {"Asia": (19, 4), "Europa": (3, 12), "EE. UU.": (8, 17)}.items()
               if (a <= h < b if a < b else h >= a or h < b)]
    return {"hora_nueva_york": ny.strftime("%Y-%m-%d %H:%M %Z"), "sesiones_activas": activas,
            "mayor_actividad": "Europa y EE. UU. a la vez" if {"Europa", "EE. UU."} <= set(activas) else None,
            "fin_de_semana": ny.weekday() >= 5,
            "nota": "BTC cotiza 24/7; la vela diaria cierra a las 00:00 UTC "
                    f"({datetime(ahora.year, ahora.month, ahora.day, tzinfo=timezone.utc).astimezone(NY):%H:%M} en Nueva York)."}


def mercado(velas, ref_vig) -> dict:
    c = velas[-1].close
    s50, s200 = estrategias._sma(velas, 50), estrategias._sma(velas, 200)
    v30 = vg._vol30(velas, len(velas) - 1)
    vol_med = sum(v.volumen for v in velas[-31:-1]) / 30
    tendencia = ("alcista (precio sobre SMA 50 y SMA 200)" if c > s50 and c > s200 else
                 "bajista (precio bajo SMA 50 y SMA 200)" if c < s50 and c < s200 else "mixta")
    return {
        "tendencia": tendencia, "sma50": s50, "sma200": s200,
        "volatilidad_30d": v30,
        "volatilidad_estado": ("alta" if v30 > ref_vig["vol_p95"] else "baja" if v30 < ref_vig["vol_p5"] else "normal"),
        "volumen_vs_media_30d": velas[-1].volumen / vol_med if vol_med else None,
        "resistencias": {"máximo 20 d": max(v.high for v in velas[-20:]), "máximo 55 d": max(v.high for v in velas[-55:])},
        "soportes": {"mínimo 20 d": min(v.low for v in velas[-20:]), "mínimo 55 d": min(v.low for v in velas[-55:])},
        "no_disponible": ["funding y open interest (solo spot)", "liquidaciones", "spread en vivo",
                          "noticias verificables", "correlación con otros activos"],
    }


# --- Decisión ---------------------------------------------------------------------

def _pesos(velas) -> dict[str, float]:
    """Pesos C1 que regirán mañana (D11), solo con datos hasta hoy."""
    res = {k: backtest(velas, estrategias.crear(*k)) for g in GRUPOS.values() for k in g}
    mangas = {g: [(ca.rents(res[k]), ca.exposiciones(res[k])) for k in ks] for g, ks in GRUPOS.items()}
    _, hist = ca.cartera([v.fecha for v in velas], mangas)
    if (velas[-1].fecha + timedelta(days=1)).month != velas[-1].fecha.month:  # mañana empieza mes: nuevos pesos
        r_est = {g: [sum(r[t] for r, _ in vs) / len(vs) for t in range(len(velas))] for g, vs in mangas.items()}
        return ca.pesos(r_est)
    return hist[-1]["pesos"]


def decidir(velas, posiciones: dict, objetivo_prev: float, vig_dia: dict | None, problemas: list[str],
            parada: dict | None, ahora: datetime, solo_validadas: bool = True) -> dict:
    """solo_validadas=False solo para repeticiones técnicas y pruebas de la maquinaria."""
    ref = referencia_train()
    v = velas[-1]
    c = v.close
    senal = {"tipo": "senal", "fecha_hora_utc": ahora.isoformat(timespec="seconds"), "vela": v.fecha.isoformat(),
             "activo": "BTC", "par": "BTCUSDT (Binance spot)", "temporalidad": "1d", "precio_referencia": c,
             "valida_hasta_utc": (datetime(v.fecha.year, v.fecha.month, v.fecha.day, tzinfo=timezone.utc)
                                  + timedelta(days=2)).isoformat(),
             "estado_validacion": ESTADO_VALIDACION,
             "confianza": "Sin porcentaje de confianza: no hay datos para calibrarlo como probabilidad.",
             "sesion": sesion(ahora), "avisos": [], "componentes": [], "justificacion": [], "invalidacion": [],
             "condiciones_para_operar": []}
    if solo_validadas and not VALIDADAS:
        senal.update(decision="VENTA" if objetivo_prev > 0 else "NO OPERAR", exposicion_anterior=objetivo_prev,
                     exposicion_objetivo=0.0, posiciones={}, estado_validacion="NINGUNA ESTRATEGIA VALIDADA")
        if objetivo_prev > 0:
            senal["orden"] = {"exposicion_objetivo": 0.0, "se_ejecuta": "en la apertura de la vela siguiente (paper)"}
        senal["justificacion"].append(
            "No hay ninguna estrategia validada: B1 20/10, B1 55/20 y T1 SMA 100 no superaron a Buy & Hold en TEST "
            "(regla D21, docs/test.md). Sin una estrategia validada no se recomienda ninguna operación.")
        senal["condiciones_para_operar"].append(
            "Que una estrategia nueva, registrada antes de probarla, supere todo el proceso (docs/decisiones.md, D22).")
        return senal
    if problemas:
        senal.update(decision="MANTENER" if objetivo_prev > 0 else "NO OPERAR", exposicion_objetivo=objetivo_prev,
                     exposicion_anterior=objetivo_prev, posiciones=posiciones)
        senal["justificacion"].append("Datos insuficientes o con anomalías: no se generan señales nuevas.")
        senal["avisos"] += problemas
        return senal
    senal["mercado"] = mercado(velas, ref["vig"])
    pesos = _pesos(velas)
    nuevas, objetivo, riesgo_salida, riesgo_hist = {}, 0.0, 0.0, 0.0
    for g, ks in GRUPOS.items():
        for k in ks:
            n = _nombre(k)
            antes = posiciones.get(n, 0.0)
            quiere = estrategias.crear(*k)(velas, antes)
            estado = (vig_dia or {}).get("estados", {}).get(n, "ACTIVA")
            if parada:
                ahora_pos, nota = 0.0, "parada activa: se cierra todo"
            elif estado != "ACTIVA":
                ahora_pos, nota = min(quiere, antes), "suspendida: sin entradas nuevas (las salidas sí se permiten)"
            else:
                ahora_pos, nota = quiere, ""
            nuevas[n] = ahora_pos
            peso = pesos[g] / len(ks) * paper.LIMITE_EXPOSICION
            objetivo += peso * ahora_pos
            salida, entrada = NIVEL_SALIDA[k](velas), ENTRADA[k](velas)
            h = ref["hist"][k]
            comp = {"estrategia": n, "estado_vigilancia": estado, "posicion_anterior": antes, "posicion_nueva": ahora_pos,
                    "peso_en_capital": peso, "nivel_salida": salida, "nivel_entrada": entrada, "nota": nota,
                    "historico_train": h}
            senal["componentes"].append(comp)
            prox = domingo_siguiente(v.fecha)
            if k[0] == "N1":
                if v.fecha.weekday() == 6 and len(velas) > 28:
                    r4 = c / velas[-29].close - 1
                    regla = f"domingo: rentabilidad de 4 semanas {r4:+.1%} ({'> 0' if r4 > 0 else '<= 0'})"
                else:
                    regla = f"N1 solo decide los domingos; el próximo es el {prox}"
            elif k[0] == "T1":
                regla = f"cierre {c:,.2f} {'>' if c > (salida or 0) else '<='} SMA 100 {salida:,.2f}"
            else:
                regla = (f"cierre {c:,.2f}; máximo de {k[1].split(',')[0][2:]} velas {entrada:,.2f}; "
                         f"mínimo de {k[1].split('M=')[1]} velas {salida:,.2f}")
            if ahora_pos > antes:
                senal["justificacion"].append(f"{n}: entra ({regla}).")
            elif ahora_pos < antes:
                senal["justificacion"].append(f"{n}: sale ({regla}){' - ' + nota if nota else ''}.")
            if ahora_pos > 0:
                d = (c - salida) / c if salida else 0.0
                # N1 no tiene salida hasta el domingo: su riesgo es una mala semana de TRAIN (percentil 5)
                riesgo_salida += peso * (abs(h["p5_semana"]) if k[0] == "N1" else max(d, 0.0))
                riesgo_hist += peso * abs(h["peor_operacion"])
                cuando = f"el cierre del domingo {prox}" if k[0] == "N1" else "un cierre diario"
                senal["invalidacion"].append(f"{n}: se invalida con {cuando} por debajo de {salida:,.2f} "
                                             f"({-d:+.1%} desde el precio de referencia).")
            else:
                if entrada:
                    cuando = f"el cierre del domingo {prox}" if k[0] == "N1" else "un cierre diario"
                    senal["condiciones_para_operar"].append(
                        f"{n}: entraría con {cuando} por encima de {entrada:,.2f} ({entrada / c - 1:+.1%})"
                        + (" (suspendida: no entrará hasta reactivarse)" if estado != "ACTIVA" else "") + ".")
    objetivo = min(objetivo, paper.LIMITE_EXPOSICION)
    abiertas = sum(1 for x in nuevas.values() if x > 0)
    assert abiertas <= paper.LIMITE_POSICIONES
    cambio = objetivo - objetivo_prev
    if parada:
        senal["avisos"].append(f"PARADA ACTIVA desde {parada.get('fecha')}: {parada.get('motivo')}. "
                               "Solo se reanuda con tu aprobación (python -m copilot reanudar).")
    if abs(cambio) >= MIN_CAMBIO or (objetivo == 0 and objetivo_prev > 0):
        decision = "COMPRA" if cambio > 0 else "VENTA"
        senal["orden"] = {"exposicion_objetivo": objetivo, "se_ejecuta": "en la apertura de la vela siguiente (paper)"}
        if not senal["justificacion"]:
            senal["justificacion"].append(f"Reequilibrio mensual de pesos (B1 {pesos['B1']:.0%}, T1 {pesos['T1']:.0%}).")
    else:
        decision = "MANTENER" if objetivo_prev > 0 else "NO OPERAR"
        objetivo = objetivo_prev if abs(cambio) < MIN_CAMBIO else objetivo
        senal["justificacion"].append("No hay ninguna operación recomendable hoy: ninguna regla registrada cambia de estado."
                                      if decision == "NO OPERAR" else
                                      "Las posiciones abiertas siguen cumpliendo su regla; no hay cambios.")
    senal.update(decision=decision, exposicion_anterior=objetivo_prev, exposicion_objetivo=objetivo,
                 posiciones=nuevas, pesos=pesos,
                 riesgo_estimado={"perdida_si_saltan_todas_las_salidas": riesgo_salida,
                                  "escenario_desfavorable_historico": riesgo_hist,
                                  "nota": "En % del capital total. Para N1: pérdida de una mala semana de TRAIN "
                                          "(solo 1 de cada 20 fue peor). Un hueco de precio puede saltarse el nivel de salida."})
    if decision == "COMPRA":
        entra = [comp for comp in senal["componentes"] if comp["posicion_nueva"] > comp["posicion_anterior"]]
        senal["objetivo"] = "; ".join(
            f"{comp['estrategia']}: sin precio objetivo fijo (sigue la tendencia); en TRAIN la operación ganadora "
            f"mediana ganó un {comp['historico_train']['mediana_ganadora']:+.1%} y acertó el "
            f"{comp['historico_train']['aciertos']:.0%} de las veces" for comp in entra) or "reequilibrio"
        senal["escenario_desfavorable"] = "; ".join(
            f"{comp['estrategia']}: peor operación en TRAIN {comp['historico_train']['peor_operacion']:+.1%} "
            f"de la posición ({comp['historico_train']['peor_operacion'] * comp['peso_en_capital']:+.2%} del capital)"
            for comp in entra) or "reequilibrio"
    senal["historico_cartera_25"] = {k: ref["c25"][k] for k in ("rentabilidad", "cagr", "sharpe", "max_drawdown")}
    return senal


# --- Ciclo diario -----------------------------------------------------------------

def _ultima(entradas, tipo):
    return next((d for d in reversed(entradas) if d["tipo"] == tipo), None)


def ciclo(velas, rutas: dict, ahora: datetime | None = None, vig: tuple[dict, list] | None = None,
          solo_validadas: bool = True) -> dict:
    """Un día del copiloto, justo después del cierre de la vela velas[-1]. Solo usa velas hasta hoy."""
    v = velas[-1]
    ahora = ahora or datetime.now(timezone.utc)
    cuenta, ent_paper = paper.cargar(rutas["paper"])
    if not ent_paper:
        registro.anadir(rutas["paper"], {"tipo": "inicio", "fecha": v.fecha.isoformat(), "capital": paper.CAPITAL_INICIAL})
        cuenta, ent_paper = paper.cargar(rutas["paper"])
    senales = [e["datos"] for e in registro.leer(rutas["senales"])]
    previa = _ultima(senales, "senal")
    problemas = vg.problemas_datos(velas, ahora)
    # 1) Orden pendiente de ayer: se ejecuta en la apertura de hoy
    if previa and previa.get("orden") and previa["vela"] == velas[-2].fecha.isoformat():
        if problemas:
            registro.anadir(rutas["paper"], {"tipo": "orden_cancelada", "fecha": v.fecha.isoformat(), "motivo": problemas})
        else:
            e = paper.simular_ejecucion(cuenta, previa["orden"]["exposicion_objetivo"], v.open, v.fecha.isoformat())
            if e:
                e["tipo"], e["precio_senal"] = "ejecucion", previa["precio_referencia"]
                registro.anadir(rutas["paper"], e)
                cuenta.aplicar(e)
    # 2) Valoración al cierre y límite de pérdidas
    val = {"tipo": "valoracion", "fecha": v.fecha.isoformat(), "precio": v.close, "valor": cuenta.valor(v.close),
           "exposicion": cuenta.exposicion(v.close)}
    registro.anadir(rutas["paper"], val)
    cuenta.valoraciones.append(val)
    parada = paper.parada_manual_activa(ent_paper)
    if not parada and cuenta.drawdown_actual() < -paper.LIMITE_PERDIDA:
        parada = {"tipo": "parada_emergencia", "fecha": v.fecha.isoformat(),
                  "motivo": f"pérdida de la cuenta {cuenta.drawdown_actual():.1%} supera el límite del 35 %"}
        registro.anadir(rutas["paper"], parada)
    # 3) Vigilancia del deterioro
    if vig is None:
        inicio = _ultima([d for d in ent_paper if d["tipo"] in ("inicio", "reanudacion")], "inicio") or {}
        reanuda = _ultima(ent_paper, "reanudacion")
        desde_f = date.fromisoformat((reanuda or inicio).get("fecha", v.fecha.isoformat()))
        desde = next(i for i, x in enumerate(velas) if x.fecha >= desde_f)
        r = vg.vigilar(velas, referencia_train()["vig"], desde, ahora=ahora)
        vig = (r["diario"][-1], [e for e in r["eventos"] if e["fecha"] == v.fecha.isoformat()])
    dia, eventos_hoy = vig
    for ev in eventos_hoy:
        registro.anadir(rutas["vigilancia"], ev)
    registro.anadir(rutas["vigilancia"], {"tipo": "estado_diario", **dia})
    if dia.get("parada_emergencia") and not parada:
        parada = {"tipo": "parada_emergencia", "fecha": v.fecha.isoformat(),
                  "motivo": "la vigilancia detectó que la cartera superó su peor drawdown del backtest"}
        registro.anadir(rutas["paper"], parada)
    # 4) Señal del día
    posiciones = previa["posiciones"] if previa else {}
    obj_prev = previa["exposicion_objetivo"] if previa else 0.0
    senal = decidir(velas, posiciones, obj_prev, dia, problemas, parada, ahora, solo_validadas)
    senal["cuenta"] = {"valor": val["valor"], "exposicion": val["exposicion"], "drawdown": cuenta.drawdown_actual()}
    registro.anadir(rutas["senales"], senal)
    # 5) Seguimiento de señales pasadas (1, 7 y 30 días)
    for s in senales:
        if s.get("tipo") == "senal" and s["decision"] in ("COMPRA", "VENTA"):
            dias = (v.fecha - date.fromisoformat(s["vela"])).days
            if dias in (1, 7, 30):
                cambio = v.close / s["precio_referencia"] - 1
                signo = 1 if s["decision"] == "COMPRA" else -1
                coste = 2 * BINANCE_SPOT.por_lado()
                registro.anadir(rutas["senales"], {
                    "tipo": "seguimiento", "senal_vela": s["vela"], "decision": s["decision"], "dias": dias,
                    "precio_referencia": s["precio_referencia"], "precio_hoy": v.close, "cambio_precio": cambio,
                    "resultado_hipotetico": signo * cambio, "costes_estimados": coste,
                    "resultado_neto_hipotetico": signo * cambio - coste})
    return senal


# --- Repetición (paper trading sobre días pasados) ---------------------------------

def repeticion(desde: date, hasta: date, carpeta: Path) -> Path:
    """Ejecuta el ciclo diario día a día sobre velas de TRAIN, como si fuera en vivo. Registros propios en `carpeta`."""
    if carpeta.exists() and any(carpeta.iterdir()):
        raise SystemExit(f"{carpeta} ya existe: una repetición no se reescribe.")
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas = {"senales": carpeta / "senales.jsonl", "paper": carpeta / "paper.jsonl",
             "vigilancia": carpeta / "vigilancia.jsonl"}
    velas = cargar_velas(train.FICHERO) + (cargar_velas(TEST_FICHERO) if hasta >= date(2023, 1, 1) else [])
    i0 = next(i for i, x in enumerate(velas) if x.fecha >= desde)
    i1 = max(i for i, x in enumerate(velas) if x.fecha <= hasta)
    # La vigilancia es causal (prueba automática), así que se calcula una vez para todo el periodo.
    r = vg.vigilar(velas[: i1 + 1], referencia_train()["vig"], i0)
    for t in range(i0, i1 + 1):
        f = velas[t].fecha
        ahora = datetime(f.year, f.month, f.day, tzinfo=timezone.utc) + timedelta(days=1, minutes=5)
        ciclo(velas[: t + 1], rutas, ahora, (r["diario"][t - i0], [e for e in r["eventos"] if e["fecha"] == f.isoformat()]),
              solo_validadas=False)  # repetición técnica de la maquinaria con las estrategias del Prompt 9
    return carpeta


def comparar(carpeta_o_rutas, velas=None) -> dict:
    """Comparación diaria paper frente a backtest (cartera C1 al 25 %) en las mismas fechas."""
    rutas = carpeta_o_rutas if isinstance(carpeta_o_rutas, dict) else {
        "senales": carpeta_o_rutas / "senales.jsonl", "paper": carpeta_o_rutas / "paper.jsonl"}
    cuenta, ent = paper.cargar(rutas["paper"])
    vals = cuenta.valoraciones
    velas = velas or cargar_velas(train.FICHERO) + cargar_velas(TEST_FICHERO)
    idx = {v.fecha.isoformat(): i for i, v in enumerate(velas)}
    i0, i1 = idx[vals[0]["fecha"]], idx[vals[-1]["fecha"]]
    bt = vg.series(velas[: i1 + 1], GRUPOS)[vg.CARTERA]
    eq_bt = [paper.CAPITAL_INICIAL * bt.equity[i] / bt.equity[i0 - 1] for i in range(i0, i1 + 1)]

    def res(eq):
        r = Resultado(capital=paper.CAPITAL_INICIAL)
        r.fechas, r.equity = [velas[i].fecha for i in range(i0, i1 + 1)], eq
        return metricas(r)

    mp, mb = res([v["valor"] for v in vals]), res(eq_bt)
    ej = cuenta.ejecuciones
    difs = [abs(e["precio_simulado"] / e["precio_teorico"] - 1) for e in ej]
    difs_senal = [abs(e["precio_teorico"] / e["precio_senal"] - 1) for e in ej if e.get("precio_senal")]
    cerradas = cuenta.operaciones_cerradas
    sen = [e["datos"] for e in registro.leer(rutas["senales"])]
    return {
        "desde": vals[0]["fecha"], "hasta": vals[-1]["fecha"], "dias": len(vals),
        "paper": mp, "backtest": mb, "equity_paper": [v["valor"] for v in vals], "equity_backtest": eq_bt,
        "fechas": [v["fecha"] for v in vals],
        "ejecuciones": len(ej), "operaciones_cerradas": len(cerradas),
        "operaciones_positivas": sum(1 for o in cerradas if o["resultado_usdt"] > 0),
        "operacion_abierta": cuenta.abierta is not None,
        "costes_usdt": cuenta.costes,
        "dif_precio_simulado_media": sum(difs) / len(difs) if difs else 0.0,
        "dif_senal_ejecucion_media": sum(difs_senal) / len(difs_senal) if difs_senal else 0.0,
        "senales": [s for s in sen if s["tipo"] == "senal"],
        "paradas": [d for d in ent if d["tipo"] in ("parada_manual", "parada_emergencia", "reanudacion")],
        "cuenta": cuenta,
    }


# --- Comunicación -----------------------------------------------------------------

def ficha(s: dict) -> str:
    l = [f"=== {s['decision']} === BTC · {s['par']} · vela {s['temporalidad']} del {s['vela']} (UTC)",
         f"Precio de referencia: {s['precio_referencia']:,.2f} USDT · válida hasta {s['valida_hasta_utc'][:16]} UTC",
         f"Hora en Nueva York: {s['sesion']['hora_nueva_york']} · sesiones activas: "
         f"{', '.join(s['sesion']['sesiones_activas']) or 'ninguna'}",
         f"Exposición a BTC: {s['exposicion_anterior']:.1%} -> {s['exposicion_objetivo']:.1%} del capital (máximo 25 %)", ""]
    for a in s["avisos"]:
        l.append(f"AVISO: {a}")
    l.append("Por qué:")
    l += [f"  - {x}" for x in s["justificacion"]]
    if s["componentes"]:
        l.append("Estrategias:")
        for c in s["componentes"]:
            h = c["historico_train"]
            l.append(f"  - {c['estrategia']} [{c['estado_vigilancia']}]: {'comprada' if c['posicion_nueva'] else 'en liquidez'}"
                     f" · TRAIN: {h['rentabilidad']:+.0%}, Sharpe {h['sharpe']:.2f}, drawdown {h['max_drawdown']:.0%},"
                     f" {h['operaciones']} operaciones")
    if s.get("riesgo_estimado"):
        r = s["riesgo_estimado"]
        l.append(f"Riesgo estimado: {r['perdida_si_saltan_todas_las_salidas']:.2%} del capital hasta la próxima decisión; "
                 f"{r['escenario_desfavorable_historico']:.2%} en el peor caso histórico. {r['nota']}")
    for clave, titulo in (("objetivo", "Objetivo"), ("escenario_desfavorable", "Escenario desfavorable")):
        if s.get(clave):
            l.append(f"{titulo}: {s[clave]}")
    if s["invalidacion"]:
        l.append("Se invalida si:")
        l += [f"  - {x}" for x in s["invalidacion"]]
    if s["condiciones_para_operar"]:
        l.append("Para operar haría falta:")
        l += [f"  - {x}" for x in s["condiciones_para_operar"]]
    if s.get("mercado"):
        m = s["mercado"]
        l.append(f"Mercado: tendencia {m['tendencia']}; volatilidad 30 d {m['volatilidad_30d']:.0%} ({m['volatilidad_estado']}); "
                 f"volumen {m['volumen_vs_media_30d']:.2f} veces la media de 30 días.")
        l.append("  Resistencias: " + ", ".join(f"{k} {x:,.0f}" for k, x in m["resistencias"].items())
                 + " · Soportes: " + ", ".join(f"{k} {x:,.0f}" for k, x in m["soportes"].items()))
        l.append("  No disponible: " + "; ".join(m["no_disponible"]) + ".")
    l += [f"Estado: {s['estado_validacion']}", s["confianza"],
          "Solo es análisis y paper trading. No se envía ninguna orden real."]
    return "\n".join(l)


def lectura_visual(lectura: dict, s: dict) -> dict:
    """Comprueba lo que Claude ha leído en una captura de pantalla. Nunca cambia la decisión: solo la complementa."""
    notas, usable = [], True
    activo = (lectura.get("activo") or "").upper()
    if "BTC" not in activo and "XBT" not in activo:
        notas.append("No se identifica BTC en el gráfico: la lectura visual no se usa.")
        usable = False
    tf = (lectura.get("temporalidad") or "").lower()
    if not tf:
        notas.append("No se identifica la temporalidad: la lectura visual no se usa.")
        usable = False
    elif tf not in ("1d", "d", "diario", "1 día"):
        notas.append(f"El gráfico es de {tf}; las estrategias usan velas diarias. Solo sirve de contexto.")
    pv = lectura.get("precio_visible")
    if usable and pv:
        d = pv / s["precio_referencia"] - 1
        if abs(d) > 0.02:
            notas.append(f"El precio visible ({pv:,.2f}) difiere un {d:+.1%} del dato ({s['precio_referencia']:,.2f}): "
                         "puede ser otra fecha, otro par u otro exchange. No se usa.")
            usable = False
    return {"usable": usable, "notas": notas, "efecto_en_la_decision": "ninguno (la decisión sale de las reglas registradas)"}


# --- Modo en vivo -----------------------------------------------------------------

def velas_en_vivo() -> list[Vela]:
    """Últimas velas diarias cerradas de Binance. Hoy siempre cae en TEST: lanza DatosTestBloqueados hasta «UNLOCK»."""
    ayer = datetime.now(timezone.utc).date() - timedelta(days=1)
    filas = datos.descargar_binance(ayer - timedelta(days=900), ayer)
    return [Vela(date.fromisoformat(f[0]), *map(float, f[1:6])) for f in filas]


def en_marcha() -> None:
    """Funcionamiento continuo: un ciclo cada día a las 00:05 UTC mientras el ordenador esté encendido."""
    while True:
        try:
            s = ciclo(velas_en_vivo(), RUTAS_VIVO)
            print(ficha(s))
        except datos.DatosTestBloqueados:
            raise
        except Exception as e:  # error de funcionamiento: se registra y se reintenta en 10 minutos
            registro.anadir(RUTAS_VIVO["paper"], {"tipo": "error", "fecha_hora_utc": datetime.now(timezone.utc).isoformat(),
                                                  "error": repr(e)})
            time.sleep(600)
            continue
        ahora = datetime.now(timezone.utc)
        siguiente = datetime(ahora.year, ahora.month, ahora.day, tzinfo=timezone.utc) + timedelta(days=1, minutes=5)
        time.sleep(max(60, (siguiente - ahora).total_seconds()))
