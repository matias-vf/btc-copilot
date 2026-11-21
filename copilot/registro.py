"""Registros de solo-añadir (JSON Lines) encadenados con SHA-256.

Cada línea es un objeto JSON con:
  n          número de entrada (1, 2, 3...)
  fecha_hora momento UTC en que se añadió
  datos      contenido de la entrada
  hash_prev  hash de la línea anterior ("0"*64 en la primera)
  hash       sha256(hash_prev + json canónico de {n, fecha_hora, datos})

El módulo solo ofrece leer y añadir. Antes de añadir verifica la cadena
completa: si alguien ha editado, borrado o reordenado una línea, el hash no
cuadra y se lanza RegistroCorrupto sin escribir nada.
shortcut: un fichero no puede impedir que alguien lo reescriba entero con
hashes nuevos; el ancla externa es el historial de Git (un commit por paso).
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

GENESIS = "0" * 64


class RegistroCorrupto(Exception):
    """La cadena de hashes no cuadra: el registro ha sido alterado."""


def _canonico(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _calcular_hash(hash_prev: str, n: int, fecha_hora: str, datos: object) -> str:
    cuerpo = _canonico({"n": n, "fecha_hora": fecha_hora, "datos": datos})
    return hashlib.sha256((hash_prev + cuerpo).encode("utf-8")).hexdigest()


def leer(ruta: Path) -> list[dict]:
    """Lee y verifica todas las entradas. Lanza RegistroCorrupto si hay alteraciones."""
    ruta = Path(ruta)
    if not ruta.exists():
        return []
    entradas: list[dict] = []
    hash_prev = GENESIS
    with ruta.open("r", encoding="utf-8") as f:
        for num_linea, linea in enumerate(f, start=1):
            if not linea.strip():
                raise RegistroCorrupto(f"{ruta.name}: línea {num_linea} vacía")
            try:
                e = json.loads(linea)
                ok = (
                    e["n"] == num_linea
                    and e["hash_prev"] == hash_prev
                    and e["hash"] == _calcular_hash(hash_prev, e["n"], e["fecha_hora"], e["datos"])
                )
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                raise RegistroCorrupto(f"{ruta.name}: línea {num_linea} ilegible ({exc})") from exc
            if not ok:
                raise RegistroCorrupto(f"{ruta.name}: la cadena de hashes se rompe en la línea {num_linea}")
            entradas.append(e)
            hash_prev = e["hash"]
    return entradas


def anadir(ruta: Path, datos: dict) -> dict:
    """Verifica la cadena y añade una entrada nueva al final. Devuelve la entrada escrita."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    previas = leer(ruta)
    n = len(previas) + 1
    hash_prev = previas[-1]["hash"] if previas else GENESIS
    fecha_hora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entrada = {
        "n": n,
        "fecha_hora": fecha_hora,
        "datos": datos,
        "hash_prev": hash_prev,
        "hash": _calcular_hash(hash_prev, n, fecha_hora, datos),
    }
    # Modo "a": el sistema operativo solo escribe al final; nunca se reabre en "w".
    with ruta.open("a", encoding="utf-8", newline="\n") as f:
        f.write(_canonico(entrada) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return entrada


def anadir_varios(ruta: Path, lista: list[dict]) -> int:
    """Como `anadir`, pero verifica la cadena una sola vez y añade todas las entradas en orden. Devuelve cuántas."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    previas = leer(ruta)
    n, hash_prev = len(previas), previas[-1]["hash"] if previas else GENESIS
    lineas = []
    for datos in lista:
        n += 1
        fecha_hora = datetime.now(timezone.utc).isoformat(timespec="seconds")
        e = {"n": n, "fecha_hora": fecha_hora, "datos": datos, "hash_prev": hash_prev,
             "hash": _calcular_hash(hash_prev, n, fecha_hora, datos)}
        lineas.append(_canonico(e) + "\n")
        hash_prev = e["hash"]
    with ruta.open("a", encoding="utf-8", newline="\n") as f:
        f.writelines(lineas)
        f.flush()
        os.fsync(f.fileno())
    return len(lista)


# --- Registros concretos -------------------------------------------------

RAIZ = Path(__file__).resolve().parent.parent
REGISTROS = RAIZ / "registros"
IDEAS = REGISTROS / "ideas.jsonl"
EXPERIMENTOS = REGISTROS / "experimentos.jsonl"
SENALES = REGISTROS / "senales.jsonl"


def registrar_experimento(datos: dict, ideas: Path = IDEAS, experimentos: Path = EXPERIMENTOS) -> dict:
    """Añade un experimento. Exige que la estrategia y la variante estén registradas antes."""
    id_estrategia = datos.get("estrategia_id")
    variante = datos.get("variante")
    idea = next(
        (e["datos"] for e in leer(ideas) if e["datos"].get("id") == id_estrategia),
        None,
    )
    if idea is None:
        raise ValueError(f"Estrategia {id_estrategia!r} no registrada en ideas: no se puede probar")
    if idea.get("estado") == "descartada":
        raise ValueError(f"Estrategia {id_estrategia!r} está descartada")
    if variante not in idea.get("configuraciones_permitidas", []):
        raise ValueError(f"Variante {variante!r} no está entre las configuraciones registradas de {id_estrategia}")
    previos = leer(experimentos)
    datos = {**datos, "contador_acumulado": len(previos) + 1}
    return anadir(experimentos, datos)


def registrar_experimentos(lista: list[dict], ideas: Path = IDEAS, experimentos: Path = EXPERIMENTOS) -> int:
    """Como `registrar_experimento` para muchos a la vez: mismas comprobaciones, una sola lectura de los registros."""
    reg = {e["datos"].get("id"): e["datos"] for e in leer(ideas)}
    for d in lista:
        idea = reg.get(d.get("estrategia_id"))
        if idea is None:
            raise ValueError(f"Estrategia {d.get('estrategia_id')!r} no registrada en ideas: no se puede probar")
        if idea.get("estado") == "descartada":
            raise ValueError(f"Estrategia {d.get('estrategia_id')!r} está descartada")
        if d.get("variante") not in idea.get("configuraciones_permitidas", []):
            raise ValueError(f"Variante {d.get('variante')!r} no registrada en {d.get('estrategia_id')}")
    base = len(leer(experimentos))
    return anadir_varios(experimentos, [{**d, "contador_acumulado": base + i + 1} for i, d in enumerate(lista)])
