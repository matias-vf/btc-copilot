import random
import unittest
from datetime import date, timedelta
from math import exp

from copilot import anticipacion, estrategias, registro
from copilot.costes import BINANCE_SPOT, Costes
from copilot.motor import Vela, alertas, backtest, metricas, requiere_costes_x2_x3

SIN_COSTES = Costes(comision=0, medio_spread=0, slippage=0)


def velas_fijas(precios):
    """Velas con open = cierre anterior; precios = cierres."""
    d0, out, prev = date(2020, 1, 1), [], precios[0]
    for i, c in enumerate(precios):
        out.append(Vela(d0 + timedelta(days=i), prev, max(prev, c), min(prev, c), c, 1.0))
        prev = c
    return out


def velas_aleatorias(n=500, semilla=1):
    rnd, p, out, d0 = random.Random(semilla), 100.0, [], date(2019, 1, 6)
    for i in range(n):
        o = p
        p = p * exp(rnd.gauss(0, 0.04))
        out.append(Vela(d0 + timedelta(days=i), o, max(o, p) * 1.01, min(o, p) * 0.99, p, 10.0))
    return out


class TestMotor(unittest.TestCase):
    def test_ejecuta_en_la_apertura_siguiente(self):
        v = velas_fijas([100, 110, 121])
        v[1] = v[1]._replace(open=105)  # la orden debe usar este precio, no el cierre 100
        r = backtest(v, estrategias.buy_hold, SIN_COSTES)
        self.assertEqual(r.ejecuciones[0]["fecha"], v[1].fecha)
        self.assertEqual(r.ejecuciones[0]["precio"], 105)
        self.assertAlmostEqual(r.equity[0], 100)            # día 0: aún en liquidez
        self.assertAlmostEqual(r.equity[2], 100 * 121 / 105)

    def test_ultima_vela_no_genera_orden(self):
        senal_tardia = lambda h, pos: 1.0 if len(h) == 3 else 0.0
        r = backtest(velas_fijas([100, 100, 100]), senal_tardia, SIN_COSTES)
        self.assertEqual(r.ejecuciones, [])

    def test_costes_ida_y_vuelta(self):
        c = Costes(comision=0.001, medio_spread=0, slippage=0)
        alterna = lambda h, pos: 1.0 if len(h) == 1 else 0.0  # compra en día 1, vende en día 2
        r = backtest(velas_fijas([100, 100, 100, 100]), alterna, c)
        self.assertAlmostEqual(r.equity[-1], 100 / 1.001 * (1 - 0.001))
        self.assertEqual(len(r.ejecuciones), 2)

    def test_liquidacion_final_y_sin_efectivo_negativo(self):
        c = Costes(comision=0.001, medio_spread=0, slippage=0)
        r = backtest(velas_fijas([100, 100, 100]), estrategias.buy_hold, c)
        self.assertAlmostEqual(r.equity[-1], 100 / 1.001 * 0.999)

    def test_multiplicador(self):
        self.assertAlmostEqual(BINANCE_SPOT.x(3).por_lado(), 3 * BINANCE_SPOT.por_lado())
        self.assertAlmostEqual(BINANCE_SPOT.por_lado(), 0.0016)

    def test_rechaza_apalancamiento(self):
        with self.assertRaises(ValueError):
            backtest(velas_fijas([1, 2, 3]), lambda h, p: 2.0)

    def test_metricas(self):
        r = backtest(velas_fijas([100, 100, 50, 100]), estrategias.buy_hold, SIN_COSTES)
        m = metricas(r)
        self.assertAlmostEqual(m["max_drawdown"], -0.5)
        self.assertAlmostEqual(m["rentabilidad"], 0.0)
        self.assertEqual(m["operaciones"], 1)
        self.assertFalse(requiere_costes_x2_x3({"ejecuciones_por_semana": 1.0}))
        self.assertTrue(requiere_costes_x2_x3({"ejecuciones_por_semana": 1.5}))

    def test_alertas(self):
        bh = {"cagr": 0.5}
        self.assertEqual(alertas({"sharpe": 1, "cagr": 0.6, "operaciones": 5, "max_drawdown": -0.6}, bh), [])
        self.assertEqual(len(alertas({"sharpe": 3, "cagr": 2.0, "operaciones": 5, "max_drawdown": -0.05}, bh)), 3)


class TestEstrategias(unittest.TestCase):
    def test_t1_sma(self):
        f = estrategias.t1_sma(3)
        self.assertEqual(f(velas_fijas([1, 1]), 0), 0.0)            # datos insuficientes
        self.assertEqual(f(velas_fijas([1, 1, 4]), 0), 1.0)         # 4 > 2
        self.assertEqual(f(velas_fijas([4, 4, 1]), 0), 0.0)

    def test_t2(self):
        f = estrategias.t2_tsmom(2)
        self.assertEqual(f(velas_fijas([1, 5, 2]), 0), 1.0)         # 2/1 - 1 > 0
        self.assertEqual(f(velas_fijas([3, 5, 2]), 0), 0.0)

    def test_b1_entrada_y_salida(self):
        f = estrategias.b1_donchian(2, 2)
        v = velas_fijas([10, 10, 10, 12])
        self.assertEqual(f(v, 0), 1.0)                                # 12 > máximo previo
        v = velas_fijas([10, 9, 10, 9.5])
        self.assertEqual(f(v, 1), 1.0)                                # 9.5 no rompe el mínimo previo (9)
        v = velas_fijas([10, 10, 10, 5])
        self.assertEqual(f(v, 1), 0.0)

    def test_rsi_wilder(self):
        h = velas_fijas([10, 11, 12, 13])
        self.assertEqual(estrategias._rsi_wilder(h, 2), 100.0)
        h = velas_fijas([10, 11, 10, 11])  # +1, -1, +1
        # media inicial: sube 0.5, baja 0.5; luego sube (0.5+1)/2=0.75, baja 0.25 -> RSI 75
        self.assertAlmostEqual(estrategias._rsi_wilder(h, 2), 75.0)

    def test_p1_exposicion_semanal(self):
        v = velas_aleatorias(120)
        f = estrategias.p1_vol_objetivo(estrategias.buy_hold, 0.4, 20)
        r = backtest(v, f, SIN_COSTES)
        # La exposición solo cambia en lunes (ejecución tras el cierre del domingo)
        for e in r.ejecuciones:
            self.assertEqual(e["fecha"].weekday(), 0, e)
        self.assertTrue(all(0 <= s <= 1 for s in r.senales))

    def test_todas_las_variantes_registradas_se_construyen(self):
        ideas = [e["datos"] for e in registro.leer(registro.IDEAS) if e["datos"]["estado"] != "descartada"
                 and e["datos"]["familia"] not in ("Cartera", "Riesgo") and e["datos"].get("busqueda", 1) == 1]
        total = 0
        for idea in ideas:
            for var in idea["configuraciones_permitidas"]:
                estrategias.crear(idea["id"], var)
                total += 1
        self.assertEqual(total, 31)


class TestAnticipacion(unittest.TestCase):
    def test_todas_las_variantes_son_causales(self):
        v = velas_aleatorias(420)
        ideas = [e["datos"] for e in registro.leer(registro.IDEAS) if e["datos"]["estado"] != "descartada"
                 and e["datos"]["familia"] not in ("Cartera", "Riesgo") and e["datos"].get("busqueda", 1) == 1]
        variantes = [("BH", "buy_hold")] + [(i["id"], x) for i in ideas for x in i["configuraciones_permitidas"]]
        for eid, var in variantes:
            with self.subTest(eid=eid, var=var):
                self.assertEqual(anticipacion.comprobar(v, lambda _d: estrategias.crear(eid, var), cortes=[250, 380]), [])

    def test_detecta_una_estrategia_tramposa(self):
        v = velas_aleatorias(200)
        def tramposa(datos):  # precalcula sobre la serie completa: mira el cierre de mañana
            return lambda h, pos: 1.0 if datos[len(h)].close > h[-1].close else 0.0
        self.assertNotEqual(anticipacion.comprobar(v, tramposa), [])


if __name__ == "__main__":
    unittest.main()


class TestRobustez(unittest.TestCase):
    def test_spearman(self):
        from copilot.robustez import spearman
        self.assertAlmostEqual(spearman([1, 2, 3], [10, 20, 30]), 1.0)
        self.assertAlmostEqual(spearman([1, 2, 3], [3, 2, 1]), -1.0)
        self.assertAlmostEqual(spearman([1, 1, 2], [1, 1, 2]), 1.0)

    def test_regimenes_y_rent_en_meses(self):
        from copilot.robustez import regimenes, rent_en_meses
        v = velas_aleatorias(400)
        reg = regimenes(v)
        meses = {f.fecha.strftime("%Y-%m") for f in v}
        self.assertEqual(set(reg["alcista"]) | set(reg["bajista"]) | set(reg["lateral"]), meses)
        self.assertEqual(set(reg["vol. alta"]) | set(reg["vol. baja"]), meses)
        r = backtest(v, estrategias.buy_hold, SIN_COSTES)
        self.assertAlmostEqual(rent_en_meses(r, sorted(meses)), r.equity[-1] / 100 - 1)


class TestCartera(unittest.TestCase):
    def _mangas(self, n=300, semilla=3):
        rnd = random.Random(semilla)
        r = lambda: [rnd.gauss(0, 0.02 * k) for k in [1] * n]
        x = [1.0] * n
        return {"B1": [(r(), x), (r(), x)], "T1": [([v * 3 for v in r()], x)]}

    def test_pesos_inversos_a_volatilidad(self):
        from copilot.cartera import pesos
        w = pesos({"A": [0.01, -0.01] * 50, "B": [0.02, -0.02] * 50})
        self.assertAlmostEqual(w["A"], 2 / 3)
        self.assertEqual(pesos({"A": [0.1], "B": [0.2]}), {"A": 0.5, "B": 0.5})  # pocos datos
        self.assertEqual(pesos({"A": [0.0] * 100, "B": [0.02, -0.02] * 50}), {"A": 0.0, "B": 1.0})

    def test_sin_costes_y_un_mes_es_la_media_ponderada(self):
        from copilot.cartera import cartera
        fechas = [date(2020, 1, 1) + timedelta(days=i) for i in range(10)]
        m = {"A": [([0.01] * 10, [1.0] * 10)], "B": [([0.0] * 10, [0.0] * 10)]}
        c, _ = cartera(fechas, m, SIN_COSTES)
        self.assertAlmostEqual(c.equity[-1], 50 * 1.01 ** 10 + 50)

    def test_cartera_causal(self):
        from copilot.cartera import cartera
        m = self._mangas()
        fechas = [date(2020, 1, 1) + timedelta(days=i) for i in range(300)]
        base, _ = cartera(fechas, m)
        t = 200
        alt = {k: [([*rr[:t + 1], *[v * 5 + 0.03 for v in rr[t + 1:]]], xx) for rr, xx in vs] for k, vs in m.items()}
        otra, _ = cartera(fechas, alt)
        self.assertEqual(base.equity[: t + 1], otra.equity[: t + 1])
        self.assertNotEqual(base.equity[-1], otra.equity[-1])


class TestRiesgo(unittest.TestCase):
    def test_dimensionar(self):
        from copilot.riesgo import dimensionar
        siempre = lambda h, pos: 1.0
        f = dimensionar(siempre, lambda h: 90.0, 0.02)       # salida a un 10 % -> 2 % / 10 % = 20 %
        h = velas_fijas([100, 100])
        self.assertAlmostEqual(f(h, 0), 0.2)
        self.assertEqual(f(h, 0.2), 0.2)                       # se mantiene hasta salir
        self.assertEqual(dimensionar(siempre, lambda h: 99.5, 0.02)(h, 0), 1.0)   # tope 100 %
        self.assertEqual(dimensionar(siempre, lambda h: 101, 0.02)(h, 0), 0.0)    # nivel incoherente: no entra
        self.assertEqual(dimensionar(lambda h, p: 0.0, lambda h: 90, 0.02)(h, 0.2), 0.0)

    def test_escalar_y_ruina(self):
        from copilot.riesgo import escalar
        v = velas_fijas([100, 100, 100, 100])
        v[2] = v[2]._replace(low=45)                           # caída intradía del 55 %
        c = backtest(v, estrategias.buy_hold, SIN_COSTES)
        c.senales = [0.0] + [1.0] * 3
        _, ruina1 = escalar(c, v, 1.0)
        r2, ruina2 = escalar(c, v, 2.0)
        self.assertFalse(ruina1)
        self.assertTrue(ruina2)
        self.assertEqual(r2.equity[-1], 0.0)

    def test_vol_objetivo_no_apalanca(self):
        from copilot.riesgo import vol_objetivo
        v = velas_aleatorias(200)
        c = backtest(v, estrategias.buy_hold, SIN_COSTES)
        c.senales = [0.0] + [1.0] * 199
        r = vol_objetivo(c, 0.30)
        self.assertTrue(all(0 <= x <= 1 for x in r.senales))
        self.assertLess(max(r.senales[100:]), 1.0)             # vol ~76 % > 30 %: reduce exposición

    def test_operaciones(self):
        from copilot.riesgo import operaciones
        alterna = lambda h, pos: 1.0 if len(h) == 1 else 0.0
        r = backtest(velas_fijas([100, 100, 110, 110]), alterna, SIN_COSTES)
        self.assertEqual(len(operaciones(r)), 1)


class TestVigilancia(unittest.TestCase):
    def test_problemas_datos(self):
        from datetime import datetime, timezone
        from copilot.vigilancia import problemas_datos
        v = velas_aleatorias(450)
        self.assertEqual(problemas_datos(v), [])
        self.assertTrue(problemas_datos(v[:100]))                                   # poca historia
        hueco = v[:-1] + [v[-1]._replace(fecha=v[-1].fecha + timedelta(days=2))]
        self.assertTrue(any("falta" in x for x in problemas_datos(hueco)))
        self.assertTrue(any("duplicada" in x for x in problemas_datos(v + [v[-1]])))
        salto = v[:-1] + [v[-1]._replace(open=v[-2].close * 1.2, high=v[-2].close * 1.3)]
        self.assertTrue(any("apertura" in x for x in problemas_datos(salto)))
        cierre = datetime(v[-1].fecha.year, v[-1].fecha.month, v[-1].fecha.day, tzinfo=timezone.utc) + timedelta(days=1)
        self.assertEqual(problemas_datos(v, cierre + timedelta(hours=2)), [])
        self.assertTrue(any("desfasados" in x for x in problemas_datos(v, cierre + timedelta(hours=30))))

    def test_mediana_azar(self):
        from copilot.vigilancia import mediana_azar
        la = [0.0] + [0.01 * i for i in range(1, 400)]                              # sube 1 % (log) cada día
        m = mediana_azar(la, 0, 365, 100, 3, 0.0, semilla=1)
        self.assertAlmostEqual(m, exp(1.0) - 1, places=9)                           # 100 días siempre suman 1,0
        self.assertLess(mediana_azar(la, 0, 365, 100, 3, 0.01, semilla=1), m)       # los costes restan
        self.assertEqual(mediana_azar(la, 0, 365, 365, 1, 0.0, semilla=1), exp(3.65) - 1)

    def test_vigilancia_causal_y_suspende(self):
        from copilot import vigilancia as vg
        v = velas_aleatorias(900, semilla=5)
        ref = vg.referencia(v[:600])
        a = vg.vigilar(v, ref, desde=600, hasta=750)
        alterado = v[:751] + [x._replace(close=x.close * 0.3, low=x.low * 0.3) for x in v[751:]]
        b = vg.vigilar(alterado, ref, desde=600, hasta=750)
        self.assertEqual(a["eventos"], b["eventos"])                                 # el futuro no cambia el pasado
        self.assertEqual(a["diario"], b["diario"])
        for d in a["diario"]:
            for k, emite in d["emite_senales"].items():
                if emite:
                    self.assertEqual(d["estados"][k], "ACTIVA")

    def test_registrar_solo_anade(self):
        import tempfile
        from pathlib import Path
        from copilot import vigilancia as vg
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "v.jsonl"
            vg.registrar({"eventos": [{"tipo": "alerta", "fecha": "2020-01-01"}],
                          "diario": [{"fecha": "2020-01-01", "estados": {}}]}, ruta)
            self.assertEqual([e["datos"]["tipo"] for e in registro.leer(ruta)], ["alerta", "estado_diario"])


class TestVigilanciaV2(unittest.TestCase):
    def test_volumen_cero_solo_en_v2(self):
        from copilot.vigilancia import problemas_datos
        v = velas_aleatorias(450)
        parado = v[:-1] + [v[-1]._replace(volumen=0.0)]
        self.assertTrue(any("volumen 0" in x for x in problemas_datos(parado)))
        self.assertEqual(problemas_datos(parado, version="v1"), [])

    def test_v1_reproduce_el_resultado_registrado(self):
        from datetime import date
        from copilot import robustez, train, vigilancia as vg
        from copilot.motor import cargar_velas
        ref = vg.referencia(cargar_velas(train.FICHERO))
        v = cargar_velas(robustez.FICHERO)
        desde = next(i for i, x in enumerate(v) if x.fecha >= date(2013, 1, 1))
        r = vg.vigilar(v, ref, desde, version="v1")
        sus = [(e["fecha"], e["estrategia"]) for e in r["eventos"] if e["tipo"] == "suspension"]
        self.assertEqual(sus, [("2013-01-01", "T1 sma_n=100"), ("2013-01-02", "B1 N=20,M=10"),
                               ("2013-04-11", "B1 N=55,M=20"), ("2013-04-11", "C1 al 25 %")])
        r2 = vg.vigilar(v, ref, desde, version="v2")
        for k, e in r2["estados"].items():          # solo se reactivan las suspensiones por azar
            for s in e["historial"]:
                if s["hasta"] is not None:
                    self.assertIn("aleatorio", s["motivo"])
