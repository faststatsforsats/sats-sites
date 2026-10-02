"""Draw the starter checklist: one US Letter page, hosted on the Acts site and linked from the welcome email.

    python3 -m pip install reportlab pyyaml pillow
    python3 scripts/checklist_pdf.py            # writes sites/acts/static/sats-stackers-starter-checklist.pdf

Every word on the page comes from scripts/checklist.yml (Jim's text); this file only lays it out. The twelve acts
mirror content/acts/first-100k-sats.md in shorter form, so change both together. Brand colors come from
shared/static/site.css (navy #071829, orange #f97e1b, dark orange #b85300 for small text on white, link blue #0b63b5);
the header carries the Acts coin and the wordmark image, never the site name retyped.
"""

from __future__ import annotations

import re
from pathlib import Path
from xml.sax.saxutils import escape

import yaml
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parent.parent
TEXT = ROOT / "scripts" / "checklist.yml"
OUT = ROOT / "sites" / "acts" / "static" / "sats-stackers-starter-checklist.pdf"
COIN = ROOT / "sites" / "acts" / "static" / "brand" / "coin-512.png"
WORDMARK = ROOT / "sites" / "acts" / "static" / "brand" / "wordmark.png"

NAVY, ORANGE, ORANGE_INK, BLUE = HexColor("#071829"), HexColor("#f97e1b"), HexColor("#b85300"), "#0b63b5"
INK, INK2, MUTED, HAIRLINE, WASH = HexColor("#0b1220"), HexColor("#4a5565"), HexColor("#67727f"), HexColor("#d9dee6"), HexColor("#f3f6fa")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def register_fonts() -> tuple[str, str]:
    base = Path("/usr/share/fonts/truetype/dejavu")
    try:
        pdfmetrics.registerFont(TTFont("Sans", str(base / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("Sans-Bold", str(base / "DejaVuSans-Bold.ttf")))
        return "Sans", "Sans-Bold"
    except Exception:  # noqa: BLE001
        return "Helvetica", "Helvetica-Bold"


def markup(text: str) -> str:
    """[words](address) becomes a clickable link; everything else is escaped for reportlab's paragraph markup."""
    out, last = [], 0
    for m in LINK.finditer(text):
        out.append(escape(text[last:m.start()]))
        out.append(f'<a href="{escape(m.group(2))}" color="{BLUE}">{escape(m.group(1))}</a>')
        last = m.end()
    out.append(escape(text[last:]))
    return "".join(out)


def linked_addresses(text: str) -> str:
    """Make a bare site address in a line clickable (fastactsforsats.com/first-100k-sats/)."""
    def repl(m):
        address = m.group(0).rstrip(".")
        tail = m.group(0)[len(address):]
        return f'<a href="https://{address}" color="{BLUE}">{address}</a>{tail}'
    return re.sub(r"fast(?:stats|facts|acts)forsats\.com[^\s<]*", repl, escape(text))


def thumbnail(path: Path, box: tuple[int, int]) -> ImageReader:
    try:
        from PIL import Image
        img = Image.open(path).convert("RGBA")
        img.thumbnail(box)
        return ImageReader(img)
    except Exception:  # noqa: BLE001
        return ImageReader(str(path))


def layout(c: canvas.Canvas, text: dict, sans: str, bold: str, scale: float, paint: bool) -> float:
    """Draw (or only measure) the page at one type scale. Returns the space left between the acts and the closing block."""
    W, H = letter
    margin = 44
    full = W - 2 * margin

    def style(name, font, size, color, leading=None):
        return ParagraphStyle(name, fontName=font, fontSize=size * scale, leading=(leading or size * 1.28) * scale, textColor=color)

    def put(par: Paragraph, x: float, top: float, width: float) -> float:
        _, h = par.wrap(width, 1000)
        if paint:
            par.drawOn(c, x, top - h)
        return h

    # Header band: the navy the logos were drawn on, with the orange rule the sites use
    band_h = 104
    if paint:
        c.setFillColor(NAVY)
        c.rect(0, H - band_h, W, band_h, stroke=0, fill=1)
        c.setFillColor(ORANGE)
        c.rect(0, H - band_h - 3, W, 3, stroke=0, fill=1)
        if COIN.exists():
            c.drawImage(thumbnail(COIN, (200, 200)), margin, H - band_h + 19, width=66, height=66, mask="auto")
        x = margin + 82
        size = 26.0
        while c.stringWidth(text["title"], bold, size) > W - margin - x and size > 16:
            size -= 0.5
        c.setFillColor(white)
        c.setFont(bold, size)
        c.drawString(x, H - 45, text["title"])
        c.setFillColor(HexColor("#d6deea"))
        c.setFont(sans, 12.5)
        c.drawString(x, H - 65, text["subtitle"])
        if WORDMARK.exists():
            mark = thumbnail(WORDMARK, (720, 80))
            mw, mh = mark.getSize()
            height = 15
            c.drawImage(mark, x, H - 90, width=height * mw / mh, height=height, mask="auto")

    # Intro
    y = H - band_h - 3 - 14
    y -= put(Paragraph(markup(text["intro"]), style("intro", sans, 10, INK2)), margin, y, full) + 9

    # The twelve acts: number, box to tick, the act (its title links to the guide), one or two lines on what to do
    box, row_gap, pad = 14, 3, 5 * scale
    col_x = margin + 38 + box + 10
    text_w = W - col_x - margin - 6
    title_style = style("act", bold, 11, INK)
    body_style = style("what", sans, 9.5, INK2)
    for n, act in enumerate(text["acts"], start=1):
        title = Paragraph(f'<a href="{escape(act["url"])}" color="{BLUE}">{escape(act["title"])}</a>.', title_style)
        what = Paragraph(markup(act["text"]), body_style)
        _, h1 = title.wrap(text_w, 1000)
        _, h2 = what.wrap(text_w, 1000)
        row_h = pad + h1 + h2 + pad
        top = y
        if paint:
            c.setFillColor(WASH if n % 2 else white)
            c.setStrokeColor(HAIRLINE)
            c.setLineWidth(0.8)
            c.roundRect(margin, top - row_h, full, row_h, 5, stroke=1, fill=1)
            c.setFillColor(NAVY)
            c.roundRect(margin + 8, top - row_h / 2 - 10, 20, 20, 4, stroke=0, fill=1)
            c.setFillColor(ORANGE)
            c.setFont(bold, 10.5)
            c.drawCentredString(margin + 18, top - row_h / 2 - 3.7, str(n))
            c.setStrokeColor(INK2)
            c.setLineWidth(1.1)
            c.rect(margin + 38, top - row_h / 2 - box / 2, box, box, stroke=1, fill=0)
            title.drawOn(c, col_x, top - pad - h1)
            what.drawOn(c, col_x, top - pad - h1 - h2)
        y = top - row_h - row_gap

    # Closing block, built up from the bottom edge: disclaimer, newsletter, the three sites, a rule, the two addresses, the closing line
    small = style("small", sans, 8, MUTED)
    lines_top = 20
    blocks = [
        Paragraph(linked_addresses(text["disclaimer"]), small),
        Paragraph(linked_addresses(text["newsletter_line"]), style("news", bold, 8.5, ORANGE_INK)),
        Paragraph(linked_addresses(text["sites_line"]), style("sites", sans, 8.5, INK2)),
    ]
    heights = [p.wrap(full, 1000)[1] for p in blocks]
    yb = lines_top
    for par, h in zip(blocks, heights):
        if paint:
            par.drawOn(c, margin, yb)
        yb += h + 2.5
    rule_y = yb + 4
    if paint:
        c.setStrokeColor(HAIRLINE)
        c.setLineWidth(0.8)
        c.line(margin, rule_y, W - margin, rule_y)
    yb = rule_y + 7
    address_style = style("address", sans, 9.5, INK)
    for entry in reversed(text["addresses"]):
        par = Paragraph(f'<font name="{bold}">{escape(entry["label"])}:</font> ' + linked_addresses(entry["address"]), address_style)
        h = par.wrap(full, 1000)[1]
        if paint:
            par.drawOn(c, margin, yb)
        yb += h + 1
    yb += 5
    closing = Paragraph(markup(text["closing"]), style("closing", sans, 9.5, INK))
    h = closing.wrap(full, 1000)[1]
    if paint:
        closing.drawOn(c, margin, yb)
    closing_top = yb + h
    return y - closing_top     # negative means the acts run into the closing block


def draw(out: Path = OUT) -> Path:
    text = yaml.safe_load(TEXT.read_text(encoding="utf-8"))
    if len(text["acts"]) != 12:
        raise SystemExit(f"scripts/checklist.yml lists {len(text['acts'])} acts; the checklist has twelve")
    sans, bold = register_fonts()
    c = canvas.Canvas(str(out), pagesize=letter)
    c.setTitle(text["title"])
    c.setAuthor("Fast Acts for Sats")
    c.setSubject(text["subtitle"])
    c.setCreator("fastactsforsats.com")
    # One page, always: use the largest type at which the twelve acts clear the closing block
    for scale in (1.16, 1.13, 1.1, 1.07, 1.04, 1.0, 0.97, 0.94, 0.91, 0.88, 0.85):
        if layout(c, text, sans, bold, scale, paint=False) >= 6:
            layout(c, text, sans, bold, scale, paint=True)
            break
    else:
        raise SystemExit("the text does not fit one page even at the smallest type; shorten a line in scripts/checklist.yml")
    c.showPage()
    c.save()
    return out


if __name__ == "__main__":
    print(draw())
