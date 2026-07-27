"""
Build the Open Production vision deck (5 slides).
Output: D:/IBM Project/Open_Production/deck/vision/open-production-vision.pptx

Slides:
 1. Title — The production process is the product
 2. Today — What every AI video tool gets wrong
 3. Architecture — Kernel + verticals + 5 differentiators
 4. Principles — The 5 Laws + 3 axioms + the NEVER list
 5. Roadmap — After the prototype: what ships next
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

# ------------------------------------------------------------------ palette

BG_DEEP    = RGBColor(0x0A, 0x0C, 0x10)
BG_PANEL   = RGBColor(0x16, 0x1B, 0x22)
BG_PANEL2  = RGBColor(0x0D, 0x11, 0x17)
STROKE     = RGBColor(0x2A, 0x35, 0x48)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
TEXT_MUTED = RGBColor(0xA8, 0xB3, 0xC5)
TEXT_DIM   = RGBColor(0x6B, 0x77, 0x87)
IBM_BLUE   = RGBColor(0x0F, 0x62, 0xFE)
CYAN       = RGBColor(0x82, 0xCF, 0xFF)
AMBER      = RGBColor(0xF1, 0xC2, 0x1B)
MAGENTA    = RGBColor(0xEE, 0x53, 0x96)
GREEN      = RGBColor(0x24, 0xA1, 0x48)

# ------------------------------------------------------------------ helpers

def add_rect(slide, x, y, w, h, fill, line=None, line_w=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        if line_w is not None:
            shape.line.width = line_w
    shape.shadow.inherit = False
    return shape

def add_text(slide, x, y, w, h, text, *, size=14, color=WHITE,
             bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
             font="Calibri", italic=False, line_spacing=None):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.margin_left = Inches(0)
    tf.margin_right = Inches(0)
    tf.margin_top = Inches(0)
    tf.margin_bottom = Inches(0)
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    lines = text.split("\n") if isinstance(text, str) else text
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if line_spacing is not None:
            p.line_spacing = line_spacing
        r = p.add_run()
        r.text = line
        r.font.name = font
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color
    return tb

def add_header(slide, title, eyebrow="OPEN PRODUCTION"):
    # Eyebrow tag
    add_rect(slide, Inches(0.5), Inches(0.4), Inches(1.6), Inches(0.22), IBM_BLUE)
    add_text(slide, Inches(0.5), Inches(0.4), Inches(1.6), Inches(0.22),
             eyebrow, size=9, color=WHITE, bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, Inches(2.2), Inches(0.4), Inches(7), Inches(0.22),
             "·  VISION DECK", size=9, color=CYAN, bold=True)
    # Title
    add_text(slide, Inches(0.5), Inches(0.8), Inches(12.33), Inches(0.7),
             title, size=30, color=WHITE, bold=True)
    # Divider
    add_rect(slide, Inches(0.5), Inches(1.55), Inches(12.33), Emu(8000), STROKE)

def add_footer(slide, page_num):
    add_text(slide, Inches(0.5), Inches(7.05), Inches(8), Inches(0.25),
             "Open Production · Production-Document-First Creative Studio",
             size=9, color=TEXT_DIM)
    add_text(slide, Inches(12.33), Inches(7.05), Inches(0.5), Inches(0.25),
             str(page_num), size=9, color=TEXT_DIM, align=PP_ALIGN.RIGHT)

def slide_add_shape_compat(slide, shape_type, x, y, w, h):
    """Thin wrapper so we can call from many places without 'shapes' noise."""
    return slide.shapes.add_shape(shape_type, x, y, w, h)

def add_bullet_list(slide, x, y, w, h, items, *, size=14,
                    color=TEXT_MUTED, bullet_color=CYAN):
    """items: list of (text, bold?) tuples; rendered with cyan square bullets."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0)
    tf.margin_top = Inches(0)
    tf.margin_bottom = Inches(0)
    for i, (text, bold) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(6)
        # Bullet glyph
        r0 = p.add_run()
        r0.text = "▪  "
        r0.font.name = "Calibri"
        r0.font.size = Pt(size)
        r0.font.bold = True
        r0.font.color.rgb = bullet_color
        # Text
        r1 = p.add_run()
        r1.text = text
        r1.font.name = "Calibri"
        r1.font.size = Pt(size)
        r1.font.bold = bold
        r1.font.color.rgb = WHITE if bold else color

def blank_slide(prs, bg=BG_DEEP):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    # Background
    bg_rect = add_rect(slide, Inches(0), Inches(0), Inches(13.33), Inches(7.5), bg)
    # Subtle grid via a few thin lines
    return slide

# ------------------------------------------------------------------ build

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)

# ====================================================================
# SLIDE 1 — TITLE
# ====================================================================
s = blank_slide(prs)

# Big eyebrow tag
add_rect(s, Inches(0.5), Inches(0.5), Inches(2.0), Inches(0.32), IBM_BLUE)
add_text(s, Inches(0.5), Inches(0.5), Inches(2.0), Inches(0.32),
         "OPEN PRODUCTION", size=12, color=WHITE, bold=True,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
add_text(s, Inches(2.6), Inches(0.5), Inches(8), Inches(0.32),
         "·  VISION DECK — WHERE THIS GOES", size=12, color=CYAN, bold=True)

# Hero statement
add_text(s, Inches(0.5), Inches(2.6), Inches(12.33), Inches(1.2),
         "The production process is the product.",
         size=58, color=WHITE, bold=True)
add_text(s, Inches(0.5), Inches(3.7), Inches(12.33), Inches(0.6),
         "AI-native creative studio where every decision is permanent, inspectable, and reversible.",
         size=20, color=TEXT_MUTED)

# Three pillars row
pillar_y = Inches(4.7)
pillar_w = Inches(4.0)
pillar_h = Inches(1.4)
gap = Inches(0.16)

pillars = [
    ("PROCESS",        "The video is a byproduct of a captured, replayable production state.",
     "The production is the artifact, not the file.", CYAN),
    ("PRODUCTION-DOC", "Every decision lives in an immutable event log. Diffable. Shareable.",
     "Audit trail is the source of truth.", CYAN),
    ("PLUG-IN SURFACE","Medium-blind kernel. Video. Research writing. Whatever ships next.",
     "Built once, extends infinitely.", CYAN),
]

for i, (head, line, sub, accent) in enumerate(pillars):
    x = Inches(0.5) + (pillar_w + gap) * i
    add_rect(s, x, pillar_y, pillar_w, pillar_h, BG_PANEL, line=STROKE, line_w=Pt(0.5))
    add_rect(s, x, pillar_y, Inches(0.06), pillar_h, accent)
    add_text(s, x + Inches(0.25), pillar_y + Inches(0.15), pillar_w - Inches(0.4), Inches(0.3),
             head, size=11, color=accent, bold=True)
    add_text(s, x + Inches(0.25), pillar_y + Inches(0.45), pillar_w - Inches(0.4), Inches(0.5),
             line, size=14, color=WHITE, bold=True, line_spacing=1.15)
    add_text(s, x + Inches(0.25), pillar_y + Inches(0.95), pillar_w - Inches(0.4), Inches(0.4),
             sub, size=11, color=TEXT_MUTED)

# Footer line
add_text(s, Inches(0.5), Inches(7.05), Inches(12.33), Inches(0.25),
         "5 slides · vision · architecture · principles · roadmap",
         size=9, color=TEXT_DIM)

# ====================================================================
# SLIDE 2 — TODAY: WHAT EVERY AI VIDEO TOOL GETS WRONG
# ====================================================================
s = blank_slide(prs)
add_header(s, "Every AI video tool treats generation as the product.")

# Left column: the pattern (60%)
add_text(s, Inches(0.5), Inches(1.85), Inches(7.5), Inches(0.35),
         "THE PATTERN THEY ALL SHARE", size=11, color=CYAN, bold=True)

# Loop diagram
loop_y = Inches(2.35)
loop_w = Inches(3.6)
loop_h = Inches(1.5)

add_rect(s, Inches(0.5), loop_y, loop_w, loop_h, BG_PANEL, line=STROKE, line_w=Pt(0.5))
add_text(s, Inches(0.5), loop_y + Inches(0.15), loop_w, Inches(0.3),
         "Prompt  →  Generate  →  Evaluate  →  Re-prompt",
         size=14, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
add_text(s, Inches(0.5), loop_y + Inches(0.55), loop_w, Inches(0.3),
         "a feedback loop, not a production workflow",
         size=11, color=TEXT_MUTED, italic=True, align=PP_ALIGN.CENTER)

# Reality column
add_text(s, Inches(4.4), Inches(1.85), Inches(8.5), Inches(0.35),
         "WHAT REAL PRODUCTION ACTUALLY IS", size=11, color=CYAN, bold=True)

real_stages = [
    ("1. Intent",        "what do we want to say?"),
    ("2. References",    "what does it look and feel like?"),
    ("3. Structure",     "how is it organized?"),
    ("4. Execution",     "how is it made?"),
    ("5. Evaluation",    "does it say what we wanted?"),
    ("6. Iteration",     "what changes?"),
    ("7. Publication",   "who sees it?"),
]

ry = Inches(2.35)
for i, (stage, desc) in enumerate(real_stages):
    row_y = ry + Inches(0.32) * i
    add_rect(s, Inches(4.4), row_y, Inches(1.7), Inches(0.28), BG_PANEL2, line=STROKE, line_w=Pt(0.5))
    add_text(s, Inches(4.4), row_y, Inches(1.7), Inches(0.28),
             stage, size=11, color=CYAN, bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, Inches(6.2), row_y + Inches(0.02), Inches(6.7), Inches(0.28),
             desc, size=11, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)

# Bottom: bold claim
add_rect(s, Inches(0.5), Inches(5.6), Inches(12.33), Inches(1.2), BG_PANEL, line=STROKE, line_w=Pt(0.5))
add_rect(s, Inches(0.5), Inches(5.6), Inches(0.08), Inches(1.2), MAGENTA)
add_text(s, Inches(0.85), Inches(5.75), Inches(11.5), Inches(0.4),
         "Most products model only step 4 (execution). Some add step 5 (evaluation).",
         size=15, color=WHITE, bold=True)
add_text(s, Inches(0.85), Inches(6.15), Inches(11.5), Inches(0.4),
         "None model steps 1–3 as first-class citizens. That's the gap we ship into.",
         size=15, color=CYAN, bold=True)

add_footer(s, 2)

# ====================================================================
# SLIDE 3 — ARCHITECTURE
# ====================================================================
s = blank_slide(prs)

# We'll embed the hero SVG here as a full-slide image
from pptx.util import Inches as IN

# Try to embed the SVG by converting via PIL/cairosvg if available; otherwise
# draw a faithful PPT-native mockup of the same layout.
def draw_native_architecture(slide):
    # background
    add_rect(slide, IN(0), IN(0), IN(13.33), IN(7.5), BG_DEEP)

    # title strip
    add_rect(slide, IN(0.4), IN(0.3), IN(2.0), IN(0.28), IBM_BLUE)
    add_text(slide, IN(0.4), IN(0.3), IN(2.0), IN(0.28),
             "OPEN PRODUCTION", size=10, color=WHITE, bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, IN(2.5), IN(0.3), IN(6), IN(0.28),
             "·  SYSTEM ARCHITECTURE", size=10, color=CYAN, bold=True)

    # Left vertical panel: VIDEO
    lx, ly, lw, lh = IN(0.4), IN(0.8), IN(4.0), IN(6.0)
    add_rect(slide, lx, ly, lw, lh, BG_PANEL, line=STROKE, line_w=Pt(0.5))
    add_rect(slide, lx, ly, lw, IN(0.5), IBM_BLUE)
    add_text(slide, lx + IN(0.2), ly + IN(0.1), IN(3), IN(0.3),
             "VIDEO PRODUCTION", size=13, color=WHITE, bold=True)
    add_text(slide, lx + IN(3.0), ly + IN(0.1), IN(0.9), IN(0.3),
             "26 stages", size=9, color=CYAN, bold=True, align=PP_ALIGN.RIGHT)

    # Pipeline rows
    row_y = ly + IN(0.7)
    stages1 = ["Idea", "Script", "Shot plan", "Generate"]
    stages2 = ["Edit", "Color", "Music", "Publish"]
    chip_w, chip_h, gap_x = IN(0.78), IN(0.32), IN(0.10)
    row_x = lx + IN(0.2)

    def draw_chip(x, y, label):
        add_rect(slide, x, y, chip_w, chip_h, BG_PANEL2, line=STROKE, line_w=Pt(0.5))
        add_text(slide, x, y, chip_w, chip_h, label, size=9, color=WHITE,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    def draw_arrow(x, y, w):
        add_rect(slide, x, y + IN(0.14), w - IN(0.03), IN(0.04), CYAN)

    def draw_lock(x, y):
        lk = slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, IN(0.16), IN(0.16))
        lk.fill.solid(); lk.fill.fore_color.rgb = AMBER
        lk.line.fill.background()
        lk.shadow.inherit = False

    for i, s_ in enumerate(stages1):
        x = row_x + (chip_w + gap_x) * i
        draw_chip(x, row_y, s_)
        if i < len(stages1) - 1:
            draw_arrow(x + chip_w, row_y, gap_x)
            draw_lock(x + chip_w + IN(0.005), row_y + IN(0.08))

    row_y2 = row_y + IN(0.55)
    for i, s_ in enumerate(stages2):
        x = row_x + (chip_w + gap_x) * i
        draw_chip(x, row_y2, s_)
        if i < len(stages2) - 1:
            draw_arrow(x + chip_w, row_y2, gap_x)
            draw_lock(x + chip_w + IN(0.005), row_y2 + IN(0.08))

    add_text(slide, lx + IN(0.2), row_y2 + IN(0.5), IN(3.6), IN(0.3),
             "+ 18 more stages, all gated", size=9, color=TEXT_DIM,
             italic=True, align=PP_ALIGN.CENTER)

    # Agents
    agt_y = row_y2 + IN(0.9)
    add_text(slide, lx + IN(0.2), agt_y, IN(3.6), IN(0.25),
             "AGENTS", size=9, color=CYAN, bold=True)
    agt_y += IN(0.3)
    agents = [("Creative Dir.", IBM_BLUE), ("Shot Designer", IBM_BLUE),
              ("Editor", IBM_BLUE), ("Reviewer", MAGENTA), ("Publisher", IBM_BLUE)]
    ax = lx + IN(0.2)
    for name, color in agents:
        w = IN(0.7 + len(name) * 0.05)
        add_rect(slide, ax, agt_y, w, IN(0.3), BG_PANEL2, line=color, line_w=Pt(0.75))
        add_text(slide, ax, agt_y, w, IN(0.3), name, size=8, color=WHITE,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        ax += w + IN(0.06)

    # Highlight box
    hl_y = agt_y + IN(0.5)
    add_rect(slide, lx + IN(0.2), hl_y, IN(3.6), IN(1.6), BG_PANEL2, line=STROKE, line_w=Pt(0.5))
    add_text(slide, lx + IN(0.3), hl_y + IN(0.1), IN(3.4), IN(0.25),
             "DIFFERENTIATOR", size=9, color=AMBER, bold=True)
    add_text(slide, lx + IN(0.3), hl_y + IN(0.35), IN(3.4), IN(0.3),
             "Consistency Contract", size=14, color=WHITE, bold=True)
    add_text(slide, lx + IN(0.3), hl_y + IN(0.7), IN(3.4), IN(0.85),
             "Every character and environment has a formal spec —\nvisual anchors, required/prohibited attributes,\nvariance tolerance. Gated by Reviewer.",
             size=10, color=TEXT_MUTED, line_spacing=1.2)

    # ===== CENTER: KERNEL =====
    cx, cy = IN(6.0), IN(3.5)
    add_text(slide, IN(4.6), IN(0.95), IN(4.4), IN(0.25),
             "AUDIT TRAIL · EVENT LOG · STATE MACHINE",
             size=9, color=CYAN, bold=True, align=PP_ALIGN.CENTER)
    # Outer ring
    ring = slide.shapes.add_shape(MSO_SHAPE.OVAL,
                                  cx - IN(1.7), cy - IN(1.7),
                                  IN(3.4), IN(3.4))
    ring.fill.background()
    ring.line.color.rgb = STROKE
    ring.line.width = Pt(0.5)
    ring.line.dash_style = 7  # dash
    ring.shadow.inherit = False

    # Pentagon of primitives
    import math
    R = IN(1.0)
    primitives = ["Source", "Transform", "Composition", "Evaluation", "Intent"]
    nodes = []
    for i, name in enumerate(primitives):
        # start at top (-90°), go clockwise
        a = math.radians(-90 + i * 72)
        nx = cx + R * math.cos(a)
        ny = cy + R * math.sin(a)
        nodes.append((nx, ny, name))

    # Connection lines
    for i in range(5):
        x1, y1, _ = nodes[i]
        x2, y2, _ = nodes[(i+1) % 5]
        line = slide.shapes.add_connector(1, x1, y1, x2, y2)
        line.line.color.rgb = CYAN
        line.line.width = Pt(0.5)
        line.shadow.inherit = False

    # Nodes
    for nx, ny, name in nodes:
        node = slide.shapes.add_shape(MSO_SHAPE.OVAL,
                                      nx - IN(0.28), ny - IN(0.28),
                                      IN(0.56), IN(0.56))
        node.fill.solid(); node.fill.fore_color.rgb = IBM_BLUE
        node.line.color.rgb = CYAN
        node.line.width = Pt(0.75)
        node.shadow.inherit = False
        add_text(slide, nx - IN(0.5), ny - IN(0.13), IN(1.0), IN(0.25),
                 name, size=9, color=WHITE, bold=True,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # Kernel core
    core = slide.shapes.add_shape(MSO_SHAPE.OVAL,
                                  cx - IN(0.55), cy - IN(0.55),
                                  IN(1.1), IN(1.1))
    core.fill.solid(); core.fill.fore_color.rgb = BG_DEEP
    core.line.color.rgb = WHITE
    core.line.width = Pt(1.5)
    core.shadow.inherit = False
    add_text(slide, cx - IN(0.5), cy - IN(0.32), IN(1.0), IN(0.25),
             "KERNEL", size=10, color=WHITE, bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, cx - IN(0.5), cy - IN(0.1), IN(1.0), IN(0.2),
             "five primitives", size=8, color=CYAN,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, cx - IN(0.5), cy + IN(0.08), IN(1.0), IN(0.2),
             "medium-blind", size=8, color=TEXT_DIM,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # Plug-in surface arrows
    for (sx, ex, y) in [(IN(4.5), IN(4.05), cy), (cx + IN(1.7), cx + IN(2.15), cy)]:
        line = slide.shapes.add_connector(1, sx, y, ex, y)
        line.line.color.rgb = CYAN
        line.line.width = Pt(1.0)
        line.line.dash_style = 7
        line.shadow.inherit = False

    add_text(slide, IN(3.6), cy - IN(0.35), IN(1.0), IN(0.25),
             "PLUG-IN", size=8, color=CYAN, bold=True,
             align=PP_ALIGN.CENTER)
    add_text(slide, IN(3.6), cy - IN(0.1), IN(1.0), IN(0.25),
             "SURFACE", size=8, color=CYAN, bold=True,
             align=PP_ALIGN.CENTER)
    add_text(slide, IN(9.7), cy - IN(0.35), IN(1.0), IN(0.25),
             "PLUG-IN", size=8, color=CYAN, bold=True,
             align=PP_ALIGN.CENTER)
    add_text(slide, IN(9.7), cy - IN(0.1), IN(1.0), IN(0.25),
             "SURFACE", size=8, color=CYAN, bold=True,
             align=PP_ALIGN.CENTER)

    # ===== RIGHT VERTICAL: RESEARCH =====
    rx, ry, rw, rh = IN(8.93), IN(0.8), IN(4.0), IN(6.0)
    add_rect(slide, rx, ry, rw, rh, BG_PANEL, line=STROKE, line_w=Pt(0.5))
    add_rect(slide, rx, ry, rw, IN(0.5), IBM_BLUE)
    add_text(slide, rx + IN(0.2), ry + IN(0.1), IN(3), IN(0.3),
             "RESEARCH WRITING", size=13, color=WHITE, bold=True)
    add_text(slide, rx + IN(3.0), ry + IN(0.1), IN(0.9), IN(0.3),
             "7 stages", size=9, color=CYAN, bold=True, align=PP_ALIGN.RIGHT)

    rrow_y = ry + IN(0.7)
    rstages1 = ["Frame", "Outline", "Draft", "Critique"]
    rstages2 = ["Revise", "Verify", "Publish"]
    rrow_x = rx + IN(0.2)

    for i, s_ in enumerate(rstages1):
        x = rrow_x + (chip_w + gap_x) * i
        draw_chip(x, rrow_y, s_)
        if i < len(rstages1) - 1:
            draw_arrow(x + chip_w, rrow_y, gap_x)
            draw_lock(x + chip_w + IN(0.005), rrow_y + IN(0.08))

    rrow_y2 = rrow_y + IN(0.55)
    for i, s_ in enumerate(rstages2):
        x = rrow_x + (chip_w + gap_x) * i
        draw_chip(x, rrow_y2, s_)
        if i < len(rstages2) - 1:
            draw_arrow(x + chip_w, rrow_y2, gap_x)
            draw_lock(x + chip_w + IN(0.005), rrow_y2 + IN(0.08))
    # close the last gap with arrow
    last_x = rrow_x + (chip_w + gap_x) * len(rstages2)
    if last_x + chip_w < rx + rw - IN(0.2):
        pass

    ragt_y = rrow_y2 + IN(0.5)
    add_text(slide, rrow_x, ragt_y, IN(3.6), IN(0.25),
             "AGENTS", size=9, color=CYAN, bold=True)
    ragt_y += IN(0.3)
    ragents = [("Reframer", IBM_BLUE), ("Outliner", IBM_BLUE),
               ("Drafter", IBM_BLUE), ("Critic", MAGENTA), ("Publisher", IBM_BLUE)]
    ax = rrow_x
    for name, color in ragents:
        w = IN(0.55 + len(name) * 0.05)
        add_rect(slide, ax, ragt_y, w, IN(0.3), BG_PANEL2, line=color, line_w=Pt(0.75))
        add_text(slide, ax, ragt_y, w, IN(0.3), name, size=8, color=WHITE,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        ax += w + IN(0.06)

    # Highlight
    rhl_y = ragt_y + IN(0.5)
    add_rect(slide, rrow_x, rhl_y, IN(3.6), IN(1.6), BG_PANEL2, line=STROKE, line_w=Pt(0.5))
    add_text(slide, rrow_x + IN(0.1), rhl_y + IN(0.1), IN(3.4), IN(0.25),
             "DIFFERENTIATOR", size=9, color=AMBER, bold=True)
    add_text(slide, rrow_x + IN(0.1), rhl_y + IN(0.35), IN(3.4), IN(0.3),
             "Production Document", size=14, color=WHITE, bold=True)
    add_text(slide, rrow_x + IN(0.1), rhl_y + IN(0.7), IN(3.4), IN(0.85),
             "Every decision is an event in an immutable log.\nThe current state is a function of the log.\nDiffable, shareable, replayable.",
             size=10, color=TEXT_MUTED, line_spacing=1.2)

    # Bottom strip: 5 differentiators
    strip_y = IN(7.0)
    add_text(slide, IN(0.4), strip_y - IN(0.3), IN(8), IN(0.25),
             "FIVE PRODUCTION-DOCUMENT-FIRST DIFFERENTIATORS",
             size=9, color=CYAN, bold=True)
    items = [
        ("01", "Production Document", IBM_BLUE),
        ("02", "Consistency Contract", IBM_BLUE),
        ("03", "Crew Model", IBM_BLUE),
        ("04", "Stage Gates", IBM_BLUE),
        ("05", "Reviewer Agent", MAGENTA),
    ]
    bx = IN(0.4)
    bw = IN(2.55)
    for num, label, color in items:
        add_rect(slide, bx, strip_y, IN(0.32), IN(0.32), color)
        add_text(slide, bx, strip_y, IN(0.32), IN(0.32),
                 num, size=10, color=WHITE, bold=True,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        add_text(slide, bx + IN(0.4), strip_y + IN(0.04), bw - IN(0.4), IN(0.25),
                 label, size=10, color=WHITE, bold=True)
        bx += bw + IN(0.05)

draw_native_architecture(s)

# ====================================================================
# SLIDE 4 — PRINCIPLES
# ====================================================================
s = blank_slide(prs)
add_header(s, "Five laws. Three axioms. Eight things we will never build.")

# Five Laws column
add_text(s, Inches(0.5), Inches(1.85), Inches(6.2), Inches(0.35),
         "THE FIVE LAWS", size=11, color=CYAN, bold=True)

laws = [
    ("1", "Generation is a service call, not a product.",
     "Plan first. Generation is the slowest, most expensive, least interesting step."),
    ("2", "Nothing is final until the user says so.",
     "Every lock is explicit. Every unlock is possible."),
    ("3", "Every decision has a reason.",
     "Capture why alongside what. The audit trail is the product."),
    ("4", "Beginners and professionals use the same engine.",
     "Different views. Same model underneath."),
    ("5", "The AI earns autonomy incrementally.",
     "Propose, never execute without approval. Trust is earned, not assumed."),
]

ly0 = Inches(2.25)
for i, (num, head, sub) in enumerate(laws):
    row_y = ly0 + Inches(0.78) * i
    add_rect(s, Inches(0.5), row_y, Inches(0.5), Inches(0.5), IBM_BLUE)
    add_text(s, Inches(0.5), row_y, Inches(0.5), Inches(0.5),
             num, size=18, color=WHITE, bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, Inches(1.15), row_y - Inches(0.05), Inches(5.6), Inches(0.4),
             head, size=14, color=WHITE, bold=True)
    add_text(s, Inches(1.15), row_y + Inches(0.3), Inches(5.6), Inches(0.35),
             sub, size=11, color=TEXT_MUTED, italic=True, line_spacing=1.2)

# Right column: NEVER list
nx = Inches(7.0)
add_text(s, nx, Inches(1.85), Inches(6.0), Inches(0.35),
         "FEATURES THAT WILL NEVER BE ADDED", size=11, color=MAGENTA, bold=True)

never_list = [
    "Magic button one-shot production",
    "Auto-publish without human approval",
    "Prompt history as production history",
    "AI-generated brand kits",
    "Irreversible operations",
    "Hidden AI decisions",
    "Gamification of production metrics",
    "Cross-production content leakage",
]

ny0 = Inches(2.25)
for i, item in enumerate(never_list):
    row_y = ny0 + Inches(0.42) * i
    # X mark in red-ish square
    x_box = slide_add_shape_compat(s, MSO_SHAPE.RECTANGLE, nx, row_y, Inches(0.3), Inches(0.3))
    x_box.fill.solid(); x_box.fill.fore_color.rgb = BG_PANEL2
    x_box.line.color.rgb = MAGENTA
    x_box.line.width = Pt(0.75)
    x_box.shadow.inherit = False
    add_text(s, nx, row_y, Inches(0.3), Inches(0.3),
             "✕", size=12, color=MAGENTA, bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, nx + Inches(0.45), row_y - Inches(0.02), Inches(5.5), Inches(0.35),
             item, size=13, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)

# Bottom strip: the 5% rule
add_rect(s, Inches(0.5), Inches(6.25), Inches(12.33), Inches(0.6),
         BG_PANEL, line=STROKE, line_w=Pt(0.5))
add_rect(s, Inches(0.5), Inches(6.25), Inches(0.08), Inches(0.6), CYAN)
add_text(s, Inches(0.85), Inches(6.3), Inches(8.5), Inches(0.5),
         "THE 5% RULE", size=11, color=CYAN, bold=True, anchor=MSO_ANCHOR.MIDDLE)
add_text(s, Inches(2.1), Inches(6.3), Inches(10.5), Inches(0.5),
         "5% generation  ·  25% planning  ·  40% iteration  ·  15% assets  ·  15% management",
         size=13, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)

add_footer(s, 4)

# ====================================================================
# SLIDE 5 — ROADMAP
# ====================================================================
s = blank_slide(prs)
add_header(s, "After the prototype, this is where Open Production goes.")

# Intro line
add_text(s, Inches(0.5), Inches(1.85), Inches(12.33), Inches(0.4),
         "Today's submission is the kernel + one production-doc vertical. The roadmap extends it.",
         size=14, color=TEXT_MUTED, italic=True)

# Timeline of 4 phases
phases = [
    ("FOUNDATION",      "0–6 mo",  IBM_BLUE,
     ["Production document data model",
      "Director's Canvas + Guided Flow",
      "5 core agents · single generation backend",
      "Immutable event log + version snapshots"]),
    ("DEPTH",           "6–12 mo", CYAN,
     ["Full 26-stage video pipeline",
      "All 12 agents",
      "Consistency Contract system",
      "Timeline editor · version branching · studio library",
      "Plugin API: backends + export formats"]),
    ("COLLABORATION",   "12–18 mo", CYAN,
     ["Real-time multi-user production state",
      "Role-based access (Director, Producer, Reviewer)",
      "Brand kit enforcement",
      "Tamper-evident enterprise audit trail"]),
    ("INTELLIGENCE",    "18–30+ mo", MAGENTA,
     ["Production memory — the studio's evolving aesthetic",
      "Automatic consistency detection",
      "Cross-production asset discovery",
      "AI-directed iteration (specific change, not 'try again')"]),
]

pw = Inches(3.05)
py = Inches(2.55)
ph = Inches(4.1)
gap = Inches(0.13)
px = Inches(0.5)

for i, (head, months, accent, items) in enumerate(phases):
    x = px + (pw + gap) * i
    add_rect(s, x, py, pw, ph, BG_PANEL, line=STROKE, line_w=Pt(0.5))
    # top accent bar
    add_rect(s, x, py, pw, Inches(0.12), accent)
    # header
    add_text(s, x + Inches(0.2), py + Inches(0.25), pw - Inches(0.4), Inches(0.3),
             head, size=14, color=WHITE, bold=True)
    add_text(s, x + Inches(0.2), py + Inches(0.6), pw - Inches(0.4), Inches(0.25),
             months, size=11, color=accent, bold=True)
    # divider
    add_rect(s, x + Inches(0.2), py + Inches(0.95), pw - Inches(0.4), Emu(6000), STROKE)
    # bullets
    bullet_y = py + Inches(1.15)
    for j, item in enumerate(items):
        ry2 = bullet_y + Inches(0.55) * j
        # dot
        dot = slide_add_shape_compat(s, MSO_SHAPE.OVAL, x + Inches(0.2), ry2 + Inches(0.1),
                                      Inches(0.08), Inches(0.08))
        dot.fill.solid(); dot.fill.fore_color.rgb = accent
        dot.line.fill.background()
        dot.shadow.inherit = False
        # text
        add_text(s, x + Inches(0.35), ry2, pw - Inches(0.55), Inches(0.5),
                 item, size=10, color=WHITE, line_spacing=1.2)

# Bottom: the closing bet
add_rect(s, Inches(0.5), Inches(6.85), Inches(12.33), Inches(0.5),
         BG_PANEL, line=STROKE, line_w=Pt(0.5))
add_rect(s, Inches(0.5), Inches(6.85), Inches(0.08), Inches(0.5), CYAN)
add_text(s, Inches(0.85), Inches(6.85), Inches(12), Inches(0.5),
         "THE BET  —  Whoever captures the production process wins the next decade of creative tooling.",
         size=13, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)

add_footer(s, 5)

# ------------------------------------------------------------------ save
out = r"D:\IBM Project\Open_Production\deck\vision\open-production-vision.pptx"
prs.save(out)
print(f"Saved: {out}")
print(f"Slides: {len(prs.slides)}")
