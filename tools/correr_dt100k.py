"""Ejecuta la búsqueda DT100K (D65). Una sola vez: el registro impide repetirla."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __name__ == "__main__":
    from copilot import dt100k
    print(json.dumps(dt100k.ejecutar(), ensure_ascii=False, indent=1))
