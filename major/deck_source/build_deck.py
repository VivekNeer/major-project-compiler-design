#!/usr/bin/env python3
"""
MSME Idea Hackathon 6.0 — pitch deck builder.
Theme 4: Industry 4.0 & 5.0 | Category: Student | Evaluation-safe (anonymized).
Every technical claim is grounded in the team's IEEE paper (main.tex) + repo.
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

I = Inches
P = Pt
def RGB(h): return RGBColor.from_string(h)

# ---------------- palette ----------------
NAVY   = "0B1B33"; NAVY3 = "1C3A63"
INK    = "0F1B2D"; BODY = "334155"; MUTED = "6B7A90"
LINE   = "E2E8F0"; CARD = "FFFFFF"; PAGE = "F5F7FB"
BLUE   = "2563EB"; BLUE_DK = "1E3A8A"; BLUE_SOFT = "EAF1FE"
AMBER  = "E08A00"; AMBER_SOFT = "FDF1DD"
GREEN  = "0CA30C"; GREEN_DK = "0A7A0A"; GREEN_SOFT = "E7F6E8"
TEAL   = "0E7C86"; TEAL_SOFT = "E1F2F3"
RED    = "D03B3B"
WHITE  = "FFFFFF"

FONT = "Calibri"
ASSETS = os.path.join(os.path.dirname(__file__), "assets")
OUTDIR = "/home/manas/Desktop/major"
OUTFILE = os.path.join(OUTDIR, "MSME_Idea_Hackathon_6.0_LeanEdge_Deck.pptx")

prs = Presentation()
prs.slide_width = I(13.333)
prs.slide_height = I(7.5)
BLANK = prs.slide_layouts[6]

SW, SH = 13.333, 7.5
MX = 0.62            # left/right margin
CW = SW - 2 * MX     # content width 12.093

# ---------------- helpers ----------------
def slide(bg=PAGE):
    s = prs.slides.add_slide(BLANK)
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    r.shadow.inherit = False
    r.fill.solid(); r.fill.fore_color.rgb = RGB(bg)
    r.line.fill.background()
    return s

def box(s, x, y, w, h, fill=None, line=None, lw=1.0, rounded=False, radius=0.06):
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    shp = s.shapes.add_shape(kind, I(x), I(y), I(w), I(h))
    shp.shadow.inherit = False
    if fill is None: shp.fill.background()
    else: shp.fill.solid(); shp.fill.fore_color.rgb = RGB(fill)
    if line is None: shp.line.fill.background()
    else: shp.line.color.rgb = RGB(line); shp.line.width = P(lw)
    if rounded:
        try: shp.adjustments[0] = radius
        except Exception: pass
    shp.text_frame.word_wrap = True
    return shp

def text(s, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, wrap=True, shrink=False):
    """paras: list of dicts {runs:[{t,size,c,bold,italic,name}], align, space_after, space_before, line_spacing}"""
    tb = s.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = tb.text_frame; tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = 0; tf.margin_right = 0; tf.margin_top = 0; tf.margin_bottom = 0
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = p.get("align", PP_ALIGN.LEFT)
        para.space_after = P(p.get("space_after", 3))
        para.space_before = P(p.get("space_before", 0))
        if "line_spacing" in p: para.line_spacing = p["line_spacing"]
        for r in p["runs"]:
            run = para.add_run(); run.text = r["t"]
            f = run.font
            f.size = P(r.get("size", 14)); f.bold = r.get("bold", False)
            f.italic = r.get("italic", False); f.name = r.get("name", FONT)
            f.color.rgb = RGB(r.get("c", INK))
    return tb

def R(t, size=14, c=INK, bold=False, italic=False, name=FONT):
    return {"t": t, "size": size, "c": c, "bold": bold, "italic": italic, "name": name}

def para(runs, align=PP_ALIGN.LEFT, space_after=3, space_before=0, line_spacing=None):
    d = {"runs": runs, "align": align, "space_after": space_after, "space_before": space_before}
    if line_spacing: d["line_spacing"] = line_spacing
    return d

def header(s, kicker, title, accent=BLUE, title_size=29):
    text(s, MX, 0.44, CW, 0.3, [para([R(kicker.upper(), 12.5, accent, bold=True)])])
    text(s, MX, 0.74, CW, 0.95, [para([R(title, title_size, INK, bold=True)], line_spacing=1.0)])
    box(s, MX + 0.02, 1.66, 0.62, 0.055, fill=accent)

def footer(s, n):
    box(s, MX, 7.02, CW, 0.014, fill=LINE)
    text(s, MX, 7.07, 9.5, 0.3, [para([R("MSME IDEA HACKATHON 6.0   ·   THEME 4 — INDUSTRY 4.0 & 5.0", 8.5, MUTED)])])
    text(s, SW - MX - 3.0, 7.07, 3.0, 0.3,
         [para([R("LeanEdge  ·  ", 8.5, MUTED), R(f"{n:02d}", 8.5, BLUE, bold=True)], align=PP_ALIGN.RIGHT)])

def card(s, x, y, w, h, fill=CARD, line=LINE, top_accent=None, lw=1.0, radius=0.055):
    c = box(s, x, y, w, h, fill=fill, line=line, lw=lw, rounded=True, radius=radius)
    if top_accent:
        box(s, x, y, w, 0.09, fill=top_accent, rounded=True, radius=0.5)
    return c

def chip(s, x, y, w, h, label, fill, textc=WHITE, size=11, bold=True, radius=0.5):
    box(s, x, y, w, h, fill=fill, rounded=True, radius=radius)
    text(s, x, y, w, h, [para([R(label, size, textc, bold=bold)], align=PP_ALIGN.CENTER)],
         anchor=MSO_ANCHOR.MIDDLE)

def arrow(s, x, y, size=22, c=MUTED):
    text(s, x, y, 0.5, 0.5, [para([R("→", size, c, bold=True)], align=PP_ALIGN.CENTER)],
         anchor=MSO_ANCHOR.MIDDLE)

def grid(s, x, y, w, col_fracs, header_row, rows, row_h=0.6, header_h=0.56,
         header_fill=NAVY, aligns=None, sizes=(11, 11), header_size=11, highlight=None):
    n = len(col_fracs)
    aligns = aligns or (["l"] + ["c"] * (n - 1))
    xs = [x];
    for f in col_fracs: xs.append(xs[-1] + f * w)
    def cell_x(i): return xs[i]
    def cell_w(i): return col_fracs[i] * w
    A = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}
    # header
    box(s, x, y, w, header_h, fill=header_fill, rounded=True, radius=0.10)
    for i, hcell in enumerate(header_row):
        pad = 0.14 if aligns[i] == "l" else 0.0
        text(s, cell_x(i) + pad, y, cell_w(i) - 2 * pad, header_h,
             [para([R(hcell, header_size, WHITE, bold=True)], align=A[aligns[i]])],
             anchor=MSO_ANCHOR.MIDDLE)
    # body
    cy = y + header_h + 0.06
    for ri, row in enumerate(rows):
        hl = (highlight is not None and ri == highlight)
        rfill = BLUE_SOFT if hl else (CARD if ri % 2 == 0 else "F8FAFD")
        box(s, x, cy, w, row_h, fill=rfill, line=LINE, lw=0.75, rounded=True, radius=0.05)
        if hl:
            box(s, x, cy, 0.07, row_h, fill=BLUE, rounded=True, radius=0.5)
        for ci, cval in enumerate(row):
            if isinstance(cval, dict):
                t = cval.get("t", ""); cc = cval.get("c", INK if ci else INK)
                cb = cval.get("bold", (ci == 0)); csz = cval.get("size", sizes[0] if ci == 0 else sizes[1])
                ca = cval.get("align", aligns[ci])
            else:
                t = cval; cc = INK; cb = (ci == 0); csz = sizes[0] if ci == 0 else sizes[1]; ca = aligns[ci]
            pad = 0.14 if ca == "l" else 0.05
            text(s, cell_x(ci) + pad, cy, cell_w(ci) - 2 * pad, row_h,
                 [para([R(t, csz, cc, bold=cb)], align=A[ca], line_spacing=0.95)],
                 anchor=MSO_ANCHOR.MIDDLE)
        cy += row_h + 0.06
    return cy

def _png_size(path):
    import struct
    with open(path, "rb") as f:
        head = f.read(26)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">I", head[16:20])[0], struct.unpack(">I", head[20:24])[0]
    return 1740, 1020

def picture_card(s, path, x, y, w, h, pad=0.12):
    """white card + image scaled to contain (no distortion)."""
    card(s, x, y, w, h, fill=CARD, line=LINE)
    iw, ih = _png_size(path)
    aw, ah = w - 2 * pad, h - 2 * pad
    ar_img = iw / ih; ar_box = aw / ah
    if ar_img > ar_box:
        dw = aw; dh = aw / ar_img
    else:
        dh = ah; dw = ah * ar_img
    dx = x + (w - dw) / 2; dy = y + (h - dh) / 2
    s.shapes.add_picture(path, I(dx), I(dy), I(dw), I(dh))

# =========================================================================
# SLIDE 1 — TITLE
# =========================================================================
s = slide(NAVY)
box(s, 0, 0, SW, 0.16, fill=AMBER)                     # top hairline accent (saffron)
box(s, 0, SH - 0.16, SW, 0.16, fill=GREEN)             # bottom hairline accent (green)
# brand square motif
for i, cc in enumerate([AMBER, WHITE, GREEN, BLUE]):
    box(s, MX + i * 0.34, 1.05, 0.24, 0.24, fill=cc, rounded=True, radius=0.18)
text(s, MX, 1.5, CW, 0.4, [para([R("MSME IDEA HACKATHON 6.0", 14, "9FC0F0", bold=True),
                                 R("     FRONTIER TECHNOLOGY IN MSMEs", 14, "8AA0BE")])])
# theme pill
box(s, MX, 2.02, 3.55, 0.42, fill=NAVY3, rounded=True, radius=0.5)
text(s, MX, 2.02, 3.55, 0.42, [para([R("THEME 4  ·  INDUSTRY 4.0 & 5.0", 11.5, WHITE, bold=True)],
     align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
# hero name
text(s, MX, 2.62, CW, 1.15, [para([R("LeanEdge", 62, WHITE, bold=True),
                                   R("   working title", 15, "7E93B2", italic=True)])])
# tagline
text(s, MX, 3.92, 11.2, 1.2,
     [para([R("An indigenous, auto-tuning code optimizer that makes MSME smart-devices ", 22, "E8EEF7"),
            R("cheaper, greener, and truly Made-in-India.", 22, AMBER, bold=True)], line_spacing=1.05)])
text(s, MX, 5.35, 11.4, 0.5,
     [para([R("Proof-of-concept built & validated — seeking incubation + grant support to reach a hardware-tested prototype.",
              14.5, "AEBED4")])])
# bottom meta row
box(s, MX, 6.15, CW, 0.02, fill=NAVY3)
text(s, MX, 6.32, CW, 0.4,
     [para([R("Student idea submission", 12, WHITE, bold=True),
            R("     ·     Submitted via an approved Host Institute", 12, "8AA0BE"),
            R("     ·     Identity withheld on content slides per concept-note guidelines", 12, "8AA0BE")])])

# =========================================================================
# SLIDE 2 — THE OPPORTUNITY
# =========================================================================
s = slide()
header(s, "The Opportunity", "Every MSME is becoming a technology company", accent=AMBER)
text(s, MX, 1.9, CW, 0.7,
     [para([R("India's push for Industry 4.0 & 5.0 means small manufacturers are adding sensors, controllers, connectivity and edge-AI to their machines and products. That intelligence doesn't run on a PC — it runs as ",
              15, BODY),
            R("firmware on a low-cost microcontroller", 15, INK, bold=True),
            R(" inside the device.", 15, BODY)], line_spacing=1.12)])
cards = [
    (AMBER, AMBER_SOFT, "6 crore+", "MSMEs in India", "the backbone of the economy — now modernizing under Industry 4.0 / 5.0."),
    (TEAL, TEAL_SOFT, "Smart = embedded", "not a PC", "sensors, control loops and edge-AI ship as firmware on tiny, cheap microcontrollers."),
    (GREEN, GREEN_SOFT, "Retrofit-first", "no rip-and-replace", "MSMEs must upgrade existing machines affordably — cost and power decide adoption."),
]
cw = (CW - 2 * 0.35) / 3
for i, (ac, soft, big, mid, desc) in enumerate(cards):
    x = MX + i * (cw + 0.35)
    card(s, x, 2.95, cw, 2.85, fill=CARD, line=LINE, top_accent=ac)
    text(s, x + 0.28, 3.28, cw - 0.56, 1.0, [para([R(big, 27, ac, bold=True)])])
    text(s, x + 0.28, 3.95, cw - 0.56, 0.5, [para([R(mid, 15, INK, bold=True)])])
    text(s, x + 0.28, 4.4, cw - 0.56, 1.3, [para([R(desc, 13, BODY)], line_spacing=1.1)])
text(s, MX, 6.05, CW, 0.6,
     [para([R("The winners will be those who make embedded intelligence ", 15, BODY),
            R("cheap enough and efficient enough", 15, INK, bold=True),
            R(" for every small manufacturer to adopt.", 15, BODY)])])
footer(s, 2)

# =========================================================================
# SLIDE 3 — THE PROBLEM
# =========================================================================
s = slide()
header(s, "The Problem", "The code doesn't fit — and it wastes power", accent=RED)
text(s, MX, 1.9, CW, 0.55,
     [para([R("A microcontroller has ", 15, BODY), R("tiny memory", 15, INK, bold=True),
            R(" and a ", 15, BODY), R("tight power budget", 15, INK, bold=True),
            R(". When firmware is bloated or poorly optimized, MSMEs hit two hard walls and one dependency:", 15, BODY)],
           line_spacing=1.12)])
probs = [
    (RED, "01", "Higher cost per unit", "Bloated code overflows a cheap chip's flash memory, forcing a costlier, higher-memory microcontroller — a tax on every unit shipped. Many such chips are imported."),
    (AMBER, "02", "Wasted energy", "Every unnecessary instruction burns clock cycles — more power drawn, shorter battery life, and missed real-time deadlines. Bad for green goals and field reliability."),
    (NAVY3, "03", "Foreign, opaque tools", "The best optimizing toolchains are foreign and proprietary. Their one-size-fits-all -O2/-Os settings are opaque and are almost never tuned to the exact chip an MSME uses."),
]
cw = (CW - 2 * 0.35) / 3
for i, (ac, num, ttl, desc) in enumerate(probs):
    x = MX + i * (cw + 0.35)
    card(s, x, 2.7, cw, 2.9, fill=CARD, line=LINE)
    chip(s, x + 0.28, 2.98, 0.62, 0.62, num, ac, size=17, radius=0.28)
    text(s, x + 0.28, 3.8, cw - 0.56, 0.5, [para([R(ttl, 16.5, INK, bold=True)])])
    text(s, x + 0.28, 4.26, cw - 0.56, 1.3, [para([R(desc, 12.2, BODY)], line_spacing=1.14)])
box(s, MX, 5.72, CW, 0.86, fill="FBECEC", line="F3C9C9", rounded=True, radius=0.09)
text(s, MX + 0.3, 5.72, CW - 0.6, 0.86,
     [para([R("Result:  ", 14.5, RED, bold=True),
            R("modernization costs more, drains more energy, and depends on foreign tools — the opposite of affordable, Aatmanirbhar Industry 4.0.",
              14.5, "7A2E2E", bold=True)], line_spacing=1.05)], anchor=MSO_ANCHOR.MIDDLE)
footer(s, 3)

# =========================================================================
# SLIDE 4 — THE SOLUTION
# =========================================================================
s = slide()
header(s, "The Solution", "LeanEdge shrinks firmware automatically", accent=BLUE)
text(s, MX, 1.9, CW, 0.8,
     [para([R("Feed LeanEdge the device's code and its target chip. It automatically finds the ",
              15.5, BODY), R("optimization recipe", 15.5, INK, bold=True),
            R(" that produces the smallest, fastest, lowest-energy firmware — and ", 15.5, BODY),
            R("proves the program still behaves identically.", 15.5, INK, bold=True)], line_spacing=1.12)])
# pipeline
py = 3.05
box(s, MX, py, 3.1, 1.15, fill="EEF2F7", line=LINE, rounded=True, radius=0.09)
text(s, MX, py, 3.1, 1.15, [para([R("Your firmware", 15, INK, bold=True)], align=PP_ALIGN.CENTER),
     para([R("+ target chip", 12.5, MUTED)], align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
arrow(s, MX + 3.2, py + 0.33, 26, BLUE)
box(s, MX + 3.78, py - 0.12, 3.55, 1.4, fill=NAVY, rounded=True, radius=0.09)
text(s, MX + 3.78, py - 0.12, 3.55, 1.4, [para([R("LeanEdge", 18, WHITE, bold=True)], align=PP_ALIGN.CENTER),
     para([R("auto-tuning optimizer", 12.5, "9FC0F0")], align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
arrow(s, MX + 7.45, py + 0.33, 26, BLUE)
box(s, MX + 8.03, py, 4.06, 1.15, fill=GREEN_SOFT, line="BFE6C0", rounded=True, radius=0.09)
text(s, MX + 8.03, py, 4.06, 1.15, [para([R("Smaller · Faster · Verified", 15, GREEN_DK, bold=True)], align=PP_ALIGN.CENTER),
     para([R("drop-in optimized build", 12.5, "3E7A3E")], align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
# three value rows
vals = [
    (AMBER, "Smaller code", "fits a cheaper microcontroller → lower bill-of-materials on every unit, and import substitution."),
    (GREEN, "Fewer cycles", "less energy per operation, longer battery life, and real-time deadlines met → greener devices."),
    (TEAL, "Indigenous & transparent", "tuned per chip, verifiable, drop-in — no foreign black box, full local control and support."),
]
vy = 4.75
cwv = (CW - 2 * 0.3) / 3
for i, (ac, ttl, desc) in enumerate(vals):
    x = MX + i * (cwv + 0.3)
    box(s, x, vy, cwv, 1.65, fill=CARD, line=LINE, rounded=True, radius=0.07)
    box(s, x, vy, 0.09, 1.65, fill=ac, rounded=True, radius=0.5)
    text(s, x + 0.26, vy + 0.2, cwv - 0.45, 0.5, [para([R(ttl, 15.5, INK, bold=True)])])
    text(s, x + 0.26, vy + 0.66, cwv - 0.45, 0.95, [para([R(desc, 12.5, BODY)], line_spacing=1.1)])
footer(s, 4)

# =========================================================================
# SLIDE 5 — CORE INNOVATION (+ scatter)
# =========================================================================
s = slide()
header(s, "The Innovation  ·  Why it's hard", "Optimization order is everything", accent=BLUE)
lx, lw = MX, 4.85
text(s, lx, 1.95, lw, 4.6, [
    para([R("Compilers improve code by running ", 14, BODY), R("optimization passes", 14, INK, bold=True),
          R(". We built six industrial-grade ones:", 14, BODY)], line_spacing=1.12, space_after=8),
    para([R("CF · DCE · CSE · CP · SR · AS", 13.5, BLUE, bold=True)], space_after=12),
    para([R("But the ", 14, BODY), R("order", 14, INK, bold=True),
          R(" they run in changes the result dramatically — some orders unlock each other, others cancel out.",
            14, BODY)], line_spacing=1.12, space_after=10),
    para([R("With 6 passes there are ", 14, BODY), R("720 possible orders", 14, INK, bold=True),
          R(". On the same program, the best and worst orders differ by nearly ", 14, BODY),
          R("2×", 14, INK, bold=True), R(" in code size.", 14, BODY)], line_spacing=1.12, space_after=10),
    para([R("LeanEdge searches this space and ", 14, BODY),
          R("auto-selects the best recipe per program + chip", 14, GREEN_DK, bold=True),
          R(" — the opposite of a fixed -O2.", 14, BODY)], line_spacing=1.12),
])
box(s, lx, 6.15, lw, 0.72, fill=BLUE_SOFT, line="C7DBFB", rounded=True, radius=0.09)
text(s, lx + 0.22, 6.15, lw - 0.4, 0.72,
     [para([R("Grounded finding:  ", 12.5, BLUE_DK, bold=True),
            R("“Constant-Folding-first” consistently wins.", 12.5, INK, bold=True)], line_spacing=1.0)],
     anchor=MSO_ANCHOR.MIDDLE)
picture_card(s, os.path.join(ASSETS, "chart_tradeoff.png"), 5.75, 1.95, 6.96, 4.9)
footer(s, 5)

# =========================================================================
# SLIDE 6 — HOW IT WORKS (block diagram)
# =========================================================================
s = slide()
header(s, "How it works", "Inside LeanEdge: a modular, verifiable pipeline", accent=TEAL)
by = 2.5; bh = 1.5
def stage(x, w, title, sub, fill=CARD, line=LINE, tc=INK, sc=MUTED, h=bh, yy=by):
    box(s, x, yy, w, h, fill=fill, line=line, lw=1.0, rounded=True, radius=0.08)
    tlines = title.split("\n"); slines = sub.split("\n")
    ps = []
    for j, ln in enumerate(tlines):
        ps.append(para([R(ln, 13, tc, bold=True)], align=PP_ALIGN.CENTER,
                       space_after=(4 if j == len(tlines) - 1 else 0), line_spacing=0.95))
    for ln in slines:
        ps.append(para([R(ln, 10.5, sc)], align=PP_ALIGN.CENTER, space_after=0, line_spacing=0.95))
    text(s, x + 0.1, yy + 0.14, w - 0.2, h - 0.28, ps, anchor=MSO_ANCHOR.MIDDLE)
stage(MX, 1.7, "Source /\nfirmware", "C-subset today →\nreal C next")
arrow(s, MX + 1.72, by + 0.5, 20, MUTED)
stage(MX + 2.18, 1.95, "Front-end", "Lexer · Parser\n→ AST")
arrow(s, MX + 4.17, by + 0.5, 20, MUTED)
stage(MX + 4.63, 1.7, "IR", "Three-Address\nCode (3AC)")
arrow(s, MX + 6.37, by + 0.5, 20, BLUE)
# pass manager (highlighted, taller)
pmx, pmw, pmh = MX + 6.83, 3.35, 2.05
box(s, pmx, by - 0.28, pmw, pmh, fill=NAVY, rounded=True, radius=0.07)
text(s, pmx, by - 0.16, pmw, 0.5, [para([R("Auto-Tuning Pass Manager", 13.5, WHITE, bold=True)], align=PP_ALIGN.CENTER)])
passes = ["CF", "DCE", "CSE", "CP", "SR", "AS"]
pcw = (pmw - 0.3) / 6
for i, pnm in enumerate(passes):
    chip(s, pmx + 0.15 + i * pcw, by + 0.34, pcw - 0.07, 0.44, pnm, BLUE, size=10.5, radius=0.35)
text(s, pmx + 0.15, by + 0.9, pmw - 0.3, 0.9,
     [para([R("reorderable passes", 10.5, "9FC0F0")], align=PP_ALIGN.CENTER, space_after=2),
      para([R("explores 721 orderings,", 11, WHITE, bold=True)], align=PP_ALIGN.CENTER, space_after=0),
      para([R("picks the best per target", 11, WHITE, bold=True)], align=PP_ALIGN.CENTER)])
arrow(s, MX + 10.3, by + 0.5, 20, GREEN)
stage(MX + 10.75, 1.34, "Verified\noutput", "runs & checks\noutput = original", fill=GREEN_SOFT, line="BFE6C0", tc=GREEN_DK, sc="3E7A3E")
# bottom callout
box(s, MX, 5.35, CW, 1.15, fill=CARD, line=LINE, rounded=True, radius=0.06)
box(s, MX, 5.35, 0.09, 1.15, fill=GREEN, rounded=True, radius=0.5)
text(s, MX + 0.3, 5.35, CW - 0.6, 1.15,
     [para([R("Correct by construction.  ", 14, GREEN_DK, bold=True),
            R("Every candidate ordering is executed and checked against the original program's output — optimization never changes behaviour.",
              14, BODY)], space_after=5, line_spacing=1.08),
      para([R("Metrics collected:  ", 12.5, INK, bold=True),
            R("static code size  ·  estimated cycles (ARM Cortex-M cost model)  ·  dynamic instruction count.", 12.5, BODY)],
           line_spacing=1.05)], anchor=MSO_ANCHOR.MIDDLE)
footer(s, 6)

# =========================================================================
# SLIDE 7 — EVIDENCE (headline results)
# =========================================================================
s = slide()
header(s, "Evidence — it works", "Validated across a real benchmark suite", accent=GREEN)
stats = [
    (GREEN, "up to 60%", "smaller code", "(factorial benchmark)"),
    (BLUE, "up to 32%", "fewer cycles", "modeled on ARM Cortex-M"),
    (AMBER, "23.8%", "geometric-mean", "code-size cut, all programs"),
    (TEAL, "100%", "outputs verified", "identical to the original"),
]
sx, sw2 = MX, 4.5
sh2 = 1.06
for i, (ac, big, mid, sub) in enumerate(stats):
    y = 1.98 + i * (sh2 + 0.16)
    box(s, sx, y, sw2, sh2, fill=CARD, line=LINE, rounded=True, radius=0.08)
    box(s, sx, y, 0.09, sh2, fill=ac, rounded=True, radius=0.5)
    text(s, sx + 0.3, y, 2.2, sh2, [para([R(big, 30, ac, bold=True)])], anchor=MSO_ANCHOR.MIDDLE)
    text(s, sx + 2.5, y, sw2 - 2.7, sh2,
         [para([R(mid, 14.5, INK, bold=True)], space_after=1), para([R(sub, 11, MUTED)])],
         anchor=MSO_ANCHOR.MIDDLE)
picture_card(s, os.path.join(ASSETS, "chart_reduction_bars.png"), 5.5, 1.98, 7.21, 4.14)
text(s, 5.5, 6.2, 7.21, 0.6,
     [para([R("8 MiBench-adapted programs  ·  6 passes  ·  721 orderings each  ·  100+ automated tests.",
              11.5, MUTED)], align=PP_ALIGN.CENTER)])
footer(s, 7)

# =========================================================================
# SLIDE 8 — EVIDENCE DEPTH (heatmap)
# =========================================================================
s = slide()
header(s, "Evidence — why CF-first", "The winning recipe leads on every metric", accent=GREEN)
picture_card(s, os.path.join(ASSETS, "chart_reduction_heatmap.png"), MX, 1.98, 7.0, 4.7)
rx = 7.9; rw = SW - MX - rx
text(s, rx, 2.1, rw, 4.6, [
    para([R("One structure, learnable.", 16, INK, bold=True)], space_after=8),
    para([R("The best ordering (", 13.5, BODY), R("CF-first", 13.5, GREEN_DK, bold=True),
          R(") cuts code size 60%, cycles 32%, and dynamic work 35%.", 13.5, BODY)], line_spacing=1.12, space_after=10),
    para([R("The worst ordering (", 13.5, BODY), R("DCE-first", 13.5, INK, bold=True),
          R(") barely helps — 17.5% / 11% / 8.6%.", 13.5, BODY)], line_spacing=1.12, space_after=10),
    para([R("Same six passes. The ", 13.5, BODY), R("order", 13.5, INK, bold=True),
          R(" drives the win — and it's searchable, which is exactly what LeanEdge automates.", 13.5, BODY)],
         line_spacing=1.12),
])
box(s, rx, 5.85, rw, 0.82, fill=GREEN_SOFT, line="BFE6C0", rounded=True, radius=0.09)
text(s, rx + 0.22, 5.85, rw - 0.44, 0.82,
     [para([R("Grounded in exhaustive evaluation — not hand-tuned heuristics.", 12.5, GREEN_DK, bold=True)],
           line_spacing=1.02)], anchor=MSO_ANCHOR.MIDDLE)
footer(s, 8)

# =========================================================================
# SLIDE 9 — VALUE TO MSMEs (3 wins)
# =========================================================================
s = slide()
header(s, "Value to MSMEs", "Three wins that matter to every small manufacturer", accent=AMBER)
wins = [
    (AMBER, AMBER_SOFT, "Cheaper hardware", "Smaller firmware fits a lower-cost microcontroller → lower cost on every unit, plus import substitution of higher-end chips.", "Reduces cost of product & process"),
    (GREEN, GREEN_SOFT, "Greener devices", "Fewer cycles means less energy per operation and longer battery life — measurable savings across a fleet of devices.", "Clean & green energy initiative"),
    (TEAL, TEAL_SOFT, "Faster modernization", "Add intelligence to existing machines and products without replacing them — affordable, retrofit-first Industry 4.0 / 5.0.", "Scalable · improves quality of life"),
]
cw = (CW - 2 * 0.35) / 3
for i, (ac, soft, ttl, desc, doo) in enumerate(wins):
    x = MX + i * (cw + 0.35)
    card(s, x, 2.05, cw, 3.55, fill=CARD, line=LINE, top_accent=ac)
    chip(s, x + 0.3, 2.4, 0.66, 0.66, str(i + 1), ac, size=20, radius=0.3)
    text(s, x + 0.3, 3.25, cw - 0.6, 0.5, [para([R(ttl, 17, INK, bold=True)])])
    text(s, x + 0.3, 3.78, cw - 0.6, 1.5, [para([R(desc, 13, BODY)], line_spacing=1.14)])
    box(s, x + 0.3, 5.02, cw - 0.6, 0.42, fill=soft, rounded=True, radius=0.4)
    text(s, x + 0.3, 5.02, cw - 0.6, 0.42, [para([R("✓ " + doo, 10.5, ac, bold=True)], align=PP_ALIGN.CENTER)],
         anchor=MSO_ANCHOR.MIDDLE)
box(s, MX, 5.9, CW, 0.72, fill=NAVY, rounded=True, radius=0.08)
text(s, MX + 0.3, 5.9, CW - 0.6, 0.72,
     [para([R("Maps directly to the Hackathon Do's:   ", 12.5, "9FC0F0", bold=True),
            R("novel & useful  ·  scalable  ·  reduces cost  ·  clean & green  ·  improves quality of life.",
              12.5, WHITE, bold=True)], line_spacing=1.0)], anchor=MSO_ANCHOR.MIDDLE)
footer(s, 9)

# =========================================================================
# SLIDE 10 — DIFFERENTIATION (table)
# =========================================================================
s = slide()
header(s, "Why LeanEdge wins", "Auto-tuned per chip — not one-size-fits-all", accent=BLUE)
G = {"c": GREEN_DK, "bold": True}; Rd = {"c": RED, "bold": True}
def yes(t="✓ " + "yes"): return {"t": t, "c": GREEN_DK, "bold": True, "align": "c"}
def no(t="× no"): return {"t": t, "c": RED, "bold": True, "align": "c"}
def part(t): return {"t": t, "c": AMBER, "bold": True, "align": "c"}
head = ["Approach", "Tuned per program + chip", "Transparent & verifiable", "Lightweight", "Indigenous"]
rows = [
    ["Fixed pipelines (-O2 / -Os)", no("× one-size"), no(), yes(), no("× foreign")],
    ["Heavy ML auto-tuners", part("~ data-hungry"), no("× black-box"), no("× heavy"), no("× mostly foreign")],
    ["Manual expert tuning", part("~ expert-scarce"), part("~ slow"), no(), part("~")],
    [{"t": "LeanEdge", "c": BLUE, "bold": True}, yes("✓ auto"), yes(), yes(), yes("✓ made in India")],
]
grid(s, MX, 2.0, CW, [0.28, 0.20, 0.20, 0.16, 0.16], head, rows,
     row_h=0.82, header_h=0.9, aligns=["l", "c", "c", "c", "c"], sizes=(13, 12), header_size=11.5, highlight=3)
text(s, MX, 6.5, CW, 0.5,
     [para([R("Our moat is the ", 13, BODY), R("auto-tuning ordering layer", 13, INK, bold=True),
            R(" — transparent, chip-specific, and buildable on top of mature open toolchains.", 13, BODY)],
           align=PP_ALIGN.CENTER)])
footer(s, 10)

# =========================================================================
# SLIDE 11 — 8 INNOVATION PROCESSES (mandate)
# =========================================================================
s = slide()
header(s, "Innovation Mandate", "All eight innovation processes, embodied", accent=TEAL)
items = [
    ("Marketing & Branding", "“Smaller, greener firmware — Made in India”, with a one-click savings report."),
    ("Ideation", "A novel auto-tuning phase-order engine aimed at a real, under-served MSME pain."),
    ("Technology", "Six reorderable passes + a 721-ordering search + built-in output verification."),
    ("Co-creation", "Cost-models co-built with pilot MSMEs for their exact target chips."),
    ("Social Innovation", "Lowers the barrier for small manufacturers to adopt Industry 4.0; open-core."),
    ("Entrepreneurship", "Student-led; a clear PoC → venture path via incubation and revenue."),
    ("Open Innovation", "Open-core engine; collaborates with MCU vendors, HIs and the toolchain community."),
    ("Business-Model Innovation", "Optimization-as-a-service + target-pack licensing, not just selling software."),
]
cols, rowsn = 4, 2
gx, gy = MX, 2.0
gap = 0.3
cwi = (CW - (cols - 1) * gap) / cols
chi = 2.2
accents = [AMBER, BLUE, TEAL, GREEN]
for idx, (ttl, desc) in enumerate(items):
    r = idx // cols; c = idx % cols
    x = gx + c * (cwi + gap); y = gy + r * (chi + 0.3)
    ac = accents[c]
    card(s, x, y, cwi, chi, fill=CARD, line=LINE, radius=0.07)
    chip(s, x + 0.22, y + 0.24, 0.5, 0.5, str(idx + 1), ac, size=14, radius=0.3)
    text(s, x + 0.22, y + 0.86, cwi - 0.44, 0.62, [para([R(ttl, 12.5, INK, bold=True)], line_spacing=0.95)])
    text(s, x + 0.22, y + 1.42, cwi - 0.44, 0.72, [para([R(desc, 10.3, BODY)], line_spacing=1.06)])
footer(s, 11)

# =========================================================================
# SLIDE 12 — BUSINESS MODEL
# =========================================================================
s = slide()
header(s, "Business Model", "From proof-of-concept to a scalable venture", accent=BLUE)
streams = [
    (BLUE, "Optimization-as-a-Service", "Device makers upload firmware and get an optimized, verified build plus a savings report. Subscription / usage-based."),
    (TEAL, "Target-Pack Licensing", "Open-core engine; paid, per-chip cost-models and backends unlock specific microcontrollers."),
    (AMBER, "Design-house service", "Hands-on firmware size / power-reduction engagements for MSME product teams."),
    (GREEN, "IP Licensing", "Embed the auto-tuning core into MCU-vendor SDKs and IDE toolchains."),
]
cw = (CW - 0.35) / 2
ch = 1.72
for i, (ac, ttl, desc) in enumerate(streams):
    r = i // 2; c = i % 2
    x = MX + c * (cw + 0.35); y = 2.0 + r * (ch + 0.28)
    card(s, x, y, cw, ch, fill=CARD, line=LINE, radius=0.07)
    box(s, x, y, 0.09, ch, fill=ac, rounded=True, radius=0.5)
    chip(s, x + 0.28, y + 0.28, 0.5, 0.5, str(i + 1), ac, size=14, radius=0.3)
    text(s, x + 0.95, y + 0.3, cw - 1.2, 0.5, [para([R(ttl, 15.5, INK, bold=True)])])
    text(s, x + 0.95, y + 0.78, cw - 1.2, 0.85, [para([R(desc, 12.3, BODY)], line_spacing=1.1)])
box(s, MX, 5.85, CW, 0.75, fill=BLUE_SOFT, line="C7DBFB", rounded=True, radius=0.08)
text(s, MX + 0.3, 5.85, CW - 0.6, 0.75,
     [para([R("Open-core drives trust & adoption; ", 13, INK, bold=True),
            R("service, target-packs and licensing capture value. Software → near-zero marginal cost → highly scalable.",
              13, BODY)], line_spacing=1.05)], anchor=MSO_ANCHOR.MIDDLE)
footer(s, 12)

# =========================================================================
# SLIDE 13 — GO TO MARKET
# =========================================================================
s = slide()
header(s, "Go-to-Market", "Land with pilots, scale through the ecosystem", accent=AMBER)
phases = [
    (GREEN, "Phase 1 — Land", "0–12 months", ["2–3 MSME embedded-device pilots", "energy monitors · EV components · IoT sensors", "prove cost + energy wins on real hardware", "via the Host-Institute network"]),
    (BLUE, "Phase 2 — Expand", "12–24 months", ["grow the set of supported chips", "integrate as a pass-order auto-tuner on LLVM / GCC", "launch the cloud optimization service", "publish measured case studies"]),
    (AMBER, "Phase 3 — Scale", "24 months +", ["open-core community + paid target-packs", "MCU-vendor SDK / IDE licensing", "export to global embedded & MSME markets", "replicate across sectors at near-zero cost"]),
]
cw = (CW - 2 * 0.35) / 3
for i, (ac, ttl, tf, pts) in enumerate(phases):
    x = MX + i * (cw + 0.35)
    card(s, x, 2.0, cw, 4.15, fill=CARD, line=LINE, top_accent=ac)
    text(s, x + 0.28, 2.32, cw - 0.56, 0.4, [para([R(ttl, 16, INK, bold=True)])])
    box(s, x + 0.28, 2.78, 1.7, 0.36, fill=ac, rounded=True, radius=0.5)
    text(s, x + 0.28, 2.78, 1.7, 0.36, [para([R(tf, 11, WHITE, bold=True)], align=PP_ALIGN.CENTER)],
         anchor=MSO_ANCHOR.MIDDLE)
    yy = 3.35
    for pt in pts:
        text(s, x + 0.28, yy, cw - 0.5, 0.6,
             [para([R("•  ", 12, ac, bold=True), R(pt, 12, BODY)], line_spacing=1.02)])
        yy += 0.66
footer(s, 13)

# =========================================================================
# SLIDE 14 — FEASIBILITY
# =========================================================================
s = slide()
header(s, "Feasibility — de-risked", "We're not starting from zero", accent=GREEN)
# left: already built
lx, lw2 = MX, 5.85
box(s, lx, 2.0, lw2, 3.7, fill=GREEN_SOFT, line="BFE6C0", rounded=True, radius=0.06)
text(s, lx + 0.3, 2.22, lw2 - 0.6, 0.5, [para([R("✓  Already built  ", 15.5, GREEN_DK, bold=True),
     R("(proof-of-concept)", 12.5, "3E7A3E")])])
built = ["Full compiler pipeline: lexer → parser → IR → optimizer → interpreter",
         "6 reorderable optimization passes (CF, DCE, CSE, CP, SR, AS)",
         "Auto-search over all 721 orderings",
         "Static + dynamic metrics + ARM Cortex-M cost model",
         "Output-equivalence verifier (correctness guaranteed)",
         "8-program MiBench-adapted benchmark suite · 100+ tests",
         "Interactive learning / explore web tool"]
yy = 2.78
for b in built:
    text(s, lx + 0.3, yy, lw2 - 0.6, 0.42, [para([R("✓  ", 12, GREEN_DK, bold=True), R(b, 11.8, "20402A")], line_spacing=1.0)])
    yy += 0.4
# right: to build
rx = lx + lw2 + 0.35; rw2 = SW - MX - rx
box(s, rx, 2.0, rw2, 3.7, fill=CARD, line=LINE, rounded=True, radius=0.06)
text(s, rx + 0.3, 2.22, rw2 - 0.6, 0.5, [para([R("→  The grant + incubation builds  ", 14.5, BLUE, bold=True)])])
tob = ["Extend front-end from C-subset to real embedded C / integrate with LLVM · GCC",
       "Real microcontroller backends + on-hardware energy measurement",
       "ML / heuristic-guided ordering to scale beyond exhaustive search",
       "2–3 MSME field pilots with measured cost + energy savings"]
yy = 2.82
for b in tob:
    text(s, rx + 0.3, yy, rw2 - 0.6, 0.6, [para([R("→  ", 12, BLUE, bold=True), R(b, 12, BODY)], line_spacing=1.05)])
    yy += 0.68
box(s, MX, 5.9, CW, 0.7, fill="F3F1E7", line="E4D9A8", rounded=True, radius=0.08)
text(s, MX + 0.3, 5.9, CW - 0.6, 0.7,
     [para([R("Honest maturity:  ", 12.5, "7A6410", bold=True),
            R("today a working PoC on a C-subset language with a modeled cost estimate; next, a hardware-validated prototype on production toolchains.",
              12.5, "5C4E12")], line_spacing=1.02)], anchor=MSO_ANCHOR.MIDDLE)
footer(s, 14)

# =========================================================================
# SLIDE 15 — ROADMAP & USE OF FUNDS
# =========================================================================
s = slide()
header(s, "12-month plan & use of funds", "A clear path from PoC to hardware-validated prototype", accent=BLUE, title_size=27)
# left: milestones
lx, lw2 = MX, 6.6
ms = [
    ("Q1 · M1–3", "Port front-end toward real embedded C / LLVM-GCC integration; build MCU test benches + power-measurement rig."),
    ("Q2 · M4–6", "Auto-tuning search on real targets; first on-hardware size + energy validation; select pilot partners."),
    ("Q3 · M7–9", "ML / heuristic-guided ordering (scale the search); pilot #1 integration + field data."),
    ("Q4 · M10–12", "Pilots #2–3 + measured case studies; cloud-service alpha; IP filing + documentation."),
]
yy = 2.05
for i, (q, d) in enumerate(ms):
    chip(s, lx, yy + 0.04, 1.35, 0.5, q, NAVY, size=11, radius=0.3)
    text(s, lx + 1.55, yy, lw2 - 1.55, 0.72, [para([R(d, 12.3, BODY)], line_spacing=1.08)])
    if i < 3:
        box(s, lx + 0.66, yy + 0.56, 0.02, 0.4, fill=LINE)
    yy += 0.98
# right: budget
rx = lx + lw2 + 0.3; rw2 = SW - MX - rx
box(s, rx, 2.0, rw2, 4.55, fill=NAVY, rounded=True, radius=0.05)
text(s, rx + 0.3, 2.22, rw2 - 0.6, 0.5, [para([R("Use of ₹15 lakh", 16, WHITE, bold=True)], space_after=1),
     para([R("indicative allocation", 10.5, "9FC0F0", italic=True)])])
bud = [("Engineering / stipends", "₹6.0L", 6.0, AMBER),
       ("Hardware & test benches", "₹3.0L", 3.0, TEAL),
       ("Pilot integration & field", "₹2.5L", 2.5, GREEN),
       ("Compute, cloud & licenses", "₹1.5L", 1.5, BLUE),
       ("IP, docs & contingency", "₹2.0L", 2.0, "9FC0F0")]
yy = 3.15
for name, amt, val, ac in bud:
    text(s, rx + 0.3, yy, rw2 - 1.2, 0.3, [para([R(name, 11.5, "DDE6F2")])])
    text(s, rx + rw2 - 1.0, yy, 0.7, 0.3, [para([R(amt, 12, WHITE, bold=True)], align=PP_ALIGN.RIGHT)])
    box(s, rx + 0.3, yy + 0.3, (rw2 - 0.6), 0.11, fill=NAVY3, rounded=True, radius=0.5)
    box(s, rx + 0.3, yy + 0.3, (rw2 - 0.6) * (val / 6.0), 0.11, fill=ac, rounded=True, radius=0.5)
    yy += 0.58
box(s, rx + 0.3, yy + 0.02, rw2 - 0.6, 0.02, fill=NAVY3)
text(s, rx + 0.3, yy + 0.12, rw2 - 0.6, 0.35,
     [para([R("Total   ", 13, "9FC0F0", bold=True), R("₹15.0 lakh", 15, WHITE, bold=True)], align=PP_ALIGN.RIGHT)])
footer(s, 15)

# =========================================================================
# SLIDE 16 — RISKS & MITIGATION
# =========================================================================
s = slide()
header(s, "Risks & mitigation", "What could go wrong — and how we've de-risked it", accent=RED, title_size=27)
head = ["Risk", "Mitigation"]
rows = [
    ["Toy language today (real-C gap)", "Integrate with mature LLVM / GCC front-ends; our IP is the auto-tuning ordering layer, not the parser."],
    ["Search explodes as passes grow", "ML / heuristic-guided ordering + pruning + per-target caching (planned in the grant phase)."],
    ["Energy savings not yet on hardware", "Prototype phase adds on-hardware power measurement to validate the modeled estimate."],
    ["Slow MSME adoption of new tools", "Deliver as a drop-in service with a one-page savings report; land through HI-led pilots."],
    ["Incumbents (-Oz, commercial tools)", "Differentiate on transparency, per-target auto-tuning, indigenous cost + local support."],
]
grid(s, MX, 2.0, CW, [0.4, 0.6], head, rows, row_h=0.78, header_h=0.56,
     aligns=["l", "l"], sizes=(12.5, 12), header_size=12)
footer(s, 16)

# =========================================================================
# SLIDE 17 — TEAM & EXECUTION (anonymized)
# =========================================================================
s = slide()
header(s, "Team & execution", "A student team that already ships", accent=TEAL)
text(s, MX, 1.95, CW, 0.75,
     [para([R("A final-year Computer Science & Engineering student team, guided by a ", 15, BODY),
            R("faculty mentor in compilers & systems", 15, INK, bold=True),
            R(". The incubatee and mentor are distinct persons, per Hackathon rules.", 15, BODY)], line_spacing=1.12)])
roles = [(BLUE, "Compiler engineering"), (TEAL, "Benchmarking & data"),
         (AMBER, "Systems / embedded"), (GREEN, "Product & GTM")]
cw = (CW - 3 * 0.3) / 4
for i, (ac, r) in enumerate(roles):
    x = MX + i * (cw + 0.3)
    box(s, x, 2.95, cw, 0.95, fill=CARD, line=LINE, rounded=True, radius=0.09)
    box(s, x, 2.95, cw, 0.09, fill=ac, rounded=True, radius=0.5)
    text(s, x + 0.15, 2.95, cw - 0.3, 0.95, [para([R(r, 12.5, INK, bold=True)], align=PP_ALIGN.CENTER, line_spacing=1.0)],
         anchor=MSO_ANCHOR.MIDDLE)
box(s, MX, 4.2, CW, 1.15, fill=GREEN_SOFT, line="BFE6C0", rounded=True, radius=0.06)
text(s, MX + 0.3, 4.2, CW - 0.6, 1.15,
     [para([R("Proof of execution:  ", 14, GREEN_DK, bold=True),
            R("this team has already shipped a complete proof-of-concept — a working compiler with six passes, an auto-search over 721 orderings, 100+ automated tests, and an interactive web tool. ",
              14, "20402A"),
            R("We build, measure, and validate.", 14, GREEN_DK, bold=True)], line_spacing=1.12)],
     anchor=MSO_ANCHOR.MIDDLE)
box(s, MX, 5.55, CW, 0.95, fill=CARD, line=LINE, rounded=True, radius=0.06)
text(s, MX + 0.3, 5.55, CW - 0.6, 0.95,
     [para([R("Commitment:  ", 13, INK, bold=True),
            R("as student applicants, we will continue and complete development beyond graduation (per Hackathon requirement).",
              13, BODY)], space_after=4, line_spacing=1.05),
      para([R("Names & institution are withheld on content slides per concept-note guidelines; full details are in the application form.",
              11, MUTED, italic=True)])], anchor=MSO_ANCHOR.MIDDLE)
footer(s, 17)

# =========================================================================
# SLIDE 18 — ALIGNMENT
# =========================================================================
s = slide()
header(s, "Strategic alignment", "Squarely aligned with India's frontier-tech mission", accent=AMBER)
lx, lw2 = MX, 5.9
box(s, lx, 2.05, lw2, 4.2, fill=NAVY, rounded=True, radius=0.05)
text(s, lx + 0.3, 2.3, lw2 - 0.6, 0.5, [para([R("National missions", 16, WHITE, bold=True)])])
miss = [("Viksit Bharat @2047", "a future-ready, self-reliant MSME sector"),
        ("Aatmanirbhar Bharat", "an indigenous toolchain; import substitution of chips & software"),
        ("Make in India", "cheaper, more capable Made-in-India devices"),
        ("Digital India · Industry 4.0/5.0", "affordable embedded intelligence for small manufacturers")]
yy = 2.95
for t, d in miss:
    text(s, lx + 0.3, yy, lw2 - 0.6, 0.72,
         [para([R(t, 13.5, AMBER, bold=True)], space_after=1),
          para([R(d, 11.5, "C6D3E5")], line_spacing=1.0)])
    yy += 0.82
rx = lx + lw2 + 0.35; rw2 = SW - MX - rx
box(s, rx, 2.05, rw2, 4.2, fill=CARD, line=LINE, rounded=True, radius=0.05)
text(s, rx + 0.3, 2.3, rw2 - 0.6, 0.5, [para([R("Hackathon Do's — all met", 16, GREEN_DK, bold=True)])])
dos = ["Novel & useful to society", "Scalable", "Reduces cost of product / process",
       "Improves quality of life & convenience", "Clean & green energy initiative"]
yy = 3.05
for d in dos:
    box(s, rx + 0.3, yy, 0.34, 0.34, fill=GREEN_SOFT, rounded=True, radius=0.3)
    text(s, rx + 0.3, yy, 0.34, 0.34, [para([R("✓", 13, GREEN_DK, bold=True)], align=PP_ALIGN.CENTER)],
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, rx + 0.8, yy, rw2 - 1.1, 0.4, [para([R(d, 13.5, INK, bold=True)])], anchor=MSO_ANCHOR.MIDDLE)
    yy += 0.6
footer(s, 18)

# =========================================================================
# SLIDE 19 — THE ASK
# =========================================================================
s = slide()
header(s, "The Ask", "What we're seeking", accent=BLUE)
box(s, MX, 2.05, CW, 1.5, fill=NAVY, rounded=True, radius=0.05)
text(s, MX + 0.4, 2.05, CW - 0.8, 1.5,
     [para([R("Up to ₹15 lakh grant + incubation", 27, WHITE, bold=True)], space_after=4),
      para([R("mentorship, lab & test-bench access — via an approved Host Institute.", 15, "9FC0F0")])],
     anchor=MSO_ANCHOR.MIDDLE)
unlocks = [(GREEN, "Hardware-validated prototype", "in 12 months, on production toolchains"),
           (BLUE, "2–3 MSME pilots", "with measured cost + energy savings"),
           (AMBER, "Launch-ready toolchain", "an indigenous optimization product")]
cw = (CW - 2 * 0.35) / 3
for i, (ac, ttl, sub) in enumerate(unlocks):
    x = MX + i * (cw + 0.35)
    card(s, x, 3.85, cw, 1.7, fill=CARD, line=LINE, top_accent=ac)
    text(s, x + 0.28, 4.15, cw - 0.56, 0.7, [para([R(ttl, 15.5, INK, bold=True)], line_spacing=1.0)])
    text(s, x + 0.28, 4.85, cw - 0.56, 0.6, [para([R(sub, 12, BODY)], line_spacing=1.05)])
box(s, MX, 5.85, CW, 0.75, fill=BLUE_SOFT, line="C7DBFB", rounded=True, radius=0.08)
text(s, MX + 0.3, 5.85, CW - 0.6, 0.75,
     [para([R("A small, catalytic grant that de-risks a ", 13.5, INK, bold=True),
            R("scalable, import-substituting deep-tech venture", 13.5, BLUE_DK, bold=True),
            R(" for India's MSMEs.", 13.5, INK, bold=True)], line_spacing=1.03)], anchor=MSO_ANCHOR.MIDDLE)
footer(s, 19)

# =========================================================================
# SLIDE 20 — VISION / CLOSING
# =========================================================================
s = slide(NAVY)
box(s, 0, 0, SW, 0.16, fill=AMBER)
box(s, 0, SH - 0.16, SW, 0.16, fill=GREEN)
for i, cc in enumerate([AMBER, WHITE, GREEN, BLUE]):
    box(s, MX + i * 0.34, 1.35, 0.24, 0.24, fill=cc, rounded=True, radius=0.18)
text(s, MX, 2.25, 12.0, 2.2,
     [para([R("Optimize the code — and every MSME device gets ", 34, WHITE, bold=True),
            R("cheaper, greener, and truly Made in India.", 34, AMBER, bold=True)], line_spacing=1.08)])
text(s, MX, 4.85, 11.6, 0.8,
     [para([R("LeanEdge — auto-tuned embedded intelligence for a self-reliant, future-ready MSME sector.",
              17, "C6D3E5")], line_spacing=1.1)])
box(s, MX, 6.0, 5.4, 0.02, fill=NAVY3)
text(s, MX, 6.15, 8.0, 0.5, [para([R("MSME Idea Hackathon 6.0   ·   Theme 4 — Industry 4.0 & 5.0", 12.5, "8AA0BE")])])
text(s, SW - MX - 3.0, 6.05, 3.0, 0.6, [para([R("Thank you.", 20, WHITE, bold=True)], align=PP_ALIGN.RIGHT)])

# =========================================================================
# SLIDE 21 — APPENDIX A: detailed results + methodology
# =========================================================================
s = slide()
header(s, "Appendix A", "Detailed results & measurement methodology", accent=MUTED, title_size=27)
# left table
head = ["Optimization sequence (factorial)", "Code size", "Est. cycles"]
rows = [
    [{"t": "Baseline (no optimization)", "c": MUTED, "bold": True}, {"t": "40", "c": MUTED, "bold": True, "align": "c"}, {"t": "81", "c": MUTED, "bold": True, "align": "c"}],
    [{"t": "CF → CSE → CP → DCE → SR", "c": GREEN_DK, "bold": True}, {"t": "16", "c": GREEN_DK, "bold": True, "align": "c"}, {"t": "55", "c": GREEN_DK, "bold": True, "align": "c"}],
    ["CSE → CP → CF → DCE → SR", {"t": "18", "align": "c"}, {"t": "57", "align": "c"}],
    ["CP → CF → DCE → CSE → SR", {"t": "19", "align": "c"}, {"t": "58", "align": "c"}],
    ["CF → DCE → CSE → CP → SR", {"t": "21", "align": "c"}, {"t": "60", "align": "c"}],
    ["CP → DCE → CF → CSE → SR", {"t": "22", "align": "c"}, {"t": "61", "align": "c"}],
    ["DCE → CF → CSE → CP → SR", {"t": "33", "align": "c"}, {"t": "72", "align": "c"}],
]
grid(s, MX, 2.0, 6.9, [0.6, 0.2, 0.2], head, rows, row_h=0.5, header_h=0.5,
     aligns=["l", "c", "c"], sizes=(11.5, 11.5), header_size=10.5)
# right methodology
rx = MX + 6.9 + 0.35; rw2 = SW - MX - rx
box(s, rx, 2.0, rw2, 4.55, fill=CARD, line=LINE, rounded=True, radius=0.05)
text(s, rx + 0.3, 2.22, rw2 - 0.6, 0.4, [para([R("Cycle cost model  (ARM Cortex-M-class)", 13.5, INK, bold=True)])])
costs = [("MUL", "3"), ("DIV / MOD", "12"), ("Branch (jump)", "2"), ("CALL", "5"),
         ("RETURN", "3"), ("PRINT / I/O", "10"), ("ALU · COPY · LOAD · PARAM", "1"), ("Labels / structural markers", "0")]
yy = 2.72
for nm, w in costs:
    text(s, rx + 0.3, yy, rw2 - 1.1, 0.3, [para([R(nm, 11.3, BODY)])])
    text(s, rx + rw2 - 0.85, yy, 0.55, 0.3, [para([R(w, 11.3, INK, bold=True)], align=PP_ALIGN.RIGHT)])
    yy += 0.315
text(s, rx + 0.3, yy + 0.08, rw2 - 0.6, 1.0,
     [para([R("Static code size excludes labels & structural markers. Dynamic instruction count comes from a direct IR interpreter. Every ordering is validated for output-equivalence against the baseline.",
              10.3, MUTED, italic=True)], line_spacing=1.08)])
footer(s, 21)

# =========================================================================
# SLIDE 22 — APPENDIX B: pass interaction
# =========================================================================
s = slide()
header(s, "Appendix B", "Pairwise pass interactions", accent=MUTED, title_size=27)
picture_card(s, os.path.join(ASSETS, "chart_pass_interaction.png"), MX, 1.98, 7.4, 4.7)
rx = MX + 7.4 + 0.35; rw2 = SW - MX - rx
text(s, rx, 2.2, rw2, 4.3, [
    para([R("Reading the map", 15, INK, bold=True)], space_after=8),
    para([R("Each cell shows the code-size change when the ", 13, BODY),
          R("row-pass runs before the column-pass", 13, INK, bold=True),
          R(".", 13, BODY)], line_spacing=1.12, space_after=10),
    para([R("Blue = running A before B ", 13, BODY), R("reduces", 13, GREEN_DK, bold=True),
          R(" size (good). Red = it increases size.", 13, BODY)], line_spacing=1.12, space_after=10),
    para([R("Running ", 13, BODY), R("Constant-Folding or Copy-Propagation before Dead-Code-Elimination",
            13, INK, bold=True),
          R(" gives the largest reductions (-11, -10) — the empirical basis for “CF-first”.",
            13, BODY)], line_spacing=1.12),
])
footer(s, 22)

prs.save(OUTFILE)
print("saved:", OUTFILE)
print("slides:", len(prs.slides._sldIdLst))
