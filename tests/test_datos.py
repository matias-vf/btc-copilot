import tempfile
import unittest
from datetime import date
from pathlib import Path

from copilot import datos


class TestDatos(unittest.TestCase):
    def setUp(self):  # la lógica del bloqueo se sigue probando aunque TEST ya esté desbloqueado (D20)
        self._antes, datos.TEST_DESBLOQUEADO = datos.TEST_DESBLOQUEADO, False

    def tearDown(self):
        datos.TEST_DESBLOQUEADO = self._antes

    def test_bloquea_test(self):
        for fn in (datos.descargar_binance, datos.descargar_bitstamp):
            with self.assertRaises(datos.DatosTestBloqueados):
                fn(date(2022, 12, 1), date(2023, 1, 1))  # falla antes de tocar la red

    def test_guardar_y_cargar_rechazan_test(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "x.csv"
            with self.assertRaises(datos.DatosTestBloqueados):
                datos.guardar([["2023-01-01", 1, 1, 1, 1, 1]], ruta)
            ruta.write_text("fecha_utc,open,high,low,close,volumen_btc\n2023-01-02,1,1,1,1,1\n")
            with self.assertRaises(datos.DatosTestBloqueados):
                datos.cargar(ruta)

    def test_validar(self):
        filas = [
            ["2020-01-01", 10, 12, 9, 11, 5],
            ["2020-01-02", 11, 10, 9, 11, 0],  # high < close: incoherente, volumen 0
            ["2020-01-02", 11, 12, 9, 11, 5],  # duplicado
            ["2020-01-04", 11, 12, 9, 11, 5],  # falta el 03
        ]
        v = datos.validar(filas)
        self.assertEqual(v["duplicados"], ["2020-01-02"])
        self.assertEqual(v["huecos"], ["2020-01-03"])
        self.assertEqual(v["ohlc_incoherentes"], ["2020-01-02"])
        self.assertEqual(v["dias_volumen_cero"], ["2020-01-02"])

    def test_ficheros_reales_sin_test(self):
        for ruta in datos.DATOS.glob("*.csv"):
            if "_test" in ruta.name or ruta.name.startswith("gld_"):
                continue  # el oro tiene calendario de bolsa: lo comprueba validar_bolsa
            filas = datos.cargar(ruta)
            v = datos.validar(filas)
            self.assertEqual(v["duplicados"], [], ruta.name)
            self.assertEqual(v["huecos"], [], ruta.name)


if __name__ == "__main__":
    unittest.main()


class TestDatosOro(unittest.TestCase):
    def test_bloquea_test_del_oro(self):
        antes, datos.TEST_ORO_DESBLOQUEADO = datos.TEST_ORO_DESBLOQUEADO, False  # la lógica se sigue probando (D43)
        self.addCleanup(setattr, datos, "TEST_ORO_DESBLOQUEADO", antes)
        with self.assertRaises(datos.DatosTestBloqueados):
            datos.descargar_yahoo("GLD", date(2018, 12, 1), date(2019, 1, 2))  # falla antes de tocar la red
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(datos.DatosTestBloqueados):
                datos.guardar_oro([["2019-01-02", 1, 1, 1, 1, 1]], Path(d) / "x.csv")

    def test_validar_bolsa(self):
        filas = [["2018-01-05", 1, 2, 1, 1, 5], ["2018-01-08", 1, 2, 1, 1, 5], ["2018-01-15", 1, 2, 1, 1, 5]]
        v = datos.validar_bolsa(filas)
        self.assertEqual(v["huecos"], [])
        self.assertEqual(v["huecos_largos"], ["2018-01-08 -> 2018-01-15"])
        self.assertEqual(v["velas_en_fin_de_semana"], [])
