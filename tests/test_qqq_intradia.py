import unittest
from datetime import datetime, timedelta

from copilot import qqq_intradia as q
from copilot.intradia import Barra


def dia(precios, d=datetime(2025, 3, 3, 9, 30)):
    """Velas horarias con open=close anterior; precios = cierres."""
    out, prev = [], precios[0]
    for i, c in enumerate(precios):
        out.append(Barra(d + timedelta(hours=i), prev, max(prev, c), min(prev, c), c, 1000))
        prev = c
    return out


class TestCostes(unittest.TestCase):
    def test_ibkr(self):
        # 25.000 USD a 500 USD = 50 acciones -> 0,175 USD -> mínimo 0,35 USD
        self.assertAlmostEqual(q.coste_lado(500), 0.35 / 25_000 + 0.0002)
        # a 10 USD = 2500 acciones -> 8,75 USD
        self.assertAlmostEqual(q.coste_lado(10), 8.75 / 25_000 + 0.0002)


class TestSimulador(unittest.TestCase):
    def test_largo_y_corto(self):
        b = dia([100, 100, 110, 110])
        r, n = q.simular_dia(b, [1, 1, 0, 0])  # compra en open de t1 (100), vende en open de t3 (110)
        c = q.coste_lado(100), q.coste_lado(110)
        self.assertAlmostEqual(r, (1 - c[0]) * 1.1 * (1 - c[1]) - 1)
        self.assertEqual(n, 2)
        r2, _ = q.simular_dia(b, [-1, -1, 0, 0])
        self.assertAlmostEqual(r2, (1 - c[0]) * 0.9 * (1 - c[1]) - 1)

    def test_fuera_al_cierre(self):
        r, n = q.simular_dia(dia([100, 100, 105, 120]), [1, 1, 1, 1])
        self.assertEqual(n, 2)  # entra en t1 y sale al cierre de la última vela
        self.assertAlmostEqual(r, (1 - q.coste_lado(100)) * 1.2 * (1 - q.coste_lado(120)) - 1)

    def test_stop(self):
        b = dia([100, 100, 90, 95])
        r, n = q.simular_dia(b, [1, 1, 1, 0], lambda t, lado, e: (98.0, None))
        self.assertEqual(n, 2)
        self.assertAlmostEqual(r, (1 - q.coste_lado(100)) * 0.98 * (1 - q.coste_lado(98)) - 1)

    def test_sin_senal(self):
        self.assertEqual(q.simular_dia(dia([100, 101, 102]), [0, 0, 0]), (0.0, 0))


class TestUniverso(unittest.TestCase):
    def test_40(self):
        u = q.universo()
        self.assertEqual(len(u), 40)
        self.assertEqual(len({(f, q.texto(p)) for f, _, p in u}), 40)

    def test_causal(self):
        # cambiar el último día no cambia los resultados de los días anteriores
        dias = [dia([100 + (i * 7 + k * 3) % 11 for k in range(7)], datetime(2025, 1, 1, 9, 30) + timedelta(days=i))
                for i in range(40)]
        barras = [x for d in dias for x in d]
        otro = barras[:-7] + dia([150, 90, 160, 80, 170, 70, 180], dias[-1][0].hora)
        for fam, _, p in q.universo():
            a, b = q.evaluar_regla(fam, p, barras), q.evaluar_regla(fam, p, otro)
            for d in list(a)[:-1]:
                self.assertEqual(a[d], b[d], (fam, p, d))


if __name__ == "__main__":
    unittest.main()
