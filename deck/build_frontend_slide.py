"""Build a real PPTX slide showing how the project works with the frontend.
ASCII-safe — no Unicode characters in the source to avoid lxml surrogate errors.
Writes: D:\\IBM Project\\Open_Production\\deck\\how-it-works-with-frontend.pptx
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# Design tokens (match the dark navy palette in landing/index.html)
BG       = RGBColor(0x0A, 0x0E, 0x1A)
PANEL    = RGBColor(0x11, 0x18, 0x2C)
PANEL2   = RGBColor(0x18, 0x22, 0x36)
INK      = RGBColor(0xE8, 0xEC, 0xF4)
INK_DIM  = RGBColor(0x9A, 0xA3, 0xB6)
INK_DIMM = RGBColor(0x5D, 0x65, 0x77)
ACCENT   = RGBColor(0x7A, 0xC9, 0xF2)
ACCENT2  = RGBColor(0xB8, 0x9C, 0xFF)
ACCENT3  = RGBColor(0xFF, 0xB3, 0x6B)
GREEN    = RGBColor(0x86, 0xE0, 0x9C)
RED      = RGBColor(0xFF, 0x8A, 0x8A)
GREY     = RGBColor(0x33, 0x3D, 0x52)
GRID     = RGBColor(0x1F, 0x29, 0x3D)
BORDER   = RGBColor(0x1E, 0x27, 0x38)

FONT_BODY = "Inter"
FONT_MONO = "JetBrains Mono"
FONT_DISPLAY = "Inter"

# ASCII glyphs only — avoid emoji to keep the slide ASCII-safe
LOTUS = "[OP]"
INPUT_PREFIX = ">"
ARROW_RIGHT = "->"
ARROW_DOWN = "v"
CHECK = "[ok]"
DONE = "[done]"
RUNNING = "[..]"
QUEUED = "[  ]"
FROZEN = "[!!]"
PENDING = "[  ]"
MONEY = "[$]"
LIVE = "[live]"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
SLIDE_W = prs.slide_width
SLIDE_H = prs.slide_height

def add_bg(slide, color=BG):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    bg.line.fill.background()
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.shadow.inherit = False

def add_text(slide, x, y, w, h, text, *, font=FONT_BODY, size=14, bold=False,
             color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0; tf.margin_right = 0
    tf.margin_top = 0; tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = text
    r.font.name = font; r.font.size = Pt(size)
    r.font.bold = bold; r.font.italic = italic
    r.font.color.rgb = color
    return tb

def add_rect(slide, x, y, w, h, *, fill=PANEL, line=None, line_w=0.5, rounded=False):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    s = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if line:
        s.line.color.rgb = line; s.line.width = Pt(line_w)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    return s

def add_pill(slide, x, y, w, h, text, *, fill=PANEL, color=INK, size=10):
    pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    pill.fill.solid(); pill.fill.fore_color.rgb = fill
    pill.line.color.rgb = color; pill.line.width = Pt(0.75)
    pill.shadow.inherit = False
    tf = pill.text_frame
    tf.margin_left = Inches(0.1); tf.margin_right = Inches(0.1)
    tf.margin_top = 0; tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text
    r.font.name = FONT_MONO; r.font.size = Pt(size); r.font.color.rgb = color
    return pill

def chrome(slide, slide_num, total, section):
    add_text(slide, 0.5, 0.35, 8, 0.3, "OPEN PRODUCTION", font=FONT_MONO, size=10, color=ACCENT, bold=True)
    add_text(slide, 11.5, 0.35, 1.4, 0.3, f"{slide_num:02d} / {total:02d}", font=FONT_MONO, size=10, color=INK_DIM, align=PP_ALIGN.RIGHT)
    sep = slide.shapes.add_connector(1, Inches(0.5), Inches(0.7), Inches(12.83), Inches(0.7))
    sep.line.color.rgb = GRID; sep.line.width = Pt(0.5)
    add_text(slide, 0.5, 7.05, 6, 0.3, section, font=FONT_MONO, size=9, color=INK_DIM)
    add_text(slide, 7.5, 7.05, 5.33, 0.3, "deck v0.1 - Boris", font=FONT_MONO, size=9, color=INK_DIM, align=PP_ALIGN.RIGHT)

# ============================================================================
# Slide 1 - The complete flow
# ============================================================================
s = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(s); chrome(s, 1, 3, "01 - HOW IT WORKS")

add_text(s, 0.5, 0.95, 12, 0.5, "How Open Production works end-to-end",
         font=FONT_DISPLAY, size=28, bold=True, color=INK)
add_text(s, 0.5, 1.45, 12, 0.35,
         "Two surfaces, one kernel. The user lands on the homepage; the kernel runs the demo.",
         font=FONT_BODY, size=13, color=INK_DIM, italic=True)

# Row 1: User
add_text(s, 0.5, 2.1, 12, 0.25, "USER", font=FONT_MONO, size=10, color=ACCENT, bold=True)
add_rect(s, 0.5, 2.4, 12.33, 0.9, fill=PANEL, line=ACCENT, line_w=1.0, rounded=True)
add_text(s, 0.7, 2.55, 5, 0.3, "Persona", font=FONT_MONO, size=10, color=INK_DIM)
add_text(s, 0.7, 2.85, 11.5, 0.4,
         "Student writing a thesis - journalist drafting a piece - educator building materials - creator exploring angles",
         font=FONT_BODY, size=13, color=INK)
for i, p in enumerate(["thesis deadline", "needs citations", "exploring angles", "audit trail"]):
    add_pill(s, 0.7 + i * 2.95, 3.15, 2.75, 0.32, p, color=ACCENT2, fill=PANEL2, size=10)

# Down arrow
down_arrow = slide_sentinel = s.shapes.add_connector(1, Inches(6.65), Inches(3.45), Inches(6.65), Inches(3.78))
down_arrow.line.color.rgb = ACCENT; down_arrow.line.width = Pt(2)

# Row 2: Frontend + CLI
add_text(s, 0.5, 3.92, 12, 0.25, "FRONTEND  +  CLI", font=FONT_MONO, size=10, color=ACCENT, bold=True)

# Frontend panel
add_rect(s, 0.5, 4.2, 6.0, 2.55, fill=PANEL, line=ACCENT2, line_w=1.0, rounded=True)
add_text(s, 0.7, 4.32, 5.5, 0.3, "Landing page", font=FONT_MONO, size=10, color=ACCENT2, bold=True)
add_text(s, 0.7, 4.6, 5.5, 0.3, "D:\\openclaw\\creative-platform-design\\landing\\index.html",
         font=FONT_MONO, size=9, color=INK_DIM)
add_text(s, 0.7, 4.95, 5.5, 0.4, "Hero with prompt input -> 5 primitives grid -> 3-step flow",
         font=FONT_BODY, size=11, color=INK)
add_text(s, 0.7, 5.45, 5.5, 0.4, "Live-studio mockup with animated pulse indicator", font=FONT_BODY, size=11, color=INK)
add_text(s, 0.7, 5.95, 5.5, 0.4, "Composition DAG with SVG edges", font=FONT_BODY, size=11, color=INK)
add_text(s, 0.7, 6.45, 5.5, 0.3, "Drop in a browser - no build, no deps.", font=FONT_MONO, size=9, color=INK_DIM, italic=True)

# CLI panel
add_rect(s, 6.83, 4.2, 6.0, 2.55, fill=PANEL, line=ACCENT3, line_w=1.0, rounded=True)
add_text(s, 7.03, 4.32, 5.5, 0.3, "Demo CLI", font=FONT_MONO, size=10, color=ACCENT3, bold=True)
add_text(s, 7.03, 4.6, 5.5, 0.3, "D:\\IBM Project\\Open_Production\\scripts\\run_demo.py",
         font=FONT_MONO, size=9, color=INK_DIM)
add_text(s, 7.03, 4.95, 5.5, 0.4, "$ make demo    ->    3 angles - 5 audit entries - JSONL",
         font=FONT_MONO, size=11, color=INK)
add_text(s, 7.03, 5.45, 5.5, 0.4, "51/51 tests passing - audit_trail.jsonl written",
         font=FONT_BODY, size=11, color=INK)
add_text(s, 7.03, 5.95, 5.5, 0.4, "Works offline - MockLLMClient, no API keys",
         font=FONT_BODY, size=11, color=INK)
add_text(s, 7.03, 6.45, 5.5, 0.3, "Auditable end-to-end - every gate decision logged",
         font=FONT_MONO, size=9, color=INK_DIM, italic=True)

# Footnote
add_rect(s, 0.5, 6.85, 12.33, 0.3, fill=PANEL2)
add_text(s, 0.7, 6.88, 11.5, 0.25,
         "Below both surfaces: the medium-blind kernel (5 primitives - 3 fail-closed gates - reconciliation loop) - same code for both.",
         font=FONT_MONO, size=10, color=INK_DIM)

# ============================================================================
# Slide 2 - Landing page mockup
# ============================================================================
s = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(s); chrome(s, 2, 3, "02 - LANDING PAGE MOCKUP")

add_rect(s, 0.5, 0.95, 12.33, 6.0, fill=RGBColor(0x05, 0x08, 0x14), line=GRID, line_w=1.0, rounded=True)
add_rect(s, 0.5, 0.95, 12.33, 0.45, fill=RGBColor(0x14, 0x18, 0x28), line=GRID)

# Browser dots
for i, c in enumerate([RGBColor(0xFF, 0x6B, 0x6B), RGBColor(0xFF, 0xB8, 0x6C), GREEN]):
    dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.65 + i * 0.2), Inches(1.10), Inches(0.12), Inches(0.12))
    dot.fill.solid(); dot.fill.fore_color.rgb = c
    dot.line.fill.background(); dot.shadow.inherit = False
add_text(s, 1.4, 1.07, 7, 0.25, "openproduction.studio", font=FONT_MONO, size=10, color=INK_DIM)
add_text(s, 9.7, 1.07, 3, 0.25, "Docs   Pricing   GitHub", font=FONT_BODY, size=10, color=INK_DIM, align=PP_ALIGN.RIGHT)

add_text(s, 0.85, 1.7, 11, 0.4, f"{LOTUS}  OPEN PRODUCTION PLATFORM",
         font=FONT_MONO, size=11, color=ACCENT, bold=True)
add_text(s, 0.85, 2.2, 11, 1.5,
         "From intent to artifact,\nfor any medium.",
         font=FONT_DISPLAY, size=40, bold=True, color=INK)

add_rect(s, 0.85, 4.4, 11.6, 0.95, fill=RGBColor(0x10, 0x16, 0x26), line=ACCENT, line_w=1.0, rounded=True)
add_text(s, 1.05, 4.55, 10, 0.4,
         "Make a 60-second explainer about how neural networks learn...",
         font=FONT_BODY, size=13, color=INK_DIM, italic=True)
add_rect(s, 10.55, 4.55, 1.8, 0.65, fill=ACCENT, rounded=True)
add_text(s, 10.55, 4.7, 1.8, 0.4, "> Produce",
         font=FONT_DISPLAY, size=14, bold=True, color=BG, align=PP_ALIGN.CENTER)

# Domain pills (ASCII labels only)
pillars = [("video", "[v]"),
           ("research", "[r]"),
           ("code", "[<>]"),
           ("design", "[d]"),
           ("audio", "[a]")]
for i, (name, icon) in enumerate(pillars):
    add_pill(s, 0.85 + i * 2.35, 5.65, 2.15, 0.4, f"{icon}  {name}",
             color=INK_DIM, fill=PANEL, size=11)

add_text(s, 0.85, 6.45, 11.6, 0.3,
         "(full page: 5 primitives -> 3-step flow -> live-studio mockup -> composition DAG -> CTA)",
         font=FONT_MONO, size=10, color=INK_DIMM, italic=True, align=PP_ALIGN.CENTER)

# ============================================================================
# Slide 3 - Live studio dashboard
# ============================================================================
s = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(s); chrome(s, 3, 3, "03 - LIVE STUDIO DASHBOARD")

add_text(s, 0.5, 0.95, 12, 0.4, "The screen judges see in the 3-min demo video",
         font=FONT_DISPLAY, size=22, bold=True, color=INK)
add_text(s, 0.5, 1.4, 12, 0.3,
         "Captured from `make demo`. Every event, every dollar, every gate decision on the wall.",
         font=FONT_BODY, size=12, color=INK_DIM, italic=True)

add_rect(s, 0.5, 1.95, 12.33, 0.5, fill=PANEL, line=GRID, rounded=True)
add_text(s, 0.7, 2.0, 6, 0.4, ">  neural-networks-explainer-60s",
         font=FONT_MONO, size=12, color=ACCENT, bold=True)
add_text(s, 7.5, 2.0, 5, 0.4, "60s explainer - 12 scenes - est. $0.42",
         font=FONT_BODY, size=10, color=INK_DIM, align=PP_ALIGN.RIGHT)

stages = [
    ("research",     DONE,    GREEN),
    ("script",       DONE,    GREEN),
    ("voice",        RUNNING, ACCENT),
    ("storyboard",   QUEUED,  INK_DIM),
    ("assets",       QUEUED,  INK_DIM),
    ("compose",      FROZEN,  GREY),
    ("render",       PENDING, INK_DIM),
    ("evaluate",     PENDING, INK_DIM),
]
stage_w = 1.45
gap = 0.05
xstart = 0.5
y = 2.7
for i, (name, status, color) in enumerate(stages):
    x = xstart + i * (stage_w + gap)
    add_rect(s, x, y, stage_w, 0.55, fill=PANEL, line=color, line_w=0.75, rounded=True)
    add_text(s, x, y + 0.05, stage_w, 0.25, name,
             font=FONT_MONO, size=10, color=INK, align=PP_ALIGN.CENTER)
    add_text(s, x, y + 0.28, stage_w, 0.25, status,
             font=FONT_MONO, size=9, color=color, bold=True, align=PP_ALIGN.CENTER)

add_text(s, 0.5, 3.45, 4, 0.3, "STORYBOARD - 12 SCENES",
         font=FONT_MONO, size=10, color=ACCENT, bold=True)
scenes = [
    ("01", "Hook",     "$0.02",  GREEN),
    ("02", "Problem",  "$0.03",  GREEN),
    ("03", "Analogy",  "$0.04",  ACCENT),
    ("04", "Neuron",   "$0.04",  ACCENT),
    ("05", "Layer",    "$0.04",  ACCENT),
    ("06", "Training", "$0.05",  INK_DIM),
    ("07", "Gradient", "$0.05",  INK_DIM),
    ("08", "Backprop", "$0.04",  INK_DIM),
    ("09", "Eval",     "$0.04",  INK_DIM),
    ("10", "Limits",   "$0.04",  INK_DIM),
    ("11", "Future",   "$0.04",  INK_DIM),
    ("12", "Outro",    "$0.03",  INK_DIM),
]
sw = 0.99
for i, (n, t, c, color) in enumerate(scenes):
    x = 0.5 + i * (sw + 0.02)
    y2 = 3.8
    add_rect(s, x, y2, sw, 1.4, fill=PANEL, line=color, line_w=0.5, rounded=True)
    add_text(s, x, y2 + 0.05, sw, 0.22, n, font=FONT_MONO, size=8,
             color=INK_DIM, align=PP_ALIGN.CENTER, bold=True)
    add_rect(s, x + 0.1, y2 + 0.32, sw - 0.2, 0.55, fill=RGBColor(0x18, 0x22, 0x36))
    add_text(s, x, y2 + 0.92, sw, 0.22, t, font=FONT_BODY, size=9,
             color=INK, align=PP_ALIGN.CENTER)
    add_text(s, x, y2 + 1.13, sw, 0.22, c, font=FONT_MONO, size=8,
             color=color, align=PP_ALIGN.CENTER)

add_rect(s, 0.5, 5.4, 12.33, 1.4, fill=PANEL, line=GRID, rounded=True)
add_text(s, 0.7, 5.5, 4, 0.3, "LIVE EVENTS",
         font=FONT_MONO, size=10, color=ACCENT, bold=True)

events = [
    ("17:31:04", CHECK,   "voice-03.tts.wav committed",        GREEN),
    ("17:31:09", RUNNING, "storyboard/03 generating asset",    ACCENT),
    ("17:31:12", CHECK,   "provider selected: gpt-image-1.5",  INK_DIM),
    ("17:31:14", MONEY,   "spent $0.07 / est $0.42",           ACCENT3),
    ("17:31:18", QUEUED,  "scene-04 queued for render",        INK_DIM),
]
for i, (t, glyph, msg, color) in enumerate(events):
    y3 = 5.85 + i * 0.18
    add_text(s, 0.7, y3, 0.9, 0.2, t, font=FONT_MONO, size=9, color=INK_DIM)
    add_text(s, 1.6, y3, 0.5, 0.2, glyph, font=FONT_MONO, size=9, color=color, bold=True)
    add_text(s, 2.1, y3, 10.5, 0.2, msg, font=FONT_MONO, size=9, color=INK)

out = r"D:\IBM Project\Open_Production\deck\how-it-works-with-frontend.pptx"
prs.save(out)
print(f"Saved: {out}")
print(f"Slides: {len(prs.slides)}")
