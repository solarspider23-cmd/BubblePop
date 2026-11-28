# blender -b --factory-startup --python tricount.py -- : tris per sub-assembly (budget tuning)
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wh_props as W
def n(sub):
    P = W.Prop('x'); sub.emit(P); return P.tris
for k in ('cartons', 'wrapped', 'drums', 'sacks', 'crates'):
    print('TRIS', k, [n(W.pallet_load(k, i, lite=True, back=False)) for i in range(3)])
s = W.Sub(); W.upright_frame(s, 0, -3.7, -.3); print('TRIS frame', n(s))
s = W.Sub(); W.beam_pair(s, -4.5, 4.5, 5, -3.6, -.4); print('TRIS beams', n(s))
