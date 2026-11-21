import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from copilot import copiloto as cp, paper, registro, train
from copilot.motor import cargar_velas


class TestPaper(unittest.TestCase):
    def test_compra_venta_costes_y_limite(self):
        c = paper.Cuenta()
        e = paper.simular_ejecucion(c, 0.9, 100.0, "2022-01-01")       # pide 90 %: se recorta al 25 %
        self.assertAlmostEqual(e["exposicion_objetivo"], 0.25)
        c.aplicar(e)
        self.assertAlmostEqual(c.efectivo, 75.0)
        self.assertAlmostEqual(e["precio_simulado"], 100 * 1.0006)     # medio spread + slippage
        self.assertLess(c.exposicion(100.0), 0.25)
        v = paper.simular_ejecucion(c, 0.0, 100.0, "2022-01-02")
        c.aplicar(v)
        self.assertEqual(c.btc, 0.0)
        self.assertAlmostEqual(c.valor(100.0), 100 - 25 * 0.0016 - 25 * 0.0016, places=2)
        self.assertEqual(len(c.operaciones_cerradas), 1)
        self.assertLess(c.operaciones_cerradas[0]["resultado_usdt"], 0)

    def test_parada_manual(self):
        ent = [{"tipo": "inicio"}, {"tipo": "parada_manual", "fecha": "x", "motivo": "m"}]
        self.assertIsNotNone(paper.parada_manual_activa(ent))
        self.assertIsNone(paper.parada_manual_activa(ent + [{"tipo": "reanudacion"}]))


class TestCopiloto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.TemporaryDirectory()
        cls.carpeta = Path(cls.dir.name) / "r"
        cp.repeticion(date(2020, 10, 1), date(2020, 11, 15), cls.carpeta)
        cls.cmp = cp.comparar(cls.carpeta)
        cls.sen = [e["datos"] for e in registro.leer(cls.carpeta / "senales.jsonl")]
        cls.pap = [e["datos"] for e in registro.leer(cls.carpeta / "paper.jsonl")]

    @classmethod
    def tearDownClass(cls):
        cls.dir.cleanup()

    def test_una_senal_por_dia_y_campos(self):
        s = [x for x in self.sen if x["tipo"] == "senal"]
        self.assertEqual(len(s), 46)
        for x in s:
            self.assertIn(x["decision"], ("COMPRA", "VENTA", "MANTENER", "NO OPERAR"))
            for campo in ("activo", "par", "temporalidad", "precio_referencia", "justificacion", "estado_validacion",
                          "componentes", "valida_hasta_utc", "sesion"):
                self.assertIn(campo, x)
            self.assertLessEqual(x["exposicion_objetivo"], paper.LIMITE_EXPOSICION + 1e-12)

    def test_ejecucion_en_la_apertura_siguiente(self):
        velas = {v.fecha.isoformat(): v for v in cargar_velas(train.FICHERO)}
        s = {x["vela"]: x for x in self.sen if x["tipo"] == "senal"}
        ejec = [x for x in self.pap if x["tipo"] == "ejecucion"]
        self.assertTrue(ejec)
        for e in ejec:
            ayer = (date.fromisoformat(e["fecha"]) - timedelta(days=1)).isoformat()
            self.assertIn("orden", s[ayer])
            self.assertEqual(e["precio_teorico"], velas[e["fecha"]].open)

    def test_paper_coincide_con_su_registro(self):
        c, _ = paper.cargar(self.carpeta / "paper.jsonl")
        v = cargar_velas(train.FICHERO)
        ult = next(x for x in v if x.fecha.isoformat() == c.valoraciones[-1]["fecha"])
        self.assertAlmostEqual(c.valor(ult.close), c.valoraciones[-1]["valor"])

    def test_repeticion_no_se_reescribe(self):
        with self.assertRaises(SystemExit):
            cp.repeticion(date(2020, 10, 1), date(2020, 10, 5), self.carpeta)

    def test_parada_cierra_todo(self):
        with tempfile.TemporaryDirectory() as d:
            rutas = {k: Path(d) / f"{k}.jsonl" for k in ("senales", "paper", "vigilancia")}
            velas = cargar_velas(train.FICHERO)
            i = next(k for k, x in enumerate(velas) if x.fecha == date(2020, 11, 10))
            ahora = lambda t: datetime(velas[t].fecha.year, velas[t].fecha.month, velas[t].fecha.day,
                                       tzinfo=timezone.utc) + timedelta(days=1, minutes=5)
            s1 = cp.ciclo(velas[: i + 1], rutas, ahora(i), solo_validadas=False)
            self.assertGreater(s1["exposicion_objetivo"], 0)              # noviembre 2020: tendencia alcista
            registro.anadir(rutas["paper"], {"tipo": "parada_manual", "fecha": "2020-11-10", "motivo": "prueba"})
            s2 = cp.ciclo(velas[: i + 2], rutas, ahora(i + 1), solo_validadas=False)
            self.assertEqual(s2["decision"], "VENTA")
            self.assertEqual(s2["exposicion_objetivo"], 0.0)
            self.assertTrue(any("PARADA" in a for a in s2["avisos"]))

    def test_sin_validadas_no_opera(self):
        velas = cargar_velas(train.FICHERO)
        i = next(k for k, x in enumerate(velas) if x.fecha == date(2020, 11, 10))
        ahora = datetime(2020, 11, 11, 0, 5, tzinfo=timezone.utc)
        s = cp.decidir(velas[: i + 1], {}, 0.0, None, [], None, ahora)
        self.assertEqual(s["decision"], "NO OPERAR")
        s = cp.decidir(velas[: i + 1], {}, 0.2, None, [], None, ahora)
        self.assertEqual((s["decision"], s["orden"]["exposicion_objetivo"]), ("VENTA", 0.0))

    def test_lectura_visual(self):
        s = {"precio_referencia": 20000.0}
        self.assertFalse(cp.lectura_visual({"activo": "ETH/USDT", "temporalidad": "1d"}, s)["usable"])
        self.assertFalse(cp.lectura_visual({"activo": "BTCUSDT"}, s)["usable"])
        self.assertFalse(cp.lectura_visual({"activo": "BTCUSDT", "temporalidad": "1d", "precio_visible": 25000}, s)["usable"])
        r = cp.lectura_visual({"activo": "BTCUSDT", "temporalidad": "4h", "precio_visible": 20100}, s)
        self.assertTrue(r["usable"])
        self.assertTrue(any("contexto" in n for n in r["notas"]))
        self.assertTrue(r["efecto_en_la_decision"].startswith("ninguno"))

    def test_sesiones_nueva_york(self):
        invierno = cp.sesion(datetime(2022, 1, 10, 14, 0, tzinfo=timezone.utc))   # 09:00 EST
        self.assertEqual(set(invierno["sesiones_activas"]), {"Europa", "EE. UU."})
        verano = cp.sesion(datetime(2022, 7, 10, 2, 0, tzinfo=timezone.utc))      # 22:00 EDT
        self.assertEqual(verano["sesiones_activas"], ["Asia"])
        self.assertTrue(cp.sesion(datetime(2022, 7, 9, 12, 0, tzinfo=timezone.utc))["fin_de_semana"])


if __name__ == "__main__":
    unittest.main()
