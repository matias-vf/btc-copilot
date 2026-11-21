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
        ideas = [e["datos"] for e in registro.leer(registro.IDEAS) if e["datos"]["estado"] != "descartada"]
        total = 0
        for idea in ideas:
            for var in idea["configuraciones_permitidas"]:
                estrategias.crear(idea["id"], var)
                total += 1
        self.assertEqual(total, 31)


class TestAnticipacion(unittest.TestCase):
    def test_todas_las_variantes_son_causales(self):
        v = velas_aleatorias(420)
        ideas = [e["datos"] for e in registro.leer(registro.IDEAS) if e["datos"]["estado"] != "descartada"]
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
