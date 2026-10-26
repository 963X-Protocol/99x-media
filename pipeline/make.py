"""Render one 99X TikTok episode (1080x1920, voice + captions + music) from an episode JSON.

usage:
  python3 pipeline/make.py pipeline/episodes/<id>.json            # full render -> videos/<id>.mp4
  python3 pipeline/make.py pipeline/episodes/<id>.json --stills   # QA contact sheet only

Writes:
  videos/<id>.mp4                 the finished video (commit this)
  pipeline/work/<id>/sheet.png    contact sheet of key frames (look at it before publishing)
See pipeline/EPISODE_SPEC.md for the JSON format.
"""
import json, os, subprocess, sys
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly, fftconvolve

os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import loopmusic as L                      # noqa: E402
from promomusic import Song, add, B        # noqa: E402

FPS, LEAD, TAIL = 30, 0.15, 1.6
TTS_SR = 24000
CTA = [
    ("Markets this fast? Trade with AI agents on ninety-nine X.", "Markets this fast? Trade with AI agents on 99X."),
    ("Your rules. Your limits. And keys that can never withdraw.", "Your rules. Your limits. Keys that can never withdraw."),
]


def voice(ep, work):
    from kokoro_onnx import Kokoro
    k = Kokoro(str(HERE / "models/kokoro-v1.0.onnx"), str(HERE / "models/voices-v1.0.bin"))
    lines = [(b["say"], b["cap"]) for b in ep["beats"]] + CTA + [(ep.get("followSay", "Follow for the daily brief."), ep.get("followCap", "Follow for the daily brief."))]
    nb = len(ep["beats"])
    parts, chunks, t = [], [], 0.0
    for i, (say, cap) in enumerate(lines):
        a, _ = k.create(say, voice="af_heart", speed=ep.get("speed", 1.06), lang="en-us")
        a = a.astype(np.float32)
        idx = np.where(np.abs(a) > 0.004)[0]
        if len(idx):
            a = a[max(idx[0] - int(0.02 * TTS_SR), 0): idx[-1] + int(0.06 * TTS_SR)]
        d = len(a) / TTS_SR
        chunks.append({"start": round(t, 3), "end": round(t + d, 3), "text": cap})
        parts.append(a); t += d
        if i < len(lines) - 1:
            g = 0.4 if i in (nb - 1, nb + 1) else 0.22
            parts.append(np.zeros(int(g * TTS_SR), np.float32)); t += g
    full = np.concatenate(parts); full = full / np.max(np.abs(full)) * 0.89
    sf.write(work / "vo.wav", full, TTS_SR, subtype="PCM_16")
    tm = {"duration": round(len(full) / TTS_SR, 3), "chunks": chunks}
    (work / "timing.json").write_text(json.dumps(tm, indent=1))
    return tm


def scene_cfg(tm):
    return {"dur": LEAD + tm["duration"] + TAIL, "lead": LEAD, "chunks": tm["chunks"]}


def open_page(b, ep, cfg):
    pg = b.new_page(viewport={"width": 540, "height": 960}, device_scale_factor=2)
    pg.goto((HERE / "template" / "brief.html").as_uri())
    pg.evaluate("([e, c]) => { window.EP = e; window.SCENE = c; }", [ep, cfg])
    pg.evaluate("() => document.fonts.load('11px \"Geist Mono\"')"); pg.evaluate("() => document.fonts.ready"); pg.wait_for_timeout(250)
    return pg


def stills(ep, tm, work):
    from playwright.sync_api import sync_playwright
    cfg = scene_cfg(tm)
    ts = [0.8] + [LEAD + c["end"] - 0.25 for c in tm["chunks"]] + [cfg["dur"] - 0.6]
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = open_page(b, ep, cfg)
        for i, t in enumerate(ts):
            pg.evaluate(f"renderAt({t:.3f})"); pg.screenshot(path=str(work / f"s_{i:02d}.png"))
        b.close()
    cols = 6
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(work / "s_%02d.png"),
                    "-vf", f"scale=300:-1,tile={cols}x{(len(ts) + cols - 1) // cols}", "-frames:v", "1", str(work / "sheet.png")], check=True)
    print("sheet", work / "sheet.png")


def video(ep, tm, work):
    from playwright.sync_api import sync_playwright
    cfg = scene_cfg(tm); n = int(round(cfg["dur"] * FPS))
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = open_page(b, ep, cfg)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                               "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS), str(work / "silent.mp4")], stdin=subprocess.PIPE)
        for i in range(n):
            pg.evaluate(f"renderAt({i / FPS:.5f})"); ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
        ff.stdin.close(); ff.wait(); b.close()
    print("frames", n)


def step_of(tm, b, n):
    ch = tm["chunks"]; dur = ch[b + 1]["start"] - ch[b]["start"]
    return min(2.0, max(0.5, (dur - 1.0) / max(n, 1)))


def buzz():
    t = L.tt(0.35); return np.sign(np.sin(2 * np.pi * 110 * t)) * np.exp(-t / 0.12) * 0.5


def audio(ep, tm, work):
    SR = L.SR
    ct = lambda i, off=0.0: LEAD + tm["chunks"][i]["start"] + off
    dur = LEAD + tm["duration"] + TAIL; nb = len(ep["beats"])
    s = Song(dur); nbeats = int(np.ceil(dur / B)) + 1
    s.pads(0, nbeats); s.groove(0, nbeats, clap=True, sixteen=False)
    fx = [(L.impact(), 0.05, 0.5), (buzz(), 0.05, 0.12), (L.ding(1568, 0.6), 0.1, 0.1), (L.ding(2093, 0.8), 0.25, 0.1), (L.whoosh(0.35, False), 0.0, 0.1)]
    for b, beat in enumerate(ep["beats"]):
        if b: fx.append((L.whoosh(0.35), ct(b, -0.25), 0.1))
        items = beat.get("items") or beat.get("rows") or []
        if beat["type"] in ("cards", "list", "levels"):
            st = step_of(tm, b, len(items)); base = 0.4 if beat["type"] == "levels" else 0.5
            fx += [(L.tick(2200 + 250 * i, 0.02), ct(b, base + i * st), 0.12) for i in range(len(items))]
        elif beat["type"] == "headline":
            fx += [(L.tick(2400, 0.02), ct(b, 1.8 + i * 1.2), 0.12) for i in range(len(items))]
        if beat["type"] == "hero" and b:
            fx.append((L.impact(), ct(b, 0.1), 0.3))
        if beat["type"] == "bars":
            fx.append((L.impact(), ct(b, 0.4), 0.3))
    fx += [(L.whoosh(0.35), ct(nb, -0.25), 0.1), (L.tick(3000), ct(nb, 1.0), 0.12), (L.ding(2093, 0.6), ct(nb, 1.2), 0.08),
           (buzz(), ct(nb + 1, 1.3), 0.18), (L.impact(), ct(nb + 2, -0.1), 0.35)]
    for sig, t0, g in fx:
        add(s.sfx, sig, t0, g)
    n = s.n
    rng = np.random.default_rng(5)
    bed = s.drums * 0.8 + s.bass + L.lp(s.arp + s.pad, 2400)
    ir = rng.standard_normal(int(1.4 * SR)) * np.exp(-L.tt(1.4) / 0.35)
    bed = bed + fftconvolve(bed, L.lp(ir, 5000) * 0.01)[:n]; bed = bed / (np.max(np.abs(bed)) or 1)
    sfx = s.sfx + fftconvolve(s.sfx, L.lp(ir, 6000) * 0.006)[:n]
    vo = np.zeros(n); a, sr = sf.read(work / "vo.wav"); add(vo, resample_poly(a, SR, sr), LEAD, 1.0)
    win = int(0.05 * SR); env = np.sqrt(np.convolve(vo ** 2, np.ones(win) / win, mode="same")); env /= env.max() or 1
    sm = np.zeros(n); prev = 0.0
    for i in range(0, n, 32):
        c = 0.9 if env[i] > prev else 0.997; prev = c * prev + (1 - c) * env[i]; sm[i:i + 32] = prev
    tsec = np.arange(n) / SR
    m = (vo + bed * 0.16 * (1 - 0.65 * np.clip(sm * 3, 0, 1)) + sfx * 0.7) * np.clip((dur - tsec) / 1.2, 0, 1)
    m = m[: int(round(dur * FPS)) * SR // FPS]; m = m / (np.max(np.abs(m)) or 1) * 0.89
    sf.write(work / "mix.wav", np.stack([m, np.roll(m, int(0.005 * SR)) * 0.98 + m * 0.02], 1).astype(np.float32), SR, subtype="PCM_24")


def mux(ep, work):
    out = REPO / "videos" / f"{ep['id']}.mp4"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(work / "mix.wav"), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = r.stderr[r.stderr.rindex("{"): r.stderr.rindex("}") + 1]; d = json.loads(js)
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}"
          f":measured_thresh={d['input_thresh']}:offset={d['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(work / "silent.mp4"), "-i", str(work / "mix.wav"), "-af", af, "-ar", "48000",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)], check=True)
    print("video", out, round(out.stat().st_size / 1e6, 1), "MB")


def main():
    ep = json.loads(Path(sys.argv[1]).read_text())
    for b in ep["beats"]:
        assert b["type"] in ("hero", "headline", "cards", "list", "bars", "levels", "quote"), b["type"]
    work = HERE / "work" / ep["id"]; work.mkdir(parents=True, exist_ok=True)
    tm = voice(ep, work)
    print("voice", tm["duration"], "s")
    stills(ep, tm, work)
    if "--stills" in sys.argv:
        return
    video(ep, tm, work); audio(ep, tm, work); mux(ep, work)


if __name__ == "__main__":
    main()
