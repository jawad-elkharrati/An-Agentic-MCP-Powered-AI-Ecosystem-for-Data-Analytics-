from __future__ import annotations

import os
from typing import Any

import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

BG = "rgba(0,0,0,0)"
CARD_DARK = "#0d1a2b"
BORDER = "#1f3551"
TEXT = "#e7eef9"
MUTED = "#9fb3c8"
GRID = "rgba(255,255,255,0.08)"
ACCENT = "#4f8cff"
PALETTE = ["#4f8cff", "#22c55e", "#f59e0b", "#7c5cff", "#f97316", "#06b6d4"]


def _normalise_dict_like(data: dict[str, Any]) -> tuple[list[Any], list[Any]]:
    labels = list(data.get("labels", []))
    values = list(data.get("values", []))
    if not labels and isinstance(data, dict):
        labels = list(data.keys())
        values = list(data.values())
    return labels, values


def _safe_filename(title: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in title.lower()).strip("_")[:60]


def _apply_theme(fig: go.Figure, title: str, height: int) -> go.Figure:
    fig.update_layout(
        title={"text": title, "font": {"size": 17, "color": TEXT}},
        height=height,
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font={"family": "Inter, Segoe UI, Arial, sans-serif", "size": 12, "color": TEXT},
        margin={"l": 36, "r": 20, "t": 50, "b": 34},
        xaxis={"showgrid": False, "linecolor": BORDER, "tickfont": {"color": MUTED}, "title": None, "zeroline": False, "fixedrange": True},
        yaxis={"showgrid": True, "gridcolor": GRID, "linecolor": BORDER, "tickfont": {"color": MUTED}, "title": None, "zeroline": False, "fixedrange": True},
        legend={"bgcolor": "rgba(0,0,0,0)", "font": {"color": TEXT}, "orientation": "v", "yanchor": "middle", "y": 0.5, "xanchor": "left", "x": 1.02},
        hoverlabel={"bgcolor": "#10213a", "font": {"color": "#f8fbff"}, "bordercolor": BORDER},
    )
    return fig


def _write_png(chart_type: str, title: str, data: dict, output_path: str) -> str:
    labels, values = _normalise_dict_like(data)
    height = int(data.get("height", 320))
    orientation = data.get("orientation", "v")
    hole = float(data.get("hole", 0.0))

    fig = plt.figure(figsize=(10, max(3.8, height / 95)), facecolor=CARD_DARK)
    ax = fig.add_subplot(111, facecolor=CARD_DARK)
    for spine in ax.spines.values():
        spine.set_color(BORDER)

    if chart_type == "line":
        x = list(range(len(labels)))
        ax.plot(x, values, color=PALETTE[0], linewidth=3, marker="o", markersize=5)
        ax.fill_between(x, values, color=PALETTE[0], alpha=0.15)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right", color=MUTED)
        ax.tick_params(axis="y", colors=MUTED)
        ax.grid(axis="y", color="#31506b", alpha=0.35, linestyle="-", linewidth=0.8)
    elif chart_type == "bar":
        colors = (PALETTE * ((len(labels) // len(PALETTE)) + 1))[: len(labels)]
        if orientation == "h":
            ax.barh(labels, values, color=colors)
            ax.tick_params(axis="x", colors=MUTED)
            ax.tick_params(axis="y", colors=MUTED)
            ax.grid(axis="x", color="#31506b", alpha=0.35, linestyle="-", linewidth=0.8)
        else:
            ax.bar(labels, values, color=colors)
            ax.tick_params(axis="x", rotation=45, labelcolor=MUTED)
            ax.tick_params(axis="y", colors=MUTED)
            ax.grid(axis="y", color="#31506b", alpha=0.35, linestyle="-", linewidth=0.8)
    elif chart_type == "pie":
        ax.clear()
        fig.patch.set_facecolor(CARD_DARK)
        colors = (PALETTE * ((len(labels) // len(PALETTE)) + 1))[: len(labels)]
        _, _, autotexts = ax.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            colors=colors,
            textprops={"color": TEXT, "fontsize": 10},
            wedgeprops={"width": 1 - hole if hole > 0 else 1, "edgecolor": CARD_DARK},
        )
        for t in autotexts:
            t.set_color(TEXT)
        ax.axis("equal")
    else:
        plt.close(fig)
        return ""

    ax.set_title(title, color=TEXT, fontsize=15, pad=16)
    if chart_type != "pie":
        ax.set_xlabel("")
        ax.set_ylabel("")
    plt.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path


def generate_chart(chart_type: str, title: str, data: dict, run_id: str) -> dict:
    try:
        charts_dir = f"runs/{run_id}/artifacts/charts"
        png_dir = f"runs/{run_id}/artifacts/charts_png"
        os.makedirs(charts_dir, exist_ok=True)
        os.makedirs(png_dir, exist_ok=True)

        safe_title = _safe_filename(title)
        output_path = f"{charts_dir}/{safe_title}.html"
        png_path = f"{png_dir}/{safe_title}.png"
        height = int(data.get("height", 320))
        orientation = data.get("orientation", "v")
        hole = float(data.get("hole", 0.0))

        if chart_type == "bar":
            labels, values = _normalise_dict_like(data)
            text_values = [f"£{v:,.0f}" if isinstance(v, (int, float)) else str(v) for v in values]
            if orientation == "h":
                fig = px.bar(x=values, y=labels, orientation="h", text=text_values, color=labels, color_discrete_sequence=PALETTE)
                fig.update_traces(textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x:,.0f}<extra></extra>", marker={"line": {"width": 0}})
            else:
                fig = px.bar(x=labels, y=values, text=text_values, color=labels, color_discrete_sequence=PALETTE)
                fig.update_traces(textposition="outside", cliponaxis=False, hovertemplate="%{x}: %{y:,.0f}<extra></extra>", marker={"line": {"width": 0}})
        elif chart_type == "line":
            labels, values = _normalise_dict_like(data)
            fig = px.line(x=labels, y=values, markers=True)
            fig.update_traces(line={"color": ACCENT, "width": 3, "shape": "spline", "smoothing": 0.65}, marker={"size": 7, "color": ACCENT, "line": {"width": 2, "color": "rgba(255,255,255,0.18)"}}, fill="tozeroy", fillcolor="rgba(79,140,255,0.14)", hovertemplate="%{x}: %{y:,.0f}<extra></extra>")
        elif chart_type == "pie":
            labels, values = _normalise_dict_like(data)
            fig = px.pie(names=labels, values=values, hole=hole, color=labels, color_discrete_sequence=PALETTE)
            fig.update_traces(textinfo="percent", textfont={"size": 12, "color": TEXT}, hovertemplate="%{label}: %{value:,.0f} (%{percent})<extra></extra>", marker={"line": {"color": "rgba(0,0,0,0)", "width": 2}}, pull=[0.02 if i == 0 else 0 for i in range(len(labels))])
        elif chart_type == "scatter":
            fig = px.scatter(x=data.get("x", []), y=data.get("y", []), size=data.get("size", None))
            fig.update_traces(marker={"size": 10, "color": ACCENT, "line": {"width": 1, "color": "rgba(255,255,255,0.2)"}}, hovertemplate="%{x}, %{y}<extra></extra>")
        else:
            return {"error": f"Unknown chart type: {chart_type}"}

        _apply_theme(fig, title, height)
        if chart_type == "pie":
            fig.update_layout(showlegend=True)
        elif chart_type == "bar" and orientation == "h":
            fig.update_layout(showlegend=False, yaxis={"categoryorder": "total ascending", "tickfont": {"color": MUTED}}, xaxis={"tickfont": {"color": MUTED}, "gridcolor": GRID})
        else:
            fig.update_layout(showlegend=False)

        standalone_html = pio.to_html(fig, include_plotlyjs="cdn", full_html=True, config={"displayModeBar": False, "responsive": True})
        embed_html = pio.to_html(fig, include_plotlyjs=False, full_html=False, config={"displayModeBar": False, "responsive": True})
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(standalone_html)
        png_written = _write_png(chart_type, title, data, png_path)

        return {"chart_path": output_path, "png_path": png_written, "chart_type": chart_type, "title": title, "embed_html": embed_html, "slot": data.get("slot", "generic")}
    except Exception as e:
        return {"error": str(e), "title": title}
