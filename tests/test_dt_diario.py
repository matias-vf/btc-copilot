import unittest
from datetime import date, timedelta

try:
    import numpy as np
    from copilot import dt_diario as dd
except ImportError:  # numpy solo está en el PC (D67)
    np = None


@unittest.skipIf(np is None, "numpy no instalado")
class TestDTDiario(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(2)
        c = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, (4, 80)), axis=1))
        o = c * np.exp(rng.normal(0, 0.005, c.shape))
        self.A = np.stack([o, np.fmax(o, c) * 1.01, np.fmin(o, c) * 0.99, c, rng.uniform(1e6, 2e6, c.shape)], axis=2)
        d0 = date(2001, 1, 1)
        self.dias = [d0 + timedelta(days=i) for i in range(80)]

    def test_sin_mirar_el_futuro(self):
        F1 = dd.rasgos(self.A, self.dias)
        B = self.A.copy()
        B[:, 60, 1:4] *= 1.3  # máximo, mínimo y cierre de hoy: desconocidos a la apertura
        B[:, 61:, :] *= 0.5
        F2 = dd.rasgos(B, self.dias)
        for f, ps in dd.FAMILIAS.items():
            np.testing.assert_array_equal(dd.senal(F1, f, ps[0])[:, :61], dd.senal(F2, f, ps[0])[:, :61], err_msg=f)

    def test_stop_cuenta_antes_que_objetivo(self):
        F = dd.rasgos(self.A, self.dias)
        F["H"][:], F["L"][:], F["C"][:] = F["O"] * 1.1, F["O"] * 0.9, F["O"] * 1.05
        op = dd.operaciones(F, ("DIA_SEMANA", 0, "seguir", "compras", "-", "-", "-", 1.0, 1.0))
        self.assertTrue(len(op["d"]) > 0)
        np.testing.assert_allclose(op["bruto"], -op["R"])  # toca los dos: cuenta el stop
        op = dd.operaciones(F, ("DIA_SEMANA", 0, "seguir", "compras", "-", "-", "-", 0.0, 0.0))
        np.testing.assert_allclose(op["bruto"], 0.05)  # sin stop ni objetivo: al cierre


if __name__ == "__main__":
    unittest.main()
