import json, math, os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, NextPageTemplate, KeepTogether, Preformatted)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

F = next((d for d in ('/usr/share/fonts/truetype/dejavu/', '/usr/share/fonts/TTF/')    # Debian / Arch
          if os.path.exists(d + 'DejaVuSans.ttf')), '/usr/share/fonts/truetype/dejavu/')
pdfmetrics.registerFont(TTFont('DV', F + 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DVB', F + 'DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DVM', F + 'DejaVuSansMono.ttf'))
pdfmetrics.registerFont(TTFont('DVSB', F + 'DejaVuSerif-Bold.ttf'))
from reportlab.lib.fonts import addMapping
addMapping('DV', 0, 0, 'DV'); addMapping('DV', 1, 0, 'DVB')

INK = colors.HexColor('#1b2a3a'); ACC = colors.HexColor('#1f5f8b'); RULE = colors.HexColor('#c9d3dc')
SH = colors.HexColor('#eef3f7')
body = ParagraphStyle('b', fontName='DV', fontSize=9.2, leading=13, textColor=INK, spaceAfter=5)
small = ParagraphStyle('s', parent=body, fontSize=8, leading=10.5)
h1 = ParagraphStyle('h1', fontName='DVSB', fontSize=17, leading=21, textColor=ACC, spaceBefore=4, spaceAfter=8)
h2 = ParagraphStyle('h2', fontName='DVB', fontSize=11.5, leading=15, textColor=ACC, spaceBefore=10, spaceAfter=5)
h3 = ParagraphStyle('h3', fontName='DVB', fontSize=9.5, leading=13, textColor=INK, spaceBefore=6, spaceAfter=3)
title = ParagraphStyle('t', fontName='DVSB', fontSize=24, leading=29, textColor=INK, spaceAfter=6)
sub = ParagraphStyle('st', parent=body, fontSize=11, leading=15, textColor=colors.HexColor('#4a5a6a'))
code = ParagraphStyle('c', fontName='DVM', fontSize=7.6, leading=9.4, textColor=INK)
bul = ParagraphStyle('bl', parent=body, leftIndent=12, bulletIndent=2)

def P(t, s=body): return Paragraph(t, s)
def B(items): return [Paragraph(i, bul, bulletText='•') for i in items]

def tbl(data, widths=None, font=7.2, head=1, mono=True, zebra=True, align='RIGHT'):
    t = Table(data, colWidths=widths, repeatRows=head)
    st = [('FONT', (0, 0), (-1, -1), 'DVM' if mono else 'DV', font),
          ('FONT', (0, 0), (-1, head - 1), 'DVB', font),
          ('TEXTCOLOR', (0, 0), (-1, -1), INK),
          ('ALIGN', (0, 0), (-1, -1), align), ('ALIGN', (0, 0), (0, -1), 'LEFT'),
          ('LINEBELOW', (0, head - 1), (-1, head - 1), 0.6, ACC),
          ('TOPPADDING', (0, 0), (-1, -1), 1.2), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.2),
          ('LEFTPADDING', (0, 0), (-1, -1), 3), ('RIGHTPADDING', (0, 0), (-1, -1), 3)]
    if zebra:
        for r in range(head, len(data)):
            if (r - head) % 2 == 1: st.append(('BACKGROUND', (0, r), (-1, r), SH))
    t.setStyle(TableStyle(st)); return t

def prose_tbl(data, widths):
    data = [[Paragraph(str(c), ParagraphStyle('x', parent=small, fontName='DVB' if i == 0 else 'DV')) for c in row]
            for i, row in enumerate(data)]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, 0), 0.6, ACC), ('LINEBELOW', (0, 1), (-1, -1), 0.3, RULE),
                           ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 2.5),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5)]))
    return t

def listing(path, cols=3, maxl=72):
    lines = [l.rstrip() for l in open(path).read().splitlines() if l.strip()]
    lines = ['%03d  %s' % (i + 1, l) for i, l in enumerate(lines)]
    out = []
    page = cols * maxl
    for p0 in range(0, len(lines), page):
        seg = lines[p0:p0 + page]
        per = math.ceil(len(seg) / cols)
        chunks = [seg[i * per:(i + 1) * per] for i in range(cols)]
        cells = [[Preformatted('\n'.join(c), code) for c in chunks]]
        t = Table(cells, colWidths=[(174 * mm) / cols] * cols)
        t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BACKGROUND', (0, 0), (-1, -1), SH),
                               ('LINEBEFORE', (1, 0), (-1, -1), 0.4, RULE), ('LEFTPADDING', (0, 0), (-1, -1), 5)]))
        out += [t, Spacer(1, 4)]
    return out

def footer(c, d):
    c.saveState(); c.setFont('DV', 7); c.setFillColor(colors.HexColor('#7a8a9a'))
    w, h = c._pagesize
    c.drawString(15 * mm, 8 * mm, 'Sun, Moon, Aries & planets on the C47 — GHA / Dec to almanac accuracy')
    c.drawRightString(w - 15 * mm, 8 * mm, 'p. %d' % d.page); c.restoreState()

