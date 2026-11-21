"""Estrategias aprobadas en el Prompt 1 y descartadas, tal y como se registran en ideas.jsonl.

Este fichero es solo la fuente del primer registro. Una vez registradas, cualquier
cambio debe entrar como entrada NUEVA (nueva versión), nunca editando las previas.
"""

CRITERIOS = {
    "version": 1,
    "periodo": "TRAIN: velas 1d desde 2017-08-17 hasta 2022-12-31 (UTC), BTC/USDT spot Binance",
    "referencia": "Buy & Hold de BTC: compra en la apertura de la primera vela operable y mantiene hasta el final de TRAIN, con los mismos costes",
    "reglas_obligatorias": [
        "Rentabilidad total neta de costes > rentabilidad total de Buy & Hold",
        "|Drawdown máximo| < |drawdown máximo de Buy & Hold|",
        "Sharpe anualizado >= Sharpe de Buy & Hold (rentabilidades diarias, 365 días/año, tipo libre de riesgo 0)",
    ],
    "costes": "Comisiones de Binance spot + slippage (se documentan en el Prompt 3). Si la estrategia opera más de una vez por semana se muestran también resultados con costes x2 y x3",
    "ejecucion": "Señal con el cierre de la vela diaria (00:00 UTC); orden en la apertura de la vela siguiente",
    "decidido": "Criterio secundario (Sharpe) elegido por el usuario el 2026-11-21, antes de ver ningún resultado",
}

COMUN = {"activo": "BTC", "par": "BTCUSDT", "mercado": "Binance spot", "temporalidad": "1d",
         "lado": "solo comprado o liquidez", "criterios_aceptacion": CRITERIOS}

T1_VARIANTES = ["sma_n=100", "sma_n=150", "sma_n=200", "cruce_sma=50/200"]

ESTRATEGIAS = [
    {
        "id": "T1", "nombre": "Precio sobre media móvil simple", "familia": "Seguimiento de tendencia",
        "estado": "registrada",
        "regla_exacta": (
            "Al cierre de la vela t: si close_t > SMA(close, n)_t -> 100 % comprado desde la apertura de t+1; "
            "si no -> 100 % liquidez (USDT). Variante cruce: comprado si SMA(50)_t > SMA(200)_t; si no, liquidez."
        ),
        "configuraciones_permitidas": T1_VARIANTES,
        "referencias": ["Gartley (1935)", "Brock, Lakonishok y LeBaron (1992), Journal of Finance",
                        "Faber (2007), Journal of Wealth Management"],
    },
    {
        "id": "T2", "nombre": "Momentum de serie temporal (TSMOM)", "familia": "Seguimiento de tendencia",
        "estado": "registrada",
        "regla_exacta": "Al cierre t: si close_t / close_(t-L) - 1 > 0 -> comprado desde la apertura de t+1; si no -> liquidez.",
        "configuraciones_permitidas": ["L=90", "L=180", "L=365"],
        "referencias": ["Moskowitz, Ooi y Pedersen (2012), Journal of Financial Economics"],
    },
    {
        "id": "B1", "nombre": "Canal de Donchian (Tortugas)", "familia": "Ruptura",
        "estado": "registrada",
        "regla_exacta": (
            "Sin posición: si close_t > máximo de high en las N velas previas (t-N..t-1) -> comprar en la apertura de t+1. "
            "Con posición: si close_t < mínimo de low en las M velas previas (t-M..t-1) -> vender en la apertura de t+1."
        ),
        "configuraciones_permitidas": ["N=20,M=10", "N=55,M=20"],
        "referencias": ["Donchian (1960)", "Reglas de las Tortugas (Dennis y Eckhardt, 1983; publicadas por Faith, 2007)"],
    },
    {
        "id": "M1", "nombre": "RSI(2) de Connors", "familia": "Reversión a la media",
        "estado": "experimental",
        "regla_exacta": (
            "Sin posición: si RSI(2)_t < u y close_t > SMA(200)_t -> comprar en la apertura de t+1. "
            "Con posición: si close_t > SMA(5)_t -> vender en la apertura de t+1. RSI con suavizado de Wilder."
        ),
        "configuraciones_permitidas": ["u=5", "u=10"],
        "referencias": ["Connors y Alvarez (2008), Short Term Trading Strategies That Work", "Wilder (1978)"],
        "nota": "EXPERIMENTAL: evidencia publicada sobre todo en acciones; en BTC la reversión de corto plazo es dudosa.",
    },
    {
        "id": "P1", "nombre": "Volatilidad objetivo", "familia": "Dimensionamiento de posiciones",
        "estado": "registrada",
        "regla_exacta": (
            "sigma_real_t = desviación típica de las rentabilidades logarítmicas diarias de las últimas w velas "
            "(hasta t incluida) x sqrt(365). Exposición e = min(1, sigma_obj / sigma_real). e se recalcula una vez por "
            "semana, con el cierre del domingo (UTC), y se aplica desde la apertura del lunes. Posición = señal de la "
            "base (1 comprado / 0 liquidez, diaria) x e de la semana. Sin apalancamiento."
        ),
        "configuraciones_permitidas": [
            f"base={b},sigma_obj={s},ventana={w}"
            for b in ["buy_hold"] + [f"T1:{v}" for v in T1_VARIANTES]
            for s in ("40%", "60%")
            for w in (20, 60)
        ],
        "referencias": ["Moreira y Muir (2017), Journal of Finance", "Harvey et al. (2018), Journal of Portfolio Management"],
    },
]

DESCARTADAS = [
    ("B2", "Ruptura en la apertura", "Ruptura", "BTC cotiza 24/7: no hay apertura real de sesión."),
    ("M2", "Bandas de Bollinger", "Reversión a la media", "Repite la idea de M1."),
    ("M3", "Reversión semanal", "Reversión a la media", "Contraria a la evidencia de momentum en cripto."),
    ("S1", "Efecto día de la semana", "Estacionalidad", "Sin mecanismo económico en BTC."),
    ("S2", "Efecto cambio de mes", "Estacionalidad", "Sin mecanismo económico en BTC (no hay flujos de nóminas/fondos comparables)."),
]


def entradas() -> list[dict]:
    out = [{**COMUN, **e} for e in ESTRATEGIAS]
    out += [
        {"id": i, "nombre": n, "familia": f, "estado": "descartada", "motivo_descarte": m,
         "configuraciones_permitidas": [], "decidido_en": "Prompt 1"}
        for i, n, f, m in DESCARTADAS
    ]
    return out
