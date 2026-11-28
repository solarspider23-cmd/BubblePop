# prop_studio wrapper: same props, but with the candy preview materials (gloss / jelly glass / cookie / frosting)
from candy_props import *
import candy_props as _C
G = _C.G
_to_kit = G.to_kit
def _wrapped(P, coll):
    _C._PM.clear()
    out = _to_kit(P, coll)
    for me in out.values(): _C.preview_mats(me)
    return out
G.to_kit = _wrapped
