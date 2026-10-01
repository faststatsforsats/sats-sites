"""The shared chart style for every chart the Daily Build draws (matplotlib).

Usage from a chart script (step 16, scripts/charts/*.py):

    from pathlib import Path
    from lib.chartstyle import render_chart

    def draw(ax, c):                      # c is the Colors for the mode being drawn
        ax.plot(dates, sats, color=c.series[0], linewidth=2)
        ax.set_ylabel("sats per dollar")

    render_chart(
        slug="sats-per-dollar",
        title="A dollar bought 1,240 sats on October 1, 2026",   # the finding, not the topic
        subtitle="Sats per US dollar, daily closing price since 2011",
        draw=draw,
        source="CoinGecko",
        pulled="October 1, 2026, 09:00 UTC",
        out_dir=Path("charts"),
    )

That writes charts/sats-per-dollar.png (light), charts/sats-per-dollar-dark.png, and charts/sats-per-dollar.svg.

Rules baked in here (from the style guide and the dataviz method):
- the title states the finding; the subtitle names the measure; the footer carries source, pull time, and site name
- one y-axis, never two; thin 2 px lines; recessive hairline grid; no top or right spines
- categorical colors in a fixed order (series[0] first, never cycled); sequential = one hue light to dark;
  diverging = blue and red around gray; status colors are reserved and never used for a series
- light and dark versions come from the same data; the dark palette is a selected set, not an inverted one

Run `python3 -m lib.chartstyle --demo out/` to draw a sample chart (labeled as sample data) and check the style.
"""

from __future__ import annotations

import datetime as _dt
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

SITE_NAME = "Fast Stats for Sats"
SITE_URL = "faststatsforsats.com"


@dataclass(frozen=True)
class Colors:
    mode: str
    surface: str
    page: str
    ink: str
    ink2: str
    muted: str
    grid: str
    axis: str
    series: tuple[str, ...]          # categorical, fixed order: blue, orange, aqua, yellow, magenta, green, violet, red
    sequential: tuple[str, ...]      # one hue (blue), light to dark
    diverging_low: str               # blue pole
    diverging_mid: str               # neutral gray
    diverging_high: str              # red pole
    good: str
    warning: str
    serious: str
    critical: str


LIGHT = Colors(
    mode="light",
    surface="#fcfcfb", page="#f9f9f7", ink="#0b0b0b", ink2="#52514e", muted="#898781", grid="#e1e0d9", axis="#c3c2b7",
    series=("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"),
    sequential=("#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"),
    diverging_low="#2a78d6", diverging_mid="#f0efec", diverging_high="#e34948",
    good="#0ca30c", warning="#fab219", serious="#ec835a", critical="#d03b3b",
)

DARK = Colors(
    mode="dark",
    surface="#1a1a19", page="#0d0d0d", ink="#ffffff", ink2="#c3c2b7", muted="#898781", grid="#2c2c2a", axis="#383835",
    series=("#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"),
    sequential=("#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"),
    diverging_low="#3987e5", diverging_mid="#383835", diverging_high="#e66767",
    good="#0ca30c", warning="#fab219", serious="#ec835a", critical="#d03b3b",
)

COLORS = {"light": LIGHT, "dark": DARK}

WIDTH_PX, HEIGHT_PX, DPI = 1600, 900, 200   # 8 by 4.5 inches at 200 dpi


def colors(mode: str = "light") -> Colors:
    return COLORS[mode]


def apply(mode: str = "light"):
    """Set matplotlib's defaults for one mode and return (plt, Colors)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    c = colors(mode)
    plt.rcdefaults()
    plt.rcParams.update({
        "figure.facecolor": c.surface,
        "axes.facecolor": c.surface,
        "savefig.facecolor": c.surface,
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Segoe UI", "Helvetica", "Arial", "sans-serif"],
        "font.size": 11,
        "text.color": c.ink,
        "axes.labelcolor": c.ink2,
        "axes.edgecolor": c.axis,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": c.grid,
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "axes.titlelocation": "left",
        "axes.prop_cycle": matplotlib.cycler(color=list(c.series)),
        "xtick.color": c.muted,
        "ytick.color": c.muted,
        "xtick.labelcolor": c.ink2,
        "ytick.labelcolor": c.ink2,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "lines.linewidth": 2,
        "lines.markersize": 5,
        "legend.frameon": False,
        "legend.fontsize": 10,
        "axes.formatter.use_mathtext": False,
    })
    return plt, c


def new_figure(title: str, subtitle: str | None, mode: str = "light"):
    """A 1600 by 900 figure with the finding as the title and the measure as the subtitle."""
    plt, c = apply(mode)
    fig = plt.figure(figsize=(WIDTH_PX / DPI, HEIGHT_PX / DPI), dpi=DPI)
    # Leave room for the title block at the top and the footer at the bottom
    ax = fig.add_axes([0.095, 0.2, 0.80, 0.59])   # room on the right for an end label, two footer lines below
    fig.text(0.04, 0.945, title, fontsize=15, fontweight="bold", color=c.ink, ha="left", va="top", wrap=True)
    if subtitle:
        fig.text(0.04, 0.875, subtitle, fontsize=11, color=c.ink2, ha="left", va="top")
    return fig, ax, c


def finish(fig, ax, c: Colors, source: str, pulled: str, site: str = SITE_NAME, site_url: str = SITE_URL) -> None:
    """Footer line, tick styling, and the thin-mark defaults."""
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(c.axis)
    ax.tick_params(which="both", length=0, pad=6)
    ax.set_facecolor(c.surface)
    fig.text(0.04, 0.075, f"Source: {source}. Pulled {pulled}.", fontsize=9, color=c.muted, ha="left", va="bottom")
    fig.text(0.04, 0.035, f"{site}  |  {site_url}", fontsize=9, color=c.muted, ha="left", va="bottom")


def label_last_point(ax, x, y, text: str, c: Colors, color: str | None = None) -> None:
    """A selective direct label at a series' last point, in text ink (never the series color)."""
    ax.annotate(
        text, xy=(x, y), xytext=(8, 0), textcoords="offset points",
        fontsize=10, color=c.ink, va="center", ha="left",
        bbox={"boxstyle": "round,pad=0.25", "fc": c.surface, "ec": color or c.axis, "lw": 0.8},
    )


def date_axis(ax) -> None:
    """Readable date ticks (Nov 2025, Jan 2026, ...) on the x axis."""
    import matplotlib.dates as mdates
    locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))


def thousands(value: float) -> str:
    """1,234 or 1.2M for axis labels."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:g}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:g}M"
    if abs(value) >= 10_000:
        return f"{value / 1_000:g}k"
    if abs(value) >= 100:
        return f"{value:,.0f}"
    return f"{value:g}"


def render_chart(
    slug: str,
    title: str,
    draw: Callable,
    source: str,
    pulled: str,
    out_dir: Path,
    subtitle: str | None = None,
    svg: bool = True,
) -> list[Path]:
    """Draw the chart in light and dark and write PNGs (and a light SVG). Returns the files written."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for mode in ("light", "dark"):
        fig, ax, c = new_figure(title, subtitle, mode)
        draw(ax, c)
        finish(fig, ax, c, source, pulled)
        suffix = "" if mode == "light" else "-dark"
        png = out_dir / f"{slug}{suffix}.png"
        fig.savefig(png, dpi=DPI)
        written.append(png)
        if svg and mode == "light":
            path = out_dir / f"{slug}.svg"
            fig.savefig(path, format="svg")
            written.append(path)
        import matplotlib.pyplot as plt
        plt.close(fig)
    return written


def demo(out_dir: Path) -> list[Path]:
    """A sample chart that exercises the style. The numbers are made up and the chart says so."""
    import numpy as np

    rng = np.random.default_rng(7)
    days = 365
    start = _dt.date(2025, 10, 1)
    x = [start + _dt.timedelta(days=i) for i in range(days)]
    y = 1200 + np.cumsum(rng.normal(0, 12, days))
    y2 = 900 + np.cumsum(rng.normal(0, 9, days))

    def draw(ax, c):
        ax.plot(x, y, color=c.series[0], label="Series A (sample)")
        ax.plot(x, y2, color=c.series[1], label="Series B (sample)")
        ax.yaxis.set_major_formatter(__import__("matplotlib").ticker.FuncFormatter(lambda v, _: thousands(v)))
        ax.set_ylabel("sample units")
        date_axis(ax)
        ax.legend(loc="lower left")
        label_last_point(ax, x[-1], y[-1], thousands(y[-1]), c, c.series[0])
        label_last_point(ax, x[-1], y2[-1], thousands(y2[-1]), c, c.series[1])

    return render_chart(
        slug="sample-style-check",
        title="Sample data, not real prices: this chart only checks the style",
        subtitle="Two made-up series over one year",
        draw=draw,
        source="generated numbers",
        pulled=_dt.datetime.now(_dt.timezone.utc).strftime("%B %d, %Y, %H:%M UTC"),
        out_dir=out_dir,
    )


if __name__ == "__main__":
    import sys

    if "--demo" in sys.argv:
        target = Path(sys.argv[sys.argv.index("--demo") + 1]) if len(sys.argv) > sys.argv.index("--demo") + 1 else Path("out")
        for path in demo(target):
            print(path)
    else:
        print(__doc__)
