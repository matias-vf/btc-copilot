"""Titulares de Yahoo Finance cada 2 minutos (D60). Solo información: nunca decide nada.

El texto viene de terceros: se guarda como dato y no se interpreta como instrucción.
"""

from __future__ import annotations

import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from copilot import registro

SIMBOLOS = ("BTC-USD", "GLD", "QQQ")
URL = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={}&region=US&lang=en-US"
REGISTRO = registro.REGISTROS / "noticias.jsonl"


def leer_rss(xml: bytes, simbolo: str) -> list[dict]:
    out = []
    for it in ET.fromstring(xml).iter("item"):
        titulo = (it.findtext("title") or "").strip()[:300]
        enlace = (it.findtext("link") or "").strip()[:500]
        guid = (it.findtext("guid") or enlace or titulo).strip()[:500]
        try:
            fecha = parsedate_to_datetime(it.findtext("pubDate") or "").astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError):
            fecha = None
        if titulo:
            out.append({"simbolo": simbolo, "id": guid, "titulo": titulo, "enlace": enlace, "publicada_utc": fecha})
    return out


def _bajar(simbolo: str) -> bytes:
    req = urllib.request.Request(URL.format(simbolo), headers={"User-Agent": "Mozilla/5.0 (btc-copilot-research)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def revisar(bajar=_bajar) -> int:
    """Guarda los titulares nuevos de cada símbolo. Devuelve cuántos son nuevos."""
    vistos = {(e["datos"]["simbolo"], e["datos"]["id"]) for e in registro.leer(REGISTRO)} if REGISTRO.exists() else set()
    nuevos = []
    for s in SIMBOLOS:
        try:
            items = leer_rss(bajar(s), s)
        except Exception as e:  # una fuente caída no para las demás
            print(f"noticias {s}: fallo {type(e).__name__}")
            continue
        for x in sorted(items, key=lambda x: x["publicada_utc"] or ""):
            if (s, x["id"]) not in vistos:
                vistos.add((s, x["id"]))
                nuevos.append({"tipo": "noticia", **x})
    if nuevos:
        registro.anadir_varios(REGISTRO, nuevos)
    return len(nuevos)


def ultimas(horas: int = 24, ahora: datetime | None = None) -> list[dict]:
    if not REGISTRO.exists():
        return []
    desde = ((ahora or datetime.now(timezone.utc)) - timedelta(hours=horas)).isoformat()
    return [e["datos"] for e in registro.leer(REGISTRO) if (e["datos"].get("publicada_utc") or e["fecha_hora"]) >= desde]
