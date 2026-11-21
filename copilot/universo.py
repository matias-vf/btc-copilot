"""Tercera búsqueda (D36): universo de 1000 variantes de reglas publicadas, en velas diarias.

Cada familia tiene una función que, con las velas, devuelve la exposición objetivo decidida al cierre de cada vela
(0 = liquidez, 1 = comprado; volatilidad objetivo puede dar fracciones). Todas son causales: el valor de la vela t solo
usa datos hasta t (lo comprueba `causal()` y las pruebas). La ejecución (apertura de t+1, costes) la hace
`backtest_rapido`, idéntico al motor normal (`motor.backtest`), comprobado por una prueba.
"""

from __future__ import annotations

from collections import deque
from itertools import product
from math import log, sqrt
from typing import Callable, Sequence

from copilot.costes import BINANCE_SPOT, Costes
from copilot.motor import Resultado, Vela

ARRANQUE = 365  # todas las variantes se miden desde la vela 365 (la ventana más larga del universo; D37)


# --- Indicadores causales (valor en t con datos hasta t; None si no hay datos suficientes) -------------

def _sma(x, n):
    out, s = [None] * len(x), 0.0
    for i, v in enumerate(x):
        s += v
        if i >= n:
            s -= x[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def _ema(x, n):
    out, a, e = [None] * len(x), 2 / (n + 1), None
    for i, v in enumerate(x):
        if i == n - 1:
            e = sum(x[:n]) / n
        elif i >= n:
            e = a * v + (1 - a) * e
        out[i] = e
    return out


def _wma(x, n):
    pesos, tot = list(range(1, n + 1)), n * (n + 1) / 2
    return [None if i < n - 1 else sum(p * v for p, v in zip(pesos, x[i - n + 1:i + 1])) / tot for i in range(len(x))]


def _rmax(x, n):
    """Máximo de x[i-n+1..i]."""
    out, d = [None] * len(x), deque()
    for i, v in enumerate(x):
        while d and x[d[-1]] <= v:
            d.pop()
        d.append(i)
        if d[0] <= i - n:
            d.popleft()
        if i >= n - 1:
            out[i] = x[d[0]]
    return out


def _rmin(x, n):
    neg = _rmax([-v for v in x], n)
    return [None if v is None else -v for v in neg]


def _previo(x):
    """Desplaza una vela: el valor en i es el de i-1 (para "las n velas previas")."""
    return [None] + x[:-1]


def _std(x, n):
    out = [None] * len(x)
    for i in range(n - 1, len(x)):
        w = x[i - n + 1:i + 1]
        m = sum(w) / n
        out[i] = sqrt(sum((v - m) ** 2 for v in w) / (n - 1))
    return out


def _rsi(c, n):
    out, sube, baja = [None] * len(c), 0.0, 0.0
    for i in range(1, len(c)):
        ch = c[i] - c[i - 1]
        g, p = max(ch, 0.0), max(-ch, 0.0)
        if i <= n:
            sube += g / n
            baja += p / n
        else:
            sube = (sube * (n - 1) + g) / n
            baja = (baja * (n - 1) + p) / n
        if i >= n:
            out[i] = 100.0 if baja == 0 else 100 - 100 / (1 + sube / baja)
    return out


def _atr(v, n):
    tr = [v[0].high - v[0].low] + [max(b.high - b.low, abs(b.high - a.close), abs(b.low - a.close))
                                   for a, b in zip(v, v[1:])]
    out, a = [None] * len(v), None
    for i, t in enumerate(tr):
        if i == n - 1:
            a = sum(tr[:n]) / n
        elif i >= n:
            a = (a * (n - 1) + t) / n
        out[i] = a
    return out


def _adx(v, n):
    pdm, mdm, tr = [0.0], [0.0], [v[0].high - v[0].low]
    for a, b in zip(v, v[1:]):
        up, dn = b.high - a.high, a.low - b.low
        pdm.append(up if up > dn and up > 0 else 0.0)
        mdm.append(dn if dn > up and dn > 0 else 0.0)
        tr.append(max(b.high - b.low, abs(b.high - a.close), abs(b.low - a.close)))
    adx, pdi, mdi = [None] * len(v), [None] * len(v), [None] * len(v)
    sp = sm = st = None
    dxs, a = [], None
    for i in range(1, len(v)):
        if i < n:
            continue
        if i == n:
            sp, sm, st = sum(pdm[1:n + 1]), sum(mdm[1:n + 1]), sum(tr[1:n + 1])
        else:
            sp, sm, st = sp - sp / n + pdm[i], sm - sm / n + mdm[i], st - st / n + tr[i]
        p, m = (100 * sp / st, 100 * sm / st) if st else (0.0, 0.0)
        pdi[i], mdi[i] = p, m
        dx = 100 * abs(p - m) / (p + m) if p + m else 0.0
        dxs.append(dx)
        if len(dxs) == n:
            a = sum(dxs) / n
        elif len(dxs) > n:
            a = (a * (n - 1) + dx) / n
        adx[i] = a
    return adx, pdi, mdi


def _obv(v):
    out, s = [0.0], 0.0
    for a, b in zip(v, v[1:]):
        s += b.volumen if b.close > a.close else -b.volumen if b.close < a.close else 0.0
        out.append(s)
    return out


def _kama(c, n, rapida=2, lenta=30):
    out, k = [None] * len(c), None
    fc, sc = 2 / (rapida + 1), 2 / (lenta + 1)
    for i in range(len(c)):
        if i < n:
            continue
        if k is None:
            k = c[i - 1]
        cambio = abs(c[i] - c[i - n])
        vol = sum(abs(c[j] - c[j - 1]) for j in range(i - n + 1, i + 1))
        er = cambio / vol if vol else 0.0
        k = k + (er * (fc - sc) + sc) ** 2 * (c[i] - k)
        out[i] = k
    return out


def _psar(v, paso, maximo):
    out = [0.0] * len(v)
    if len(v) < 2:
        return out
    alcista, sar, ep, af = True, v[0].low, v[0].high, paso
    for i in range(1, len(v)):
        sar = sar + af * (ep - sar)
        if alcista:
            sar = min(sar, v[i - 1].low, v[i - 2].low if i >= 2 else v[i - 1].low)
            if v[i].low < sar:
                alcista, sar, ep, af = False, ep, v[i].low, paso
            elif v[i].high > ep:
                ep, af = v[i].high, min(af + paso, maximo)
        else:
            sar = max(sar, v[i - 1].high, v[i - 2].high if i >= 2 else v[i - 1].high)
            if v[i].high > sar:
                alcista, sar, ep, af = True, ep, v[i].high, paso
            elif v[i].low < ep:
                ep, af = v[i].low, min(af + paso, maximo)
        out[i] = 1.0 if alcista else 0.0
    return out


def _vol_anual(c, n):
    lr = [0.0] + [log(b / a) for a, b in zip(c, c[1:])]
    s = _std(lr, n)
    return [None if x is None else x * sqrt(365) for x in s]


# --- Reglas con estado --------------------------------------------------------------------------------

def _con_estado(n, entra: Callable[[int], bool], sale: Callable[[int], bool]):
    out, pos = [0.0] * n, 0.0
    for i in range(n):
        pos = (1.0 if entra(i) else 0.0) if pos == 0 else (0.0 if sale(i) else 1.0)
        out[i] = pos
    return out


def _con_tenencia(n, entra, dias):
    out, quedan = [0.0] * n, 0
    for i in range(n):
        if quedan > 0:
            quedan -= 1
            out[i] = 1.0 if quedan > 0 else 0.0
        elif entra(i):
            quedan = dias
            out[i] = 1.0
    return out


def _ok(*xs):
    return all(x is not None for x in xs)


# --- Familias -----------------------------------------------------------------------------------------

def f01_sma(v, n, banda):
    c = [x.close for x in v]
    m = _sma(c, n)
    return _con_estado(len(v), lambda i: _ok(m[i]) and c[i] > m[i] * (1 + banda),
                       lambda i: _ok(m[i]) and c[i] < m[i] * (1 - banda))


def f02_cruce_sma(v, s, l, banda):
    c = [x.close for x in v]
    a, b = (c if s == 1 else _sma(c, s)), _sma(c, l)
    return _con_estado(len(v), lambda i: _ok(a[i], b[i]) and a[i] > b[i] * (1 + banda),
                       lambda i: _ok(a[i], b[i]) and a[i] < b[i] * (1 - banda))


def f03_cruce_ema(v, s, l):
    c = [x.close for x in v]
    a, b = _ema(c, s), _ema(c, l)
    return [1.0 if _ok(a[i], b[i]) and a[i] > b[i] else 0.0 for i in range(len(v))]


def f04_tsmom(v, L, umbral):
    c = [x.close for x in v]
    return [1.0 if i >= L and c[i] / c[i - L] - 1 > umbral else 0.0 for i in range(len(v))]


def f05_tsmom_semanal(v, semanas):
    c, out, pos = [x.close for x in v], [0.0] * len(v), 0.0
    for i, x in enumerate(v):
        if x.fecha.weekday() == 6:
            j = i - 7 * semanas
            pos = 1.0 if j >= 0 and c[i] / c[j] - 1 > 0 else 0.0
        out[i] = pos
    return out


def f06_filtro(v, x, y):
    c, out, pos, ref = [b.close for b in v], [0.0] * len(v), 0.0, None
    for i, p in enumerate(c):
        if pos == 0:
            ref = p if ref is None else min(ref, p)
            if p >= ref * (1 + x):
                pos, ref = 1.0, p
        else:
            ref = max(ref, p)
            if p <= ref * (1 - y):
                pos, ref = 0.0, p
        out[i] = pos
    return out


def f07_donchian(v, N, M):
    hmax, lmin = _previo(_rmax([x.high for x in v], N)), _previo(_rmin([x.low for x in v], M))
    return _con_estado(len(v), lambda i: _ok(hmax[i]) and v[i].close > hmax[i],
                       lambda i: _ok(lmin[i]) and v[i].close < lmin[i])


def f08_trb(v, n, banda):
    c = [x.close for x in v]
    mx, mn = _previo(_rmax(c, n)), _previo(_rmin(c, n))
    return _con_estado(len(v), lambda i: _ok(mx[i]) and c[i] > mx[i] * (1 + banda),
                       lambda i: _ok(mn[i]) and c[i] < mn[i] * (1 - banda))


def f09_trb_tenencia(v, n, dias, banda):
    c = [x.close for x in v]
    mx = _previo(_rmax(c, n))
    return _con_tenencia(len(v), lambda i: _ok(mx[i]) and c[i] > mx[i] * (1 + banda), dias)


def f10_rsi(v, periodo, umbral, salida, filtro):
    c = [x.close for x in v]
    r, s200, s5 = _rsi(c, periodo), _sma(c, 200), _sma(c, 5)

    def entra(i):
        return _ok(r[i]) and r[i] < umbral and (not filtro or (_ok(s200[i]) and c[i] > s200[i]))

    def sale(i):
        if salida == "rsi50":
            return _ok(r[i]) and r[i] > 50
        if salida == "rsi70":
            return _ok(r[i]) and r[i] > 70
        return _ok(s5[i]) and c[i] > s5[i]
    return _con_estado(len(v), entra, sale)


def f11_bollinger_rev(v, n, k, salida):
    c = [x.close for x in v]
    m, s = _sma(c, n), _std(c, n)
    return _con_estado(len(v), lambda i: _ok(m[i], s[i]) and c[i] < m[i] - k * s[i],
                       lambda i: _ok(m[i], s[i]) and c[i] > (m[i] if salida == "media" else m[i] + k * s[i]))


def f12_bollinger_rup(v, n, k):
    c = [x.close for x in v]
    m, s = _sma(c, n), _std(c, n)
    return _con_estado(len(v), lambda i: _ok(m[i], s[i]) and c[i] > m[i] + k * s[i],
                       lambda i: _ok(m[i]) and c[i] < m[i])


def f13_reversion(v, k, caida, dias):
    c = [x.close for x in v]
    return _con_tenencia(len(v), lambda i: i >= k and c[i] / c[i - k] - 1 < -caida, dias)


def f14_cerca_maximo(v, ventana, x):
    c, mx = [b.close for b in v], _rmax([b.high for b in v], ventana)
    return [1.0 if _ok(mx[i]) and c[i] >= (1 - x) * mx[i] else 0.0 for i in range(len(v))]


def f15_macd(v, rapida, lenta, senal, regla):
    c = [x.close for x in v]
    er, el = _ema(c, rapida), _ema(c, lenta)
    macd = [a - b if _ok(a, b) else None for a, b in zip(er, el)]
    inicio = next((i for i, x in enumerate(macd) if x is not None), len(c))
    sig = [None] * inicio + _ema(macd[inicio:], senal)
    if regla == "cero":
        return [1.0 if _ok(m) and m > 0 else 0.0 for m in macd]
    return [1.0 if _ok(m, s) and m > s else 0.0 for m, s in zip(macd, sig)]


def f16_obv(v, n, filtro):
    c, o = [x.close for x in v], _obv(v)
    mo, mc = _sma(o, n), _sma(c, n)
    return [1.0 if _ok(mo[i]) and o[i] > mo[i] and (not filtro or (_ok(mc[i]) and c[i] > mc[i])) else 0.0
            for i in range(len(v))]


def f17_estocastico(v, n, entrada, salida):
    hi, lo = _rmax([x.high for x in v], n), _rmin([x.low for x in v], n)
    k = [None if not _ok(h, l) or h == l else 100 * (x.close - l) / (h - l) for x, h, l in zip(v, hi, lo)]
    return _con_estado(len(v), lambda i: _ok(k[i]) and k[i] < entrada, lambda i: _ok(k[i]) and k[i] > salida)


def f18_adx(v, n, umbral):
    a, p, m = _adx(v, n)
    return [1.0 if _ok(a[i], p[i], m[i]) and a[i] > umbral and p[i] > m[i] else 0.0 for i in range(len(v))]


def f19_keltner(v, n, k):
    c = [x.close for x in v]
    m, a = _ema(c, n), _atr(v, n)
    return _con_estado(len(v), lambda i: _ok(m[i], a[i]) and c[i] > m[i] + k * a[i],
                       lambda i: _ok(m[i]) and c[i] < m[i])


def _base(v, nombre):
    if nombre == "bh":
        return [1.0] * len(v)
    if nombre.startswith("sma"):
        return f01_sma(v, int(nombre[3:]), 0.0)
    return f04_tsmom(v, int(nombre[5:]), 0.0)


def f20_vol_objetivo(v, base, sigma, ventana):
    b, vol, out, e = _base(v, base), _vol_anual([x.close for x in v], ventana), [0.0] * len(v), 0.0
    for i, x in enumerate(v):
        if x.fecha.weekday() == 6:  # se fija con el cierre del domingo (como P1)
            e = 0.0 if not _ok(vol[i]) else (1.0 if vol[i] == 0 else min(1.0, sigma / vol[i]))
        out[i] = b[i] * e
    return out


def f21_estacionalidad(v, tipo, valor):
    """La exposición para la vela t+1 depende solo de su fecha (calendario conocido de antemano)."""
    from datetime import timedelta
    out = []
    for x in v:
        manana = x.fecha + timedelta(days=1)
        if tipo == "dia":
            out.append(1.0 if manana.weekday() == valor else 0.0)
        elif tipo == "mes":
            out.append(1.0 if manana.month == valor else 0.0)
        else:  # cambio de mes: últimos y primeros `valor` días
            fin = (manana.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            out.append(1.0 if manana.day <= valor or (fin - manana).days < valor else 0.0)
    return out


def f22_psar(v, paso, maximo):
    return _psar(v, paso, maximo)


def f23_ichimoku(v, t, k, b, regla):
    hi, lo, c = [x.high for x in v], [x.low for x in v], [x.close for x in v]
    mid = lambda n: [None if not _ok(h, l) else (h + l) / 2 for h, l in zip(_rmax(hi, n), _rmin(lo, n))]
    tk, kj, sb = mid(t), mid(k), mid(b)
    sa = [None if not _ok(a, z) else (a + z) / 2 for a, z in zip(tk, kj)]
    out = []
    for i in range(len(v)):
        if regla == "tk":
            out.append(1.0 if _ok(tk[i], kj[i]) and tk[i] > kj[i] else 0.0)
        else:  # precio sobre la nube, que se proyecta k velas hacia delante (usa datos de i-k)
            j = i - k
            ok = j >= 0 and _ok(sa[j], sb[j])
            out.append(1.0 if ok and c[i] > max(sa[j], sb[j]) else 0.0)
    return out


def f24_williams(v, n, entrada, salida):
    hi, lo = _rmax([x.high for x in v], n), _rmin([x.low for x in v], n)
    r = [None if not _ok(h, l) or h == l else -100 * (h - x.close) / (h - l) for x, h, l in zip(v, hi, lo)]
    return _con_estado(len(v), lambda i: _ok(r[i]) and r[i] < entrada, lambda i: _ok(r[i]) and r[i] > salida)


def f25_doble(v, L, n):
    c, m = [x.close for x in v], _sma([x.close for x in v], n)
    return [1.0 if i >= L and c[i] > c[i - L] and _ok(m[i]) and c[i] > m[i] else 0.0 for i in range(len(v))]


def f26_ruptura_volumen(v, N, k):
    hmax, lmin = _previo(_rmax([x.high for x in v], N)), _previo(_rmin([x.low for x in v], max(2, N // 2)))
    vm = _previo(_sma([x.volumen for x in v], 30))
    return _con_estado(len(v), lambda i: _ok(hmax[i], vm[i]) and v[i].close > hmax[i] and v[i].volumen > k * vm[i],
                       lambda i: _ok(lmin[i]) and v[i].close < lmin[i])


def f27_stop_atr(v, base, k, n):
    b = f04_tsmom(v, 28, 0.0) if base == "tsmom28" else f07_donchian(v, 20, 10)
    a, c = _atr(v, n), [x.close for x in v]
    out, pos, maxc = [0.0] * len(v), 0.0, 0.0
    for i in range(len(v)):
        if pos == 0:
            if b[i] > 0 and (i == 0 or b[i - 1] == 0) and _ok(a[i]):
                pos, maxc = 1.0, c[i]
        else:
            maxc = max(maxc, c[i])
            if b[i] == 0 or (_ok(a[i]) and c[i] < maxc - k * a[i]):
                pos = 0.0
        out[i] = pos
    return out


def f28_tsmom_vol(v, L, pct):
    c, vol = [x.close for x in v], _vol_anual([x.close for x in v], 30)
    out = []
    for i in range(len(v)):
        pas = [x for x in vol[max(0, i - 364):i + 1] if x is not None]
        lim = sorted(pas)[int(pct * (len(pas) - 1))] if len(pas) >= 30 else None
        out.append(1.0 if i >= L and c[i] > c[i - L] and _ok(vol[i], lim) and vol[i] <= lim else 0.0)
    return out


def f29_kama(v, n):
    c = [x.close for x in v]
    k = _kama(c, n)
    return [1.0 if _ok(k[i]) and c[i] > k[i] else 0.0 for i in range(len(v))]


def f30_wma(v, n, banda):
    c = [x.close for x in v]
    m = _wma(c, n)
    return _con_estado(len(v), lambda i: _ok(m[i]) and c[i] > m[i] * (1 + banda),
                       lambda i: _ok(m[i]) and c[i] < m[i] * (1 - banda))


def f31_darvas(v, N):
    return f07_donchian(v, N, N)


# --- Catálogo: familias, referencias y rejillas ------------------------------------------------------

def _rej(**ejes):
    claves = list(ejes)
    return [dict(zip(claves, vals)) for vals in product(*ejes.values())]


FAMILIAS = [
    ("F01", "Precio sobre media móvil (con banda)", f01_sma, "Brock, Lakonishok y LeBaron (1992); Faber (2007)",
     _rej(n=[5, 10, 15, 20, 30, 40, 50, 60, 75, 100, 125, 150, 175, 200, 250, 300], banda=[0.0, 0.01, 0.02])),
    ("F02", "Cruce de medias móviles (con banda)", f02_cruce_sma, "Brock, Lakonishok y LeBaron (1992)",
     [p for p in _rej(s=[1, 2, 5, 10, 20, 30, 50], l=[50, 75, 100, 150, 200, 250, 300], banda=[0.0, 0.01]) if p["s"] < p["l"]]),
    ("F03", "Cruce de medias exponenciales", f03_cruce_ema, "Appel (1979); Murphy (1999)",
     _rej(s=[5, 8, 10, 12, 20], l=[21, 26, 50, 100, 200])),
    ("F04", "Momentum de serie temporal diario (con umbral)", f04_tsmom,
     "Moskowitz, Ooi y Pedersen (2012); Liu y Tsyvinski (2021)",
     _rej(L=[7, 10, 14, 21, 28, 35, 42, 56, 70, 84, 98, 112, 140, 168, 182, 210, 252, 280, 315, 365],
          umbral=[0.0, 0.02, 0.05, 0.10])),
    ("F05", "Momentum semanal (decide el domingo)", f05_tsmom_semanal, "Liu y Tsyvinski (2021)",
     _rej(semanas=[1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 26, 39, 52, 65, 78])),
    ("F06", "Regla de filtro (x % arriba entra, y % abajo sale)", f06_filtro, "Alexander (1961); Fama y Blume (1966)",
     _rej(x=[0.01, 0.02, 0.03, 0.04, 0.05, 0.07, 0.10, 0.15, 0.20, 0.25],
          y=[0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20, 0.25, 0.30])),
    ("F07", "Canal de Donchian (máximos y mínimos)", f07_donchian, "Donchian (1960); reglas de las Tortugas",
     [{"N": N, "M": max(2, round(N * r))} for N in [10, 15, 20, 30, 40, 55, 70, 100, 150, 200]
      for r in [0.25, 0.5, 0.75, 1.0]]),
    ("F08", "Ruptura del rango con cierres (con banda)", f08_trb,
     "Brock, Lakonishok y LeBaron (1992); Gerritsen y otros (2020)",
     _rej(n=[10, 20, 30, 50, 75, 100, 150, 200, 250, 300], banda=[0.0, 0.01, 0.02])),
    ("F09", "Ruptura del rango con tenencia fija", f09_trb_tenencia, "Brock, Lakonishok y LeBaron (1992)",
     _rej(n=[20, 50, 100, 150, 200], dias=[5, 10, 20, 40, 60], banda=[0.0, 0.01])),
    ("F10", "Reversión con RSI", f10_rsi, "Wilder (1978); Connors y Alvarez (2008)",
     _rej(periodo=[2, 3, 5, 14], umbral=[5, 10, 20, 30], salida=["rsi50", "rsi70", "sma5"], filtro=[True, False])),
    ("F11", "Reversión con bandas de Bollinger", f11_bollinger_rev, "Bollinger (2001)",
     _rej(n=[10, 20, 30, 50], k=[1.5, 2.0, 2.5, 3.0], salida=["media", "superior"])),
    ("F12", "Ruptura de bandas de Bollinger", f12_bollinger_rup, "Bollinger (2001)",
     _rej(n=[10, 20, 30, 50], k=[1.0, 1.5, 2.0, 2.5])),
    ("F13", "Reversión a corto plazo tras una caída", f13_reversion, "Jegadeesh (1990); Lehmann (1990)",
     _rej(k=[1, 2, 3, 5, 7], caida=[0.03, 0.05, 0.07, 0.10, 0.15], dias=[1, 3, 5, 10])),
    ("F14", "Cerca del máximo de N días", f14_cerca_maximo, "George y Hwang (2004)",
     _rej(ventana=[60, 90, 120, 180, 252, 365], x=[0.05, 0.10, 0.15, 0.20, 0.25, 0.30])),
    ("F15", "MACD", f15_macd, "Appel (1979)",
     [{"rapida": a, "lenta": b, "senal": s, "regla": r} for (a, b, s) in
      [(12, 26, 9), (5, 35, 5), (8, 17, 9), (19, 39, 9), (6, 13, 5), (10, 20, 7)] for r in ["senal", "cero"]]),
    ("F16", "Volumen en balance (OBV)", f16_obv, "Granville (1963)", _rej(n=[5, 10, 20, 30, 50, 100], filtro=[False, True])),
    ("F17", "Oscilador estocástico", f17_estocastico, "Lane (1984)",
     _rej(n=[5, 9, 14, 21], entrada=[10, 20, 30], salida=[70, 80])),
    ("F18", "ADX con DI+ > DI-", f18_adx, "Wilder (1978)", _rej(n=[10, 14, 20, 28], umbral=[15, 20, 25, 30])),
    ("F19", "Canal de Keltner (ATR)", f19_keltner, "Keltner (1960)", _rej(n=[10, 20, 30, 50], k=[1.0, 1.5, 2.0, 2.5])),
    ("F20", "Volatilidad objetivo sobre una regla base", f20_vol_objetivo,
     "Moreira y Muir (2017); Harvey y otros (2018)",
     _rej(base=["bh", "sma50", "sma100", "sma200", "tsmom28", "tsmom90"], sigma=[0.3, 0.5, 0.7], ventana=[20, 60])),
    ("F21", "Estacionalidad de calendario", f21_estacionalidad,
     "Caporale y Plastun (2019); Baur, Cahill, Godfrey y Liu (2019)",
     [{"tipo": "dia", "valor": d} for d in range(7)] + [{"tipo": "mes", "valor": m} for m in range(1, 13)]
     + [{"tipo": "cambio_mes", "valor": w} for w in range(1, 7)]),
    ("F22", "SAR parabólico", f22_psar, "Wilder (1978)", _rej(paso=[0.01, 0.02, 0.03, 0.04], maximo=[0.1, 0.2, 0.3])),
    ("F23", "Ichimoku", f23_ichimoku, "Hosoda (1969)",
     [{"t": a, "k": b, "b": c, "regla": r} for (a, b, c) in [(9, 26, 52), (7, 22, 44), (10, 30, 60), (20, 60, 120)]
      for r in ["nube", "tk"]]),
    ("F24", "Williams %R", f24_williams, "Williams (1973)", _rej(n=[7, 14, 21], entrada=[-80, -90], salida=[-20, -50])),
    ("F25", "Momentum y media a la vez", f25_doble, "Antonacci (2014); Faber (2007)",
     _rej(L=[28, 56, 90, 180], n=[50, 100, 200])),
    ("F26", "Ruptura con volumen alto", f26_ruptura_volumen, "Granville (1963); Brock y otros (1992)",
     _rej(N=[20, 55, 100], k=[1.0, 1.5, 2.0])),
    ("F27", "Tendencia con stop de ATR", f27_stop_atr, "Wilder (1978); LeBeau y Lucas (1992)",
     _rej(base=["tsmom28", "donchian20"], k=[2.0, 3.0, 4.0, 5.0], n=[14, 22])),
    ("F28", "Momentum solo con volatilidad baja", f28_tsmom_vol, "Barroso y Santa-Clara (2015)",
     _rej(L=[28, 90], pct=[0.5, 0.75, 0.9])),
    ("F29", "Media adaptativa de Kaufman (KAMA)", f29_kama, "Kaufman (1995)", _rej(n=[10, 20, 30, 50])),
    ("F30", "Precio sobre media ponderada (con banda)", f30_wma, "Murphy (1999)",
     _rej(n=[10, 20, 50, 100, 200], banda=[0.0, 0.01])),
    ("F31", "Caja de Darvas", f31_darvas, "Darvas (1960); Cohen (2020)", _rej(N=[3, 4, 5, 6, 8])),
]


def texto_variante(p: dict) -> str:
    return ",".join(f"{k}={v}" for k, v in p.items())


def catalogo() -> list[tuple[str, str, Callable, str, dict]]:
    """[(id U0001.., familia, función, referencia, parámetros)], exactamente 1000."""
    out = []
    for fid, nombre, fn, ref, rejilla in FAMILIAS:
        for p in rejilla:
            out.append((f"U{len(out) + 1:04d}", fid, fn, ref, p))
    assert len(out) == 1000, len(out)
    return out


def senales(fid: str, variante: str, velas: Sequence[Vela]) -> list[float]:
    fn = next(f for i, _, f, _, _ in FAMILIAS if i == fid)
    p = next(p for i, _, _, _, r in FAMILIAS if i == fid for p in r if texto_variante(p) == variante)
    return fn(velas, **p)


def como_estrategia(fid: str, variante: str):
    """Versión para el motor normal y el copiloto: recalcula las señales con las velas que recibe (O(n) por llamada)."""
    def f(h, pos):
        return senales(fid, variante, h)[-1]
    return f


# --- Backtest rápido: mismo modelo de ejecución que motor.backtest --------------------------------------

def backtest_rapido(velas: Sequence[Vela], objetivos: Sequence[float], costes: Costes = BINANCE_SPOT,
                    capital: float = 100.0) -> Resultado:
    r = Resultado(capital=capital)
    tasa = costes.por_lado()
    efectivo, unidades, objetivo, pendiente = capital, 0.0, 0.0, None
    ultima = len(velas) - 1
    for t, v in enumerate(velas):
        if pendiente is not None and pendiente != objetivo:
            valor = efectivo + unidades * v.open
            actual, deseado = unidades * v.open, pendiente * valor
            if deseado > actual:
                nocional = (deseado - actual) / (1 + tasa)
                delta = nocional / v.open
            else:
                nocional = actual - deseado
                delta = -nocional / v.open
            coste = nocional * tasa
            efectivo -= delta * v.open + coste
            unidades += delta
            r.costes_pagados += coste
            r.ejecuciones.append({"fecha": v.fecha, "precio": v.open, "de": objetivo, "a": pendiente,
                                  "nocional": nocional, "coste": coste})
            objetivo = pendiente
        pendiente = None
        valor = efectivo + unidades * v.close
        if t == ultima:
            valor -= unidades * v.close * tasa
        r.fechas.append(v.fecha)
        r.equity.append(valor)
        if t < ultima:
            pendiente = float(objetivos[t])
            r.senales.append(pendiente)
        else:
            r.senales.append(objetivo)
    return r


def causal(fid: str, variante: str, velas: Sequence[Vela], cortes: Sequence[int], semilla: int = 7) -> bool:
    """Alterar las velas posteriores a cada corte no debe cambiar ninguna señal hasta el corte."""
    from copilot.anticipacion import _alterar
    base = senales(fid, variante, velas)
    for t in cortes:
        alt = list(velas[: t + 1]) + _alterar(velas[t + 1:], semilla + t)
        if senales(fid, variante, alt)[: t + 1] != base[: t + 1]:
            return False
    return True
