import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from copilot import box, noticias, registro

T0 = datetime(2025, 3, 3, tzinfo=timezone.utc)  # BTC: días UTC


def dias(*dias_ohlc):
    """Cada día: lista de (o, h, l, c) por hora desde las 00:00 UTC."""
    out = []
    for d, velas in enumerate(dias_ohlc):
        out += [box.V(T0 + timedelta(days=d, hours=h), *x) for h, x in enumerate(velas)]
    return out


AYER = [(100, 110, 100, 105)] * 24  # caja: suelo 100, techo 110, R = 10


class TestSenales(unittest.TestCase):
    def test_zonas(self):
        v = dias(AYER, [(102, 103, 102, 102), (105, 105, 105, 105), (109, 109, 109, 109)])
        s = box.senales(v, "B1")
        self.assertTrue(all(x is None for x in s[:24]))  # el primer día no tiene caja
        self.assertEqual(s[24], (1, 99.0, 105.0))       # 102 está en el 35 % inferior
        self.assertIsNone(s[25])                         # 105: zona media
        self.assertEqual(s[26], (-1, 111.0, 105.0))      # 109: 35 % superior
        self.assertEqual(box.senales(v, "B2")[24], (1, 99.0, 110.0))

    def test_fuera_de_la_caja_no(self):
        v = dias(AYER, [(98, 99, 97, 98)])
        self.assertIsNone(box.senales(v, "B1")[24])


class TestSimular(unittest.TestCase):
    def test_objetivo_y_coste(self):
        v = dias(AYER, [(102, 103, 102, 102), (102, 106, 102, 106)] + [(106, 106, 106, 106)] * 22)
        t = box.simular("BTC", v, box.senales(v, "B1"), 0.001)
        self.assertEqual(t[0]["motivo"], "objetivo")
        self.assertAlmostEqual(t[0]["ret"], 105 / 102 - 1 - 0.002)

    def test_fin_del_dia_y_abierta(self):
        v = dias(AYER, [(102, 103, 102, 102)] + [(103, 104, 102, 103)] * 23)
        t = box.simular("BTC", v, box.senales(v, "B2"), 0.0)
        self.assertEqual(t[0]["motivo"], "fin del día")
        abierta = box.simular("BTC", v[:30], box.senales(v[:30], "B2"), 0.0)
        self.assertTrue(abierta[-1]["abierta"])

    def test_causal(self):
        v = dias(AYER, [(102, 103, 102, 102)] * 24, [(105, 105, 105, 105)] * 24)
        w = v[:-24] + [box.V(x.t, 1, 500, 0.5, 1) for x in v[-24:]]
        self.assertEqual(box.senales(v, "B1")[:48], box.senales(w, "B1")[:48])


class TestRegistros(unittest.TestCase):
    def test_tick_no_duplica_y_noticias(self):
        with tempfile.TemporaryDirectory() as d:
            v = dias(AYER, [(102, 103, 102, 102), (102, 106, 102, 106)] + [(106, 106, 106, 106)] * 22)
            with mock.patch.object(box, "PAPER", Path(d) / "box.jsonl"), \
                    mock.patch.object(box, "INICIO_PAPER", v[24].t.date()), \
                    mock.patch.object(box, "_velas_btc", lambda ahora: (v, {}, "prueba")):
                self.assertEqual(box.tick(mercados=("BTC",)), 4)  # B1 y B2: abierta + cerrada
                self.assertEqual(box.tick(mercados=("BTC",)), 0)
                self.assertEqual(box.estado()[("BTC", "B1")]["cerradas"], 1)
            rss = b"<rss><channel><item><title>Hola</title><guid>g1</guid><pubDate>Mon, 23 Nov 2026 10:00:00 GMT</pubDate></item></channel></rss>"
            with mock.patch.object(noticias, "REGISTRO", Path(d) / "n.jsonl"):
                self.assertEqual(noticias.revisar(lambda s: rss), 3)
                self.assertEqual(noticias.revisar(lambda s: rss), 0)
                self.assertEqual(len(registro.leer(Path(d) / "n.jsonl")), 3)


if __name__ == "__main__":
    unittest.main()
