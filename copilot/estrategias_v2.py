"""Segunda búsqueda (D23): estrategias N1-N4 tal y como se registran en ideas.jsonl, con el criterio versión 2.

Este fichero es solo la fuente del registro. Cualquier cambio posterior entra como entrada NUEVA.
"""

CRITERIOS_V2 = {
    "version": 2,
    "decidido": "Por el usuario el 2026-11-21 (D23), antes de ver ningún resultado de N1-N4",
    "reglas_obligatorias": [
        "|Drawdown máximo| < |drawdown máximo de Buy & Hold|",
        "Sharpe anualizado >= Sharpe de Buy & Hold (rentabilidades diarias, 365 días/año, tipo libre de riesgo 0)",
    ],
    "no_exige": "Superar a Buy & Hold en rentabilidad (diferencia con la versión 1)",
    "fases": [
        "Selección: TRAIN 2017-08-17 a 2022-12-31, Binance BTCUSDT spot",
        "Robustez: Bitstamp BTC/USD 2011-08-18 a 2016-12-31 (reglas del Prompt 5 que se fijen antes de ejecutarlo)",
        "Segunda validación: TEST 2023-01-01 a 2026-11-20 (AVISO: ya visto en la primera búsqueda)",
        "Prueba final: al menos un mes de paper trading en vivo; hasta entonces, solo EXPERIMENTAL en el copiloto",
    ],
    "costes": "Los mismos (0,16 % por lado). Si opera más de una vez por semana: también costes x2 y x3",
    "ejecucion": "Señal con el cierre de la vela diaria (00:00 UTC); orden en la apertura de la vela siguiente",
}

COMUN = {"activo": "BTC", "par": "BTCUSDT", "mercado": "Binance spot", "temporalidad": "1d",
         "lado": "solo comprado o liquidez", "busqueda": 2, "criterios_aceptacion": CRITERIOS_V2}

ESTRATEGIAS_V2 = [
    {
        "id": "N1", "nombre": "Momentum semanal", "familia": "Seguimiento de tendencia", "estado": "registrada",
        "regla_exacta": (
            "Solo se decide con el cierre de la vela del domingo (00:00 UTC del lunes). r = close_domingo / "
            "close_del_domingo_de_hace_L_semanas - 1. Si r > 0 -> 100 % comprado desde la apertura del lunes y toda la "
            "semana; si no -> 100 % liquidez. Entre semana no se cambia la posición."),
        "configuraciones_permitidas": ["L=1", "L=2", "L=4"],
        "referencias": ["Liu y Tsyvinski (2021), Review of Financial Studies 34(6), 2689-2727"],
    },
    {
        "id": "N2", "nombre": "Media móvil corta", "familia": "Seguimiento de tendencia", "estado": "registrada",
        "regla_exacta": ("Al cierre de la vela t: si close_t > SMA(close, n)_t -> 100 % comprado desde la apertura de "
                         "t+1; si no -> 100 % liquidez."),
        "configuraciones_permitidas": ["n=5", "n=10", "n=20"],
        "referencias": ["Detzel, Liu, Strauss, Zhou y Zhu (2021), Financial Management, doi 10.1111/fima.12310"],
    },
    {
        "id": "N3", "nombre": "Ruptura del rango (soporte/resistencia)", "familia": "Ruptura", "estado": "registrada",
        "regla_exacta": (
            "Sin posición: si close_t > máximo de los cierres de las n velas previas (t-n..t-1) -> comprar en la apertura "
            "de t+1. Con posición: si close_t < mínimo de los cierres de las n velas previas -> vender en la apertura de t+1."),
        "configuraciones_permitidas": ["n=50", "n=150", "n=200"],
        "referencias": ["Brock, Lakonishok y LeBaron (1992), Journal of Finance",
                        "Gerritsen, Bouri, Ramezanifar y Roubaud (2020), Finance Research Letters 34, doi 10.1016/j.frl.2019.08.011"],
        "nota": "Parecida a B1 (Donchian), que no superó TEST en la primera búsqueda. Prioridad baja.",
    },
    {
        "id": "N4", "nombre": "Cerca del máximo de 52 semanas", "familia": "Ruptura", "estado": "experimental",
        "regla_exacta": (
            "Al cierre de la vela t: si close_t >= (1 - x) * máximo de high de las últimas 365 velas (hasta t incluida) "
            "-> 100 % comprado desde la apertura de t+1; si no -> 100 % liquidez. Con menos de 365 velas: liquidez."),
        "configuraciones_permitidas": ["x=10%", "x=20%"],
        "referencias": ["George y Hwang (2004), Journal of Finance (citada de memoria: verificar)"],
        "nota": "EXPERIMENTAL: evidencia publicada sobre todo en acciones; en BTC es escasa.",
    },
]


def entradas() -> list[dict]:
    return [{**COMUN, **e} for e in ESTRATEGIAS_V2]
