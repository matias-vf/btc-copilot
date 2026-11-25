import unittest

try:
    import numpy as np
    from copilot import dt100k as dt
except ImportError:  # numpy solo está en el PC (D65)
    np = None


def F_simple(velas, gap=0.02):
    """Una acción, 30 días; solo el último día tiene datos que importan. velas = 7 tuplas (O, H, L, C)."""
    D = 30
    A = np.full((1, D, 7), 100.0)
    O, H, L, C = A.copy(), A.copy(), A.copy(), A.copy()
    for j, (o, h, l, c) in enumerate(velas):
        O[0, -1, j], H[0, -1, j], L[0, -1, j], C[0, -1, j] = o, h, l, c
    PC = np.full((1, D), 100.0)
    PC[0, -1] = 100.0 / (1 + gap)
    uno = np.ones((1, D))
    return {"O": O, "H": H, "L": L, "C": C, "PC": PC, "atrp": uno * 0.02, "ATR": uno * 2.0,
            "RVOL": np.ones((1, D, 7)), "sO": np.full((D, 7), 100.0), "sC": np.full((D, 7), 101.0),
            "sPC": np.full(D, 100.0), "terc": uno}


@unittest.skipIf(np is None, "numpy no instalado")
class TestDT100K(unittest.TestCase):
    def test_stop_antes_que_objetivo_y_hueco(self):
        # hueco de +2 % (1 ATR): seguir, compra en la apertura a 100; stop 0,5 ATR = 1 % -> 99; objetivo 2R -> 102
        velas = [(100, 101, 99.5, 100.5), (100.5, 102.5, 98.5, 101)] + [(101, 101, 101, 101)] * 5
        r = ("HUECO", -1, 0.5, "seguir", "compras", "-", "-", "-", 0.5, 2.0, 0)
        op = dt.operaciones(F_simple(velas), r)
        self.assertEqual(len(op["d"]), 1)
        # la vela 2 toca stop y objetivo: cuenta el stop
        self.assertAlmostEqual(op["bruto"][0], -0.01)

    def test_objetivo_y_salida_al_cierre(self):
        velas = [(100, 100.8, 99.5, 100.5), (100.5, 102.4, 100.2, 102)] + [(102, 102, 102, 102)] * 5
        r = ("HUECO", -1, 0.5, "seguir", "compras", "-", "-", "-", 0.5, 2.0, 0)
        self.assertAlmostEqual(dt.operaciones(F_simple(velas), r)["bruto"][0], 0.02)
        r_sin = ("HUECO", -1, 0.5, "seguir", "compras", "-", "-", "-", 0.5, 0.0, 0)
        self.assertAlmostEqual(dt.operaciones(F_simple(velas), r_sin)["bruto"][0], 0.02)  # cierre 102

    def test_contraria_y_corto(self):
        velas = [(100, 100.4, 99, 99.2)] + [(99.2, 99.3, 98, 98)] * 6
        r = ("HUECO", -1, 0.5, "contraria", "cortos", "-", "-", "-", 1.0, 0.0, 0)
        op = dt.operaciones(F_simple(velas), r)
        self.assertAlmostEqual(op["bruto"][0], 0.02)  # corto a 100, cierre 98
        self.assertEqual(len(dt.operaciones(F_simple(velas), r[:4] + ("compras",) + r[5:])["d"]), 0)

    def test_sin_mirar_el_futuro(self):
        rng = np.random.default_rng(1)
        A = 100 * np.exp(np.cumsum(rng.normal(0, 0.003, (4, 60, 7)), axis=(1)))
        A = np.stack([A, A * 1.004, A * 0.996, A, rng.uniform(1e5, 2e5, A.shape)], axis=3)
        for fam, (entradas, params) in dt.FAMILIAS.items():
            for e in entradas:
                s1 = dt.senal(dt.rasgos(A), fam, e, params[0])
                B = A.copy()
                B[:, 50, e + 1:, :] *= 1.5  # cambia el resto del día 50 tras la entrada
                if e < 0:
                    B[:, 50, 0, 0] = A[:, 50, 0, 0]  # la apertura sí se conoce al entrar
                B[:, 51:, :, :] *= 0.5  # y todos los días siguientes
                s2 = dt.senal(dt.rasgos(B), fam, e, params[0])
                np.testing.assert_array_equal(s1[:, :51], s2[:, :51], err_msg=f"{fam} e={e}")

    def test_coste_y_sorteo(self):
        self.assertAlmostEqual(float(dt.coste(np.array([100.0]))[0]), 0.35 / 5000 + 0.0002)
        self.assertAlmostEqual(float(dt.coste(np.array([20.0]))[0]), 0.0035 * 250 / 5000 + 0.0002)
        self.assertEqual(dt.elegir()[:3], dt.elegir()[:3])
        self.assertGreater(len(dt.todas()), dt.N_REGLAS)


if __name__ == "__main__":
    unittest.main()
