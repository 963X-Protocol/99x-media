"""Music + sound effects for the 99X House promos, 128 BPM, synced to the visuals.

usage: python3 promomusic.py house_launch house_winloss
"""
import json
import sys
import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve

import loopmusic as L

SR = L.SR
B = 60 / 128
DUR = {"house_launch": 52 * B, "house_winloss": 40 * B}
CH = [[57, 60, 64], [53, 57, 60], [55, 60, 64], [55, 59, 62]]   # Am F C G, one bar each
ROOTS = [45, 41, 48, 43]
rng = np.random.default_rng(128)


def add(buf, sig, t0, g=1.0):
    i = int(t0 * SR)
    if i < 0 or i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * g


def crash():
    t = L.tt(1.6)
    return L.hp(rng.standard_normal(len(t)), 4000) * np.exp(-t / 0.55)


class Song:
    def __init__(self, dur):
        self.n = int(dur * SR) + SR
        self.drums, self.bass, self.arp, self.pad, self.sfx = (np.zeros(self.n) for _ in range(5))

    def groove(self, b0, b1, kick=True, clap=True, sixteen=False, bass=True, arp=True, octave=False):
        for b in range(int(b0), int(b1)):
            t0, ch = b * B, (b // 4) % 4
            if kick:
                add(self.drums, L.kick(), t0, 0.55)
            add(self.drums, L.hat(), t0 + B / 2, 0.12)
            if sixteen:
                for s in (1, 3):
                    add(self.drums, L.hat(), t0 + s * B / 4, 0.06)
            if clap and b % 2 == 1:
                add(self.drums, L.clap(), t0, 0.17)
            if bass:
                add(self.bass, L.bassnote(L.midi(ROOTS[ch] - 12), B * 0.45), t0 + B / 2, 0.3)
            if arp:
                for s in range(4):
                    i = b * 4 + s
                    n = CH[ch][i % 3] + 12 + (12 if (octave and i % 6 == 5) else 0)
                    add(self.arp, L.pluck(L.midi(n)), t0 + s * B / 4, 0.045)

    def pads(self, b0, b1):
        for bar in range(int(b0) // 4, int(np.ceil(b1 / 4))):
            for n in CH[bar % 4]:
                add(self.pad, L.padnote(L.midi(n), 4 * B + 0.5), bar * 4 * B, 0.04)

    def roll(self, b0, b1):
        b, step = b0, 0.5
        while b < b1:
            add(self.drums, L.clap(), b * B, 0.06 + 0.12 * (b - b0) / (b1 - b0))
            b += step
            step = max(0.125, step * 0.8)

    def mix(self, open_curve, fade_out_from=None):
        tsec = np.arange(self.n) / SR
        k = open_curve(tsec)
        tonal = self.arp + self.pad
        tonal = L.lp(tonal, 450) * (1 - k) + L.lp(tonal, 3200) * k
        bed = self.drums + self.bass + tonal
        ir = rng.standard_normal(int(1.8 * SR)) * np.exp(-L.tt(1.8) / 0.45)
        bed = bed + fftconvolve(bed, L.lp(ir, 5000) * 0.01)[: self.n]
        sfx = self.sfx + fftconvolve(self.sfx, L.lp(ir, 6000) * 0.008)[: self.n]
        m = bed + sfx
        if fade_out_from is not None:
            m *= np.clip(1 - (tsec - fade_out_from) / (tsec[-1] - SR / SR - fade_out_from), 0, 1)
        m /= np.max(np.abs(m)) or 1
        m *= 0.89
        return np.stack([m, np.roll(m, int(0.006 * SR)) * 0.98 + m * 0.02], 1)


def house_launch():
    s = Song(DUR["house_launch"])
    s.pads(0, 52)
    s.groove(0, 8, kick=False, clap=False, bass=False)
    s.roll(6, 8)
    add(s.sfx, L.whoosh(4 * B, True), 4 * B, 0.12)
    s.groove(8, 15)
    s.groove(16, 24)
    s.groove(24, 44, sixteen=True, octave=True)
    for b in (8, 38, 44):
        add(s.sfx, L.impact(), b * B, 0.45 if b != 44 else 0.3)
        add(s.sfx, crash(), b * B, 0.08)
    add(s.sfx, L.ding(1318.5, 1.2), 8 * B, 0.12)
    for b, f in ((16, 1568), (20, 1760), (24, 1976), (28, 2093), (32, 2349)):
        add(s.sfx, L.impact(), b * B, 0.16)
        add(s.sfx, L.ding(f, 0.8), b * B, 0.09)
    for i in range(int(3.5 * B / 0.1)):                              # price ticks during live pricing
        add(s.sfx, L.tick(2600 + 400 * (i % 2), 0.025), 28 * B + i * 0.1, 0.05)
    add(s.sfx, L.whoosh(2.5, True), 32.3 * B, 0.07)                   # pool filling
    add(s.sfx, L.ding(1318.5, 1.6), 46 * B, 0.12)                     # cta
    add(s.bass, L.bassnote(L.midi(33), 6 * B), 44 * B, 0.35)          # held low A under the end card
    curve = lambda t: np.clip(t / (8 * B), 0, 1) ** 2
    return s.mix(curve, fade_out_from=48 * B)


def house_winloss():
    s = Song(DUR["house_winloss"])
    s.pads(0, 40)
    s.groove(0, 2, kick=False, clap=False)
    s.groove(2, 24)
    s.groove(24, 30, sixteen=True, octave=True)
    s.groove(30, 32, sixteen=True, octave=True, clap=False)
    s.roll(30, 32)
    add(s.sfx, L.impact(), 32 * B, 0.5)
    add(s.sfx, crash(), 32 * B, 0.09)
    add(s.sfx, L.impact(), 35.5 * B, 0.3)
    add(s.sfx, L.ding(1318.5, 1.6), 37 * B, 0.12)
    add(s.bass, L.bassnote(L.midi(33), 8 * B), 32 * B, 0.35)
    for e in json.load(open("events_house_winloss.json")):
        g = 0.75 if e["t"] > 24 * B else 1.0
        if e["big"]:
            add(s.sfx, L.impact(), e["t"], 0.2)
            add(s.sfx, L.ding(1568, 1.0), e["t"], 0.09)
            add(s.sfx, L.ding(2093, 1.0), e["t"] + 0.05, 0.08)
        elif e["win"]:
            add(s.sfx, L.ding(2093, 0.35), e["t"], 0.055 * g)          # cash ding
        else:
            add(s.sfx, L.clink(), e["t"], 0.07 * g)                   # coin clink: 99X farmed
    curve = lambda t: np.clip(t / (2 * B), 0, 1)
    return s.mix(curve, fade_out_from=37.5 * B)


if __name__ == "__main__":
    for name in sys.argv[1:]:
        st = globals()[name]()[: int(round(DUR[name] * 30)) * SR // 30]
        sf.write(f"promoaudio_{name}.wav", st.astype(np.float32), SR, subtype="PCM_24")
        print(name, round(len(st) / SR, 3), "s")
