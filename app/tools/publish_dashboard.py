from __future__ import annotations

import json
import os
from datetime import datetime
from html import escape
from typing import Any

BG = "#07111f"
SIDEBAR = "#081322"
CARD = "#0d1a2b"
CARD_ALT = "#101f33"
BORDER = "rgba(148, 163, 184, 0.16)"
TEXT = "#ecf3ff"
MUTED = "#8ea4c0"
ACCENT = "#4f8cff"
ACCENT_2 = "#7c5cff"
SUCCESS = "#22c55e"
WARNING = "#f59e0b"
DANGER = "#f97316"

NAV_ICONS = {
    "home": "M3 9.5 12 2l9 7.5V21a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z",
    "dashboard": "M4 4h7v7H4zm9 0h7v4h-7zM4 13h4v7H4zm6 3h10v4H10z",
    "reports": "M6 3h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1zm8 1v5h5",
    "kpis": "M4 18 9 12l4 3 7-9",
    "explorer": "M4 10a8 8 0 1 0 16 0 8 8 0 1 0-16 0m8-4v4l3 3",
    "alerts": "M12 3 2 20h20L12 3zm0 6v5m0 4h.01",
    "users": "M16 11a4 4 0 1 0-8 0 4 4 0 0 0 8 0M4 21a8 8 0 0 1 16 0",
    "download": "M12 3v10m0 0 4-4m-4 4-4-4M4 17v3h16v-3",
    "refresh": "M20 12a8 8 0 1 1-2.34-5.66M20 4v5h-5",
    "calendar": "M7 2v3m10-3v3M4 7h16M5 4h14a1 1 0 0 1 1 1v15a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1z",
    "filter": "M4 5h16l-6 7v6l-4 2v-8z",
    "menu": "M4 7h16M4 12h16M4 17h16",
    "close": "M6 6l12 12M18 6 6 18",
    "sun": "M12 4V2m0 20v-2m8-8h2M2 12h2m13.66 5.66 1.41 1.41M4.93 4.93l1.41 1.41m11.32-1.41-1.41 1.41M6.34 17.66l-1.41 1.41M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10",
    "moon": "M21 12.79A9 9 0 1 1 11.21 3c0 .33-.02.66-.02 1A8 8 0 0 0 20 12c.34 0 .67-.02 1-.03z",
    "spark": "M13 2 3 14h8l-1 8 11-14h-8z",
    "eye": "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12zm10 3a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
}


def _fmt_currency(value: Any, decimals: int = 0) -> str:
    try:
        num = float(value)
    except Exception:
        return "-"
    return f"GBP {num:,.{decimals}f}"


def _fmt_number(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except Exception:
        return "-"


def _fmt_percent(value: Any, scale_hint: bool = True) -> str:
    try:
        num = float(value)
    except Exception:
        return "-"
    if scale_hint and num <= 1:
        num *= 100
    return f"{num:.1f}%"


def _parse_month_keys(monthly: dict[str, Any]) -> tuple[str, str]:
    if not monthly:
        return ("Latest run", "")
    keys = list(monthly.keys())
    try:
        start = datetime.strptime(keys[0], "%Y-%m")
        end = datetime.strptime(keys[-1], "%Y-%m")
        return (start.strftime("%b %Y"), end.strftime("%b %Y"))
    except Exception:
        return (str(keys[0]), str(keys[-1]))


def _compute_change(monthly: dict[str, Any]) -> float:
    values = list(monthly.values())
    if len(values) < 2:
        return 0.0
    prev = float(values[-2]) or 1.0
    curr = float(values[-1])
    return ((curr - prev) / prev) * 100


def _safe_id(label: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in label).strip("-") or "dashboard"


def _svg(path: str, size: int = 18, color: str = "currentColor") -> str:
    return (
        f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" '
        f'stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        f'<path d="{path}"></path></svg>'
    )


def _asset_href(path: str, output_dir: str) -> str:
    """Return a browser-friendly link relative to dashboard.html.

    The previous dashboard wrote paths like runs/run_002/artifacts/charts_png/a.png.
    Because dashboard.html itself is already inside runs/run_002/artifacts, those links
    became invalid when opened from the file system. This makes the Asset Center stable.
    """
    if not path:
        return ""
    if path.startswith(("http://", "https://", "data:", "#")):
        return path
    try:
        return os.path.relpath(path, output_dir).replace(os.sep, "/")
    except Exception:
        return path.replace(os.sep, "/")


def _sparkline(values: list[float], color: str) -> str:
    clean_values: list[float] = []
    for value in values:
        try:
            clean_values.append(float(value))
        except Exception:
            pass
    if not clean_values:
        clean_values = [2, 4, 3, 6, 5, 7, 8]
    pts = []
    vmin = min(clean_values)
    vmax = max(clean_values)
    span = (vmax - vmin) or 1.0
    width = 150
    height = 52
    for idx, val in enumerate(clean_values):
        x = idx * (width / max(len(clean_values) - 1, 1))
        y = height - ((val - vmin) / span) * (height - 8) - 4
        pts.append(f"{x:.1f},{y:.1f}")
    return (
        f'<svg viewBox="0 0 {width} {height}" class="sparkline">'
        f'<polyline fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" '
        f'stroke-linejoin="round" points="{" ".join(pts)}"/></svg>'
    )


def _metric_cards(kpis: dict[str, Any]) -> str:
    monthly = list((kpis.get("CA_par_mois") or {}).values())
    change = _compute_change(kpis.get("CA_par_mois") or {})
    quality = float(kpis.get("data_quality_score", 1.0) or 0.0)
    cards = [
        ("Total Revenue", _fmt_currency(kpis.get("CA_total"), 0), f"{change:+.1f}% vs previous month", ACCENT, _svg(NAV_ICONS["dashboard"], 18, ACCENT), _sparkline(monthly, ACCENT)),
        ("Orders", _fmt_number(kpis.get("nb_commandes")), "Total processed orders", SUCCESS, _svg(NAV_ICONS["reports"], 18, SUCCESS), _sparkline(monthly[-12:] or monthly, SUCCESS)),
        ("Average Basket", _fmt_currency(kpis.get("panier_moyen") or kpis.get("revenue_moyen"), 2), "Average transaction value", ACCENT_2, _svg(NAV_ICONS["kpis"], 18, ACCENT_2), _sparkline(monthly[-10:] or monthly, ACCENT_2)),
        ("Customers", _fmt_number(kpis.get("nb_clients_uniques")), "Unique active customers", WARNING, _svg(NAV_ICONS["users"], 18, WARNING), _sparkline(monthly[::2] or monthly, WARNING)),
        ("Data Quality", _fmt_percent(kpis.get("data_quality_score"), True), f"Cancellation rate {_fmt_percent(kpis.get('taux_annulation'), True)}", SUCCESS if quality >= 0.95 else WARNING, _svg(NAV_ICONS["alerts"], 18, SUCCESS if quality >= 0.95 else WARNING), _sparkline([0.96, 0.97, 0.98, 0.99, quality or 1.0], SUCCESS if quality >= 0.95 else WARNING)),
    ]
    blocks = []
    for label, value, delta, accent, icon, spark in cards:
        blocks.append(
            f'<section class="metric-card reveal">'
            f'<div class="metric-glow" style="--glow:{accent}"></div>'
            f'<div class="metric-head"><span class="metric-icon">{icon}</span><div>'
            f'<p class="metric-label">{escape(label)}</p><h3 class="metric-value">{escape(value)}</h3>'
            f'<p class="metric-delta" style="color:{accent}">{escape(delta)}</p></div></div>'
            f'<div class="metric-foot">{spark}</div></section>'
        )
    return "".join(blocks)


def _render_top_products(kpis: dict[str, Any]) -> str:
    products = list((kpis.get("top_10_produits") or {}).items())[:5]
    if not products:
        return "<tr><td colspan='3' class='empty'>No product ranking available.</td></tr>"
    total = sum(float(v) for _, v in products) or 1.0
    rows = []
    for idx, (product, sales) in enumerate(products, start=1):
        share = (float(sales) / total) * 100
        rows.append(
            f'<tr><td><div class="product-cell"><span class="rank-badge">{idx:02d}</span><div>'
            f'<div class="product-name">{escape(str(product))}</div><div class="mini-bar"><span style="width:{min(max(share, 8), 100):.1f}%"></span></div>'
            f'</div></div></td><td>{escape(_fmt_currency(sales, 0))}</td><td>{share:.1f}%</td></tr>'
        )
    return "".join(rows)


def _render_alerts(alertes: list[dict[str, Any]]) -> str:
    if not alertes:
        return (
            "<div class='alert-item ok reveal'><span class='status-pill good'></span>"
            "<div><strong>System healthy</strong><p>All monitored KPI thresholds are within the expected operating range.</p></div>"
            "<small>Updated now</small></div>"
        )
    blocks = []
    for idx, alert in enumerate(alertes[:5]):
        level = str(alert.get("niveau", "warning")).lower()
        color = DANGER if level == "critical" else WARNING
        label = "Critical" if level == "critical" else "Warning"
        blocks.append(
            f"<div class='alert-item reveal'><span class='status-pill' style='background:{color};box-shadow:0 0 0 6px {color}22;'></span>"
            f"<div><strong>{escape(str(alert.get('kpi', 'KPI')))} · {label}</strong><p>{escape(str(alert.get('message', '')))}</p></div>"
            f"<small>{idx + 1}m ago</small></div>"
        )
    return "".join(blocks)


def _render_agent_flow(agent_context: dict[str, Any]) -> str:
    flow = agent_context.get("flow") or ["Data Engineer", "Data Scientist", "BI Agent", "Reporter"]
    return "".join(
        f"<div class='flow-step reveal'><span class='flow-index'>{idx}</span><span>{escape(str(step))}</span></div>"
        for idx, step in enumerate(flow, start=1)
    )


def _download_button(label: str, href: str, filename: str = "") -> str:
    if not href:
        return ""
    safe_href = escape(href)
    safe_label = escape(label)
    safe_filename = escape(filename or os.path.basename(href) or label)
    return (
        f'<a class="asset-btn" href="{safe_href}" download="{safe_filename}" '
        f'onclick="return downloadAsset(event, this)">{_svg(NAV_ICONS["download"], 14)}<span>{safe_label}</span></a>'
    )


HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>InsightFlow - Executive Overview</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
<style>
:root{--bg:__BG__;--sidebar:__SIDEBAR__;--card:__CARD__;--card-alt:__CARD_ALT__;--border:__BORDER__;--text:__TEXT__;--muted:__MUTED__;--accent:__ACCENT__;--accent2:__ACCENT_2__;--success:__SUCCESS__;--warning:__WARNING__;--danger:__DANGER__;--drawer:252px;--shadow:0 22px 52px rgba(0,0,0,.22);--blur:blur(18px);--ring:rgba(79,140,255,.28)}
body.light{--bg:#f4f7fb;--sidebar:#ffffff;--card:#ffffff;--card-alt:#f8fbff;--border:rgba(15,23,42,.09);--text:#132136;--muted:#5f728a;--accent:#2563eb;--accent2:#6d5df6;--success:#16a34a;--warning:#d97706;--danger:#ea580c;--shadow:0 18px 42px rgba(15,23,42,.10);--ring:rgba(37,99,235,.18)}
*{box-sizing:border-box} html{scroll-behavior:smooth} body{margin:0;min-height:100vh;font-family:Inter,Segoe UI,Arial,sans-serif;color:var(--text);background:radial-gradient(circle at 9% 4%,rgba(79,140,255,.16),transparent 26%),radial-gradient(circle at 92% 0%,rgba(124,92,255,.15),transparent 26%),linear-gradient(180deg,var(--bg),#040b15 78%);transition:background .25s ease,color .25s ease;overflow-x:hidden} body.light{background:radial-gradient(circle at 9% 4%,rgba(37,99,235,.10),transparent 25%),radial-gradient(circle at 92% 0%,rgba(109,93,246,.10),transparent 25%),linear-gradient(180deg,var(--bg),#edf3fb 78%)} a{color:inherit;text-decoration:none}.shell{display:grid;grid-template-columns:var(--drawer) 1fr;min-height:100vh;transition:grid-template-columns .24s ease} body.drawer-collapsed{--drawer:92px}.overlay{position:fixed;inset:0;background:rgba(3,8,16,.55);backdrop-filter:blur(4px);opacity:0;pointer-events:none;transition:opacity .2s ease;z-index:20} body.drawer-open .overlay{opacity:1;pointer-events:auto}.sidebar{position:sticky;top:0;height:100vh;padding:18px 16px;background:linear-gradient(180deg,rgba(8,19,34,.98),rgba(5,13,24,.96));border-right:1px solid var(--border);overflow:hidden;z-index:30;transition:transform .25s ease,background .25s ease} body.light .sidebar{background:linear-gradient(180deg,#fff,#fbfdff)}.brand{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:24px}.brand-main{display:flex;align-items:center;gap:12px;min-width:0}.brand-badge{width:42px;height:42px;border-radius:16px;background:linear-gradient(135deg,var(--accent),var(--accent2));box-shadow:0 14px 28px var(--ring);position:relative;overflow:hidden}.brand-badge:after{content:"";position:absolute;inset:-30%;background:linear-gradient(120deg,transparent,rgba(255,255,255,.45),transparent);transform:rotate(20deg);animation:sheen 4s ease-in-out infinite}.brand-copy{display:grid}.brand-copy strong{font-size:15px;letter-spacing:.2px}.brand-copy small{font-size:11px;color:var(--muted);margin-top:2px}.drawer-close{display:none}.nav{display:grid;gap:8px}.nav-link{display:flex;align-items:center;gap:12px;padding:11px 12px;border-radius:15px;color:var(--muted);transition:all .18s ease;white-space:nowrap;position:relative}.nav-link:hover,.nav-link.active{background:rgba(79,140,255,.10);color:var(--text);transform:translateX(3px)} body.light .nav-link:hover,body.light .nav-link.active{background:rgba(37,99,235,.08)}.nav-link.active:before{content:"";position:absolute;left:-16px;width:3px;height:22px;border-radius:999px;background:var(--accent)}body.drawer-collapsed .brand-copy,body.drawer-collapsed .nav-label,body.drawer-collapsed .workspace-copy,body.drawer-collapsed .workspace-label,body.drawer-collapsed .workspace-run{display:none}.workspace{position:absolute;left:16px;right:16px;bottom:18px;padding:12px;border:1px solid var(--border);border-radius:18px;background:rgba(255,255,255,.035)}body.light .workspace{background:#f8fbff}.workspace-label{text-transform:uppercase;letter-spacing:.13em;color:var(--muted);font-size:10px;margin-bottom:9px}.workspace-user{display:flex;align-items:center;gap:10px}.avatar{width:34px;height:34px;border-radius:999px;display:grid;place-items:center;background:linear-gradient(135deg,var(--accent),var(--accent2));font-size:12px;font-weight:800;color:#fff}.workspace-copy{display:grid;min-width:0}.workspace-copy strong{font-size:13px}.workspace-copy span{color:var(--muted);font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.workspace-run{margin-top:10px;color:var(--muted);font-size:11px}.page{padding:22px;max-width:1720px;width:100%;margin:0 auto}.hero{position:relative;border:1px solid var(--border);border-radius:32px;background:linear-gradient(135deg,rgba(13,26,43,.88),rgba(16,31,51,.72));box-shadow:var(--shadow);padding:24px;margin-bottom:20px;overflow:hidden}.hero:before{content:"";position:absolute;inset:-80px -20px auto auto;width:420px;height:220px;border-radius:999px;background:rgba(79,140,255,.18);filter:blur(55px);pointer-events:none}.hero:after{content:"";position:absolute;inset:auto auto -110px 22%;width:460px;height:180px;border-radius:999px;background:rgba(124,92,255,.12);filter:blur(55px);pointer-events:none}body.light .hero{background:rgba(255,255,255,.82);backdrop-filter:var(--blur)}.topbar{position:relative;z-index:1;display:flex;justify-content:space-between;align-items:flex-start;gap:18px}.hero-start{display:flex;gap:16px;align-items:flex-start;max-width:850px}.drawer-toggle{display:none}.eyebrow{text-transform:uppercase;letter-spacing:.18em;color:var(--accent);font-size:11px;font-weight:800;margin-bottom:8px}.headline{font-size:42px;line-height:1.02;margin:0 0 10px;letter-spacing:-1px}.subtitle{color:var(--muted);line-height:1.7;max-width:900px;font-size:14px}.actions{display:flex;flex-wrap:wrap;align-items:center;justify-content:flex-end;gap:10px;min-width:420px}.btn,.chip{border:1px solid var(--border);background:rgba(255,255,255,.045);color:var(--text);border-radius:15px;padding:10px 13px;display:inline-flex;align-items:center;gap:8px;font-size:13px;font-weight:700;cursor:pointer;transition:transform .18s ease,box-shadow .18s ease,background .18s ease}.btn:hover,.chip:hover{transform:translateY(-2px);box-shadow:0 14px 28px rgba(0,0,0,.16);background:rgba(79,140,255,.10)}body.light .btn,body.light .chip{background:#fff}.btn.primary{background:linear-gradient(135deg,var(--accent),var(--accent2));border-color:transparent;color:#fff;box-shadow:0 15px 34px var(--ring)}.btn.primary svg,#pdfBtn svg{stroke:#fff!important}.btn.primary span,#pdfBtn span{color:#fff!important}body.light .btn.primary,body.light #pdfBtn{display:inline-flex!important;visibility:visible!important;opacity:1!important;background:linear-gradient(135deg,#2563eb,#6d5df6)!important;color:#fff!important;border-color:transparent!important}#pdfBtn:disabled{opacity:.82!important;cursor:wait;filter:saturate(.95)}.hero-stats{position:relative;z-index:1;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-top:24px}.hero-stat{border:1px solid var(--border);border-radius:22px;background:rgba(255,255,255,.04);padding:15px;transition:transform .18s ease,background .18s ease}.hero-stat:hover{transform:translateY(-3px);background:rgba(79,140,255,.08)}body.light .hero-stat{background:#fff}.hero-stat-label{font-size:11px;text-transform:uppercase;letter-spacing:.12em;color:var(--muted);font-weight:800}.hero-stat-value{font-size:19px;font-weight:850;margin-top:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.grid{display:grid;gap:18px}.metrics{grid-template-columns:repeat(5,minmax(0,1fr));margin-bottom:18px}.metric-card,.panel{position:relative;border:1px solid var(--border);border-radius:26px;background:linear-gradient(180deg,rgba(13,26,43,.88),rgba(13,26,43,.64));box-shadow:var(--shadow);overflow:hidden}.metric-card{padding:18px;min-height:174px}.metric-glow{position:absolute;right:-34px;top:-44px;width:130px;height:130px;border-radius:999px;background:var(--glow);opacity:.12;filter:blur(14px)}body.light .metric-card,body.light .panel{background:rgba(255,255,255,.86);backdrop-filter:var(--blur)}.metric-head{position:relative;display:flex;align-items:flex-start;gap:12px}.metric-icon{width:38px;height:38px;border-radius:14px;display:grid;place-items:center;background:rgba(79,140,255,.12);flex:0 0 auto}.metric-label{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.12em;font-weight:800;margin:0}.metric-value{font-size:25px;margin:6px 0 0;letter-spacing:-.4px}.metric-delta{margin:6px 0 0;font-size:12px;font-weight:800}.metric-foot{position:absolute;left:18px;right:18px;bottom:12px}.sparkline{width:100%;height:48px;opacity:.88}.content{grid-template-columns:1.2fr .8fr}.span-2{grid-column:span 2}.panel{padding:18px;min-height:250px}.panel-header{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;margin-bottom:14px}.panel-header h2{font-size:17px;margin:0 0 5px}.panel-sub{font-size:12px;color:var(--muted);line-height:1.5}.panel-meta{font-size:11px;font-weight:800;color:var(--accent);border:1px solid var(--border);border-radius:999px;padding:7px 10px;white-space:nowrap;background:rgba(79,140,255,.07)}.panel-header-right{display:flex;align-items:center;gap:8px;flex-wrap:wrap;justify-content:flex-end}.asset-actions{display:flex;gap:8px;flex-wrap:wrap}.asset-btn{border:1px solid var(--border);background:rgba(79,140,255,.08);color:var(--text);border-radius:13px;padding:8px 10px;display:inline-flex;align-items:center;gap:7px;font-size:12px;font-weight:800;transition:all .18s ease}.asset-btn:hover{transform:translateY(-2px);border-color:var(--accent);box-shadow:0 12px 26px var(--ring)}body.light .asset-btn{background:#f8fbff}.js-plotly-plot,.plotly-graph-div{width:100% !important}.table{width:100%;border-collapse:collapse;margin-top:10px}.table th{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);text-align:left;padding:10px 8px;border-bottom:1px solid var(--border)}.table td{padding:12px 8px;border-bottom:1px solid var(--border);font-size:13px}.product-cell{display:grid;grid-template-columns:36px 1fr;gap:10px;align-items:center}.rank-badge{width:30px;height:30px;border-radius:10px;display:grid;place-items:center;font-size:11px;font-weight:900;color:#fff;background:linear-gradient(135deg,var(--accent),var(--accent2))}.product-name{font-weight:800;line-height:1.35}.mini-bar{height:6px;border-radius:999px;background:rgba(148,163,184,.18);overflow:hidden;margin-top:7px}.mini-bar span{display:block;height:100%;border-radius:inherit;background:linear-gradient(90deg,var(--accent),var(--accent2));animation:growBar 1.1s ease both}.alert-item{display:grid;grid-template-columns:auto 1fr auto;gap:12px;align-items:start;padding:13px;border:1px solid var(--border);border-radius:18px;background:rgba(255,255,255,.035);margin-bottom:10px}body.light .alert-item{background:#f8fbff}.alert-item strong{font-size:13px}.alert-item p{margin:5px 0 0;color:var(--muted);font-size:12px;line-height:1.5}.alert-item small{color:var(--muted);font-size:11px;white-space:nowrap}.status-pill{width:10px;height:10px;border-radius:999px;background:var(--warning);display:block;margin-top:6px}.status-pill.good{background:var(--success);box-shadow:0 0 0 6px rgba(34,197,94,.12)}.insight-box{font-size:14px;line-height:1.7}.insight-box ul{padding-left:20px;margin:8px 0 0}.insight-box li{margin-bottom:8px}.flow-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:14px}.flow-step{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:15px;border:1px solid rgba(79,140,255,.18);background:rgba(79,140,255,.06)}body.light .flow-step{background:rgba(37,99,235,.045);border-color:rgba(37,99,235,.12)}.flow-index{width:25px;height:25px;border-radius:999px;display:grid;place-items:center;background:rgba(79,140,255,.16);font-size:12px;font-weight:900}.footer-note{margin-top:12px;color:var(--muted);font-size:12px}.empty{padding:22px;border:1px dashed var(--border);border-radius:18px;color:var(--muted);text-align:center}.asset-card-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.asset-card{border:1px solid var(--border);border-radius:20px;padding:14px;background:rgba(255,255,255,.035);transition:all .18s ease}.asset-card:hover{transform:translateY(-3px);box-shadow:0 14px 30px var(--ring)}body.light .asset-card{background:#f8fbff}.asset-card strong{display:block;margin-bottom:5px}.asset-card span{display:block;color:var(--muted);font-size:12px;margin-bottom:12px}.pdf-render-root{position:fixed!important;left:0!important;top:0!important;width:1600px!important;max-width:1600px!important;padding:18px!important;background:var(--bg)!important;color:var(--text)!important;z-index:-9999!important;pointer-events:none!important;overflow:visible!important}.pdf-render-root .actions,.pdf-render-root .drawer-toggle,.pdf-render-root .drawer-close,.pdf-render-root .asset-actions{display:none!important}.pdf-render-root .reveal{opacity:1!important;transform:none!important;animation:none!important}.pdf-render-root .hero,.pdf-render-root .metric-card,.pdf-render-root .panel{break-inside:avoid;page-break-inside:avoid}.toast{position:fixed;right:22px;bottom:22px;max-width:340px;padding:13px 15px;border-radius:15px;z-index:100;border:1px solid rgba(79,140,255,.25);background:rgba(8,19,34,.96);color:#fff;font-size:13px;box-shadow:0 18px 36px rgba(0,0,0,.28);opacity:0;transform:translateY(14px);pointer-events:none;transition:all .2s ease}.toast.show{opacity:1;transform:translateY(0)}.pdf-export .sidebar,.pdf-export .actions,.pdf-export .toast,.pdf-export .overlay,.pdf-export .drawer-toggle,.pdf-export .asset-actions{display:none !important}.pdf-export .shell{display:block}.pdf-export .page{max-width:none;padding:0}.pdf-export #dashboardCapture{padding:0}.pdf-export .hero{margin-bottom:12px}.pdf-export .reveal{opacity:1 !important;transform:none !important}.reveal{opacity:0;transform:translateY(18px);animation:fadeUp .75s ease forwards}.metrics .reveal:nth-child(2){animation-delay:.06s}.metrics .reveal:nth-child(3){animation-delay:.12s}.metrics .reveal:nth-child(4){animation-delay:.18s}.metrics .reveal:nth-child(5){animation-delay:.24s}@keyframes fadeUp{to{opacity:1;transform:translateY(0)}}@keyframes sheen{0%,70%{transform:translateX(-60%) rotate(20deg)}100%{transform:translateX(80%) rotate(20deg)}}@keyframes growBar{from{width:0}}@media (max-width:1380px){.metrics{grid-template-columns:repeat(3,minmax(0,1fr))}.hero-stats{grid-template-columns:repeat(2,minmax(0,1fr))}.asset-card-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.flow-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media (max-width:1180px){.shell{grid-template-columns:1fr}.sidebar{position:fixed;inset:0 auto 0 0;width:min(290px,86vw);transform:translateX(-100%);box-shadow:0 24px 48px rgba(0,0,0,.25)}body.drawer-open .sidebar{transform:translateX(0)}.drawer-close{display:inline-flex}.drawer-toggle{display:inline-flex}.content{grid-template-columns:1fr}.span-2{grid-column:span 1}.page{padding:16px}.topbar{flex-direction:column;align-items:stretch}.actions{justify-content:flex-start;min-width:0}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}body.drawer-collapsed{--drawer:252px}}@media (max-width:720px){.metrics,.hero-stats,.asset-card-grid,.flow-grid{grid-template-columns:1fr}.headline{font-size:28px}.btn,.chip{width:100%;justify-content:center}.actions{width:100%}.hero-start{flex-direction:column}}@media print{body{background:#fff !important;color:#111827}.sidebar,.actions,.toast,.overlay,.drawer-toggle{display:none !important}.shell{display:block}.page{padding:0}.hero,.metric-card,.panel{box-shadow:none;background:#fff !important;color:#111827;border-color:#e5e7eb}.table td,.table th{border-bottom-color:#e5e7eb}}
</style>
</head>
<body>
<div class="overlay" onclick="closeDrawer()" aria-hidden="true"></div>
<div class="shell">
<aside class="sidebar">
<div class="brand"><div class="brand-main"><span class="brand-badge"></span><div class="brand-copy"><strong>InsightFlow</strong><small>Agentic BI Workspace</small></div></div><button class="btn drawer-close" type="button" onclick="closeDrawer()">__ICON_CLOSE__</button></div>
<nav class="nav">__NAV_ITEMS__</nav>
<div class="workspace"><div class="workspace-label">Workspace</div><div class="workspace-user"><div class="avatar">BI</div><div class="workspace-copy"><strong>Executive View</strong><span>Generated by BI Agent</span></div></div><div class="workspace-run">Run ID: __RUN_ID__</div></div>
</aside>
<main class="page" id="executive-view">
<section class="hero reveal">
<div class="topbar"><div class="hero-start"><button class="btn drawer-toggle" type="button" onclick="toggleDrawer()">__ICON_MENU__<span>Drawer</span></button><div><div class="eyebrow">Executive Dashboard</div><h1 class="headline">Executive Overview</h1><div class="subtitle">A premium BI dashboard generated from insights.json with working drawer controls, live active navigation, light/dark themes, reliable PDF export, working asset downloads, animated cards, and a clean executive view for decision makers.</div></div></div><div class="actions"><div class="chip">__ICON_CALENDAR__<span>__DATE_LABEL__</span></div><button class="btn" type="button" onclick="scrollToSection('executive-view')">__ICON_EYE__<span>Executive View</span></button><button class="btn" id="themeBtn" type="button" onclick="toggleTheme()">__ICON_SUN__<span id="themeText">Light mode</span></button><button class="btn primary" id="pdfBtn" type="button" onclick="downloadDashboardPDF()">__ICON_DOWNLOAD_WHITE__<span>Download PDF</span></button><button class="btn" type="button" onclick="refreshDashboard()">__ICON_REFRESH__<span>Refresh</span></button></div></div>
<div class="hero-stats"><div class="hero-stat"><div class="hero-stat-label">Lead market</div><div class="hero-stat-value">__COUNTRY_LEADER__</div></div><div class="hero-stat"><div class="hero-stat-label">Lead market revenue</div><div class="hero-stat-value">__COUNTRY_LEADER_VALUE__</div></div><div class="hero-stat"><div class="hero-stat-label">Orders / Customers</div><div class="hero-stat-value">__ORDERS__ / __CUSTOMERS__</div></div><div class="hero-stat"><div class="hero-stat-label">Average basket / Quality</div><div class="hero-stat-value">__BASKET__ / __QUALITY__</div></div></div>
</section>
<div id="dashboardCapture">
<section class="grid metrics">__METRIC_CARDS__</section>
<section class="grid content">
<article class="panel span-2 reveal" id="sales-trend">__TREND_HEADER____TREND__</article>
<article class="panel reveal" id="products">__PRODUCTS_HEADER____PRODUCTS_CHART__<table class="table"><thead><tr><th>Product</th><th>Revenue</th><th>Share</th></tr></thead><tbody>__TOP_PRODUCTS__</tbody></table></article>
<article class="panel span-2 reveal" id="country-breakdown">__BREAKDOWN_HEADER____BREAKDOWN__</article>
<article class="panel reveal" id="country-mix">__MIX_HEADER____MIX__</article>
<article class="panel reveal" id="alerts"><div class="panel-header"><div><h2>Recent Alerts</h2><div class="panel-sub">Active KPI threshold monitoring and health checks</div></div><div class="panel-meta">__ALERT_COUNT__ active</div></div>__ALERTS__</article>
<article class="panel reveal" id="insights"><div class="panel-header"><div><h2>AI Insight</h2><div class="panel-sub">Narrative summary created from upstream agent outputs</div></div><div class="panel-meta">Agent handoff</div></div><div class="insight-box"><ul>__AI_SUMMARY__</ul></div><div class="flow-grid">__AGENT_FLOW__</div><div class="footer-note">Communication pipeline: __PIPELINE__</div></article>
<article class="panel span-2 reveal" id="asset-center"><div class="panel-header"><div><h2>Export Center</h2><div class="panel-sub">Downloads are now generated with paths relative to this dashboard file, so they work when opened locally from artifacts/dashboard.html.</div></div><div class="panel-meta">Exports</div></div><div class="asset-card-grid">__EXPORT_CARDS__</div></article>
</section>
</div>
</main>
</div>
<div id="toast" class="toast"></div>
<script>
const themeConfig={dark:{label:'Light mode',icon:`__ICON_SUN__`,font:'#e7eef9',muted:'#9fb3c8',grid:'rgba(255,255,255,0.08)',axis:'rgba(148,163,184,0.18)',hover:'#10213a',line:'#4f8cff',fill:'rgba(79,140,255,0.14)'},light:{label:'Dark mode',icon:`__ICON_MOON__`,font:'#132136',muted:'#5f728a',grid:'rgba(15,23,42,0.08)',axis:'rgba(15,23,42,0.12)',hover:'#ffffff',line:'#2563eb',fill:'rgba(37,99,235,0.12)'}};
function showToast(msg){const t=document.getElementById('toast');if(!t)return;t.textContent=msg;t.classList.add('show');clearTimeout(window.__toast);window.__toast=setTimeout(()=>t.classList.remove('show'),2700)}
const sectionLabels={'executive-view':'Executive View','sales-trend':'Dashboards','products':'Products','country-breakdown':'Markets','insights':'Insights','alerts':'Alerts','asset-center':'Export Center'};
function getSectionLabel(id){return sectionLabels[id]||'Section'}
function setActiveNav(id){document.querySelectorAll('.nav-link[data-section]').forEach(link=>{const active=link.dataset.section===id;link.classList.toggle('active',active);if(active)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current')})}
function closeDrawer(){document.body.classList.remove('drawer-open');if(window.innerWidth>1180)document.body.classList.add('drawer-collapsed')}
function toggleDrawer(){if(window.innerWidth<=1180){document.body.classList.toggle('drawer-open')}else{document.body.classList.toggle('drawer-collapsed')}}
function syncDrawer(){if(window.innerWidth>1180){document.body.classList.remove('drawer-open')}else{document.body.classList.remove('drawer-collapsed')}}
function scrollToSection(id){const el=document.getElementById(id);if(el){setActiveNav(id);el.scrollIntoView({behavior:'smooth',block:'start'});if(window.innerWidth<=1180)closeDrawer();showToast(getSectionLabel(id)+' opened.')}}
function updateNavByScroll(){const ids=Array.from(document.querySelectorAll('.nav-link[data-section]')).map(a=>a.dataset.section);let current=ids[0]||'executive-view';const marker=window.scrollY+150;ids.forEach(id=>{const el=document.getElementById(id);if(el&&el.offsetTop<=marker)current=id});setActiveNav(current)}
function refreshDashboard(){showToast('Refreshing dashboard...');setTimeout(()=>window.location.reload(),350)}
function applyPlotlyTheme(mode){if(!window.Plotly)return;const s=themeConfig[mode];document.querySelectorAll('.js-plotly-plot').forEach(plot=>{try{Plotly.relayout(plot,{paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font:{color:s.font},title:{font:{color:s.font}},xaxis:{tickfont:{color:s.muted},linecolor:s.axis,gridcolor:s.grid,zeroline:false},yaxis:{tickfont:{color:s.muted},linecolor:s.axis,gridcolor:s.grid,zeroline:false},legend:{font:{color:s.font}},hoverlabel:{bgcolor:s.hover,bordercolor:s.axis,font:{color:s.font}}});(plot.data||[]).forEach((trace,idx)=>{if(trace.type==='scatter'){Plotly.restyle(plot,{'line.color':s.line,'marker.color':s.line,'fillcolor':s.fill},[idx])}if(trace.type==='pie'){Plotly.restyle(plot,{'textfont.color':s.font,'marker.line.color':mode==='light'?'#ffffff':'rgba(0,0,0,0)'},[idx])}if(trace.type==='bar'){Plotly.restyle(plot,{'textfont.color':s.font},[idx])}});Plotly.Plots.resize(plot)}catch(e){console.warn('Plotly theme sync failed',e)}})}
function setTheme(mode){const isLight=mode==='light';document.body.classList.toggle('light',isLight);localStorage.setItem('insightflow-theme',mode);const btn=document.getElementById('themeBtn');if(btn)btn.innerHTML=`${themeConfig[mode].icon}<span id="themeText">${themeConfig[mode].label}</span>`;setTimeout(()=>applyPlotlyTheme(mode),120)}
function toggleTheme(){setTheme(document.body.classList.contains('light')?'dark':'light')}
function downloadAsset(event, anchor){const href=anchor.getAttribute('href')||'';if(!href||href==='#'){event.preventDefault();showToast('Export file is not available for this chart.');return false}showToast('Opening download: '+(anchor.getAttribute('download')||anchor.textContent.trim()));return true}
function wait(ms){return new Promise(resolve=>setTimeout(resolve,ms))}
function makePdfClone(source,mode){const clone=source.cloneNode(true);clone.id='pdf-render-root';clone.classList.add('pdf-render-root');clone.querySelectorAll('.actions,.drawer-toggle,.drawer-close,.asset-actions').forEach(el=>el.remove());clone.querySelectorAll('.reveal').forEach(el=>{el.style.opacity='1';el.style.transform='none';el.style.animation='none'});clone.style.background=mode==='light'?'#f4f7fb':'#07111f';document.body.appendChild(clone);return clone}
async function downloadDashboardPDF(){const source=document.getElementById('executive-view');if(!source){showToast('Dashboard capture area not found.');return}const btn=document.getElementById('pdfBtn');const old=btn?btn.innerHTML:'';if(btn){btn.disabled=true;btn.innerHTML=`__ICON_DOWNLOAD_WHITE__<span>Preparing PDF...</span>`}showToast('Generating PDF export...');const mode=document.body.classList.contains('light')?'light':'dark';let clone=null;try{applyPlotlyTheme(mode);if(document.fonts&&document.fonts.ready)await document.fonts.ready;await wait(250);if(typeof html2pdf==='undefined')throw new Error('html2pdf is not loaded');clone=makePdfClone(source,mode);await wait(250);await html2pdf().set({margin:[7,7,7,7],filename:'insightflow-executive-dashboard-__RUN_ID_SAFE__.pdf',image:{type:'jpeg',quality:0.98},html2canvas:{scale:2,useCORS:true,allowTaint:true,logging:false,backgroundColor:mode==='light'?'#f4f7fb':'#07111f',scrollX:0,scrollY:0,windowWidth:1600,windowHeight:Math.max(clone.scrollHeight,900)},jsPDF:{unit:'mm',format:'a4',orientation:'landscape'},pagebreak:{mode:['css','legacy'],avoid:['.metric-card','.panel','.hero-stat','.asset-card']}}).from(clone).save();showToast('PDF downloaded successfully.')}catch(e){console.error(e);showToast('PDF export fallback: print dialog opened.');window.print()}finally{if(clone&&clone.parentNode)clone.parentNode.removeChild(clone);if(btn){btn.disabled=false;btn.innerHTML=old}setTimeout(()=>applyPlotlyTheme(mode),120)}}
document.addEventListener('DOMContentLoaded',()=>{setTheme(localStorage.getItem('insightflow-theme')||'dark');syncDrawer();setActiveNav('executive-view');window.addEventListener('resize',syncDrawer);let ticking=false;window.addEventListener('scroll',()=>{if(!ticking){window.requestAnimationFrame(()=>{updateNavByScroll();ticking=false});ticking=true}},{passive:true});document.querySelectorAll('.nav-link[data-section]').forEach(link=>{link.addEventListener('click',e=>{e.preventDefault();scrollToSection(link.dataset.section)})});document.addEventListener('keydown',e=>{if(e.key==='Escape')closeDrawer()});document.querySelectorAll('.reveal').forEach((el,i)=>{el.style.animationDelay=(Math.min(i,12)*0.045)+'s'});setTimeout(()=>applyPlotlyTheme(document.body.classList.contains('light')?'light':'dark'),450)});
</script>
</body>
</html>'''


def publish_dashboard(
    charts: list[dict],
    run_id: str,
    kpis: dict | None = None,
    alertes: list[dict] | None = None,
    insights: list[str] | None = None,
    agent_context: dict | None = None,
) -> dict:
    try:
        kpis = kpis or {}
        alertes = alertes or []
        insights = insights or []
        agent_context = agent_context or {}

        output_path = f"runs/{run_id}/artifacts/dashboard.html"
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)

        normalized_charts: list[dict[str, Any]] = []
        for chart in charts:
            c = dict(chart)
            c["chart_href"] = _asset_href(str(c.get("chart_path", "")), output_dir)
            c["png_href"] = _asset_href(str(c.get("png_path", "")), output_dir)
            normalized_charts.append(c)

        chart_by_slot = {chart.get("slot", f"chart_{idx}"): chart for idx, chart in enumerate(normalized_charts)}
        monthly = kpis.get("CA_par_mois") or {}
        date_start, date_end = _parse_month_keys(monthly)
        date_label = f"{date_start} - {date_end}" if date_end else date_start
        country_sales = kpis.get("CA_par_pays_top10") or {}
        country_leader = str(next(iter(country_sales.keys()), "-"))
        country_leader_value = _fmt_currency(next(iter(country_sales.values()), 0), 0)
        ai_summary = insights[:4] or [
            "The BI agent consolidated the analytics payload and generated this dashboard.",
            "No extra narrative insights were provided.",
        ]
        pipeline = escape(" -> ".join(agent_context.get("received_from", ["data_scientist"]) + ["bi_agent", "reporter"]))

        nav_specs = [
            ("home", "Executive", "executive-view"),
            ("dashboard", "Dashboards", "sales-trend"),
            ("reports", "Products", "products"),
            ("kpis", "Markets", "country-breakdown"),
            ("explorer", "Insights", "insights"),
            ("alerts", "Alerts", "alerts"),
            ("download", "Exports", "asset-center"),
        ]
        nav_items = "".join(
            f'<a class="nav-link {"active" if idx == 0 else ""}" href="#{section}" data-section="{section}">'
            f'{_svg(NAV_ICONS[icon], 16)}<span class="nav-label">{label}</span></a>'
            for idx, (icon, label, section) in enumerate(nav_specs)
        )

        def header(title: str, subtitle: str, chart: dict, badge: str = "") -> str:
            html_href = chart.get("chart_href", "")
            png_href = chart.get("png_href", "")
            meta = f'<div class="panel-meta">{escape(badge)}</div>' if badge else ""
            actions = _download_button("HTML", html_href, f"{_safe_id(title)}.html") + _download_button("PNG", png_href, f"{_safe_id(title)}.png")
            return (
                f'<div class="panel-header"><div><h2>{escape(title)}</h2><div class="panel-sub">{escape(subtitle)}</div></div>'
                f'<div class="panel-header-right">{meta}<div class="asset-actions">{actions}</div></div></div>'
            )

        def export_card(title: str, subtitle: str, href: str, filename: str) -> str:
            if not href:
                return ""
            return (
                f'<div class="asset-card"><strong>{escape(title)}</strong><span>{escape(subtitle)}</span>'
                f'{_download_button("Download", href, filename)}</div>'
            )

        export_cards = [
            export_card("Dashboard HTML", "Main interactive executive dashboard", _asset_href(output_path, output_dir), "dashboard.html"),
            export_card("Payload JSON", "Exact KPI payload used by the dashboard", "dashboard_payload.json", "dashboard_payload.json"),
            export_card("Manifest JSON", "List of generated dashboard artifacts", "dashboard_artifacts_manifest.json", "dashboard_artifacts_manifest.json"),
        ]
        for idx, chart in enumerate(normalized_charts, start=1):
            export_cards.append(export_card(f"Chart {idx} PNG", str(chart.get("title") or "Chart image"), chart.get("png_href", ""), f"chart_{idx}.png"))
            export_cards.append(export_card(f"Chart {idx} HTML", str(chart.get("title") or "Interactive chart"), chart.get("chart_href", ""), f"chart_{idx}.html"))
        export_cards_html = "".join(card for card in export_cards if card) or "<div class='empty'>No export files were generated.</div>"

        replacements = {
            "__BG__": BG,
            "__SIDEBAR__": SIDEBAR,
            "__CARD__": CARD,
            "__CARD_ALT__": CARD_ALT,
            "__BORDER__": BORDER,
            "__TEXT__": TEXT,
            "__MUTED__": MUTED,
            "__ACCENT__": ACCENT,
            "__ACCENT_2__": ACCENT_2,
            "__SUCCESS__": SUCCESS,
            "__WARNING__": WARNING,
            "__DANGER__": DANGER,
            "__ICON_CLOSE__": _svg(NAV_ICONS["close"], 18),
            "__ICON_MENU__": _svg(NAV_ICONS["menu"], 16),
            "__ICON_CALENDAR__": _svg(NAV_ICONS["calendar"], 16),
            "__ICON_EYE__": _svg(NAV_ICONS["eye"], 16),
            "__ICON_SUN__": _svg(NAV_ICONS["sun"], 16),
            "__ICON_MOON__": _svg(NAV_ICONS["moon"], 16),
            "__ICON_DOWNLOAD_WHITE__": _svg(NAV_ICONS["download"], 16, "white"),
            "__ICON_REFRESH__": _svg(NAV_ICONS["refresh"], 16),
            "__NAV_ITEMS__": nav_items,
            "__RUN_ID__": escape(run_id),
            "__RUN_ID_SAFE__": _safe_id(run_id),
            "__DATE_LABEL__": escape(date_label),
            "__COUNTRY_LEADER__": escape(country_leader),
            "__COUNTRY_LEADER_VALUE__": escape(country_leader_value),
            "__ORDERS__": escape(_fmt_number(kpis.get("nb_commandes"))),
            "__CUSTOMERS__": escape(_fmt_number(kpis.get("nb_clients_uniques"))),
            "__BASKET__": escape(_fmt_currency(kpis.get("panier_moyen") or kpis.get("revenue_moyen"), 2)),
            "__QUALITY__": escape(_fmt_percent(kpis.get("data_quality_score"), True)),
            "__METRIC_CARDS__": _metric_cards(kpis),
            "__TREND_HEADER__": header("Sales Over Time", "Monthly revenue performance across the reporting window", chart_by_slot.get("trend", {}), "Trend analysis"),
            "__TREND__": chart_by_slot.get("trend", {}).get("embed_html", "<div class='empty'>No trend chart available.</div>"),
            "__PRODUCTS_HEADER__": header("Top Products", "Highest revenue-generating products", chart_by_slot.get("products", {}), "Top 5"),
            "__PRODUCTS_CHART__": chart_by_slot.get("products", {}).get("embed_html", ""),
            "__TOP_PRODUCTS__": _render_top_products(kpis),
            "__BREAKDOWN_HEADER__": header("Sales by Country", "Top market contribution ranked by revenue", chart_by_slot.get("breakdown", {}), "Geographic view"),
            "__BREAKDOWN__": chart_by_slot.get("breakdown", {}).get("embed_html", "<div class='empty'>No country chart available.</div>"),
            "__MIX_HEADER__": header("Country Mix", "Distribution of revenue among leading markets", chart_by_slot.get("mix", {}), country_leader),
            "__MIX__": chart_by_slot.get("mix", {}).get("embed_html", "<div class='empty'>No mix chart available.</div>"),
            "__ALERT_COUNT__": str(len(alertes)),
            "__ALERTS__": _render_alerts(alertes),
            "__AI_SUMMARY__": "".join(f"<li>{escape(str(x))}</li>" for x in ai_summary),
            "__AGENT_FLOW__": _render_agent_flow(agent_context),
            "__PIPELINE__": pipeline,
            "__EXPORT_CARDS__": export_cards_html,
        }

        html = HTML_TEMPLATE
        for key, value in replacements.items():
            html = html.replace(key, value)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        payload_path = f"runs/{run_id}/artifacts/dashboard_payload.json"
        manifest_path = f"runs/{run_id}/artifacts/dashboard_artifacts_manifest.json"
        with open(payload_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "run_id": run_id,
                    "dashboard_path": output_path,
                    "kpis": kpis,
                    "alertes": alertes,
                    "insights": insights,
                    "agent_context": agent_context,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "run_id": run_id,
                    "dashboard_path": output_path,
                    "payload_path": payload_path,
                    "charts": [
                        {
                            "html": c.get("chart_path"),
                            "html_href": c.get("chart_href"),
                            "png": c.get("png_path"),
                            "png_href": c.get("png_href"),
                            "slot": c.get("slot"),
                            "title": c.get("title"),
                        }
                        for c in normalized_charts
                    ],
                    "png_exports": [c.get("png_path") for c in normalized_charts if c.get("png_path")],
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        return {
            "dashboard_path": output_path,
            "payload_path": payload_path,
            "manifest_path": manifest_path,
            "nb_charts": len(normalized_charts),
            "published": True,
        }
    except Exception as e:
        return {"error": str(e), "published": False}
