import unittest
from datetime import datetime, timedelta, timezone

from copilot import paperbot as p
from copilot.btc_intradia import H

T0 = datetime(2024, 1, 1, 20, tzinfo=timezone.utc)


def v(ohlc):
    return [H(T0 + timedelta(hours=i), *x) for i, x in enumerate(ohlc)]


class TestRun(unittest.TestCase):
    def test_corto_objetivo_y_costes(self):
        b = v([(100, 100, 100, 100), (100, 100, 100, 100), (99, 99, 90, 92), (92, 92, 92, 92)])
        sig = [(-1, 105.0, 95.0), None, None, None]
        t = p._run(b, sig)
        self.assertEqual(len(t), 1)
        self.assertAlmostEqual(t[0]["ret"], 0.05 - 2 * p.LADO)  # objetivo 95 desde 100
        self.assertAlmostEqual(t[0]["r"], (0.05 - 2 * p.LADO) / 0.05)

    def test_funding_cortos_cobran(self):
        b = v([(100, 100, 100, 100)] * 6)
        sig = [(-1, 105.0, 95.0)] + [None] * 5
        fu = {b[4].t: 0.001}
        t = p._run(b, sig, fu=fu, perp_desde=b[0].t.date())
        self.assertAlmostEqual(t[0]["ret"], -2 * p.LADO + 0.001)

    def test_salida_fin_de_dia(self):
        b = v([(100, 100, 100, 100)] * 6)  # 20:00 .. 01:00
        t = p._run(b, [(-1, 105.0, 95.0)] + [None] * 5, dia=True)
        self.assertEqual(t[0]["horas"], 3)  # entra a las 21:00, sale al cierre de las 23:00

    def test_causal(self):
        import random
        random.seed(1)
        x, b = 100.0, []
        for _ in range(1400):
            x *= 1 + random.uniform(-0.01, 0.0095)
            b.append((x, x * 1.004, x * 0.996, x))
        a = p.breakdown_short(v(b), 12, 1.5)
        c = p.breakdown_short(v(b[:-50] + [(1, 2, 0.5, 1)] * 50), 12, 1.5)
        self.assertEqual(a[:1350], c[:1350])
        self.assertTrue(any(a))


if __name__ == "__main__":
    unittest.main()
