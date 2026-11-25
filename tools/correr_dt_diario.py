"""Ejecuta la búsqueda DTD (D67). Una sola vez: el registro impide repetirla."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __name__ == "__main__":
    from copilot import dt_diario
    print(json.dumps(dt_diario.ejecutar(), ensure_ascii=False, indent=1))
