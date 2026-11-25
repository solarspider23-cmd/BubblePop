#!/usr/bin/env python3
"""Makes BubblePop's own sound effects from scratch (no samples, so we own them outright)
and writes them as WAV files to art/sounds/. Pure Python, no extra installs.

    python3 tools/make_sounds.py

Upload them with tools/upload_audio.py, then put the ids in Config/Sounds.lua.

A real bubble-wrap pop is a tiny burst of air: a very sharp click, a short bright
"tock" from the plastic snapping, a soft low thump, and a hiss of air that dies in
a few hundredths of a second. Each pop below mixes those with different settings.
"""
import math
import random
import struct
import wave
from pathlib import Path

SR = 44100
OUT = Path(__file__).resolve().parent.parent / "art" / "sounds"


def bandpass(signal, freq, q):
    """Biquad band-pass (constant skirt gain)."""
    w0 = 2 * math.pi * freq / SR
    alpha = math.sin(w0) / (2 * q)
    b0, b1, b2 = alpha, 0.0, -alpha
    a0, a1, a2 = 1 + alpha, -2 * math.cos(w0), 1 - alpha
    b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
    out, x1, x2, y1, y2 = [], 0.0, 0.0, 0.0, 0.0
    for x in signal:
        y = b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        out.append(y)
        x2, x1, y2, y1 = x1, x, y1, y
    return out


def highpass1(signal, freq):
    rc = 1 / (2 * math.pi * freq)
    a = rc / (rc + 1 / SR)
    out, prev_x, prev_y = [], 0.0, 0.0
    for x in signal:
        y = a * (prev_y + x - prev_x)
        out.append(y)
        prev_x, prev_y = x, y
    return out


def mix(*tracks):
    n = max(len(t) for t in tracks)
    return [sum(t[i] if i < len(t) else 0.0 for t in tracks) for i in range(n)]


def finish(sig, peak=0.9, fade=0.004):
    m = max(abs(x) for x in sig) or 1
    sig = [x / m * peak for x in sig]
    nf = int(fade * SR)
    for i in range(nf):
        sig[-1 - i] *= i / nf
    return sig


def write(name, sig):
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / (name + ".wav")), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x)) * 32767)) for x in sig))
    print("wrote art/sounds/%s.wav (%.0f ms)" % (name, len(sig) / SR * 1000))


def pop(seed, length=0.11, click=1.0, tock_freq=2300, tock_decay=0.010, tock=0.8,
        thump_freq=170, thump=0.45, air_freq=3500, air=0.5, air_decay=0.022, glide=0.25):
    rnd = random.Random(seed)
    n = int(length * SR)
    t = [i / SR for i in range(n)]
    noise = [rnd.uniform(-1, 1) for _ in range(n)]
    # 1. the snap: a 1-2 ms burst of bright noise
    c = highpass1([noise[i] * math.exp(-t[i] / 0.0012) for i in range(n)], 1500)
    # 2. the plastic "tock": damped tones that slide down a little as the bubble collapses
    phase1 = phase2 = 0.0
    k = []
    for i in range(n):
        f1 = tock_freq * (1 - glide * min(1, t[i] / 0.03))
        phase1 += 2 * math.pi * f1 / SR
        phase2 += 2 * math.pi * f1 * 2.13 / SR
        k.append(math.sin(phase1) * math.exp(-t[i] / tock_decay)
                 + 0.35 * math.sin(phase2) * math.exp(-t[i] / (tock_decay * 0.5)))
    # 3. a soft low thump gives it weight
    th = [math.sin(2 * math.pi * thump_freq * t[i]) * math.exp(-t[i] / 0.018)
          * min(1, t[i] / 0.0015) for i in range(n)]
    # 4. the puff of air escaping
    a = bandpass([noise[i] * math.exp(-t[i] / air_decay) for i in range(n)], air_freq, 0.9)
    return finish(mix([x * click for x in c], [x * tock for x in k], [x * thump for x in th],
                      [x * air * 3 for x in a]))


def pop2(seed, f0=3100, q=6.0, decay=0.008, tone=0.5, crack=1.0, double=0.6, air=0.35,
         body=0.25, body_freq=240, length=0.075):
    """A more real pop: the plastic snaps (one or two very sharp cracks), the little air
    pocket rings briefly like a hollow "pock" (noise through resonances, plus a hint of
    tone), a puff of air and a tiny low body. Each seed is a slightly different take."""
    rnd = random.Random(seed)
    f0 *= rnd.uniform(0.9, 1.1)
    decay *= rnd.uniform(0.85, 1.15)
    n = int(length * SR)
    t = [i / SR for i in range(n)]
    noise = [rnd.uniform(-1, 1) for _ in range(n)]
    # cracks: a main snap and (sometimes) a second one a few ms later
    gap = int(rnd.uniform(0.0012, 0.0035) * SR)
    second = double * rnd.uniform(0.4, 1.0)
    c = []
    for i in range(n):
        e = math.exp(-t[i] / 0.0006)
        if i >= gap:
            e += second * math.exp(-(i - gap) / SR / 0.0005)
        c.append(noise[i] * e)
    c = highpass1(highpass1(c, 2500), 2500)
    # the hollow ring: short noise burst through two resonances, plus a hint of falling tone
    ex = [noise[i] * math.exp(-t[i] / 0.0015) for i in range(n)]
    r1 = bandpass(ex, f0, q)
    r2 = bandpass(ex, f0 * rnd.uniform(1.55, 1.75), q * 1.3)
    ring = [(r1[i] + 0.5 * r2[i]) * math.exp(-t[i] / decay) * 6 for i in range(n)]
    ph, tn = 0.0, []
    for i in range(n):
        f = f0 * (1 - 0.18 * min(1, t[i] / 0.02))
        ph += 2 * math.pi * f / SR
        tn.append(math.sin(ph) * math.exp(-t[i] / (decay * 0.8)) * min(1, t[i] / 0.0004))
    a = bandpass([noise[i] * math.exp(-t[i] / 0.012) for i in range(n)], 2200, 0.8)
    b = [math.sin(2 * math.pi * body_freq * t[i]) * math.exp(-t[i] / 0.008) * min(1, t[i] / 0.001)
         for i in range(n)]
    return finish(mix([x * crack for x in c], ring, [x * tone for x in tn], [x * air * 3 for x in a],
                      [x * body for x in b]), fade=0.006)


def squeeze(seed, length=0.45):
    """Plastic stretching under the stick: stick-slip creaks that speed up."""
    rnd = random.Random(seed)
    n = int(length * SR)
    sig = [0.0] * n
    t, i = 0.0, 0
    while i < n:
        rate = 28 + 70 * (i / n) ** 1.5  # creaks per second, speeding up
        amp = 0.25 + 0.75 * (i / n)
        burst = int(0.006 * SR)
        f = 900 + rnd.uniform(-120, 120) + 600 * (i / n)
        for j in range(burst):
            if i + j < n:
                sig[i + j] += amp * math.sin(2 * math.pi * f * j / SR) * math.exp(-j / (0.0018 * SR)) \
                    + amp * 0.3 * rnd.uniform(-1, 1) * math.exp(-j / (0.0008 * SR))
        i += int(SR / rate * rnd.uniform(0.8, 1.2))
    sig = bandpass(sig, 1400, 0.7)
    return finish(sig, peak=0.6, fade=0.03)


if __name__ == "__main__":
    write("Pop_Crisp", pop(1))  # bright, snappy
    write("Pop_Juicy", pop(2, tock_freq=1600, thump=0.7, thump_freq=140, air=0.4, tock_decay=0.013))  # fuller
    write("Pop_Tiny", pop(3, tock_freq=3100, thump=0.2, air=0.6, tock_decay=0.007, length=0.08))  # small bubble
    write("Pop_Big", pop(4, tock_freq=1250, thump=0.9, thump_freq=110, air=0.55, air_decay=0.035,
                         tock_decay=0.016, length=0.15))  # big bubble / stomp
    write("Squeeze", squeeze(5))
    # Second batch: built around Tiny (the owner's favourite). 4 takes each, played at random.
    for take in range(1, 5):
        write("PopTinyPlus_%d" % take, pop2(100 + take))  # Tiny, but more real
        write("PopSnap_%d" % take, pop2(200 + take, f0=4200, q=5, decay=0.005, tone=0.3, crack=1.4,
                                        double=0.9, air=0.3, body=0.15, length=0.06))  # sharper, snappier
        write("PopPock_%d" % take, pop2(300 + take, f0=2500, q=10, decay=0.011, tone=0.6, crack=0.8,
                                        double=0.4, air=0.3, body=0.35, body_freq=200))  # hollow "pock"
