import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from copilot import retroceso as rt
from copilot.intradia import Barra

T0 = datetime(2026, 10, 5, 9, 30, tzinfo=ZoneInfo("America/New_York"))
SIN = lambda p: 0.0  # sin costes


def dia(velas):
    return [Barra(T0 + timedelta(minutes=5 * i), *v, 1000) for i, v in enumerate(velas)]


RANGO = [(100, 102, 99, 101), (101, 102, 100, 101), (101, 101, 98, 100)]  # alto 102, bajo 98, mitad 100


class TestVideo(unittest.TestCase):
    def test_retroceso_y_objetivo(self):
        b = dia(RANGO + [(101, 104, 101, 103.5),    # ruptura: cierra sobre 102
                         (103.5, 104, 101.8, 102.5),  # retroceso: toca 102 -> entra a 102
                         (102.5, 106.5, 102.4, 106)]  # objetivo 102 + 2 * 2 = 106
                  + [(106, 106, 106, 106)] * 70)
        o = rt.operar_dia(b, SIN)
        self.assertEqual((o["lado"], o["entrada"], o["salida"], o["motivo"]), (1, 102, 106, "objetivo"))
        self.assertAlmostEqual(o["bruto"] / o["riesgo"], 2.0)

    def test_sin_retroceso_no_opera(self):
        b = dia(RANGO + [(101, 104, 101, 103.5)] + [(104, 106, 103, 105)] * 70)
        self.assertIsNone(rt.operar_dia(b, SIN))

    def test_corto_stop(self):
        b = dia(RANGO + [(99, 99, 96, 97),       # ruptura bajista
                         (97, 98.2, 96.5, 98),   # retroceso a 98 -> corto a 98
                         (98, 100.5, 97.5, 100.2)]  # toca la mitad (100) -> stop
                  + [(100, 100, 100, 100)] * 70)
        o = rt.operar_dia(b, SIN)
        self.assertEqual((o["lado"], o["entrada"], o["salida"], o["motivo"]), (-1, 98, 100, "stop"))

    def test_ruptura_fallida(self):
        b = dia(RANGO + [(101, 104, 101, 103.5), (103, 103.5, 97, 97.5)] + [(98, 99, 97, 98)] * 70)
        o = rt.operar_dia(b, SIN)
        # la vela que vuelve a 102 también cierra bajo el rango: entra en el borde y salta el stop en la misma vela
        self.assertEqual(o["motivo"], "stop")


if __name__ == "__main__":
    unittest.main()
