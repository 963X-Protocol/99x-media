"""Seamless background music + sound effects for the 15.53 s trade-to-earn loops.

32 beats per loop (~123.6 BPM). Each track is built over three loops and the middle
loop is kept, so reverb/echo tails wrap and the loop point is inaudible.
usage: python3 loopmusic.py everytrade tradelog coinflip split
"""
import sys
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
DUR = 466 / 30.0
B = DUR / 32
N = int(round(DUR * SR))
TOT = 3 * N
rng = np.random.default_rng(7)


def lp(x, f): return sosfilt(butter(2, f, "lowpass", fs=SR, output="sos"), x)
def hp(x, f): return sosfilt(butter(2, f, "highpass", fs=SR, output="sos"), x)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], "bandpass", fs=SR, output="sos"), x)
def midi(n): return 440 * 2 ** ((n - 69) / 12)
def tt(d): return np.arange(int(d * SR)) / SR


def add(buf, sig, t0, g=1.0):
    """Place `sig` at time t0 (seconds) in every one of the three loops."""
    for k in range(3):
        i = int((t0 + k * DUR) * SR)
        if i < 0 or i >= len(buf):
            continue
        j = min(len(buf), i + len(sig))
        buf[i:j] += sig[: j - i] * g


# ---------------- instruments
def kick():
    t = tt(0.42)
    return np.sin(2 * np.pi * (46 * t + 70 * 0.045 * (1 - np.exp(-t / 0.045)))) * np.exp(-t / 0.2)

def hat():
    n = rng.standard_normal(int(0.05 * SR))
    return hp(n, 7500) * np.exp(-tt(0.05) / 0.011)

def clap():
    n = bp(rng.standard_normal(int(0.25 * SR)), 900, 4000)
    env = np.exp(-tt(0.25) / 0.06)
    for d in (0.0, 0.012, 0.024):
        env[int(d * SR):int(d * SR) + 60] += 0.6
    return n * env * 0.6

def pluck(f, d=0.35):
    t = tt(d)
    return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t)) * np.exp(-t / 0.09)

def padnote(f, d):
    t = tt(d)
    s = sum(np.sin(2 * np.pi * f * h * (1 + det) * t + h) / h for h in range(1, 6) for det in (-0.003, 0.003))
    env = np.minimum(1, t / 0.5) * np.minimum(1, (d - t) / 0.6)
    return s * env

def bassnote(f, d):
    t = tt(d)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
    return s * np.minimum(1, t / 0.01) * np.exp(-t / (d * 0.9))

def tick(f=2600, d=0.03):
    t = tt(d)
    return np.sin(2 * np.pi * f * t) * np.exp(-t / 0.006)

def ding(f=1318.5, d=1.0):
    t = tt(d)
    return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t) + 0.25 * np.sin(2 * np.pi * f * 2.01 * t)) * np.exp(-t / 0.3)

def clink():
    t = tt(0.6)
    return sum(np.sin(2 * np.pi * f * t) * np.exp(-t / dd) for f, dd in ((2100, 0.12), (3370, 0.08), (5200, 0.05)))

def whoosh(d=0.8, up=True):
    n = bp(rng.standard_normal(int(d * SR)), 500, 6000)
    env = np.linspace(0, 1, len(n)) ** 2 if up else np.linspace(1, 0, len(n)) ** 2
    return n * env * np.hanning(len(n)) ** 0.3

def impact():
    t = tt(0.9)
    return np.sin(2 * np.pi * (38 * t + 50 * 0.07 * (1 - np.exp(-t / 0.07)))) * np.exp(-t / 0.35) + lp(rng.standard_normal(len(t)), 1200) * np.exp(-t / 0.08) * 0.4


# ---------------- groove
CHORDS = [[57, 60, 64], [53, 57, 60], [55, 60, 64], [55, 59, 62]]   # Am F C G, 2 bars each
ROOTS = [45, 41, 48, 43]


def groove(drums=True, drum_from=0.0, drum_to=99.0):
    mus = np.zeros(TOT)
    k, h, c = kick(), hat(), clap()
    for b in range(32):
        t0 = b * B
        bar = b // 4
        ch = (bar // 2) % 4
        if drums and drum_from <= t0 < drum_to:
            add(mus, k, t0, 0.55)
            add(mus, h, t0 + B / 2, 0.12)
            if b % 2 == 1:
                add(mus, c, t0, 0.16)
        # bass on the off-eighths
        add(mus, bassnote(midi(ROOTS[ch] - 12), B * 0.45), t0 + B / 2, 0.28)
        # 16th arp
        for s in range(4):
            n = CHORDS[ch][(b * 4 + s) % 3] + 12 + (12 if (b * 4 + s) % 6 == 5 else 0)
            add(mus, pluck(midi(n)), t0 + s * B / 4, 0.045)
    # pads, one chord per two bars
    pad = np.zeros(TOT)
    for i in range(4):
        for n in CHORDS[i]:
            add(pad, padnote(midi(n), 8 * B + 0.6), i * 8 * B, 0.035)
    return mus, pad


def finish(mus, pad, sfx, pump=True, filt=None):
    # sidechain-style pump on pads and bass from the kick grid
    if pump:
        tm = (np.arange(TOT) / SR) % B
        env = 1 - 0.55 * np.exp(-tm / 0.11)
        pad = pad * env
        mus = mus * (0.75 + 0.25 * env)
    bed = mus + lp(pad, 2600)
    if filt is not None:
        bed = filt(bed)
    ir = rng.standard_normal(int(1.6 * SR)) * np.exp(-tt(1.6) / 0.4)
    bed = bed + fftconvolve(bed, lp(ir, 5000) * 0.01)[:TOT]
    sfx = sfx + fftconvolve(sfx, lp(ir, 6000) * 0.008)[:TOT]
    mix = bed + sfx
    mid = mix[N:2 * N]
    mid = mid / (np.max(np.abs(mid)) or 1) * 0.89
    st = np.stack([mid, np.roll(mid, int(0.006 * SR)) * 0.98 + mid * 0.02], 1)
    return st


# ---------------- per-clip arrangements
def everytrade():
    mus, pad = groove()
    sfx = np.zeros(TOT)
    for s in (0.7, 8.6):
        add(sfx, whoosh(1.2, True), s + 1.25, 0.10)          # riser into the tag
        # counter ticks, slowing down like the eased number
        for i in range(40):
            p = 1 - (1 - i / 40) ** 0.25
            add(sfx, tick(2400 + 600 * (i % 2)), s + p * 2.4, 0.10)
        add(sfx, impact(), s + 2.45, 0.35)
        add(sfx, ding(1760), s + 2.5, 0.10)
    return finish(mus, pad, sfx)


def tradelog():
    mus, pad = groove()
    sfx = np.zeros(TOT)
    for r in range(16):
        t0 = r * DUR / 16
        add(sfx, tick(3000, 0.04), t0, 0.16)
        add(sfx, ding(2093, 0.4), t0 + 0.06, 0.05)
    return finish(mus, pad, sfx)


def coinflip():
    H = DUR / 2
    mus, pad = groove(drums=True)
    sfx = np.zeros(TOT)
    for half in (0, 1):
        o = half * H
        add(sfx, whoosh(0.5, True), o + 4 * B - 0.35, 0.18)          # toss
        for s in range(9):                                              # spin flutter
            add(sfx, tick(1500 + 200 * (s % 3), 0.02), o + 4 * B + s * (3 * B / 9), 0.06)
        add(sfx, clink(), o + 7 * B, 0.22)                              # landing
        add(sfx, whoosh(0.35, False), o + 9 * B, 0.12)                  # flip
        add(sfx, ding(1318.5, 1.2), o + 10 * B, 0.20)                   # 99X reveal
        add(sfx, ding(1975.5, 1.0), o + 10 * B + 0.08, 0.08)
    return finish(mus, pad, sfx)


def split():
    mus, pad = groove(drums=True, drum_from=9 * B, drum_to=31 * B)
    sfx = np.zeros(TOT)
    for b in (2, 4, 6):
        add(sfx, tick(900, 0.05), b * B, 0.12)                          # muted left side
    add(sfx, impact(), 9 * B, 0.30)                                     # 99X arrives
    for b in (11, 13):
        add(sfx, ding(1568, 0.8), b * B, 0.16)                          # +99X pops
    add(sfx, whoosh(0.5, False), 0.6, 0.08)                             # reset swish

    def filt(x):
        tl = (np.arange(TOT) / SR) % DUR
        dark = lp(x, 500)
        # bright at the seam (finished state), darkens when the screen resets, opens as 99X appears
        k = np.where(tl < 0.6, 1.0, 1 - np.clip((tl - 0.6) / 0.4, 0, 1))
        k = np.maximum(k, np.clip((tl - 8.6 * B) / (0.6 * B), 0, 1))
        return dark * (1 - k) + x * k
    return finish(mus, pad, sfx, filt=filt)


if __name__ == "__main__":
    for name in sys.argv[1:]:
        st = globals()[name]()
        sf.write(f"loopaudio_{name}.wav", st.astype(np.float32), SR, subtype="PCM_24")
        print(name, round(len(st) / SR, 3), "s")
