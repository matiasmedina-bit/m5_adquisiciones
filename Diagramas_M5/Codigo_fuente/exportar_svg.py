# -*- coding: utf-8 -*-
"""Vuelve a correr los generadores de matplotlib guardando además una copia .svg de cada figura."""
import runpy, os, sys
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure

DEST = '/home/claude/final/svg'
os.makedirs(DEST, exist_ok=True)
original = Figure.savefig
generadas = []


def savefig(self, fname, *a, **k):
    original(self, fname, *a, **k)
    if isinstance(fname, str) and fname.lower().endswith('.png'):
        destino = os.path.join(DEST, os.path.basename(fname)[:-4] + '.svg')
        k2 = dict(k)
        k2.pop('dpi', None)
        original(self, destino, *a, **k2)
        generadas.append(os.path.basename(destino))


Figure.savefig = savefig
sys.path.insert(0, '/home/claude/final')
for script in ('graficas2.py', 'graficas_inc1.py'):
    print('>>>', script)
    runpy.run_path('/home/claude/final/' + script, run_name='__main__')

print()
print('SVG generados:', len(generadas))
for g in sorted(generadas):
    print('  ', g)
