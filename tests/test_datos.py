import tempfile
import unittest
from datetime import date
from pathlib import Path

from copilot import datos


class TestDatos(unittest.TestCase):
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
            filas = datos.cargar(ruta)
            v = datos.validar(filas)
            self.assertEqual(v["duplicados"], [], ruta.name)
            self.assertEqual(v["huecos"], [], ruta.name)


if __name__ == "__main__":
    unittest.main()
