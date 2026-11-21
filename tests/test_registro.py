import json
import tempfile
import unittest
from pathlib import Path

from copilot import registro
from copilot.registro import RegistroCorrupto, anadir, leer, registrar_experimento


class TestRegistro(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.ruta = Path(self.dir.name) / "r.jsonl"

    def tearDown(self):
        self.dir.cleanup()

    def test_cadena_valida(self):
        a = anadir(self.ruta, {"x": 1})
        b = anadir(self.ruta, {"x": 2})
        self.assertEqual(b["hash_prev"], a["hash"])
        self.assertEqual([e["datos"]["x"] for e in leer(self.ruta)], [1, 2])

    def _lineas(self):
        return self.ruta.read_text(encoding="utf-8").splitlines(keepends=True)

    def test_detecta_edicion(self):
        anadir(self.ruta, {"x": 1})
        anadir(self.ruta, {"x": 2})
        lineas = self._lineas()
        e = json.loads(lineas[0])
        e["datos"]["x"] = 99
        lineas[0] = json.dumps(e) + "\n"
        self.ruta.write_text("".join(lineas), encoding="utf-8")
        with self.assertRaises(RegistroCorrupto):
            leer(self.ruta)
        with self.assertRaises(RegistroCorrupto):
            anadir(self.ruta, {"x": 3})

    def test_detecta_borrado(self):
        for i in range(3):
            anadir(self.ruta, {"x": i})
        lineas = self._lineas()
        self.ruta.write_text(lineas[0] + lineas[2], encoding="utf-8")
        with self.assertRaises(RegistroCorrupto):
            leer(self.ruta)

    def test_detecta_borrado_ultima_linea_no_es_posible_sin_ancla(self):
        # Limitación documentada: truncar el final deja una cadena válida.
        # El ancla es Git (cada paso se commitea).
        anadir(self.ruta, {"x": 1})
        anadir(self.ruta, {"x": 2})
        self.ruta.write_text(self._lineas()[0], encoding="utf-8")
        self.assertEqual(len(leer(self.ruta)), 1)

    def test_experimento_exige_idea_registrada(self):
        ideas = Path(self.dir.name) / "ideas.jsonl"
        exps = Path(self.dir.name) / "exps.jsonl"
        with self.assertRaises(ValueError):
            registrar_experimento({"estrategia_id": "T1", "variante": "n=100"}, ideas, exps)
        anadir(ideas, {"id": "T1", "estado": "registrada", "configuraciones_permitidas": ["n=100"]})
        with self.assertRaises(ValueError):
            registrar_experimento({"estrategia_id": "T1", "variante": "n=999"}, ideas, exps)
        e1 = registrar_experimento({"estrategia_id": "T1", "variante": "n=100"}, ideas, exps)
        e2 = registrar_experimento({"estrategia_id": "T1", "variante": "n=100"}, ideas, exps)
        self.assertEqual((e1["datos"]["contador_acumulado"], e2["datos"]["contador_acumulado"]), (1, 2))

    def test_experimento_rechaza_descartada(self):
        ideas = Path(self.dir.name) / "ideas.jsonl"
        anadir(ideas, {"id": "S1", "estado": "descartada", "configuraciones_permitidas": []})
        with self.assertRaises(ValueError):
            registrar_experimento({"estrategia_id": "S1", "variante": "x"}, ideas, Path(self.dir.name) / "e.jsonl")

    def test_registros_reales_intactos(self):
        for ruta in (registro.IDEAS, registro.EXPERIMENTOS, registro.SENALES):
            leer(ruta)  # lanza si están corruptos


if __name__ == "__main__":
    unittest.main()
