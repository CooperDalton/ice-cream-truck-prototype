"""Synthesizes every sound effect and the truck's music-box jingle for the Unity project, PS1-style (22 kHz, 16-bit mono,
crunchy). Nothing is sampled; rerun to regenerate.

python3 sfx_synth.py  ->  Zombie Ice Cream Truck/Assets/Audio/*.wav

The jingle is Scott Joplin's "The Entertainer" (1902, public domain), played on a synthesized music box.
"""
import math
import os
import wave

import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../Zombie Ice Cream Truck/Assets/Audio")
RATE = 22050
rng = np.random.default_rng(11)


# ------------------------------------------------------------------------------------------------ building blocks

def t_axis(seconds):
    return np.arange(int(seconds * RATE)) / RATE


def noise(seconds):
    return rng.uniform(-1, 1, int(seconds * RATE))


def env(seconds, attack=0.002, decay=0.2, curve=1.0):
    t = t_axis(seconds)
    a = np.clip(t / max(attack, 1e-5), 0, 1)
    return a * np.exp(-np.maximum(t - attack, 0) / decay) ** curve


def sweep(seconds, f0, f1, shape="sine", exp=True):
    t = t_axis(seconds)
    freq = f0 * (f1 / f0) ** (t / seconds) if exp else f0 + (f1 - f0) * t / seconds
    phase = np.cumsum(freq) / RATE * 2 * np.pi
    if shape == "sine":
        return np.sin(phase)
    if shape == "square":
        return np.sign(np.sin(phase))
    if shape == "saw":
        return 2 * ((phase / (2 * np.pi)) % 1) - 1
    if shape == "tri":
        return 2 * np.abs(2 * ((phase / (2 * np.pi)) % 1) - 1) - 1
    raise ValueError(shape)


def tone(seconds, freq, shape="sine"):
    return sweep(seconds, freq, freq, shape)


def lowpass(x, cutoff):
    """One-pole lowpass; cutoff may be a number or an array (per-sample sweep)."""
    cut = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    a = 1 - np.exp(-2 * np.pi * cut / RATE)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def bandpass(x, freq, q):
    """RBJ biquad band-pass (constant peak gain); freq may sweep per sample."""
    f = np.broadcast_to(np.asarray(freq, dtype=float), x.shape)
    y = np.zeros_like(x)
    x1 = x2 = y1 = y2 = 0.0
    for i in range(len(x)):
        w = 2 * np.pi * f[i] / RATE
        alpha = math.sin(w) / (2 * q)
        cw = math.cos(w)
        a0 = 1 + alpha
        out = (alpha * x[i] - alpha * x2 + 2 * cw * y1 - (1 - alpha) * y2) / a0
        x2, x1 = x1, x[i]
        y2, y1 = y1, out
        y[i] = out
    return y


def formant(source, vowel):
    """Very rough vowel shaping with three band-passes."""
    table = {"o": (450, 800, 2830), "a": (730, 1090, 2440), "u": (325, 700, 2530), "e": (530, 1840, 2480)}
    f1, f2, f3 = table[vowel]
    return bandpass(source, f1, 6) + 0.6 * bandpass(source, f2, 8) + 0.25 * bandpass(source, f3, 10)


def crush(x, bits=8, hold=2):
    """PS1-ish grit: sample-and-hold plus bit reduction."""
    held = np.repeat(x[::hold], hold)[:len(x)]
    steps = 2 ** (bits - 1)
    return np.round(held * steps) / steps


def mix(*parts):
    length = max(len(p) for p in parts)
    out = np.zeros(length)
    for p in parts:
        out[:len(p)] += p
    return out


def layer(parts):
    return mix(*list(parts))


def at(x, seconds, total=None):
    pad = np.zeros(int(seconds * RATE))
    out = np.concatenate([pad, x])
    if total is not None:
        out = np.pad(out, (0, max(0, int(total * RATE) - len(out))))
    return out


def fit(x, seconds):
    n = int(seconds * RATE)
    return x[:n] if len(x) >= n else np.pad(x, (0, n - len(x)))


def normalize(x, peak=0.9):
    m = np.max(np.abs(x))
    return x if m == 0 else x / m * peak


def soft_clip(x, drive=1.5):
    return np.tanh(x * drive) / np.tanh(drive)


def note_freq(name):
    names = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
    pitch, octave = name[:-1], int(name[-1])
    return 440 * 2 ** ((names[pitch] + (octave - 4) * 12 - 9) / 12)


def write(name, x, peak=0.9, gritty=True):
    x = normalize(x, peak)
    if gritty:
        x = crush(x, bits=10, hold=1)
    data = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data)


def seamless(x, fade):
    """Makes a loop by crossfading the tail over the head."""
    n = int(fade * RATE)
    body, tail = x[:-n].copy(), x[-n:]
    ramp = np.linspace(0, 1, n)
    body[:n] = body[:n] * ramp + tail * (1 - ramp)
    return body


# ------------------------------------------------------------------------------------------------ weapons

def gunshot(length, thump_hz, crack_cut, decay, body_decay, wet=0.0):
    crack = lowpass(noise(length), crack_cut) * env(length, 0.0005, decay)
    thump = sweep(length, thump_hz, thump_hz * 0.35) * env(length, 0.001, body_decay)
    parts = [crack * 1.3, thump]
    if wet:
        parts.append(squelch(length, 0.6) * wet)
    return soft_clip(mix(*parts), 2.2)


def squelch(length=0.35, decay=0.12, f0=1400, f1=260):
    source = noise(length) * 0.6 + sweep(length, 90, 60, "saw") * 0.4
    return bandpass(source, np.geomspace(f0, f1, int(length * RATE)), 4) * env(length, 0.003, decay)


def pistol():
    return mix(gunshot(0.32, 180, 5000, 0.05, 0.09), at(squelch(0.2, 0.05, 1800, 600) * 0.35, 0.02))


def shotgun():
    boom = gunshot(0.7, 110, 3500, 0.12, 0.2)
    rattle = lowpass(noise(0.6), 1500) * env(0.6, 0.01, 0.18) * 0.5
    return mix(boom, at(rattle, 0.03))


def smg():
    return gunshot(0.14, 260, 7000, 0.025, 0.04)


def sniper():
    crack = gunshot(0.6, 140, 9000, 0.04, 0.12)
    ting = (tone(1.2, 2093) + 0.6 * tone(1.2, 2093 * 2.76) + 0.3 * tone(1.2, 2093 * 5.4)) * env(1.2, 0.001, 0.35) * 0.35
    return mix(crack, at(ting, 0.01))


def launcher():
    fwoomp = sweep(0.45, 70, 220) * env(0.45, 0.01, 0.15)
    air = bandpass(noise(0.45), np.geomspace(300, 1500, int(0.45 * RATE)), 2) * env(0.45, 0.02, 0.12) * 0.7
    return soft_clip(mix(fwoomp, air), 1.8)


def harpoon():
    # Karplus-Strong twang plus a whoosh.
    period = int(RATE / 110)
    buf = list(rng.uniform(-1, 1, period))
    out = np.zeros(int(0.9 * RATE))
    for i in range(len(out)):
        out[i] = buf[i % period]
        buf[i % period] = 0.996 * 0.5 * (buf[i % period] + buf[(i + 1) % period])
    whoosh = bandpass(noise(0.4), np.geomspace(2500, 500, int(0.4 * RATE)), 3) * env(0.4, 0.05, 0.1)
    return mix(out * 0.8, whoosh * 0.6)


def minigun():
    return gunshot(0.1, 300, 6000, 0.02, 0.03)


def empty_click():
    return highpass(noise(0.05), 2000) * env(0.05, 0.0005, 0.006)


def reload():
    click = lambda: highpass(noise(0.08), 1500) * env(0.08, 0.0005, 0.012)
    slide = bandpass(noise(0.18), np.geomspace(800, 2400, int(0.18 * RATE)), 3) * env(0.18, 0.04, 0.06) * 0.5
    plop = squelch(0.15, 0.05, 900, 300) * 0.4
    return mix(click(), at(slide, 0.06), at(plop, 0.2), at(click() * 1.2, 0.32))


def throw():
    return bandpass(noise(0.35), np.geomspace(600, 2200, int(0.35 * RATE)), 2.5) * env(0.35, 0.12, 0.08)


# ------------------------------------------------------------------------------------------------ hits and gore

def hit(seed_shift):
    f0 = 1300 + seed_shift * 250
    return mix(squelch(0.3, 0.07, f0, 250), lowpass(noise(0.08), 3000) * env(0.08, 0.0005, 0.015) * 0.6)


def headshot():
    pop = sweep(0.25, 900, 120) * env(0.25, 0.001, 0.05)
    ding = (tone(1.0, 1568) + 0.5 * tone(1.0, 1568 * 2.0) + 0.3 * tone(1.0, 2349)) * env(1.0, 0.002, 0.25) * 0.55
    return mix(pop, squelch(0.35, 0.1, 2000, 300) * 0.8, at(ding, 0.03))


def kill():
    crunch = lowpass(noise(0.25), 2500) * env(0.25, 0.001, 0.05)
    bones = layer(at(highpass(noise(0.04), 2500) * env(0.04, 0.0005, 0.008), d) for d in (0.0, 0.035, 0.07, 0.12))
    return soft_clip(mix(squelch(0.6, 0.18, 1600, 140) * 1.2, crunch, bones * 0.7), 1.6)


def splat_land():
    return squelch(0.25, 0.06, 900, 200)


def explosion(length=1.8, sub=55):
    boom = lowpass(noise(length), np.geomspace(4000, 200, int(length * RATE))) * env(length, 0.002, 0.45)
    sub_drop = sweep(length, sub * 2, sub * 0.5) * env(length, 0.005, 0.5)
    crackle = highpass(noise(length), 3000) * (rng.uniform(0, 1, int(length * RATE)) > 0.985) * env(length, 0.05, 0.4)
    return soft_clip(mix(boom * 1.4, sub_drop * 1.2, crackle * 0.8), 2.5)


def bloater_pop():
    pop = sweep(0.4, 300, 40) * env(0.4, 0.001, 0.12)
    gurgle = layer(at(squelch(0.18, 0.05, 700 + 150 * k, 200) * 0.5, 0.15 + 0.07 * k) for k in range(6))
    return soft_clip(mix(explosion(1.4, 45) * 0.8, pop * 1.2, squelch(0.8, 0.25, 1200, 100) * 1.3, gurgle), 2.0)


def freeze():
    shimmer = layer(at(tone(0.9, f) * env(0.9, 0.002, 0.25) * 0.4, d)
                  for d, f in ((0, 2637), (0.05, 3136), (0.1, 3951), (0.15, 4699), (0.2, 3520)))
    crack = highpass(noise(0.3), 2500) * env(0.3, 0.001, 0.04)
    return mix(crack, shimmer)


def ice_shatter():
    tinkles = layer(at(tone(0.3, f) * env(0.3, 0.001, 0.06) * 0.35, d)
                  for d, f in zip(rng.uniform(0, 0.25, 12), rng.uniform(2500, 6000, 12)))
    return mix(highpass(noise(0.4), 2000) * env(0.4, 0.001, 0.08), tinkles)


# ------------------------------------------------------------------------------------------------ zombies and survivors

def groan(f0, f1, length, vowel, wobble=6.0):
    t = t_axis(length)
    freq = np.geomspace(f0, f1, len(t)) * (1 + 0.04 * np.sin(2 * np.pi * wobble * t) + 0.02 * rng.uniform(-1, 1, len(t)))
    source = 2 * ((np.cumsum(freq) / RATE) % 1) - 1
    source += 0.15 * noise(length)
    swell = np.sin(np.pi * np.clip(t / length, 0, 1)) ** 0.7
    return soft_clip(formant(source, vowel) * swell, 1.8)


def snarl():
    source = sweep(0.5, 140, 90, "saw") + 0.8 * noise(0.5)
    return soft_clip(formant(source, "a") * env(0.5, 0.02, 0.18), 2.5)


def hurt():
    return formant(sweep(0.3, 220, 140, "saw") + 0.1 * noise(0.3), "u") * env(0.3, 0.01, 0.1)


def death():
    notes = [(0, "E4"), (0.22, "C4"), (0.44, "A3"), (0.66, "F3")]
    return mix(*(at(tone(0.5, note_freq(n), "square") * env(0.5, 0.005, 0.18) * 0.4, d) for d, n in notes))


def revive():
    notes = [(0, "C5"), (0.08, "E5"), (0.16, "G5"), (0.24, "C6"), (0.32, "E6")]
    return mix(*(at(tone(0.4, note_freq(n), "square") * env(0.4, 0.003, 0.12) * 0.35, d) for d, n in notes))


def wipe():
    # Sad trombone: four sagging saw notes through an "wah" filter.
    parts = []
    for i, (n, length) in enumerate((("D4", 0.4), ("C#4", 0.4), ("C4", 0.4), ("B3", 1.3))):
        f = note_freq(n)
        t = t_axis(length)
        vib = 1 + 0.03 * np.sin(2 * np.pi * 6 * t) * (i == 3)
        src = 2 * ((np.cumsum(f * vib) / RATE) % 1) - 1
        parts.append(at(bandpass(src, np.linspace(400, 1400, len(t)), 2) * env(length, 0.03, length * 0.8), i * 0.42))
    return mix(*parts)


# ------------------------------------------------------------------------------------------------ truck and world

def engine_loop():
    length = 2.2
    t = t_axis(length)
    rpm = 38 * (1 + 0.03 * np.sin(2 * np.pi * 1.3 * t))
    phase = np.cumsum(rpm) / RATE
    pulses = np.exp(-((phase % 1) * 9))  # one combustion pulse per cycle
    rumble = lowpass(pulses * 2 - 0.5 + 0.35 * noise(length), 900)
    rattle = bandpass(noise(length), 2400, 4) * 0.08
    return seamless(soft_clip(rumble + rattle, 2.0), 0.2)


def bell():
    partials = [(1, 1.0), (2.0, 0.6), (2.76, 0.4), (5.4, 0.25), (8.9, 0.1)]
    ding = lambda f: sum(tone(1.4, f * k) * a for k, a in partials) * env(1.4, 0.001, 0.4)
    return mix(ding(1318), at(ding(1318), 0.28))


def pickup():
    notes = [(0, "A5"), (0.05, "C#6"), (0.1, "E6")]
    return mix(*(at(tone(0.15, note_freq(n), "square") * env(0.15, 0.002, 0.05) * 0.4, d) for d, n in notes))


def kaching():
    clunk = lowpass(noise(0.12), 1500) * env(0.12, 0.001, 0.03)
    chime = (tone(1.0, 2637) + 0.7 * tone(1.0, 3520) + 0.4 * tone(1.0, 5274)) * env(1.0, 0.002, 0.3) * 0.5
    coins = layer(at(tone(0.12, f) * env(0.12, 0.001, 0.03) * 0.3, d) for d, f in zip(np.linspace(0.12, 0.45, 8), rng.uniform(3500, 6500, 8)))
    return mix(clunk, at(chime, 0.08), coins)


def tip():
    notes = [(0, "E6"), (0.06, "B6")]
    return mix(*(at(tone(0.3, note_freq(n), "tri") * env(0.3, 0.002, 0.1) * 0.4, d) for d, n in notes))


def crank():
    clicks = [at(highpass(noise(0.03), 1800) * env(0.03, 0.0005, 0.006) * (1.0 if k % 2 else 0.6), k * 0.07) for k in range(6)]
    creak = bandpass(sweep(0.42, 300, 360, "saw"), 900, 6) * 0.15
    return mix(*clicks, creak)


def scoop():
    scrape = bandpass(noise(0.3), np.geomspace(1500, 3500, int(0.3 * RATE)), 5) * env(0.3, 0.05, 0.08)
    return mix(scrape * 0.6, at(squelch(0.2, 0.05, 900, 300) * 0.6, 0.22))


def crash():
    thud = sweep(0.6, 90, 35) * env(0.6, 0.001, 0.15)
    crunch = lowpass(noise(0.6), 3500) * env(0.6, 0.001, 0.12)
    ring = sum(tone(1.2, f) * a for f, a in ((310, 0.5), (523, 0.35), (797, 0.3), (1290, 0.2))) * env(1.2, 0.002, 0.35) * 0.4
    glass = ice_shatter() * 0.5
    return soft_clip(mix(thud * 1.4, crunch * 1.2, ring, at(glass, 0.05)), 2.2)


def depot_jingle():
    notes = [(0, "C5"), (0.12, "E5"), (0.24, "G5"), (0.36, "C6"), (0.6, "G5"), (0.72, "C6")]
    return mix(*(at(tone(0.5, note_freq(n), "square") * env(0.5, 0.003, 0.15) * 0.35, d) for d, n in notes))


def gib_bounce():
    return squelch(0.15, 0.03, 1200, 400)


# ------------------------------------------------------------------------------------------------ hot spots, fuel and shop

def hose():
    spurt = squelch(0.16, 0.05, 1100, 500) * 0.9
    hiss = bandpass(noise(0.16), 3200, 2) * env(0.16, 0.005, 0.05) * 0.5
    return mix(spurt, hiss)


def bazooka():
    thump = sweep(0.9, 55, 140) * env(0.9, 0.005, 0.2)
    roar = bandpass(noise(0.9), np.geomspace(250, 2200, int(0.9 * RATE)), 1.5) * env(0.9, 0.03, 0.35) * 0.9
    return soft_clip(mix(thump * 1.3, roar), 2.2)


def jackpot_shot():
    ding = (tone(0.4, 1760, "square") * 0.3 + tone(0.4, 2637) * 0.3) * env(0.4, 0.001, 0.08)
    return mix(pistol() * 0.8, at(ding, 0.02))


def fanfare(notes, step, shape="square", length=0.35):
    return mix(*(at(tone(length, note_freq(n), shape) * env(length, 0.003, 0.12) * 0.35, i * step) for i, n in enumerate(notes)))


def jackpot_win():
    return mix(fanfare(["C5", "E5", "G5", "C6", "G5", "C6", "E6"], 0.07), at(kaching() * 0.7, 0.3))


def melee_swing():
    return bandpass(noise(0.22), np.geomspace(400, 1800, int(0.22 * RATE)), 3) * env(0.22, 0.06, 0.05)


def melee_hit():
    thwack = sweep(0.25, 160, 60) * env(0.25, 0.001, 0.05)
    return soft_clip(mix(thwack * 1.2, squelch(0.3, 0.07, 1500, 250), lowpass(noise(0.06), 2500) * env(0.06, 0.0005, 0.012) * 0.8), 1.8)


def slots_spin():
    length = 1.9
    out = np.zeros(int(length * RATE))
    t = 0.0
    k = 0
    while t < length - 0.05:
        tick = at(highpass(noise(0.03), 2500) * env(0.03, 0.0005, 0.005) * (1.0 if k % 3 == 0 else 0.6), t)
        out[:len(tick)] += tick[:len(out)]
        t += 0.045 + 0.02 * (t / length) ** 2
        k += 1
    whirr = bandpass(sweep(length, 180, 120, "saw"), 700, 5) * 0.12
    return mix(out, whirr)


def slots_win():
    return mix(fanfare(["G5", "C6", "E6"], 0.09), at(tone(0.5, note_freq("G6"), "square") * env(0.5, 0.003, 0.2) * 0.35, 0.27))


def slots_lose():
    parts = []
    for i, (a, b) in enumerate((("G4", "F#4"), ("F4", "E4"), ("D#4", "C4"))):
        length = 0.3 if i < 2 else 0.8
        parts.append(at(sweep(length, note_freq(a), note_freq(b), "square") * env(length, 0.005, length * 0.6) * 0.35, i * 0.32))
    return mix(*parts)


def slots_brains():
    organ = sum(tone(1.2, note_freq(n), "saw") * 0.2 for n in ("D3", "F3", "G#3", "B3")) * env(1.2, 0.01, 0.5)
    return mix(lowpass(organ, 1800), at(groan(140, 70, 1.3, "a", 5) * 0.8, 0.2))


def refuel():
    glugs = layer(at(sweep(0.12, 300 + 60 * k, 700 + 90 * k) * env(0.12, 0.01, 0.04) * 0.5, 0.11 * k) for k in range(6))
    pour = lowpass(noise(0.8), 900) * env(0.8, 0.05, 0.3) * 0.3
    return mix(glugs, pour)


def out_of_fuel():
    coughs = layer(at(lowpass(noise(0.18), 600) * env(0.18, 0.005, 0.06) * (1 - 0.2 * k), 0.25 * k + 0.05 * (k % 2)) for k in range(4))
    honk = (tone(0.7, 233, "saw") + tone(0.7, 220, "saw")) * env(0.7, 0.02, 0.35) * 0.25
    return mix(coughs, at(lowpass(honk, 1500), 1.0))


def horde():
    chorus = mix(*(at(groan(f0, f0 * 0.7, 2.0, v, w) * 0.4, d) for f0, v, w, d in
                   ((100, "o", 5, 0), (130, "a", 7, 0.1), (85, "u", 4, 0.2), (160, "a", 9, 0.15), (115, "o", 6, 0.3))))
    stab = sum(tone(0.9, note_freq(n), "square") * 0.18 for n in ("C4", "D#4", "F#4")) * env(0.9, 0.003, 0.3)
    return soft_clip(mix(chorus, stab), 1.6)


def denied():
    return tone(0.35, 110, "square") * env(0.35, 0.003, 0.2) * 0.5 + tone(0.35, 117, "square") * env(0.35, 0.003, 0.2) * 0.5


def kevin_babble():
    # Short blips at random pitches, like a cartoon shopkeeper talking.
    blips = [at(tone(0.07, f, "square") * env(0.07, 0.003, 0.03) * 0.35, k * 0.075) for k, f in enumerate(rng.uniform(240, 520, 12))]
    return lowpass(mix(*blips), 2500)


def sprinter_shriek(f0, f1, length):
    """A rising, ragged scream: a saw through an "ee" formant with a gargle of noise, so a charging sprinter cuts
    through the mix."""
    t = t_axis(length)
    freq = np.geomspace(f0, f1, len(t)) * (1 + 0.06 * np.sin(2 * np.pi * 23 * t))
    source = 2 * ((np.cumsum(freq) / RATE) % 1) - 1 + 0.35 * noise(length)
    shape = np.minimum(1, t / 0.04) * np.exp(-np.maximum(t - length * 0.55, 0) / (length * 0.2))
    return soft_clip(formant(source, "e") * shape * 1.4, 2.8)


def sprinter_steps():
    """One second of fast running footsteps (seven slaps with a gravel scuff), seamless for looping."""
    length = 1.0
    out = np.zeros(int(length * RATE))
    for k in range(7):
        start = int(k / 7 * length * RATE)
        slap = lowpass(noise(0.07), 1800) * env(0.07, 0.001, 0.015) * (1.0 if k % 2 else 0.75)
        thud = sweep(0.08, 120, 60) * env(0.08, 0.001, 0.02) * 0.8
        step = mix(slap, thud)
        out[start:start + len(step)] += step[:len(out) - start]
    return seamless(np.concatenate([out, out[:int(0.05 * RATE)]]), 0.05)


# ------------------------------------------------------------------------------------------------ music box

def music_box_note(freq, length):
    t = t_axis(length)
    tine = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2 * t) + 0.12 * np.sin(2 * np.pi * freq * 3.01 * t)
    tine += 0.05 * np.sin(2 * np.pi * freq * 5.4 * t) * np.exp(-t / 0.05)
    return tine * env(length, 0.002, 0.45)


def entertainer():
    sixteenth = 0.13
    a1 = [("D5", 1), ("D#5", 1), ("E5", 1), ("C6", 2), ("E5", 1), ("C6", 2), ("E5", 1), ("C6", 6)]
    a2 = [("C6", 1), ("D6", 1), ("D#6", 1), ("E6", 1), ("C6", 1), ("D6", 1), ("E6", 2), ("B5", 1), ("D6", 2), ("C6", 6)]
    b2 = [("A5", 1), ("G5", 1), ("F#5", 1), ("A5", 1), ("C6", 1), ("E6", 2), ("D6", 1), ("C6", 1), ("A5", 1), ("D6", 6)]
    run = [("C6", 1), ("D6", 1), ("E6", 1), ("C6", 1), ("D6", 1), ("E6", 2), ("C6", 1), ("D6", 1), ("C6", 1), ("E6", 1), ("C6", 1),
           ("D6", 1), ("E6", 2), ("C6", 1), ("D6", 1), ("C6", 1), ("E6", 1), ("C6", 1), ("D6", 1), ("E6", 2), ("B5", 1), ("D6", 2), ("C6", 8)]
    melody = a1 + a2 + a1 + b2 + a1 + a2 + run
    bass_plan = [("C3", "G3")] * 2 + [("C3", "G3")] * 2 + [("C3", "G3")] * 2 + [("A2", "E3"), ("D3", "A3")] + [("C3", "G3")] * 4 + [("G2", "D3"), ("C3", "G3")]
    total = sum(d for _, d in melody) + 4
    song = np.zeros(int((total * sixteenth + 2) * RATE))
    pos = 0
    for name, d in melody:
        note = music_box_note(note_freq(name), 1.6)
        start = int(pos * sixteenth * RATE)
        song[start:start + len(note)] += note[:len(song) - start]
        pos += d
    # Soft oom-pah underneath, one bass/chord pair per 8 sixteenths.
    bars = int(math.ceil(total / 8))
    for b in range(bars):
        root, fifth = bass_plan[min(b * len(bass_plan) // bars, len(bass_plan) - 1)]
        for k, name in enumerate((root, fifth)):
            note = music_box_note(note_freq(name), 1.0) * 0.35
            start = int((b * 8 + k * 4) * sixteenth * RATE)
            if start < len(song):
                song[start:start + len(note)] += note[:len(song) - start]
    loop_len = int(total * sixteenth * RATE)
    loop = song[:loop_len].copy()
    loop[:len(song) - loop_len] += song[loop_len:]  # ring-over wraps into the start so the loop is seamless
    return loop


def main():
    os.makedirs(OUT, exist_ok=True)
    sounds = {
        "gun_pistol": pistol, "gun_shotgun": shotgun, "gun_smg": smg, "gun_sniper": sniper, "gun_launcher": launcher,
        "gun_harpoon": harpoon, "gun_minigun": minigun, "gun_empty": empty_click, "gun_reload": reload, "throw": throw,
        "hit_1": lambda: hit(0), "hit_2": lambda: hit(1), "hit_3": lambda: hit(2), "headshot": headshot, "kill": kill,
        "splat_land": splat_land, "explosion": explosion, "bloater_pop": bloater_pop, "freeze": freeze, "ice_shatter": ice_shatter,
        "groan_1": lambda: groan(110, 85, 1.4, "o"), "groan_2": lambda: groan(95, 120, 1.1, "a", 4), "groan_3": lambda: groan(130, 70, 1.7, "u", 8),
        "groan_4": lambda: groan(75, 60, 1.3, "o", 3), "groan_sprinter": lambda: groan(180, 140, 0.7, "a", 12), "snarl": snarl,
        "hurt": hurt, "death": death, "revive": revive, "wipe": wipe, "engine_loop": engine_loop, "bell": bell, "pickup": pickup,
        "kaching": kaching, "tip": tip, "crank": crank, "scoop": scoop, "crash": crash, "depot": depot_jingle, "gib": gib_bounce,
        # Appended after the originals so the shared random generator gives those the same output as before.
        "gun_hose": hose, "gun_bazooka": bazooka, "gun_jackpot": jackpot_shot, "jackpot_win": jackpot_win, "melee_swing": melee_swing,
        "melee_hit": melee_hit, "slots_spin": slots_spin, "slots_win": slots_win, "slots_lose": slots_lose, "slots_brains": slots_brains,
        "refuel": refuel, "out_of_fuel": out_of_fuel, "horde": horde, "denied": denied, "kevin_babble": kevin_babble,
        "sprinter_shriek_1": lambda: sprinter_shriek(320, 900, 0.9), "sprinter_shriek_2": lambda: sprinter_shriek(260, 1100, 1.1),
        "sprinter_steps": sprinter_steps,
    }
    for name, make in sounds.items():
        write(name, make())
        print("wrote", name)
    write("music_entertainer", entertainer(), peak=0.8, gritty=False)
    print("wrote music_entertainer")


if __name__ == "__main__":
    main()
