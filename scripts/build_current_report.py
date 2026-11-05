"""Build the current PDF from versioned Markdown. Requires reportlab==4.4.9."""
from pathlib import Path
import os
import re
import shutil
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/REPORT_2026_11_05.md'
OUTPUT = ROOT / 'docs/EvidenceAtlas_Food_Report_2026_11_05.pdf'
GREEN, INK, MUTED, PALE, PAPER = [colors.HexColor(c) for c in
    ('#144d3b', '#203c31', '#5e6f64', '#eef3e9', '#fafbf7')]
fonts = {}
for key, filename, fallback in (
    ('body', 'segoeui.ttf', 'Helvetica'),
    ('bold', 'segoeuib.ttf', 'Helvetica-Bold'),
    ('title', 'georgia.ttf', 'Times-Roman'),
):
    path = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / filename
    fonts[key] = fallback
    if path.exists():
        fonts[key] = 'EA-' + key
        pdfmetrics.registerFont(TTFont(fonts[key], str(path)))

styles = {
    'body': ParagraphStyle('body', fontName=fonts['body'], fontSize=9.5,
        leading=14.2, textColor=INK, spaceAfter=10),
    'section': ParagraphStyle('section', fontName=fonts['bold'], fontSize=10,
        leading=14, textColor=GREEN, spaceAfter=14),
    'title': ParagraphStyle('title', fontName=fonts['title'], fontSize=23,
        leading=29, textColor=GREEN, spaceAfter=16),
    'source': ParagraphStyle('source', fontName=fonts['body'], fontSize=7.5,
        leading=10.5, textColor=MUTED, spaceBefore=4, spaceAfter=6),
    'cell': ParagraphStyle('cell', fontName=fonts['body'], fontSize=8.5,
        leading=12, textColor=INK),
    'header': ParagraphStyle('header', fontName=fonts['bold'], fontSize=8.5,
        leading=12, textColor=colors.white),
    'code': ParagraphStyle('code', fontName='Courier', fontSize=8.3,
        leading=12.5, textColor=INK, backColor=PALE, borderPadding=9,
        spaceBefore=3, spaceAfter=13),
}

def rich(text):
    return re.sub(r'\*\*(.+?)\*\*', lambda m:
        '<font name="' + fonts['bold'] + '">' + m.group(1) + '</font>', escape(text))

def footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    canvas.setFillColor(GREEN)
    canvas.rect(0, 0, 9, height, fill=1, stroke=0)
    canvas.setFont(fonts['title'], 12)
    canvas.drawString(48, height - 34, 'EvidenceAtlas Food')
    canvas.setFont(fonts['body'], 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(width - 48, height - 33, 'PROJECT UPDATE / 05 NOV 2026')
    canvas.setStrokeColor(colors.HexColor('#d8e1d3'))
    canvas.line(48, height - 46, width - 48, height - 46)
    canvas.line(48, 43, width - 48, 43)
    canvas.drawString(48, 28, 'CSD358 / TRACK T6     |     SOURCE-LINKED LITERATURE RETRIEVAL')
    canvas.drawRightString(width - 48, 28, f'{doc.page:02d}')
    canvas.restoreState()

def build():
    lines = SOURCE.read_text(encoding='utf-8').splitlines()
    story = []
    i = sections = 0
    width = A4[0] - 96
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line or line.startswith('# '):
            continue
        if line.startswith('## '):
            if sections:
                story.append(PageBreak())
            sections += 1
            story.append(Paragraph(rich(line[3:].upper()), styles['section']))
        elif line.startswith('### '):
            story.append(Paragraph(rich(line[4:]), styles['title']))
        elif line.startswith('```'):
            block = []
            while i < len(lines) and not lines[i].startswith('```'):
                block.append(escape(lines[i])); i += 1
            i += 1
            story.append(Paragraph('<br/>'.join(block), styles['code']))
        elif line.startswith('|'):
            rows = [line]
            while i < len(lines) and lines[i].startswith('|'):
                rows.append(lines[i]); i += 1
            data = []
            for row in rows:
                cells = [c.strip() for c in row.strip('|').split('|')]
                if all(re.fullmatch(r'[:\- ]+', c) for c in cells):
                    continue
                style = styles['header'] if not data else styles['cell']
                data.append([Paragraph(rich(c), style) for c in cells])
            n = len(data[0])
            fractions = {2: [.35, .65], 4: [.52, .16, .16, .16],
                         5: [.28, .17, .17, .18, .20]}[n]
            table = Table(data, colWidths=[width*f for f in fractions], repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), GREEN),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, PALE]),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 9),
                ('RIGHTPADDING', (0,0), (-1,-1), 9),
                ('TOPPADDING', (0,0), (-1,-1), 7),
                ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ]))
            story.extend([table, Spacer(1, 13)])
        else:
            style = styles['source'] if line.startswith('Sources:') else styles['body']
            story.append(Paragraph(rich(line), style))
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=48,
        leftMargin=48, topMargin=65, bottomMargin=58,
        title='EvidenceAtlas Food - Updated Project Report - November 5, 2026',
        author='Adil Muhammed', subject='Implementation, collection, evaluation and limitations')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    shutil.copyfile(OUTPUT, ROOT / 'docs/EvidenceAtlas_Food_Report.pdf')
    shutil.copyfile(SOURCE, ROOT / 'docs/REPORT.md')
    print(OUTPUT)

if __name__ == '__main__':
    build()
