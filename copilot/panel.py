"""Panel HTML local (un solo archivo, sin internet) con el estado del paper trading frente al backtest."""

from __future__ import annotations

from html import escape
from pathlib import Path


def _p(x: float) -> str:
    return f"{x * 100:,.1f} %".replace(",", " ")


def _svg(fechas, a, b) -> str:
    w, h, pad = 760, 220, 30
    lo, hi = min(a + b), max(a + b)
    rng = (hi - lo) or 1

    def linea(serie):
        n = len(serie) - 1 or 1
        return " ".join(f"{pad + i * (w - 2 * pad) / n:.1f},{h - pad - (y - lo) / rng * (h - 2 * pad):.1f}"
                        for i, y in enumerate(serie))
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Evolución del capital">'
            f'<polyline fill="none" stroke="var(--a)" stroke-width="2" points="{linea(a)}"/>'
            f'<polyline fill="none" stroke="var(--b)" stroke-width="2" stroke-dasharray="5 4" points="{linea(b)}"/>'
            f'<text x="{pad}" y="16" class="t">{hi:.1f} USD</text><text x="{pad}" y="{h - 8}" class="t">{lo:.1f} USD · '
            f'{escape(fechas[0])} a {escape(fechas[-1])}</text></svg>')


def generar(cmp: dict, salida: Path, titulo: str) -> Path:
    mp, mb, c = cmp["paper"], cmp["backtest"], cmp["cuenta"]
    ult = cmp["senales"][-1]
    pos = cmp["operaciones_positivas"] / cmp["operaciones_cerradas"] if cmp["operaciones_cerradas"] else 0.0
    filas = "".join(
        f"<tr><td>{escape(s['vela'])}</td><td class='d {escape(s['decision'][:2])}'>{escape(s['decision'])}</td>"
        f"<td>{s['precio_referencia']:,.0f}</td><td>{_p(s['exposicion_objetivo'])}</td>"
        f"<td>{escape(' '.join(s['justificacion'])[:140])}</td></tr>"
        for s in [x for x in cmp["senales"] if x["decision"] in ("COMPRA", "VENTA")][-15:][::-1])
    comp = "".join(f"<tr><td>{escape(x['estrategia'])}</td><td>{escape(x['estado_vigilancia'])}</td>"
                   f"<td>{'comprada' if x['posicion_nueva'] else 'liquidez'}</td></tr>" for x in ult["componentes"])
    html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(titulo)}</title><style>
:root{{--bg:#fafaf7;--fg:#1d1d1b;--mut:#6b6b66;--card:#fff;--line:#e4e2dc;--a:#1f6feb;--b:#9a6700;--ok:#1a7f37;--ko:#cf222e}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141413;--fg:#ecebe6;--mut:#a3a29c;--card:#1d1d1b;--line:#33322f;--a:#58a6ff;--b:#d29922;--ok:#3fb950;--ko:#f85149}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif}}main{{max-width:980px;margin:auto;padding:16px}}
h1{{font-size:22px;margin:8px 0}}h2{{font-size:16px;margin:24px 0 8px}}.mut,.t{{color:var(--mut);fill:var(--mut);font-size:12px}}
.g{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}.k{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px}}
.k b{{display:block;font-size:20px}}table{{width:100%;border-collapse:collapse;background:var(--card)}}td,th{{border-bottom:1px solid var(--line);padding:6px;text-align:left;font-size:13px}}
.wrap{{overflow-x:auto}}.CO{{color:var(--ok);font-weight:600}}.VE{{color:var(--ko);font-weight:600}}svg{{width:100%;height:auto;background:var(--card);border:1px solid var(--line);border-radius:8px}}
.ley span{{display:inline-block;width:18px;height:3px;margin:0 6px 3px 12px;vertical-align:middle}}</style></head><body><main>
<h1>{escape(titulo)}</h1><p class="mut">Paper trading con 100 USD ficticios. Solo análisis: no se envía ninguna orden real.
{escape(cmp['desde'])} a {escape(cmp['hasta'])} ({cmp['dias']} días). {escape(ult['estado_validacion'])}</p>
<h2>Última decisión: <span class="{escape(ult['decision'][:2])}">{escape(ult['decision'])}</span> · {ult['precio_referencia']:,.2f} USDT</h2>
<p>{escape(' '.join(ult['justificacion']))}</p>
<div class="g">
<div class="k">Capital virtual<b>{c.valoraciones[-1]['valor']:.2f} USD</b></div>
<div class="k">Rentabilidad<b>{_p(mp['rentabilidad'])}</b><span class="mut">backtest {_p(mb['rentabilidad'])}</span></div>
<div class="k">Beneficio / pérdida<b>{c.valoraciones[-1]['valor'] - c.capital_inicial:+.2f} USD</b></div>
<div class="k">Drawdown máximo<b>{_p(mp['max_drawdown'])}</b><span class="mut">backtest {_p(mb['max_drawdown'])}</span></div>
<div class="k">Sharpe<b>{mp['sharpe']:.2f}</b><span class="mut">backtest {mb['sharpe']:.2f}</span></div>
<div class="k">Operaciones<b>{cmp['operaciones_cerradas']} cerradas{' + 1 abierta' if cmp['operacion_abierta'] else ''}</b><span class="mut">{cmp['ejecuciones']} órdenes · {_p(pos)} positivas</span></div>
<div class="k">Costes pagados<b>{cmp['costes_usdt']:.2f} USD</b></div>
<div class="k">Precio simulado frente a teórico<b>{_p(cmp['dif_precio_simulado_media'])}</b><span class="mut">señal → ejecución {_p(cmp['dif_senal_ejecucion_media'])}</span></div>
</div><h2>Evolución del capital</h2><p class="ley mut"><span style="background:var(--a)"></span>paper<span style="background:var(--b)"></span>backtest (C1 al 25 %)</p>
{_svg(cmp['fechas'], cmp['equity_paper'], cmp['equity_backtest'])}
<h2>Estrategias (vigilancia)</h2><div class="wrap"><table><tr><th>Estrategia</th><th>Estado</th><th>Posición</th></tr>{comp}</table></div>
<h2>Últimas órdenes</h2><div class="wrap"><table><tr><th>Vela</th><th>Decisión</th><th>Precio</th><th>Exposición</th><th>Por qué</th></tr>{filas}</table></div>
</main></body></html>"""
    salida.write_text(html, encoding="utf-8", newline="\n")
    return salida
