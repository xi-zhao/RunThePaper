#!/usr/bin/env python3
"""Embed the reviewed workflow artwork into a PDF without altering its pixels.

Figure 1 is a conceptual, AI-assisted design asset, not a data plot.
Requires reportlab==4.4.9. Figures 2-4 remain numerical plots.
"""
from pathlib import Path
import struct
from reportlab import rl_config
from reportlab.pdfgen import canvas

# Keep compressed image streams binary in the versioned PDF.
rl_config.useA85 = 0

HERE = Path(__file__).resolve().parent

def build_figure1():
    source = HERE / 'figures/fig1_workflow.png'
    header = source.read_bytes()[:24]
    if header[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Expected the reviewed PNG artwork')
    width, height = struct.unpack('>II', header[16:24])
    target = HERE / 'figures/fig1_workflow.pdf'
    c = canvas.Canvas(str(target), pagesize=(width, height), invariant=1)
    c.setTitle('PRAgent research workflow')
    c.drawImage(str(source), 0, 0, width=width, height=height)
    c.showPage()
    c.save()
    print(f'Embedded unchanged {width} x {height} artwork into {target.name}')

if __name__ == '__main__':
    build_figure1()
