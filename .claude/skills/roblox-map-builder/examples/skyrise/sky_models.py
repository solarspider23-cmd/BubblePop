# Skyrise v2 models: higher-detail replacements for the first-pass kit (same names, same origins / fronts).
# Imported at the end of sky_props.py so these definitions override the old ones.
import math, random
import bmesh
from mathutils import Vector, Matrix
import sky_props as K
from sky_props import G, Prop, S, at, lathe, sphere, torus, gem, box, cyl, spike, tube, hull, ngon_prism, rock_pts, nz

def lumpy(r, seed, sub=2, amp=.16, sq=1.0):
    """icosphere with noise displacement: chunky stylised foliage / cloud / rock lump"""
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    for v in bm.verts:
        n = nz(v.co.x * 1.0, v.co.y * 1.0, v.co.z * 1.0, r * .55, seed) - .5
        v.co *= 1 + n * amp * 2
        v.co.y *= sq
    return bm

def bevel_box(size, bev=None):
    return box(size, bev if bev is not None else min(size) * .18)

# ======================================================================== trees
def puffy_tree(seed, h=13.0, col='leaf', bloom=None):
    """trunk that forks into 2-3 limbs, root flares into the ground, chunky lumpy canopy clumps (faceted) with
    small tufts breaking the silhouette, darker underneath"""
    rng = random.Random(seed); P = Prop('Puffy%d_%s%s' % (seed, {'leaf': 'green'}.get(col, col), '_b' if bloom else ''))   # name the colour, not 'leaf': it is a whole tree
    bark = S('wood', grad=(-.5, h * .6, .28, .62), jit=.03)
    bend = Vector((rng.uniform(-1, 1), 0, rng.uniform(-1, 1))) * h * .05
    fork = Vector((0, h * .42, 0)) + bend
    P.add(tube([Vector((0, -.8, 0)), Vector((0, h * .08, 0)), Vector((0, h * .2, 0)) + bend * .3, fork],
               [h * .12, h * .085, h * .068, h * .058], sides=10, rough=.05, seed=seed), bark)
    for k in range(5):                                                        # root flares: thick, low, melting into the ground
        a = k * math.tau / 5 + rng.uniform(-.25, .25); R = h * .1
        P.add(tube([Vector((0, R * 1.1, 0)), Vector((math.cos(a) * R * 1.2, R * .45, math.sin(a) * R * 1.2)),
                    Vector((math.cos(a) * R * 2.1, -.2, math.sin(a) * R * 2.1))], [R * .62, R * .45, R * .18], sides=7), bark)
    clumps = []
    top = fork + Vector((0, h * .26, 0))
    limbs = rng.randint(2, 3)
    for k in range(limbs):                                                    # limbs to side clumps
        a = k * math.tau / limbs + rng.uniform(-.4, .4)
        end = fork + Vector((math.cos(a) * h * .22, h * rng.uniform(.14, .22), math.sin(a) * h * .22))
        P.add(tube([fork, fork.lerp(end, .5) + Vector((0, h * .03, 0)), end], [h * .045, h * .032, h * .022], sides=7), bark)
        clumps.append((end + Vector((0, h * .05, 0)), h * rng.uniform(.2, .25)))
    P.add(tube([fork, top], [h * .05, h * .03], sides=7), bark)
    clumps.append((top + Vector((0, h * .08, 0)), h * .3))
    for k in range(4):
        a = k * math.tau / 4 + rng.uniform(-.4, .4)
        clumps.append((top + Vector((math.cos(a) * h * .2, h * rng.uniform(.0, .16), math.sin(a) * h * .2)), h * rng.uniform(.19, .24)))
    clumps.append((top + Vector((0, h * .3, 0)), h * .2))
    y0 = min(c.y - r for c, r in clumps); y1 = max(c.y + r for c, r in clumps)
    for i, (c, r) in enumerate(clumps):
        tint = rng.uniform(-.05, .05)
        P.add(at(lumpy(r, seed * 13 + i, 2, .12, .86), c), S(col, grad=(y0, y1, .22 + tint, .94 + tint), up=.14, jit=.02, seed=i))
        for j in range(3):                                                    # tufts on the clump underside
            a = rng.uniform(0, math.tau)
            p = c + Vector((math.cos(a) * r * .85, -r * .45, math.sin(a) * r * .85))
            P.add(at(lumpy(r * .32, seed * 31 + i * 7 + j, 1, .2, .8), p), S(col, grad=(y0, y1, .2, .7), jit=.03, seed=j))
        if bloom:                                                             # 5-petal blossoms on the upper face of each clump
            for j in range(4):
                a = rng.uniform(0, math.tau); el = rng.uniform(.25, 1.2)
                n = Vector((math.cos(a) * math.cos(el), math.sin(el), math.sin(a) * math.cos(el)))
                p = c + Vector((n.x, n.y * .86, n.z)) * r * 1.02
                fl = ngon_prism([(math.cos(b) * (.95 if q % 2 == 0 else .45) * h / 13, math.sin(b) * (.95 if q % 2 == 0 else .45) * h / 13)
                                 for q, b in enumerate([m * math.pi / 5 for m in range(10)])], -.05, .05)
                rq = Vector((0, 1, 0)).rotation_difference(n); bmesh.ops.rotate(fl, cent=Vector(), matrix=rq.to_matrix(), verts=fl.verts)
                P.add(at(fl, p), S(bloom, base=.78, jit=0))
                P.add(at(sphere(.22 * h / 13, 5, 4), p + n * .08), S('gold', base=.7, jit=0))
    P.add(at(torus(h * .062, h * .018, n=10, sides=5), fork + Vector((0, -h * .04, 0))), S('wood', base=.35))   # bark collar at the fork
    knot = bend * .15 + Vector((h * .07, h * .26, 0))
    P.add(at(lumpy(h * .03, seed, 1, .2), knot), S('wood', base=.3))                                          # knot
    return P

def blossom_tree(seed, h=13.0):
    return puffy_tree(seed, h, 'leaf', bloom='pink')

def snow_tree(seed, h=14.0):
    """pine: 4 star tiers with drooping snow caps, trunk, root collar"""
    rng = random.Random(seed); P = Prop('SnowTree%d' % seed)
    P.add(tube([Vector((0, -.6, 0)), Vector((0, h * .5, 0)), Vector((0, h * .95, 0))], [h * .055, h * .04, h * .012], sides=8), S('wood', base=.38))
    for k in range(4):
        a = k * math.tau / 4; R = h * .06
        P.add(tube([Vector((0, R * 1.5, 0)), Vector((math.cos(a) * R * 2.4, -.4, math.sin(a) * R * 2.4))], [R * .6, R * .15], sides=5), S('wood', base=.35))
    tiers = 4; yaw = rng.uniform(0, 60)
    for i in range(tiers):
        y = h * (.18 + .19 * i); R = h * .36 * (1 - i * .2); ht = h * .3; n = 12
        bm = bmesh.new(); tip = bm.verts.new((0, y + ht, 0)); rim_v = []; snow_v = []
        for k in range(n):
            a = math.radians(yaw) + k * math.tau / n; rr = R * (1 if k % 2 == 0 else .78); dy = -h * .035 if k % 2 == 0 else 0
            rim_v.append(bm.verts.new((math.cos(a) * rr, y + dy, math.sin(a) * rr)))
        inner = [bm.verts.new((math.cos(math.radians(yaw) + k * math.tau / 6) * R * .3, y + h * .05, math.sin(math.radians(yaw) + k * math.tau / 6) * R * .3)) for k in range(6)]
        for k in range(n): bm.faces.new((tip, rim_v[(k + 1) % n], rim_v[k]))
        for k in range(n):
            j = int(k / n * 6) % 6; j2 = int((k + 1) / n * 6) % 6
            if j == j2: bm.faces.new((rim_v[k], rim_v[(k + 1) % n], inner[j]))
            else: bm.faces.new((rim_v[k], rim_v[(k + 1) % n], inner[j2], inner[j]))
        bm.faces.new(inner); bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        P.add(bm, S('leaf', grad=(y - h * .04, y + ht, .22 + i * .04, .55 + i * .05), up=.15, jit=.03, seed=i))
        # snow cap: a thinner star cone sitting on the upper 60% of the tier, with points that droop
        sb = bmesh.new(); st = sb.verts.new((0, y + ht + .15, 0)); sr = []
        for k in range(n):
            a = math.radians(yaw) + k * math.tau / n; full = R * (1 if k % 2 == 0 else .78); rr = full * (.7 if k % 2 == 0 else .62)
            ys = y + (-h * .035 if k % 2 == 0 else 0) + (ht + (h * .035 if k % 2 == 0 else 0)) * (1 - rr / full)   # on the cone face
            sr.append(sb.verts.new((math.cos(a) * rr, ys + .14 - (h * .02 if k % 2 == 0 else 0), math.sin(a) * rr)))
        for k in range(n): sb.faces.new((st, sr[(k + 1) % n], sr[k]))
        sb.faces.new(list(reversed(sr))); bmesh.ops.recalc_face_normals(sb, faces=list(sb.faces))
        P.add(sb, S('snow', grad=(y, y + ht, .62, .96), up=.1, jit=.02))
    return P

# ======================================================================== island underside + grass rim
def island_under(seed, R, depth, rim_fn, top_y=0.0, n=72, top_col='grass'):
    """underside: 16 rings to a rough tip, noise-displaced (no big flat triangles), terrace ledges every few rings,
    strata colours warped by noise, boulders pushing out of the face, glow crystals, vines, roots; plus a jagged
    'grass drip' skirt under the top lip in the island's top colour"""
    rng = random.Random(seed); P = Prop('IslandUnder%d' % seed)
    bm = bmesh.new(); rings = []; Kr = 16
    for k in range(Kr + 1):
        t = k / Kr
        f = .16 + .84 * (1 - t ** 1.55)
        ledge = .035 if k % 3 == 1 else 0                                       # a lip every third ring = terraces
        y = top_y - .6 - depth * t ** 1.1
        ring = []
        for i in range(n):
            a = i * math.tau / n; r0 = rim_fn(a)
            r = r0 * (f + ledge * (1 - t)) if k else r0
            if k:
                r *= 1 + (nz(math.cos(a) * 30, y * .6, math.sin(a) * 30, 9, seed) - .5) * .22
            yy = y + ((nz(math.cos(a) * 20, k * 3.0, math.sin(a) * 20, 6, seed + 5) - .5) * 3.0 if 0 < k < Kr else 0)
            ring.append(bm.verts.new((math.cos(a) * r, yy, math.sin(a) * r)))
        rings.append(ring)
    for A, B in zip(rings, rings[1:]):
        for i in range(n): bm.faces.new((A[i], A[(i + 1) % n], B[(i + 1) % n], B[i]))
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(Vector((c.x, -1.0 if abs(c.x) + abs(c.z) > 1e-3 else -2.0, c.z))) < 0: f.normal_flip()
    bottom = top_y - .6 - depth
    for k in range(5):                                                         # broken tip: big hanging chunks
        a = k * math.tau / 5 + rng.uniform(-.3, .3); d = R * rng.uniform(.0, .1)
        hh = depth * rng.uniform(.18, .32); rr = R * rng.uniform(.07, .11)
        P.add(at(spike(rr, hh, sides=6, shoulder=.35), (math.cos(a) * d, bottom + 1.5, math.sin(a) * d), (180 + rng.uniform(-14, 14), rng.uniform(0, 60), 0)),
              S('rock', grad=(bottom - hh, bottom, .3, .5), jit=.03))
    bands = [.34, .5, .42, .6, .38, .55, .46]
    def strata(f):
        c = f.calc_center_median(); warp = (nz(c.x, 0, c.z, 18, seed + 9) - .5) * 5
        d = top_y - c.y + warp
        if d < 2.6: col, v = 'dirt', .5
        else: col, v = 'rock', bands[int(d / (depth / 7.0)) % len(bands)]
        v += f.normal.y * .12 - max(0, -f.normal.y) * .1 + (rng.random() - .5) * .04
        return [(G.PAL.u(col), max(.05, min(.95, v)))] * len(f.loops)
    P.solid.add(bm, strata)
    for k in range(int(R * .4)):                                              # boulders pushing out of the face
        a = rng.uniform(0, math.tau); t = rng.uniform(.08, .75)
        r = rim_fn(a) * (1 - t ** 1.55) * .97; y = top_y - .6 - depth * t ** 1.1
        s = rng.uniform(4.0, 9.0) * (1.2 - t * .6)
        r += s * .5                                                             # push the boulder out so it reads
        P.add(at(hull(rock_pts((s, s * .7, s * .8), n=14, seed=seed * 50 + k)), (math.cos(a) * r, y, math.sin(a) * r)),
              S('rock', base=rng.uniform(.38, .6), up=.18, jit=.04, seed=k))
    for k in range(int(R * .3)):                                              # hanging rock spikes
        a = rng.uniform(0, math.tau); t = rng.uniform(.2, .8)
        r = rim_fn(a) * (1 - t ** 1.55) * .94; y = top_y - .6 - depth * t ** 1.1
        h = rng.uniform(4, 11) * (1.3 - t * .5)
        P.add(at(spike(rng.uniform(1.4, 2.8), h, sides=6, shoulder=.3), (math.cos(a) * r, y + .6, math.sin(a) * r), (180 + rng.uniform(-10, 10), rng.uniform(0, 360), 0)),
              S('rock', grad=(y - h, y, .3, .55), jit=.03))
    for k in range(3 + int(R * .03)):                                         # glow crystal clusters
        a = rng.uniform(0, math.tau); t = rng.uniform(.25, .6)
        r = rim_fn(a) * (1 - t ** 1.55) * .96 + 2.5; y = top_y - .6 - depth * t ** 1.1
        out = Vector((math.cos(a), -.3, math.sin(a))).normalized()
        P.add(at(hull(rock_pts((2.8, 2.0, 2.4), n=12, seed=seed + k)), (math.cos(a) * r, y, math.sin(a) * r)), S('rock', base=.32))
        for j in range(4):
            hh = rng.uniform(8, 15) if j else 17
            g = lathe([(0, -.4), (1.5, .25 * hh), (1.5, .78 * hh), (0, hh)], n=6)
            dirv = (out + Vector((rng.uniform(-.35, .35), rng.uniform(-.3, .3), rng.uniform(-.35, .35)))).normalized()
            q = Vector((0, 1, 0)).rotation_difference(dirv); bmesh.ops.rotate(g, cent=Vector(), matrix=q.to_matrix(), verts=g.verts)
            if j == 3: P.add(at(g, (math.cos(a) * r, y, math.sin(a) * r)), S('ice', grad=(y - 8, y + 8, .45, .9)))
            else: P.gadd(at(g, (math.cos(a) * r, y, math.sin(a) * r)), 'crystal')
    # grass overhang: a continuous jagged skirt (two layers) hanging from the top lip in the island's top colour
    for layer, (out_o, len_k, base_v) in enumerate(((.35, 1.0, .5), (.05, 1.5, .36))):
        sk = bmesh.new(); ndr = int(R * 2.2); top_r = []; low_r = []
        for k in range(ndr):
            a = k * math.tau / ndr; r = rim_fn(a) + out_o
            L = (rng.uniform(1.4, 3.2) if k % 2 == 0 else rng.uniform(.5, 1.0)) * len_k
            if top_col == 'basalt': L *= .5
            top_r.append(sk.verts.new((math.cos(a) * r, top_y + .05, math.sin(a) * r)))
            low_r.append(sk.verts.new((math.cos(a) * (r + .15), top_y - .5 - L, math.sin(a) * (r + .15))))
        for k in range(ndr):
            j = (k + 1) % ndr; sk.faces.new((top_r[k], top_r[j], low_r[j], low_r[k]))
        for f in sk.faces:
            f.normal_update(); c = f.calc_center_median()
            if f.normal.dot(Vector((c.x, 0, c.z))) < 0: f.normal_flip()
        P.add(sk, S(top_col, grad=(top_y - 4, top_y, base_v - .12, base_v + .08), up=.05, jit=.02, seed=layer))
    for k in range(int(R * .22)):                                             # vines with leaves
        a = rng.uniform(0, math.tau); r = rim_fn(a) + .3
        p0 = Vector((math.cos(a) * r, top_y - .3, math.sin(a) * r)); out = Vector((math.cos(a), 0, math.sin(a)))
        L = rng.uniform(5, 13); pts = [p0, p0 + out * .9 + Vector((0, -L * .45, 0)), p0 + out * .5 + Vector((0, -L, 0))]
        P.add(tube(pts, [.3, .22, .12], sides=5), S('leaf', base=.4))
        for j in range(4):
            q = pts[0].lerp(pts[2], (j + .6) / 4.4) + out * .7
            P.add(at(lumpy(.65, seed + k * 9 + j, 1, .25, .7), q), S('leaf', base=.5 + j * .04, jit=.03))
    return P

# ======================================================================== zone gate
def zone_gate(z, w=16.0):
    """carved stone gate: stepped plinths, octagonal banded shafts with capitals, a voussoir arch of separate
    stones with a gem keystone, torches on the pillars, glowing bar barrier + rune ring, price stand in front"""
    P = Prop('ZoneGate%d' % z); hw = w / 2; px = hw + 2.0; key = 'z%d' % z
    for sx in (-1, 1):
        x = sx * px
        for k, (s, hh) in enumerate(((5.6, .9), (4.8, .8), (4.2, .6))):
            P.add(at(bevel_box((s, hh, s), .2), (x, -.3 + sum(v for _, v in ((5.6, .9), (4.8, .8), (4.2, .6))[:k]) + hh / 2, 0)),
                  S('stone', base=.5 + k * .05, up=.25))
        P.add(at(lathe([(1.7, 0), (1.7, 13.5)], n=8), (x, 2.0, 0)), S('stone', grad=(2, 15, .5, .66), up=.15))
        for y in (4.0, 8.0, 12.0): P.add(at(cyl(1.95, .55, sides=8), (x, y, 0)), S('gold', base=.55))
        P.add(at(lathe([(1.8, 0), (2.4, .7), (2.6, 1.3), (2.6, 1.9), (1.9, 2.1)], n=8), (x, 15.4, 0)), S('stone', base=.68))
        for sz in (-1,):                                                       # torch on the approach face
            P.add(at(bevel_box((.6, 1.6, .6), .1), (x, 9.6, sz * 2.1)), S('basalt', base=.4))
            P.add(at(lathe([(.25, 0), (.75, .5), (.85, 1.0), (0, 1.05)], n=8), (x, 10.3, sz * 2.5)), S('gold', base=.5))
            P.gadd(at(lathe([(0, 0), (.6, .4), (.3, 1.4), (0, 2.0)], n=6), (x, 11.2, sz * 2.5)), 'lamp')
    n = 9; R_in, R_out = px - .2, px + 2.2; cy = 17.4
    for k in range(n):                                                         # arch voussoirs
        a0, a1 = math.pi * k / n + .015, math.pi * (k + 1) / n - .015
        bmv = bmesh.new(); vs = []
        for rr in (R_in, R_out):
            for aa in (a0, a1):
                for zz in (-1.4, 1.4): vs.append(bmv.verts.new((math.cos(aa) * rr, cy + math.sin(aa) * rr, zz)))
        bmesh.ops.convex_hull(bmv, input=vs)
        P.add(bmv, S('stone', base=.56 + (k % 2) * .07, up=.2, jit=.02, seed=k))
    P.add(at(bevel_box((3.2, 4.2, 3.4), .3), (0, cy + R_out - 1.2, 0)), S('stone', base=.72))           # keystone
    P.gadd(at(gem(1.3, 2.6), (0, cy + R_out - 2.2, -1.9), (90, 0, 0)), key)
    P.add(at(torus(1.6, .3, n=12, sides=5), (0, cy + R_out - 1.2, -1.75), (90, 0, 0)), S('gold', base=.6))
    P.gadd(at(torus(5.6, .28, n=40, sides=5), (0, cy + 1.0, 0), (90, 0, 0)), key)                      # rune ring in the arch
    for k in range(8):
        a = k * math.tau / 8
        P.gadd(at(gem(.4, .9), (math.cos(a) * 5.6, cy + 1.0 + math.sin(a) * 5.6, 0), (0, 0, math.degrees(a) - 90)), key)
    for k in range(11):                                                        # bar barrier
        P.gadd(at(cyl(.22, 15.4, sides=6, y0=.6), (-hw + w * (k + .5) / 11, 0, .3)), key)
    for y in (1.2, 9.0, 16.0): P.gadd(at(bevel_box((w + .4, .35, .35), .08), (0, y, .3)), key)
    # price stand in front (approach side = -Z): post + slanted plate with coin + lock
    P.add(at(bevel_box((1.0, 3.6, 1.0), .15), (hw - 1, 1.5, -5.5)), S('stone', base=.55))
    P.add(at(bevel_box((5.2, 3.2, .5), .2), (hw - 1, 4.2, -5.5), (-18, 0, 0)), S('basalt', base=.5))
    P.add(at(cyl(1.0, .35, sides=16), (hw - 2.5, 4.3, -5.85), (72, 0, 0)), S('gold', base=.72, jit=0))
    P.add(at(bevel_box((2.2, .4, .2), .05), (hw - .3, 4.7, -5.75), (-18, 0, 0)), S('gold', base=.75, jit=0))
    P.add(at(bevel_box((1.5, .4, .2), .05), (hw - .65, 3.9, -5.62), (-18, 0, 0)), S('gold', base=.75, jit=0))
    P.add(at(bevel_box((2.0, 1.7, .6), .2), (0, 7.0, -.3)), S('gold', base=.6))                        # padlock on the bars
    P.add(at(torus(.75, .25, n=14, sides=5), (0, 7.9, -.3), (90, 0, 0)), S('gold', base=.45))
    return P
