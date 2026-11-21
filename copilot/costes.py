"""Modelo de costes de BTC/USDT spot en Binance (ver docs/costes.md).

Todos los costes se expresan como fracción del importe negociado, por lado (compra o venta).
"""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Costes:
    comision: float = 0.0010      # Binance spot, usuario normal, taker 0,100 % (página oficial, 2026-11-21)
    medio_spread: float = 0.0001  # estimación: medio spread 0,01 % (conservador; hoy suele ser mucho menor)
    slippage: float = 0.0005      # estimación: 0,05 % por ejecutar a mercado en la apertura
    funding: float = 0.0          # no aplica: spot, sin perpetuos ni apalancamiento
    conversion: float = 0.0       # no aplica: la cuenta simulada está en USDT, no se convierte a USD
    multiplicador: float = 1.0    # x2 y x3 para estrategias que operan más de una vez por semana

    def por_lado(self) -> float:
        return (self.comision + self.medio_spread + self.slippage + self.conversion) * self.multiplicador

    def x(self, k: float) -> "Costes":
        return replace(self, multiplicador=k)


BINANCE_SPOT = Costes()
