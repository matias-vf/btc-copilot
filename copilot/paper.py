"""Paper trading: cuenta simulada en USDT. Nunca envía órdenes reales; no hay ningún cliente de exchange aquí.

La cuenta se reconstruye siempre desde su registro de solo añadir (`paper.jsonl`), así cada cifra es trazable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from copilot import registro
from copilot.costes import BINANCE_SPOT, Costes

LIMITE_EXPOSICION = 0.25   # D14: exposición máxima a BTC
LIMITE_POSICIONES = 3      # D13: como mucho una posición por componente
LIMITE_PERDIDA = 0.35      # D13: drawdown máximo tolerado de la cuenta
CAPITAL_INICIAL = 100.0


@dataclass
class Cuenta:
    efectivo: float = CAPITAL_INICIAL
    btc: float = 0.0
    capital_inicial: float = CAPITAL_INICIAL
    ejecuciones: list[dict] = field(default_factory=list)
    valoraciones: list[dict] = field(default_factory=list)
    operaciones_cerradas: list[dict] = field(default_factory=list)
    abierta: dict | None = None
    costes: float = 0.0

    def valor(self, precio: float) -> float:
        return self.efectivo + self.btc * precio

    def exposicion(self, precio: float) -> float:
        v = self.valor(precio)
        return self.btc * precio / v if v > 0 else 0.0

    def drawdown(self) -> float:
        pico, dd = self.capital_inicial, 0.0
        for v in self.valoraciones:
            pico = max(pico, v["valor"])
            dd = min(dd, v["valor"] / pico - 1)
        return dd

    def drawdown_actual(self) -> float:
        if not self.valoraciones:
            return 0.0
        pico = max([self.capital_inicial] + [v["valor"] for v in self.valoraciones])
        return self.valoraciones[-1]["valor"] / pico - 1

    def aplicar(self, e: dict) -> None:
        """Aplica una ejecución ya registrada (o recién calculada)."""
        flujo = -e["coste_total_usdt"] if e["lado"] == "compra" else e["ingreso_usdt"]
        self.efectivo += flujo
        self.btc += e["cantidad_btc"] if e["lado"] == "compra" else -e["cantidad_btc"]
        if abs(self.btc) < 1e-12:
            self.btc = 0.0
        self.costes += e["comision_usdt"] + e["coste_deslizamiento_usdt"]
        self.ejecuciones.append(e)
        if self.abierta is None and e["lado"] == "compra":
            self.abierta = {"desde": e["fecha"], "flujo": 0.0}
        if self.abierta is not None:
            self.abierta["flujo"] += flujo
            if self.btc == 0.0:
                self.operaciones_cerradas.append({"desde": self.abierta["desde"], "hasta": e["fecha"],
                                                  "resultado_usdt": self.abierta["flujo"]})
                self.abierta = None


def simular_ejecucion(cuenta: Cuenta, objetivo: float, precio_teorico: float, fecha: str,
                      costes: Costes = BINANCE_SPOT) -> dict | None:
    """Calcula la ejecución simulada para llevar la exposición a `objetivo`. No toca la cuenta."""
    objetivo = max(0.0, min(LIMITE_EXPOSICION, objetivo))  # límite de exposición, siempre
    V = cuenta.valor(precio_teorico)
    actual, deseado = cuenta.btc * precio_teorico, objetivo * V
    if abs(deseado - actual) < 0.01:  # menos de un céntimo: nada que hacer
        return None
    m = costes.multiplicador
    desliz, comision = (costes.medio_spread + costes.slippage) * m, costes.comision * m
    if deseado > actual:
        precio = precio_teorico * (1 + desliz)
        gasto = min(deseado - actual, cuenta.efectivo)
        nocional = gasto / (1 + comision)
        qty = nocional / precio
        return {"fecha": fecha, "lado": "compra", "cantidad_btc": qty, "precio_teorico": precio_teorico,
                "precio_simulado": precio, "comision_usdt": nocional * comision,
                "coste_deslizamiento_usdt": qty * (precio - precio_teorico), "coste_total_usdt": gasto,
                "exposicion_objetivo": objetivo}
    qty = cuenta.btc if objetivo == 0 else (actual - deseado) / precio_teorico
    precio = precio_teorico * (1 - desliz)
    bruto = qty * precio
    return {"fecha": fecha, "lado": "venta", "cantidad_btc": qty, "precio_teorico": precio_teorico,
            "precio_simulado": precio, "comision_usdt": bruto * comision,
            "coste_deslizamiento_usdt": qty * (precio_teorico - precio), "ingreso_usdt": bruto * (1 - comision),
            "exposicion_objetivo": objetivo}


def cargar(ruta: Path) -> tuple[Cuenta, list[dict]]:
    """Reconstruye la cuenta desde el registro. Devuelve también todas las entradas (para paradas, etc.)."""
    entradas = [e["datos"] for e in registro.leer(ruta)]
    c = Cuenta()
    for d in entradas:
        if d["tipo"] == "inicio":
            c = Cuenta(efectivo=d["capital"], capital_inicial=d["capital"])
        elif d["tipo"] == "ejecucion":
            c.aplicar(d)
        elif d["tipo"] == "valoracion":
            c.valoraciones.append(d)
    return c, entradas


def parada_manual_activa(entradas: list[dict]) -> dict | None:
    """La última parada manual o de emergencia sin una reanudación posterior aprobada por el usuario."""
    activa = None
    for d in entradas:
        if d["tipo"] in ("parada_manual", "parada_emergencia"):
            activa = d
        elif d["tipo"] == "reanudacion":
            activa = None
    return activa
