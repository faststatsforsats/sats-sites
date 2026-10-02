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
- one y-axis, never two; a 3 px line with a soft halo and a wash beneath it; recessive hairline grid; no top or right spines
- the key figure in the title and the latest value at the line's end are set in the series color; peaks, lows, and the halvings are marked in ink
- categorical colors in a fixed order (series[0] first, never cycled); sequential = one hue light to dark;
  diverging = blue and red around gray; status colors are reserved and never used for a series
- light and dark versions come from the same data; the dark palette is a selected set, not an inverted one

Run `python3 -m lib.chartstyle --demo out/` to draw a sample chart (labeled as sample data) and check the style.
"""

from __future__ import annotations

import datetime as _dt
import os
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
    event: str = "#b9c3d1"           # vertical markers for dated events (the halvings)

    def rule_color(self) -> str:
        return self.axis


LIGHT = Colors(
    mode="light",
    surface="#ffffff", page="#f6f7f9", ink="#0b1220", ink2="#4a5565", muted="#67727f", grid="#e3e6eb", axis="#c6ccd6",
    # Brand order: the wordmark orange first (deepened to hold 3:1 on white), then the rim blue, teal, gold, pink, green, purple, red
    series=("#dd6a08", "#1a6fb5", "#0f8f7a", "#b08400", "#d5588f", "#2e8b2e", "#6b5bd2", "#d9453d"),
    sequential=("#fde8d6", "#fbd7b8", "#f9c59a", "#f7b27b", "#f59f5c", "#f28c3d", "#ee7a22", "#dd6a08", "#c45e07", "#aa5206", "#904505", "#763904", "#5c2c03"),
    diverging_low="#1a6fb5", diverging_mid="#eef0f3", diverging_high="#d9453d",
    good="#1d7a1d", warning="#e0a800", serious="#ec835a", critical="#d03b3b",
    event="#b9c3d1",
)

DARK = Colors(
    mode="dark",
    surface="#122238", page="#0b1a2b", ink="#f2f5f9", ink2="#c0c9d6", muted="#8794a6", grid="#22344d", axis="#2f4563",
    series=("#f08020", "#2f9ae8", "#1aa88f", "#d1a414", "#dc669e", "#3ab543", "#9386ee", "#ed5b53"),
    sequential=("#5c2c03", "#763904", "#904505", "#aa5206", "#c45e07", "#dd6a08", "#ee7a22", "#f28c3d", "#f59f5c", "#f7b27b", "#f9c59a", "#fbd7b8", "#fde8d6"),
    diverging_low="#5cc3ff", diverging_mid="#2f4563", diverging_high="#ff7b73",
    good="#5fd35f", warning="#f2c744", serious="#ff9a6b", critical="#ff7b73",
    event="#3a5170",
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
        "font.size": 12,
        "text.color": c.ink,
        "axes.labelcolor": c.ink2,
        "axes.edgecolor": c.axis,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": c.grid,
        "grid.linewidth": 0.7,
        "xtick.labelsize": 11.5,
        "ytick.labelsize": 11.5,
        "axes.labelsize": 11.5,
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


def new_figure(title: str, subtitle: str | None, mode: str = "light", highlight: str | None = None, accent: str | None = None):
    """A 1600 by 900 figure with the finding as the title and the measure as the subtitle.

    ``highlight`` is the part of the title to set in the series color (the key figure), so the takeaway
    reads first; the rest of the title stays in ink. The size steps down until the title fits one line."""
    plt, c = apply(mode)
    fig = plt.figure(figsize=(WIDTH_PX / DPI, HEIGHT_PX / DPI), dpi=DPI)
    # Leave room for the title block at the top and the footer at the bottom
    ax = fig.add_axes([0.105, 0.2, 0.745, 0.57])   # room on the right for the latest-value pill, two footer lines below
    _title(fig, c, title, highlight, accent or c.series[0])
    if subtitle:
        fig.text(0.04, 0.862, subtitle, fontsize=12, color=c.ink2, ha="left", va="top")
    return fig, ax, c


def _title(fig, c: Colors, title: str, highlight: str | None, accent: str) -> None:
    """Draw the title as up to three runs (before, the highlighted figure, after) on one line."""
    parts: list[tuple[str, str]]
    if highlight and highlight in title:
        before, after = title.split(highlight, 1)
        parts = [(before, c.ink), (highlight, accent), (after, c.ink)]
    else:
        parts = [(title, c.ink)]
    renderer = fig.canvas.get_renderer()
    limit = WIDTH_PX * (1 - 2 * 0.04)
    size = 19.0
    while size >= 13:
        x = 0.04
        texts = []
        for text, color in parts:
            if not text:
                continue
            t = fig.text(x, 0.945, text, fontsize=size, fontweight="bold", color=color, ha="left", va="top")
            w = t.get_window_extent(renderer=renderer).width
            texts.append(t)
            x += w / WIDTH_PX
        if (x - 0.04) * WIDTH_PX <= limit:
            return
        for t in texts:
            t.remove()
        size -= 1


def finish(fig, ax, c: Colors, source: str, pulled: str, site: str = SITE_NAME, site_url: str = SITE_URL) -> None:
    """Footer line, tick styling, and the thin-mark defaults."""
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(c.axis)
    ax.tick_params(which="both", length=0, pad=6)
    ax.set_facecolor(c.surface)
    renderer = fig.canvas.get_renderer()
    limit = WIDTH_PX * 0.86   # keep clear of the coin in the corner
    line1 = fig.text(0.04, 0.078, f"Source: {source}. Pulled {pulled}.", fontsize=9.5, color=c.muted, ha="left", va="bottom")
    line2 = f"{site}  |  {site_url}"
    if line1.get_window_extent(renderer=renderer).x1 > limit:
        line1.set_text(f"Source: {source}.")
        line2 = f"{site}  |  {site_url}  |  Pulled {pulled}"
    fig.text(0.04, 0.036, line2, fontsize=9.5, color=c.muted, ha="left", va="bottom")
    brand_mark(fig)


COIN_MARK = Path(__file__).resolve().parent.parent / "shared" / "static" / "brand" / "stats-coin.png"


def brand_mark(fig, size_px: int = 96) -> None:
    """The site's coin in the bottom-right corner of the footer, so a chart carries the brand when it is embedded elsewhere."""
    if not COIN_MARK.exists():
        return
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        return
    coin = Image.open(COIN_MARK).convert("RGBA").resize((size_px, size_px), Image.LANCZOS)
    fig.figimage(np.asarray(coin), xo=WIDTH_PX - size_px - 36, yo=22, origin="upper", zorder=10)


def label_last_point(ax, x, y, text: str, c: Colors, color: str | None = None) -> None:
    """A selective direct label at a series' last point, in text ink (never the series color)."""
    ax.annotate(
        text, xy=(x, y), xytext=(8, 0), textcoords="offset points",
        fontsize=10, color=c.ink, va="center", ha="left",
        bbox={"boxstyle": "round,pad=0.25", "fc": c.surface, "ec": color or c.axis, "lw": 0.8},
    )


VECTOR_PASS = False   # set while the SVG is written: no halo passes and no wash, to keep the file small


def glow_line(ax, xs, ys, color: str, c: Colors, linewidth: float = 3.0) -> None:
    """The series line, thick, with a soft halo under it (three wider, faint passes); the wash comes from area_wash."""
    halo = 0.10 if c.mode == "light" else 0.16
    if not VECTOR_PASS:
        for mult, alpha in ((5.0, halo * 0.5), (3.0, halo), (1.8, halo * 1.6)):
            ax.plot(xs, ys, color=color, linewidth=linewidth * mult, alpha=alpha, solid_capstyle="round", solid_joinstyle="round", zorder=2)
    ax.plot(xs, ys, color=color, linewidth=linewidth, solid_capstyle="round", solid_joinstyle="round", zorder=3)


def area_wash(ax, xs, ys, color: str, c: Colors, strength: float | None = None) -> None:
    """A wash under the line that fades to nothing toward the bottom of the plot (works on log axes too)."""
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap, to_rgb

    strength = strength if strength is not None else (0.28 if c.mode == "light" else 0.34)
    r, g, b = to_rgb(color)
    cmap = LinearSegmentedColormap.from_list("wash", [(r, g, b, 0.0), (r, g, b, strength)])
    gradient = np.linspace(0, 1, 256).reshape(-1, 1)
    xlim, ylim = ax.get_xlim(), ax.get_ylim()   # the image must not move the data limits
    if VECTOR_PASS:
        return   # the vector file keeps only the line, so it stays small enough to embed
    poly = ax.fill_between(xs, ys, ylim[0], color="none", linewidth=0, zorder=1)
    image = ax.imshow(gradient, extent=(0, 1, 0, 1), transform=ax.transAxes, aspect="auto", cmap=cmap,
                      origin="lower", zorder=1, interpolation="bicubic")
    image.set_clip_path(poly.get_paths()[0], transform=ax.transData)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)


def remember_label(ax, bbox) -> None:
    """Register a box (display pixels) that later point marks must keep clear of."""
    _remember(ax, bbox)


def _remember(ax, bbox) -> None:
    placed = getattr(ax, "_sats_labels", None)
    if placed is None:
        placed = []
        ax._sats_labels = placed
    placed.append(bbox)


def latest_pill(ax, x, y, text: str, color: str, c: Colors) -> None:
    """The latest value as a bold pill in the series color at the end of the line, with a glowing end dot.

    The plot is narrowed if the pill would otherwise run off the right edge of the figure. Call it before the
    point marks, so they can keep clear of it."""
    ax.plot([x], [y], marker="o", markersize=22, color=color, alpha=0.22, zorder=4, linestyle="none")
    ax.plot([x], [y], marker="o", markersize=10, color=color, markeredgecolor=c.surface, markeredgewidth=2, zorder=5, linestyle="none")
    note = ax.annotate(
        text, xy=(x, y), xytext=(14, 0), textcoords="offset points",
        fontsize=12.5, fontweight="bold", color="#ffffff", va="center", ha="left", zorder=6,
        bbox={"boxstyle": "round,pad=0.4,rounding_size=0.6", "fc": color, "ec": "none"},
    )
    fig = ax.figure
    renderer = fig.canvas.get_renderer()
    pad = 0.4 * 12.5 * DPI / 72
    width = note.get_window_extent(renderer=renderer).width + 2 * pad   # text plus the bbox pad
    needed = 14 * DPI / 72 + width + 16                                  # offset, pill, margin
    pos = ax.get_position()
    right_px = pos.x1 * WIDTH_PX
    if WIDTH_PX - right_px < needed:
        new_right = max(0.68, (WIDTH_PX - needed) / WIDTH_PX)
        ax.set_position([pos.x0, pos.y0, new_right - pos.x0, pos.height])
    _remember(ax, note.get_window_extent(renderer=renderer).expanded(1.0, 1.0).padded(pad))


def mark_point(ax, x, y, text: str, color: str, c: Colors, side: str = "above", align: str = "auto", obstacles=None) -> None:
    """A labeled dot for a peak, a low, or a milestone: the dot in the series color, the words in ink on a surface tag.

    ``side`` and ``align`` are preferences. Every placement is scored against the line (``obstacles``, the series
    in display pixels), the labels already placed, and the figure's edges; the cheapest one wins."""
    import matplotlib.dates as mdates
    import numpy as np

    ax.plot([x], [y], marker="o", markersize=9, color=color, markeredgecolor=c.surface, markeredgewidth=2, zorder=5, linestyle="none")
    xn = mdates.date2num(x) if not isinstance(x, (int, float)) else x
    x0, x1 = ax.get_xlim()
    fx = (xn - x0) / (x1 - x0)
    if align == "auto":
        align = "left" if fx < 0.5 else "right"
    other_align = "right" if align == "left" else "left"
    other_side = "below" if side == "above" else "above"
    candidates = [
        (side, align, 22), (side, other_align, 22), (side, align, 44), (side, other_align, 44),
        ("beside", align, 16), ("beside", other_align, 16),
        (side, align, 66), (side, other_align, 66), (side, align, 88), (side, other_align, 88),
        (other_side, align, 22), (other_side, other_align, 22), (other_side, align, 44),
        (other_side, other_align, 44), (other_side, align, 66), (other_side, other_align, 66),
    ]
    fig = ax.figure
    renderer = fig.canvas.get_renderer()
    pad = 0.3 * 10.5 * DPI / 72
    placed = getattr(ax, "_sats_labels", [])
    pts = np.asarray(obstacles) if obstacles is not None else np.zeros((0, 2))
    top_limit, bottom_limit = HEIGHT_PX * 0.815, HEIGHT_PX * 0.165   # under the subtitle, above the date ticks
    best, best_cost = None, None
    for s_side, s_align, dist in candidates:
        if s_side == "beside":
            dx = dist if s_align == "left" else -dist
            dy, va = 0, "center"
        else:
            dx = 10 if s_align == "left" else -10
            dy = dist if s_side == "above" else -dist
            va = "bottom" if s_side == "above" else "top"
        note = ax.annotate(
            text, xy=(x, y), xytext=(dx, dy), textcoords="offset points",
            fontsize=10.5, color=c.ink, va=va, ha=s_align, zorder=6, linespacing=1.15,
            multialignment="left" if s_align == "left" else "right",
            bbox={"boxstyle": "round,pad=0.35", "fc": c.surface, "ec": c.rule_color(), "lw": 0.8, "alpha": 0.96},
            arrowprops={"arrowstyle": "-", "color": c.axis, "lw": 0.9, "shrinkA": 0, "shrinkB": 5},
        )
        box = note.get_window_extent(renderer=renderer).padded(pad)
        cost = 0.0
        if len(pts):
            inside = (pts[:, 0] >= box.x0 - 4) & (pts[:, 0] <= box.x1 + 4) & (pts[:, 1] >= box.y0 - 4) & (pts[:, 1] <= box.y1 + 4)
            cost += inside.sum() * (1.0 if len(pts) < 400 else 400.0 / len(pts))
        for other in placed:
            if box.overlaps(other):
                cost += 1000           # labels never sit on each other
        if box.x0 < 6 or box.x1 > WIDTH_PX - 6 or box.y1 > top_limit or box.y0 < bottom_limit:
            cost += 1000               # or run off the figure
        cost += dist * 0.02            # all else equal, stay close to the point
        if s_side != side:
            cost += 1.5 if s_side == "beside" else 3.0   # and on the side the chart asked for
        if os.environ.get("SATS_LABEL_DEBUG"):
            print(f"    {text[:28]:28} {s_side:5} {s_align:5} {dist:3} cost {cost:7.2f}")
        if best_cost is None or cost < best_cost:
            if best is not None:
                best.remove()
            best, best_cost, best_box = note, cost, box
        else:
            note.remove()
        if best_cost == 0:
            break
    _remember(ax, best_box)


def event_lines(ax, dates, label: str, c: Colors, where: str = "top") -> None:
    """Thin vertical markers for dated events (the halvings), named once beside the first one in view."""
    import matplotlib.dates as mdates
    x0, x1 = ax.get_xlim()
    inside = [d for d in dates if x0 <= mdates.date2num(d) <= x1]
    for d in inside:
        ax.axvline(d, color=c.event, linewidth=1.2, zorder=1.5)
    if inside:
        y, va, dy = (1.0, "top", -3) if where == "top" else (0.0, "bottom", 3)
        ax.annotate(label, xy=(inside[0], y), xycoords=("data", "axes fraction"), xytext=(5, dy), textcoords="offset points",
                    fontsize=9.5, color=c.muted, ha="left", va=va, zorder=6)


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
    if abs(value) >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:g}T"
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:g}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:g}M"
    if abs(value) >= 10_000:
        return f"{value / 1_000:g}k"
    if abs(value) >= 100:
        return f"{value:,.0f}"
    if 0 < abs(value) < 1:
        return f"{value:.12f}".rstrip("0").rstrip(".")
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
    highlight: str | None = None,
    slot: int = 0,
) -> list[Path]:
    """Draw the chart in light and dark and write PNGs (and a light SVG). Returns the files written.

    ``highlight`` is the figure inside the title to set in the series color; ``slot`` is that series' color slot."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    global VECTOR_PASS
    import matplotlib.pyplot as plt
    passes = [("light", False), ("dark", False)] + ([("light", True)] if svg else [])
    for mode, vector in passes:
        VECTOR_PASS = vector
        try:
            c0 = colors(mode)
            fig, ax, c = new_figure(title, subtitle, mode, highlight=highlight, accent=c0.series[slot])
            draw(ax, c)
            finish(fig, ax, c, source, pulled)
            if vector:
                path = out_dir / f"{slug}.svg"
                fig.savefig(path, format="svg")
            else:
                suffix = "" if mode == "light" else "-dark"
                path = out_dir / f"{slug}{suffix}.png"
                fig.savefig(path, dpi=DPI)
            written.append(path)
            plt.close(fig)
        finally:
            VECTOR_PASS = False
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
