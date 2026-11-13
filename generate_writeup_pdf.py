"""Generate the two-page submission PDF from the reviewable Markdown write-up.
Run: pip install reportlab && python generate_writeup_pdf.py
"""
from pathlib import Path
from html import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

ROOT = Path(__file__).parent
raw = (ROOT / 'GRIT_Interview_Design_Writeup.md').read_text(encoding='utf-8')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='GritTitle', fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=colors.HexColor('#223252'), spaceAfter=8))
styles.add(ParagraphStyle(name='GritHeading', fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=colors.HexColor('#223252'), spaceBefore=9, spaceAfter=5))
styles.add(ParagraphStyle(name='GritBody', fontName='Helvetica', fontSize=9.1, leading=12.2, spaceAfter=7, textColor=colors.HexColor('#202a3a')))
styles.add(ParagraphStyle(name='GritCell', fontName='Helvetica', fontSize=8.15, leading=10.3))
styles.add(ParagraphStyle(name='GritHeader', fontName='Helvetica-Bold', fontSize=8.15, leading=10.3))

def clean(value):
    return escape(value).replace('“', '&quot;').replace('”', '&quot;').replace('’', "'").replace('–', '-').replace('—', '-')

story = []
lines = raw.splitlines()
i = 0
while i < len(lines):
    line = lines[i].strip()
    if not line:
        i += 1
        continue
    if line.startswith('|'):
        rows = []
        while i < len(lines) and lines[i].startswith('|'):
            cells = [part.strip() for part in lines[i].strip().strip('|').split('|')]
            if not all(set(part) <= {'-', ':', ' '} for part in cells):
                sty = styles['GritHeader'] if not rows else styles['GritCell']
                rows.append([Paragraph(clean(cell), sty) for cell in cells])
            i += 1
        width = 6.83 * inch
        table = Table(rows, colWidths=[1.67*inch, width-1.67*inch], repeatRows=1, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf0f9')),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('GRID',(0,0),(-1,-1),.4,colors.HexColor('#cdd7e5')),
            ('LEFTPADDING',(0,0),(-1,-1),8), ('RIGHTPADDING',(0,0),(-1,-1),8),
            ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6),
        ]))
        story.append(table)
        continue
    if line.startswith('# '):
        sty = styles['GritTitle']; line = line[2:]
    elif line.startswith('## '):
        sty = styles['GritHeading']; line = line[3:]
    else:
        sty = styles['GritBody']
    story.append(Paragraph(clean(line), sty))
    i += 1
pdf = ROOT / 'GRIT_Interview_Design_Writeup.pdf'
SimpleDocTemplate(str(pdf),pagesize=(595.28,841.89),leftMargin=48,rightMargin=48,topMargin=42,bottomMargin=43,title='GRIT Interview Scheduling - Round 1').build(story)
print(pdf)
