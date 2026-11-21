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
            i = next(k for k, x in enumerate(velas) if x.fecha == date(2020, 11, 15))  # domingo: N1 decide
            ahora = lambda t: datetime(velas[t].fecha.year, velas[t].fecha.month, velas[t].fecha.day,
                                       tzinfo=timezone.utc) + timedelta(days=1, minutes=5)
            s1 = cp.ciclo(velas[: i + 1], rutas, ahora(i), solo_validadas=False)
            self.assertGreater(s1["exposicion_objetivo"], 0)              # noviembre 2020: tendencia alcista
            registro.anadir(rutas["paper"], {"tipo": "parada_manual", "fecha": "2020-11-15", "motivo": "prueba"})
            s2 = cp.ciclo(velas[: i + 2], rutas, ahora(i + 1), solo_validadas=False)
            self.assertEqual(s2["decision"], "VENTA")
            self.assertEqual(s2["exposicion_objetivo"], 0.0)
            self.assertTrue(any("PARADA" in a for a in s2["avisos"]))

    def test_sin_validadas_no_opera(self):
        antes, cp.VALIDADAS = cp.VALIDADAS, set()
        self.addCleanup(setattr, cp, "VALIDADAS", antes)
        velas = cargar_velas(train.FICHERO)
        i = next(k for k, x in enumerate(velas) if x.fecha == date(2020, 11, 10))
        ahora = datetime(2020, 11, 11, 0, 5, tzinfo=timezone.utc)
        s = cp.decidir(velas[: i + 1], {}, 0.0, None, [], None, ahora)
        self.assertEqual(s["decision"], "NO OPERAR")
        s = cp.decidir(velas[: i + 1], {}, 0.2, None, [], None, ahora)
        self.assertEqual((s["decision"], s["orden"]["exposicion_objetivo"]), ("VENTA", 0.0))

    def test_nivel_n1(self):
        velas = cargar_velas(train.FICHERO)
        i = next(k for k, x in enumerate(velas) if x.fecha == date(2020, 11, 11))       # miércoles
        h = velas[: i + 1]
        base = date(2020, 11, 15) - timedelta(days=28)                                 # domingo 15 menos 4 semanas
        self.assertEqual(cp.nivel_n1(h), next(x.close for x in h if x.fecha == base))
        self.assertEqual(cp.domingo_siguiente(date(2020, 11, 15)), date(2020, 11, 22))  # domingo -> el siguiente

    def test_poner_al_dia_recupera_dias(self):
        with tempfile.TemporaryDirectory() as d:
            rutas = {k: Path(d) / f"{k}.jsonl" for k in ("senales", "paper", "vigilancia")}
            velas = cargar_velas(train.FICHERO)
            i = next(k for k, x in enumerate(velas) if x.fecha == date(2020, 11, 15))
            cierre = lambda t: datetime(velas[t].fecha.year, velas[t].fecha.month, velas[t].fecha.day,
                                        tzinfo=timezone.utc) + timedelta(days=1, minutes=5)
            self.assertEqual(len(cp.poner_al_dia(rutas, velas[: i + 1], cierre(i))), 1)   # primera vez: solo hoy
            s = cp.poner_al_dia(rutas, velas[: i + 4], cierre(i + 3))                      # 3 días sin encender
            self.assertEqual([x["vela"] for x in s], [velas[i + k].fecha.isoformat() for k in (1, 2, 3)])
            self.assertEqual([x.get("recuperada_tarde", False) for x in s], [True, True, False])
            self.assertEqual(cp.poner_al_dia(rutas, velas[: i + 4], cierre(i + 3)), [])    # nada nuevo
            ejec = [e["datos"] for e in registro.leer(rutas["paper"]) if e["datos"]["tipo"] == "ejecucion"]
            self.assertEqual(ejec[0]["fecha"], velas[i + 1].fecha.isoformat())             # compra del domingo, lunes

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


class TestVigia(unittest.TestCase):
    def test_observar(self):
        from copilot import vigia
        velas = cargar_velas(train.FICHERO)
        h = [v for v in velas if v.fecha <= date(2020, 11, 17)]                 # hasta un martes
        ahora = datetime(2020, 11, 18, 12, 0, tzinfo=timezone.utc)            # miércoles
        nivel = next(v.close for v in h if v.fecha == date(2020, 11, 22) - timedelta(days=28))
        o = vigia.observar(h, {"precio": nivel * 1.10, "cambio_24h": 0.06}, ahora, 0.0)
        self.assertEqual(o["domingo_decision"], "2020-11-22")
        self.assertEqual(o["si_cerrase_asi"], "COMPRA (entraría)")
        self.assertTrue(any("Movimiento fuerte" in a for a in o["avisos"]))
        o = vigia.observar(h, {"precio": nivel * 0.99, "cambio_24h": 0.0}, ahora, 1.0)
        self.assertEqual(o["si_cerrase_asi"], "VENTA (saldría a liquidez)")
        self.assertTrue(any("del nivel de N1" in a for a in o["avisos"]))
        self.assertIn("no es una señal", o["nota"])
        domingo = vigia.observar(h + [h[-1]._replace(fecha=date(2020, 11, 18))], {"precio": nivel, "cambio_24h": 0},
                                 datetime(2020, 11, 22, 9, 0, tzinfo=timezone.utc), 0.0)
        self.assertEqual(domingo["domingo_decision"], "2020-11-22")              # en domingo, la decisión es hoy


class TestCopilotoOro(unittest.TestCase):
    def test_oro_en_proceso_aparte(self):
        import subprocess, sys
        codigo = r'''
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from copilot import copiloto as cp, oro, registro
cp.usar_oro()
v = oro.velas(oro.FICHEROS["TRAIN"])
i = next(k for k, x in enumerate(v) if x.fecha.isoformat() == "2018-11-30")   # viernes
d = Path(tempfile.mkdtemp())
rutas = {k: d / f"{k}.jsonl" for k in ("senales", "paper", "vigilancia")}
cierre = lambda t: datetime(v[t].fecha.year, v[t].fecha.month, v[t].fecha.day, 21, tzinfo=timezone.utc) + timedelta(hours=1)
cp.poner_al_dia(rutas, v[: i + 1], cierre(i))
s = cp.poner_al_dia(rutas, v[: i + 15], cierre(i + 14))
assert len(s) == 14, len(s)
assert all("Datos insuficientes" not in " ".join(x["justificacion"]) for x in s), [x["avisos"] for x in s]
assert all(x["activo"] == "ORO" and "GLD" in x["par"] for x in s)
assert max(x["exposicion_objetivo"] for x in s) <= 0.25
for e in [e["datos"] for e in registro.leer(rutas["paper"]) if e["datos"]["tipo"] == "ejecucion"]:
    r = e["precio_simulado"] / e["precio_teorico"]
    assert abs(r - (1.0005 if e["lado"] == "compra" else 0.9995)) < 1e-12, r
print("ORO OK")
'''
        r = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, encoding="utf-8",
                           cwd=str(Path(__file__).resolve().parents[1]))
        self.assertIn("ORO OK", r.stdout, r.stderr[-2000:])


class TestIntradia(unittest.TestCase):
    def _dia(self, precios):
        from copilot.intradia import NY, Barra
        h0 = datetime(2026, 11, 2, 9, 30, tzinfo=NY)
        return [Barra(h0 + timedelta(minutes=5 * i), o, hi, lo, c, 1.0) for i, (o, hi, lo, c) in enumerate(precios)]

    def test_reglas_orb(self):
        from copilot.intradia import eventos_del_dia
        bajista = self._dia([(100, 101, 99, 99.5), (99.5, 100, 99, 99.8)])
        self.assertEqual(eventos_del_dia(bajista), [])
        stop = self._dia([(100, 101, 99, 100.5), (100.6, 101, 100, 100.8), (100.8, 101, 98.5, 99)])
        ev = eventos_del_dia(stop)
        self.assertEqual((ev[0]["precio"], ev[1]["motivo"], ev[1]["precio"]), (100.6, "stop", 99))
        self.assertAlmostEqual(ev[0]["exposicion"], min(0.25, 0.01 / (1.6 / 100.6)))
        hueco = self._dia([(100, 101, 99, 100.5), (100.6, 101, 100, 100.8), (98, 98.5, 97, 98)])
        self.assertEqual(eventos_del_dia(hueco)[1]["precio"], 98)                    # abre por debajo del stop
        objetivo = self._dia([(100, 101, 99.9, 100.5), (100.6, 101, 100.5, 100.8), (100.8, 108, 100.7, 107)])
        self.assertEqual(eventos_del_dia(objetivo)[1]["motivo"], "objetivo")          # 100.6 + 10 x 0.7 = 107.6
        abierta = self._dia([(100, 101, 99, 100.5), (100.6, 101, 100, 100.8)])
        self.assertEqual(len(eventos_del_dia(abierta)), 1)                           # sesión sin terminar: sigue dentro

    def test_ciclo_paper_no_repite(self):
        import tempfile
        from copilot import intradia as I
        with tempfile.TemporaryDirectory() as d:
            rutas = {"senales": Path(d) / "s.jsonl", "paper": Path(d) / "p.jsonl"}
            barras = self._dia([(100, 101, 99, 100.5), (100.6, 101, 100, 100.8), (100.8, 101, 98.5, 99)])
            ahora = barras[1].hora + timedelta(minutes=5)                            # solo 2 velas cerradas
            self.assertEqual([s["decision"] for s in I.ciclo(barras, ahora, rutas)], ["COMPRA"])
            self.assertEqual(I.ciclo(barras, ahora, rutas), [])                      # no repite
            fin = barras[2].hora + timedelta(minutes=5)
            self.assertEqual([s["decision"] for s in I.ciclo(barras, fin, rutas)], ["VENTA"])
            ej = [e["datos"] for e in registro.leer(rutas["paper"]) if e["datos"]["tipo"] == "ejecucion"]
            self.assertEqual([e["lado"] for e in ej], ["compra", "venta"])
