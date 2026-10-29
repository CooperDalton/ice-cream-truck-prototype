"""Synthesizes the "Divorced Dads" mode sounds and music, PS1-style (22 kHz, 16-bit mono). Nothing is sampled; rerun to
regenerate. Builds on the building blocks in sfx_synth.py (importing it does not regenerate the zombie sounds).

python3 sfx_dads.py [name ...]  ->  Zombie Ice Cream Truck/Assets/Audio/Dads/*.wav   (no names = everything)

Voices are Animal-Crossing-style babble: a buzzy source through gliding vowel formants. Files ending in _loop and the
music loop seamlessly. "Greensleeves" is traditional (16th century, public domain).
"""
import math
import os
import sys
import wave

import numpy as np

import sfx_synth as S
from sfx_synth import (RATE, at, bandpass, crush, env, fit, highpass, layer, lowpass, mix, music_box_note, noise, note_freq,
                       seamless, soft_clip, squelch, sweep, t_axis, tone)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../Zombie Ice Cream Truck/Assets/Audio/Dads")
rng = S.rng = np.random.default_rng(42)  # sfx_synth.noise() draws from S.rng


# ------------------------------------------------------------------------------------------------ building blocks

def curve(length, *points):
    """Per-sample curve through (fraction, value) points."""
    n = int(length * RATE)
    return np.interp(np.linspace(0, 1, n), [p[0] for p in points], [p[1] for p in points])


def osc(freq, shape="saw"):
    phase = np.cumsum(freq) / RATE
    if shape == "saw":
        return 2 * (phase % 1) - 1
    if shape == "sine":
        return np.sin(2 * np.pi * phase)
    if shape == "square":
        return np.sign(np.sin(2 * np.pi * phase))
    if shape == "pulse":  # narrow pulse, buzzy and nasal
        p = ((phase % 1) < 0.22).astype(float)
        return p - p.mean()
    raise ValueError(shape)


def smooth_env(length, attack=0.01, release=0.04):
    n = int(length * RATE)
    e = np.ones(n)
    a, r = max(1, int(attack * RATE)), max(1, int(release * RATE))
    e[:a] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a))
    e[-r:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, r))
    return e


VOWELS = {"a": (800, 1200, 2600), "ae": (700, 1700, 2500), "e": (550, 1900, 2600), "i": (320, 2400, 3100),
          "o": (500, 850, 2600), "u": (350, 750, 2500), "uh": (620, 1200, 2550), "r": (420, 1100, 1650), "n": (280, 1500, 2500)}


def vowel_filter(src, vowels, scale=1.0):
    """Three formant band-passes gliding through the vowel list over the length of the source."""
    pos = np.linspace(0, 1, len(vowels)) if len(vowels) > 1 else np.array([0.0])
    x = np.linspace(0, 1, len(src))
    out = np.zeros_like(src)
    for k, (gain, q) in enumerate(((1.0, 5), (0.7, 8), (0.3, 10))):
        f = np.interp(x, pos, [VOWELS[v][k] * scale for v in vowels]) if len(vowels) > 1 else VOWELS[vowels[0]][k] * scale
        out += gain * bandpass(src, f, q)
    return out


def syllable(length, pitch, vowels, scale=1.3, onset=None, vib=0.0, vib_rate=7.0, breath=0.05, shape="saw", body=0.25):
    """One babble syllable. pitch is (f0, f1) or a list of (fraction, hz) points."""
    t = t_axis(length)
    f0 = np.geomspace(pitch[0], pitch[1], len(t)) if isinstance(pitch, tuple) else curve(length, *pitch)
    f0 = f0 * (1 + vib * np.sin(2 * np.pi * vib_rate * t))
    src = osc(f0, shape) + breath * noise(length)
    voice = vowel_filter(src, vowels, scale) + body * osc(f0, "sine")
    voice *= smooth_env(length, 0.012, min(0.06, length * 0.4))
    if onset == "h":  # breathy onset through the first vowel
        h = vowel_filter(noise(0.06), vowels[:1], scale) * env(0.06, 0.005, 0.025) * 1.2
        voice = mix(h, at(voice, 0.035))
    elif onset == "k":  # plosive click
        voice = mix(highpass(noise(0.02), 2500) * env(0.02, 0.0005, 0.004) * 0.6, at(voice, 0.015))
    return voice


def sparkle(count=4, spread=0.15, lo=3500, hi=6500, level=0.18):
    return layer(at(tone(0.25, f) * env(0.25, 0.001, 0.05) * level, d)
                 for d, f in zip(np.sort(rng.uniform(0, spread, count)), rng.uniform(lo, hi, count)))


def thump(length, f0, f1, decay, crack=0.4, crack_cut=1200):
    body = sweep(length, f0, f1) * env(length, 0.001, decay)
    hit = lowpass(noise(length), crack_cut) * env(length, 0.0005, decay * 0.3) * crack
    return body + hit


def click(length=0.03, cut=2500, decay=0.004):
    return highpass(noise(length), cut) * env(length, 0.0005, decay)


def ring(partials, length, decay, attack=0.001):
    return sum(tone(length, f) * a for f, a in partials) * env(length, attack, decay)


def grains(length, density, lo, hi, grain=0.004, shape=None):
    """Crackly texture: sparse random impulses smeared into tiny noise grains (paper, leaves, wafer)."""
    n = int(length * RATE)
    hits = (rng.uniform(0, 1, n) < density / RATE) * rng.uniform(0.3, 1.0, n)
    kernel = np.exp(-np.arange(int(grain * 5 * RATE)) / (grain * RATE))
    gate = np.convolve(hits, kernel)[:n]
    if shape is not None:
        gate *= shape
    return bandpass(noise(length), math.sqrt(lo * hi), math.sqrt(lo * hi) / (hi - lo)) * gate


def coin(f, decay=0.06):
    return ring(((f, 1.0), (f * 1.52, 0.6), (f * 2.41, 0.35)), 0.3, decay)


def brass(freq, length, vib=0.0, release=0.06):
    """Saw horn whose brightness opens with the attack."""
    t = t_axis(length)
    f = freq * (1 + vib * np.sin(2 * np.pi * 5.5 * t) * np.clip(t / 0.3, 0, 1)) * (1 - 0.03 * np.exp(-t / 0.02))
    src = osc(f, "saw") + 0.3 * osc(f * 0.5, "square")
    bright = lowpass(src, 500 + 2800 * np.exp(-t / 0.15) + 900)
    return bright * smooth_env(length, 0.02, release)


def pluck(freq, length, bright=12):
    """Vectorized plucked string: harmonics that decay faster the higher they are."""
    t = t_axis(length)
    out = sum(np.sin(2 * np.pi * freq * k * t) * np.exp(-t * (3 + 2.5 * k)) / k for k in range(1, bright + 1))
    return out * np.clip(t / 0.002, 0, 1)


def stick_slip(length, rate_pts, res=(700, 1500), jitter=0.25):
    """Creak: an irregular click train ringing through wooden/metal resonances."""
    rate = curve(length, *rate_pts) * (1 + jitter * rng.uniform(-1, 1, int(length * RATE)))
    phase = np.cumsum(rate) / RATE
    ticks = np.diff(np.floor(phase), prepend=0) * rng.uniform(0.5, 1, len(phase))
    return sum(bandpass(ticks, f, 9) for f in res)


def place(buf, x, start):
    """Adds x into a loop buffer at a sample offset, wrapping the overflow to the start."""
    idx = (np.arange(len(x)) + int(start)) % len(buf)
    np.add.at(buf, idx, x)


def circular(fn, x):
    """Runs a stateful filter over a loop so its state at the seam matches: filter two periods, keep the second."""
    return fn(np.concatenate([x, x]))[len(x):]


# ------------------------------------------------------------------------------------------------ kids

def kid_yay(variant):
    plans = {
        1: [(0.12, (520, 600), ["i", "a"], None), (0.32, (640, 900), ["a", "ae", "i"], None)],
        2: [(0.1, (480, 540), ["i", "i"], None), (0.1, (600, 680), ["i", "i"], "k"), (0.28, (720, 880), ["i", "e", "i"], None)],
        3: [(0.09, (450, 500), ["u", "a"], None), (0.09, (560, 620), ["u", "o"], "h"), (0.09, (680, 740), ["i", "i"], None),
            (0.26, (780, 900), ["i", "a"], None)],
    }[variant]
    parts, pos = [], 0.0
    for length, pitch, vowels, onset in plans:
        parts.append(at(syllable(length, pitch, vowels, 1.35, onset, vib=0.02 if length > 0.2 else 0, body=0.12), pos))
        pos += length + 0.03
    return mix(*parts, at(sparkle(4, 0.12), pos - 0.15))


def kid_eww():
    eh = syllable(0.12, (620, 560), ["e", "e"], 1.35, shape="pulse", body=0.1)
    eww = syllable(0.55, [(0, 600), (0.3, 520), (1, 340)], ["i", "e", "u", "u"], 1.35, vib=0.03, vib_rate=9, shape="pulse",
                   body=0.1)
    nasal = bandpass(eww, 2700, 6) * 0.4  # pinched-nose buzz
    return mix(eh, at(eww + nasal, 0.14))


def kid_cry():
    sob = syllable(0.14, (700, 760), ["uh", "a"], 1.35, onset="h")
    wail = syllable(1.0, [(0, 820), (0.15, 900), (0.6, 720), (1, 540)], ["u", "a", "ae", "a", "uh"], 1.35, vib=0.06,
                    vib_rate=6.5)
    sniff = bandpass(noise(0.12), 3500, 2) * env(0.12, 0.03, 0.03) * 0.25
    return mix(sob, at(wail, 0.18), at(sniff, 1.14))


def kid_giggle():
    parts = []
    for k, (d, f) in enumerate(((0, 820), (0.11, 780), (0.21, 800), (0.32, 740), (0.42, 700))):
        parts.append(at(syllable(0.075 + 0.01 * (k == 4), (f, f * 0.92), ["i", "i"], 1.4, onset="h", breath=0.25), d))
    return mix(*parts, at(sparkle(2, 0.05, level=0.1), 0.45))


# ------------------------------------------------------------------------------------------------ fat kid

def fat_kid_stomp():
    boom = thump(0.5, 95, 38, 0.12, crack=0.9, crack_cut=600)
    smack = thump(0.12, 180, 90, 0.03, crack=0.6, crack_cut=2500) * 0.6
    rumble = lowpass(noise(0.6), 140) * env(0.6, 0.02, 0.2) * 2.5
    debris = layer(at(click(0.03, 3000, 0.005) * 0.15, d) for d in rng.uniform(0.05, 0.3, 5))
    return soft_clip(mix(boom * 1.3, smack, rumble, debris), 2.0)


def fart_source(length, f0, jitter=0.12, flutter=17.0):
    """Lip-trill buzz: an uneven narrow pulse train with a flapping amplitude."""
    t = t_axis(length)
    wobble = lowpass(rng.uniform(-1, 1, len(t)), 60)
    wobble /= np.max(np.abs(wobble))
    buzz = osc(f0 * (1 + jitter * wobble), "pulse")
    flap = 1 + 0.6 * np.sin(2 * np.pi * flutter * t + 3 * wobble)
    return buzz * flap + 0.15 * lowpass(noise(length), 1200)


def burp():
    length = 1.0
    t = t_axis(length)
    fry = lowpass(rng.uniform(-1, 1, len(t)), 30)
    f0 = curve(length, (0, 92), (0.3, 80), (0.7, 74), (1, 62)) * (1 + 0.1 * fry / np.max(np.abs(fry)))
    src = osc(f0, "pulse") + 0.2 * noise(length)
    gurgle = 1 + 0.5 * np.sin(2 * np.pi * curve(length, (0, 14), (1, 9)).cumsum() / RATE)
    voice = vowel_filter(src, ["o", "a", "a", "o", "u"], 0.85) * gurgle * smooth_env(length, 0.03, 0.2)
    gulp = squelch(0.1, 0.03, 500, 200) * 0.4
    return soft_clip(mix(gulp, at(voice * 1.6, 0.04)), 2.2)


def fat_kid_roar():
    hun = syllable(0.42, [(0, 125), (0.5, 150), (1, 140)], ["uh", "uh", "n"], 0.8, onset="h", breath=0.3, body=0.5)
    gry = syllable(0.68, [(0, 165), (0.25, 175), (1, 105)], ["r", "a", "i", "i"], 0.8, onset="k", breath=0.3, vib=0.04,
                   vib_rate=5, body=0.5)
    voice = mix(hun, at(gry, 0.5))
    t = t_axis(len(voice) / RATE)
    growl = voice * (1 + 0.5 * np.sin(2 * np.pi * 31 * t)) + 0.4 * lowpass(noise(len(voice) / RATE), 500) * np.abs(voice)
    sub = lowpass(voice, 220) * 1.5
    return soft_clip(growl + sub * 0.7, 1.8)


def fart(short):
    if short:
        length = 0.38
        body = fart_source(length, curve(length, (0, 95), (1, 72)), jitter=0.18, flutter=21)
        out = lowpass(lowpass(body, 700), 1100) * smooth_env(length, 0.005, 0.08) * curve(length, (0, 1), (0.4, 0.7), (1, 0.9))
        return soft_clip(out * 1.5, 1.8)
    length = 1.25
    f0 = curve(length, (0, 75), (0.35, 68), (0.55, 110), (0.8, 300), (0.92, 420), (1, 380))
    body = fart_source(length, f0, jitter=0.1, flutter=13)
    cut = curve(length, (0, 800), (0.5, 900), (0.85, 2200), (1, 2400))
    out = lowpass(lowpass(body, cut), cut * 1.5) * smooth_env(length, 0.01, 0.06) * curve(length, (0, 1), (0.5, 0.8), (1, 1.1))
    pfft = bandpass(noise(0.15), 1500, 1.5) * env(0.15, 0.005, 0.04) * 0.35
    return soft_clip(mix(out * 1.6, at(pfft, length - 0.04)), 1.8)


def gas_hiss_loop():
    length = 2.0
    t = t_axis(length)
    hiss = circular(lambda x: bandpass(x, 3800, 1.2), noise(length)) * 0.35
    hiss *= 1 + 0.25 * np.sin(2 * np.pi * t / length) + 0.15 * np.sin(2 * np.pi * 3 * t / length)
    murk = circular(lambda x: lowpass(x, 350), noise(length)) * 0.6
    buf = hiss + murk
    for d, f in zip(np.linspace(0, length, 9, endpoint=False) + rng.uniform(0, 0.15, 9), rng.uniform(220, 650, 9)):
        dur = rng.uniform(0.04, 0.09)
        place(buf, sweep(dur, f, f * 1.7) * env(dur, 0.003, dur * 0.35) * 0.7, d * RATE)
    return buf


def cough():
    def hack(f0, length, level):
        src = noise(length) * 0.9 + osc(np.geomspace(f0, f0 * 0.8, int(length * RATE)), "saw") * 0.5
        burst = vowel_filter(src, ["a", "uh"], 1.0) * env(length, 0.004, length * 0.35)
        return (burst + thump(length, 120, 60, 0.03, crack=0.3) * 0.5) * level
    wheeze = vowel_filter(noise(0.3), ["i", "e"], 1.1) * smooth_env(0.3, 0.1, 0.1) * 0.25
    return mix(hack(130, 0.2, 1.0), at(hack(125, 0.18, 0.8), 0.22), at(hack(120, 0.18, 0.75), 0.42),
               at(wheeze, 0.62), at(hack(105, 0.3, 1.1), 0.95))


# ------------------------------------------------------------------------------------------------ ice cream

def plop():
    soft = thump(0.18, 170, 60, 0.05, crack=0.3, crack_cut=900)
    pop = sweep(0.07, 320, 1300) * env(0.07, 0.002, 0.025)
    wet = squelch(0.16, 0.035, 1100, 350) * 0.5
    blip = tone(0.08, 2093, "tri") * env(0.08, 0.001, 0.025) * 0.25
    return mix(soft * 1.1, at(pop, 0.02), at(wet, 0.01), at(blip, 0.07))


def shove():
    whoosh = bandpass(noise(0.22), np.geomspace(500, 2200, int(0.22 * RATE)), 2.5) * env(0.22, 0.15, 0.04)
    splorch = squelch(0.45, 0.13, 1600, 140) * 1.4
    smoosh = thump(0.25, 140, 55, 0.06, crack=0.5)
    drips = layer(at(squelch(0.08, 0.02, 1400, 600) * 0.3, d) for d in (0.12, 0.2, 0.31))
    return soft_clip(mix(whoosh * 0.7, at(splorch, 0.19), at(smoosh, 0.19), at(drips, 0.2)), 1.6)


def splat_face():
    return soft_clip(mix(squelch(0.28, 0.07, 1900, 220) * 1.3, thump(0.12, 160, 70, 0.03, crack=0.6, crack_cut=3000) * 0.6), 1.5)


def scoop_shot():
    t = t_axis(0.4)
    thoomp = sweep(0.4, 240, 90) * env(0.4, 0.002, 0.07)
    spring = np.sin(2 * np.pi * np.cumsum(330 * (1 + 0.12 * np.sin(2 * np.pi * 32 * t))) / RATE) * env(0.4, 0.002, 0.12) * 0.35
    pop = bandpass(noise(0.06), np.geomspace(500, 2500, int(0.06 * RATE)), 3) * env(0.06, 0.001, 0.015)
    cork = sweep(0.05, 400, 1400) * env(0.05, 0.001, 0.015) * 0.5
    return soft_clip(mix(thoomp * 1.2, spring, pop * 2.2, cork * 1.8), 1.6)


def coin_burst():
    pop = sweep(0.12, 600, 150) * env(0.12, 0.001, 0.03) * 0.6
    coins = layer(at(coin(f, rng.uniform(0.04, 0.09)) * a, d)
                  for d, f, a in zip(np.sort(rng.uniform(0.03, 0.6, 11)) ** 1.2, rng.uniform(2600, 5200, 11), rng.uniform(0.25, 0.5, 11)))
    rustle = grains(0.4, 900, 2000, 6000, 0.003, curve(0.4, (0, 1), (1, 0))) * 0.7
    return mix(pop, coins, at(rustle, 0.02))


def coin_pickup():
    first = tone(0.07, note_freq("B5"), "square") * smooth_env(0.07, 0.002, 0.01) * 0.4
    second = tone(0.25, note_freq("E6"), "square") * env(0.25, 0.002, 0.08) * 0.4
    return lowpass(mix(first, at(second, 0.07)), 6000)


def cone_grab():
    crunch = grains(0.2, 500, 1800, 6000, 0.0012, curve(0.2, (0, 1), (0.3, 0.8), (1, 0)))
    crunch = mix(crunch, layer(at(bandpass(noise(0.02), f, 3) * env(0.02, 0.0003, 0.003) * 1.5, d) for d, f in ((0.0, 2600), (0.05, 3400), (0.09, 2200))))
    snap = bandpass(noise(0.03), 2500, 2) * env(0.03, 0.0005, 0.006)
    paper = grains(0.12, 600, 2500, 7000, 0.004) * 0.3
    return mix(paper, at(snap, 0.05), at(crunch, 0.05))


def refill():
    def pump(f0):
        return mix(squelch(0.22, 0.06, f0, 180) * 3.0, thump(0.1, 150, 80, 0.025, crack=0.3) * 0.5,
                   at(sweep(0.06, 250, 700) * env(0.06, 0.003, 0.02) * 0.6, 0.1))
    latch = click(0.04, 2000, 0.005) + ring(((2400, 0.3), (3900, 0.2)), 0.04, 0.012)
    return mix(pump(800), at(pump(700), 0.2), at(latch * 0.6, 0.46))


def churn_whir():
    run = 1.3
    t = t_axis(run)
    f = curve(run, (0, 35), (0.6, 140), (1, 185))
    motor = lowpass(osc(f, "saw") + 0.5 * osc(f * 2, "square"), 1400) * 0.6
    whine = osc(f * 6, "sine") * np.clip(t / run, 0, 1) * 0.25
    rattle = bandpass(noise(run), 2000, 3) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * np.cumsum(f / 2) / RATE))) * 0.2
    whir = (motor + whine + rattle) * smooth_env(run, 0.05, 0.12)
    partials = ((1, 1.0), (2.0, 0.5), (2.76, 0.35), (5.4, 0.2))
    ding = sum(tone(0.7, 1760 * k) * a for k, a in partials) * env(0.7, 0.001, 0.16) * 0.6
    return mix(whir, at(ding, run - 0.03))


# ------------------------------------------------------------------------------------------------ truck, cops, dads

def honk():
    def blast(freqs, length):
        t = t_axis(length)
        bend = 1 - 0.07 * np.exp(-t / 0.025)
        src = sum(osc(f * bend, "saw") for f in freqs)
        honky = bandpass(src, 1000, 1.4) + 0.4 * lowpass(src, 500)
        return soft_clip(honky * 1.5, 2.5) * smooth_env(length, 0.008, 0.04)
    return mix(blast((370, 466), 0.2), at(blast((330, 415), 0.34), 0.25))


def siren_loop():
    length, centre, depth = 2.0, 1000, 420  # centre * length is a whole number of cycles, so the phase wraps exactly
    t = np.arange(int(length * RATE)) / RATE
    phase = 2 * np.pi * (centre * t - depth * length / (2 * np.pi) * np.sin(2 * np.pi * t / length))
    wave_ = np.tanh(2.2 * np.sin(phase)) + 0.25 * np.sin(2 * phase)
    return circular(lambda x: lowpass(x, 4000), wave_)


def whistle():
    def blast(length):
        t = t_axis(length)
        trill = np.sin(2 * np.pi * 38 * t)
        f = 2900 * (1 + 0.035 * trill)
        tone_ = osc(f, "sine") * (0.75 + 0.25 * trill)
        air = bandpass(noise(length), 2900, 3) * 0.35
        return (tone_ + air) * smooth_env(length, 0.012, 0.05)
    return mix(blast(0.13), at(blast(0.55), 0.2))


def busted():
    tackle = soft_clip(thump(0.35, 110, 40, 0.09, crack=1.0, crack_cut=1500) * 1.4, 1.8)
    cloth = bandpass(noise(0.15), 1200, 1.5) * env(0.15, 0.005, 0.04) * 0.4
    teeth = layer(at(click(0.03, 3000, 0.003) * 0.5 + ring(((3300, 0.15), (5100, 0.1)), 0.03, 0.008), 0.32 + k * 0.035)
                  for k in range(6))
    clack = mix(click(0.05, 1800, 0.008), ring(((2100, 0.35), (3700, 0.25)), 0.12, 0.03)) * 0.9
    sad = layer(at(lowpass(sweep(0.25, f, f * 0.75, "square"), 2500) * smooth_env(0.25, 0.005, 0.08) * 0.3, d)
                for d, f in ((0.72, note_freq("G4")), (0.98, note_freq("E4"))))
    return mix(tackle, cloth, teeth, at(clack, 0.56), sad)


def ticket():
    rip_len = 0.32
    rip = grains(rip_len, 2500, 1500, 5000, 0.002, curve(rip_len, (0, 0.3), (0.8, 1), (1, 0))) * 1.2
    tear = bandpass(noise(rip_len), np.geomspace(1500, 4000, int(rip_len * RATE)), 2) * env(rip_len, 0.15, 0.06) * 0.4
    return mix(rip * 0.45, tear * 0.6, at(stamp(), 0.38))


def stamp():
    whoosh = bandpass(noise(0.07), 900, 2) * env(0.07, 0.05, 0.01) * 0.3
    thunk = thump(0.4, 120, 45, 0.08, crack=1.0, crack_cut=1800)
    body = bandpass(noise(0.1), 180, 4) * env(0.1, 0.001, 0.03) * 2
    slap = bandpass(noise(0.04), 1600, 2) * env(0.04, 0.0005, 0.008) * 0.6
    return soft_clip(mix(whoosh, at(thunk * 1.3 + fit(body, 0.4) + fit(slap, 0.4), 0.06)), 2.0)


def oof():
    hit = soft_clip(thump(0.3, 100, 40, 0.07, crack=0.9) * 1.3, 1.8)
    voice = syllable(0.22, [(0, 175), (0.3, 165), (1, 105)], ["uh", "u", "u"], 0.95, onset="h", breath=0.15, body=0.4) * 2.6
    slide_len = 0.6
    t = t_axis(slide_len)
    f = np.geomspace(1700, 380, len(t)) * (1 + 0.02 * np.sin(2 * np.pi * 6 * t))
    slide = (osc(f, "sine") + 0.1 * bandpass(noise(slide_len), f, 4)) * smooth_env(slide_len, 0.03, 0.1) * 0.2
    return mix(hit, at(voice, 0.03), at(slide, 0.26))


def tumble():
    parts = []
    for d, a in ((0, 1.0), (0.17, 0.75), (0.31, 0.6), (0.5, 0.45), (0.66, 0.3)):
        parts.append(at(thump(0.18, 110 + rng.uniform(-15, 15), 45, 0.04, crack=0.7, crack_cut=800) * a, d))
        parts.append(at(bandpass(noise(0.1), 900, 1.5) * smooth_env(0.1, 0.02, 0.05) * 0.2 * a, d + 0.05))
    return soft_clip(mix(*parts) * 1.2, 1.5)


# ------------------------------------------------------------------------------------------------ world props

def gate_open():
    run = 0.9
    t = t_axis(run)
    f = curve(run, (0, 80), (0.2, 140), (1, 160))
    motor = bandpass(osc(f, "saw"), 700, 2) + 0.3 * osc(f * 4, "sine")
    motor *= (0.85 + 0.15 * np.sin(2 * np.pi * np.cumsum(f / 8) / RATE)) * smooth_env(run, 0.05, 0.1)
    clunk = thump(0.3, 150, 60, 0.05, crack=0.8, crack_cut=2000) + ring(((520, 0.3), (1310, 0.2), (2210, 0.12)), 0.3, 0.07)
    return mix(motor * 1.6, at(clunk, run - 0.02))


def vault_open():
    tumblers = layer(at(click(0.04, 2500, 0.004) * 0.6 + ring(((2600, 0.15), (4100, 0.1)), 0.04, 0.01), d) for d in (0, 0.12, 0.24))
    clunk = soft_clip(thump(0.5, 75, 35, 0.12, crack=1.0, crack_cut=1200) * 1.4
                      + ring(((220, 0.4), (560, 0.3), (930, 0.2)), 0.5, 0.2), 1.6)
    hiss = highpass(noise(0.5), 2200) * env(0.5, 0.01, 0.15) * 0.5
    creak_len = 0.8
    creak = stick_slip(creak_len, [(0, 30), (0.4, 55), (1, 38)], (600, 1400)) * smooth_env(creak_len, 0.08, 0.15) * 2.5
    return mix(tumblers, at(clunk, 0.4), at(hiss, 0.5), at(creak, 0.72))


def plate_click():
    snap = click(0.03, 2200, 0.004)
    clunk = thump(0.12, 230, 120, 0.03, crack=0.6, crack_cut=1500)
    spring = tone(0.15, 880) * env(0.15, 0.001, 0.04) * 0.15
    return mix(snap, at(clunk, 0.03), at(spring, 0.03))


def tree_shake():
    length = 1.0
    t = t_axis(length)
    shake = (0.55 + 0.45 * np.sin(2 * np.pi * 6 * t)) * smooth_env(length, 0.05, 0.3)
    leaves = grains(length, 3000, 1800, 7000, 0.003, shake) + bandpass(noise(length), 3500, 1) * shake * 0.25
    creak = stick_slip(0.5, [(0, 25), (0.5, 45), (1, 30)], (380, 900)) * smooth_env(0.5, 0.06, 0.1) * 2
    return mix(leaves, at(creak, 0.08))


def nut_drop():
    def bonk(f, level):
        t = t_axis(0.15)
        body = osc(f * (1 - 0.15 * t / 0.15), "sine") + 0.35 * osc(f * 2.6 * np.ones(len(t)), "sine")
        return (body * env(0.15, 0.0008, 0.03) + click(0.15, 2000, 0.002) * 0.4) * level
    parts = []
    for d, f, a in ((0, 900, 1.0), (0.16, 1150, 0.8), (0.27, 1020, 0.7), (0.48, 1250, 0.6)):
        parts += [at(bonk(f, a), d), at(bonk(f * 1.05, a * 0.4), d + 0.09), at(bonk(f * 1.08, a * 0.15), d + 0.15)]
    return mix(*parts)


def mud_squelch():
    grab = mix(squelch(0.4, 0.12, 750, 140) * 2.5, at(squelch(0.3, 0.09, 1100, 200) * 1.5, 0.08))
    body = thump(0.15, 120, 60, 0.04, crack=0.4, crack_cut=500) * 0.5
    suck = bandpass(noise(0.18), np.geomspace(250, 900, int(0.18 * RATE)), 4) * env(0.18, 0.06, 0.05) * 1.6
    bubbles = layer(at(sweep(0.05, f, f * 1.8) * env(0.05, 0.002, 0.015) * 0.45, d) for d, f in ((0.3, 280), (0.36, 340), (0.42, 300), (0.47, 260)))
    return mix(grab, body, at(suck, 0.25), bubbles)


def berry_pick():
    rustle = grains(0.25, 2000, 2000, 6500, 0.003, curve(0.25, (0, 1), (1, 0.2)))
    pops = layer(at(sweep(0.035, 950, 420) * env(0.035, 0.0008, 0.01) * 0.6 + click(0.035, 1500, 0.002) * 0.3, d)
                 for d in (0.15, 0.3, 0.43))
    return mix(rustle * 0.5, pops * 1.6)


def coffee_grab():
    length = 0.55
    t = t_axis(length)
    slosh = bandpass(noise(length), 650 + 250 * np.sin(2 * np.pi * 5 * t), 3) * smooth_env(length, 0.05, 0.2) * 0.8
    glugs = layer(at(sweep(0.05, f, f * 1.6) * env(0.05, 0.002, 0.015) * 0.2, d) for d, f in zip((0.1, 0.22, 0.33), (420, 500, 380)))
    ice = layer(at(ring(((f, 0.5), (f * 2.3, 0.25)), 0.08, 0.018) + click(0.08, 3000, 0.002) * 0.3, d)
                for d, f in zip(np.sort(rng.uniform(0.03, 0.45, 9)), rng.uniform(2200, 4200, 9)))
    crinkle = grains(0.1, 1500, 2500, 7000, 0.002) * 0.5
    return mix(crinkle, at(slosh, 0.03), at(glugs, 0.03), at(ice, 0.02))


def barista_hey():
    voice = syllable(0.38, [(0, 230), (0.3, 310), (1, 210)], ["ae", "e", "i"], 1.05, onset="h", breath=0.1, body=0.3)
    return soft_clip(voice * 1.5, 1.6)


def cash_register():
    key = lambda: click(0.06, 1500, 0.006) + ring(((1800, 0.2), (2900, 0.1)), 0.06, 0.012) + thump(0.06, 300, 200, 0.01, crack=0) * 0.3
    keys = layer(at(key(), d) for d in (0, 0.08, 0.16))
    roll_len = 0.22
    t = t_axis(roll_len)
    drawer = lowpass(noise(roll_len), 900) * (0.6 + 0.4 * np.sin(2 * np.pi * 45 * t)) * smooth_env(roll_len, 0.02, 0.02) * 0.6
    slam = thump(0.2, 160, 70, 0.04, crack=0.8, crack_cut=1500)
    partials = ((1, 1.0), (2.0, 0.5), (2.76, 0.4), (5.4, 0.2))
    bell = sum(tone(1.0, 2093 * k) * a for k, a in partials) * env(1.0, 0.001, 0.28) * 0.6
    return mix(keys, at(drawer, 0.28), at(slam, 0.5), at(bell, 0.3))


# ------------------------------------------------------------------------------------------------ stingers

def sad_trombone():
    parts = []
    notes = (("A#3", 0.3), ("A3", 0.3), ("G#3", 0.3), ("G3", 1.05))
    pos = 0.0
    for i, (name, length) in enumerate(notes):
        t = t_axis(length)
        last = i == len(notes) - 1
        f = note_freq(name) * np.ones(len(t)) * (1 + (0.025 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.15) / 0.2, 0, 1) if last else 0))
        src = osc(f, "saw")
        wah = curve(length, (0, 350), (0.35, 1500), (1, 500)) if not last else 450 + 900 * (0.5 + 0.5 * np.sin(2 * np.pi * 2.6 * t - np.pi / 2))
        parts.append(at(bandpass(src, wah, 2.2) * smooth_env(length, 0.03, 0.12 if not last else 0.35), pos))
        pos += length + 0.04
    return mix(*parts)


def fanfare():
    plan = [(0.0, 0.1, ("G4", "E4")), (0.12, 0.1, ("G4", "E4")), (0.24, 0.1, ("G4", "E4")), (0.36, 0.42, ("C5", "G4", "E4")),
            (0.82, 0.14, ("A4", "F4")), (0.98, 0.14, ("B4", "G4")), (1.14, 0.9, ("C5", "G4", "E4", "C4"))]
    parts = [at(sum(brass(note_freq(n), length, vib=0.012 if length > 0.5 else 0, release=0.35 if length > 0.5 else 0.06) * (1 if k == 0 else 0.6) for k, n in enumerate(chord)), d)
             for d, length, chord in plan]
    timpani = thump(0.8, 98, 85, 0.25, crack=0.3, crack_cut=400) * 1.2
    shimmer = highpass(noise(0.9), 5000) * env(0.9, 0.01, 0.3) * 0.15
    return soft_clip(mix(*parts, at(timpani, 1.14), at(shimmer, 1.14)) * 0.7, 1.4)


def rooster():
    def crow(length, pitch, vowels, onset=None, vib=0.0):
        voice = syllable(length, pitch, vowels, 1.5, onset, vib=vib, vib_rate=11, breath=0.4, shape="pulse", body=0.15)
        return voice + bandpass(voice, 2800, 3) * 0.6  # strained rasp
    return soft_clip(mix(crow(0.12, (560, 650), ["o", "a"], "k"),
                         at(crow(0.08, (620, 600), ["uh", "uh"]), 0.14),
                         at(crow(0.14, (700, 780), ["u", "u"], "k"), 0.24),
                         at(crow(0.88, [(0, 780), (0.2, 960), (0.6, 900), (1, 640)], ["u", "o", "o", "u"], "k", vib=0.03), 0.4)) * 1.8, 1.8)


def dusk_chime():
    def tine(name, length=1.0):
        f = note_freq(name)
        t = t_axis(length)
        return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) + 0.08 * np.sin(2 * np.pi * 3.9 * f * t)) * env(length, 0.006, 0.4)
    return mix(*(at(tine(n) * a, d) for d, n, a in ((0, "E6", 0.8), (0.22, "C6", 0.85), (0.44, "A5", 0.9), (0.66, "E5", 1.0))))


def brain_freeze():
    crackle = grains(0.45, 2500, 4000, 9000, 0.0015, curve(0.45, (0, 1), (1, 0.1))) * 1.3
    tinkle = sparkle(6, 0.3, 3000, 7000, 0.15)
    brr = syllable(0.75, [(0, 210), (0.5, 190), (1, 160)], ["u", "r", "r"], 1.0, onset="h", breath=0.2, vib=0.07, vib_rate=27, body=0.4)
    brr *= 0.6 + 0.4 * np.sin(2 * np.pi * 27 * np.arange(len(brr)) / RATE)
    return mix(crackle * 0.7, tinkle, at(brr * 5, 0.25))


def lesson_ding():
    """Tutorial step done: a quick rising C-E-G sparkle."""
    def tine(name, length=0.6):
        f = note_freq(name)
        t = t_axis(length)
        return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t)) * env(length, 0.004, 0.3)
    return mix(*(at(tine(n) * a, d) for d, n, a in ((0, "C6", 0.8), (0.08, "E6", 0.85), (0.16, "G6", 1.0))))


# ------------------------------------------------------------------------------------------------ ambience loops

def birds_loop():
    length = 6.0
    t = t_axis(length)
    air = circular(lambda x: lowpass(x, 450), noise(length)) * (1 + 0.3 * np.sin(2 * np.pi * t / length)) * 0.5
    air += circular(lambda x: highpass(x, 3000), noise(length)) * 0.02
    buf = air

    def tweet(f, length=0.07):
        return osc(curve(length, (0, f), (0.45, f * 1.45), (1, f * 0.85)), "sine") * np.sin(np.pi * np.linspace(0, 1, int(length * RATE))) ** 2

    def trill(f, count):
        return layer(at(tweet(f * (1 - 0.03 * k), 0.035), k * 0.05) for k in range(count))

    def feebee():
        a = osc(curve(0.25, (0, 4150), (1, 4050)), "sine") * smooth_env(0.25, 0.02, 0.06)
        b = osc(curve(0.25, (0, 3500), (1, 3450)), "sine") * smooth_env(0.25, 0.02, 0.08)
        return mix(a, at(b, 0.3))
    events = [(0.3, tweet(3200) * 0.7), (0.42, tweet(3400) * 0.6), (1.25, trill(5200, 7) * 0.35), (2.4, feebee() * 0.4),
              (3.4, tweet(2800) * 0.6), (4.3, trill(4500, 5) * 0.3), (5.55, tweet(3600) * 0.6), (5.68, tweet(3900) * 0.5)]
    for d, x in events:
        place(buf, x, d * RATE)
    return buf


def crickets_loop():
    length = 4.0
    n = int(length * RATE)
    t = np.arange(n) / RATE
    buf = circular(lambda x: lowpass(x, 300), noise(length)) * 0.15
    for carrier, period, pulses, offset, level in ((4400, 0.5, 3, 0.0, 1.0), (4900, 4 / 7, 4, 0.21, 0.5), (3900, 0.8, 3, 0.37, 0.35)):
        gate = np.zeros(n)
        pulse = np.sin(np.pi * np.linspace(0, 1, int(0.014 * RATE))) ** 2
        for k in range(int(round(length / period))):
            for p in range(pulses):
                place(gate, pulse, (offset + k * period + p * 0.03) * RATE)
        buf += (np.sin(2 * np.pi * carrier * t) + 0.2 * np.sin(2 * np.pi * 2 * carrier * t)) * gate * level  # whole-Hz carriers wrap at 4 s
    return buf


# ------------------------------------------------------------------------------------------------ music

def render_score(notes, unit, total_units, instrument):
    """notes: (start_unit, name, level, ring_seconds). Rendered into a loop with the ring-over wrapped to the start."""
    loop = np.zeros(int(round(total_units * unit * RATE)))
    for start, name, level, length in notes:
        place(loop, instrument(note_freq(name), length) * level, start * unit * RATE)
    return loop


def greensleeves():
    unit = 0.16  # one eighth note; 32 bars of 3/4 = 192 eighths = 30.7 s
    q, h, dq, e, dh = 2, 4, 3, 1, 6
    verse_a = [("C5", h), ("D5", q), ("E5", dq), ("F5", e), ("E5", q), ("D5", h), ("B4", q), ("G4", dq), ("A4", e), ("B4", q),
               ("C5", h), ("A4", q), ("A4", dq), ("G#4", e), ("A4", q), ("B4", h), ("G#4", q), ("E4", h), ("A4", q)]
    verse_b = [("C5", h), ("D5", q), ("E5", dq), ("F5", e), ("E5", q), ("D5", h), ("B4", q), ("G4", dq), ("A4", e), ("B4", q),
               ("C5", dq), ("B4", e), ("A4", q), ("G#4", dq), ("F#4", e), ("G#4", q), ("A4", dh), (None, dh)]
    chorus_a = [("G5", dh), ("G5", dq), ("F#5", e), ("E5", q), ("D5", h), ("B4", q), ("G4", dq), ("A4", e), ("B4", q),
                ("C5", h), ("A4", q), ("A4", dq), ("G#4", e), ("A4", q), ("B4", h), ("G#4", q), ("E4", dh)]
    chorus_b = [("G5", dh), ("G5", dq), ("F#5", e), ("E5", q), ("D5", h), ("B4", q), ("G4", dq), ("A4", e), ("B4", q),
                ("C5", dq), ("B4", e), ("A4", q), ("G#4", dq), ("F#4", e), ("G#4", q), ("A4", dh), (None, h), ("A4", q)]
    melody = verse_a + verse_b + chorus_a + chorus_b
    notes, pos = [], 0
    for name, d in melody:
        if name:
            notes.append((pos, name, 1.0, 1.6))
        pos += d
    assert pos == 192, pos
    chords = {"Am": ("A2", "C4", "E4"), "C": ("C3", "E4", "G4"), "G": ("G2", "B3", "D4"), "Em": ("E2", "G3", "B3"),
              "E": ("E2", "G#3", "B3")}
    plan = ("Am C G Em Am E E E " "Am C G Em Am E Am Am " "C C G Em Am E E E " "C C G Em Am E Am Am").split()
    for bar, chord in enumerate(plan):
        root, third, fifth = chords[chord]
        notes += [(bar * 6, root, 0.45, 1.2), (bar * 6 + 2, third, 0.18, 0.8), (bar * 6 + 2, fifth, 0.18, 0.8),
                  (bar * 6 + 4, third, 0.15, 0.8), (bar * 6 + 4, fifth, 0.15, 0.8)]
    return render_score(notes, unit, 192, music_box_note)


def curfew():
    beat = 0.5  # 120 bpm, 8 bars of 4/4 = 16 s
    bass = ["A2", "C3", "E3", "C3", "A2", "C3", "D#3", "E3", "D3", "F3", "A3", "F3", "D3", "F3", "G#3", "A3",
            "E3", "G#3", "B3", "G#3", "E3", "D3", "C3", "B2", "A2", "C3", "E3", "A3", "A2", "E2", "F2", "G#2"]
    notes = [(k * 2, n, 0.9, 0.45) for k, n in enumerate(bass)]  # units are eighths
    bass_track = render_score(notes, beat / 2, 64, pluck)
    motif = {0: [(1, "E5"), (2, "F5"), (3, "E5"), (6, "C5")], 1: [(1, "E5"), (2, "F5"), (3, "E5"), (6, "A4")],
             2: [(1, "F5"), (2, "G5"), (3, "F5"), (6, "D5")], 3: [(1, "F5"), (2, "G#5"), (3, "A5"), (5, "G#5"), (6, "F5")],
             4: [(1, "G#5"), (2, "B5"), (3, "G#5"), (6, "E5")], 5: [(0, "E5"), (2, "D5"), (4, "C5"), (6, "B4")],
             6: [(1, "C5"), (2, "E5"), (3, "A5"), (5, "G#5"), (7, "A5")], 7: [(0, "E6"), (3, "D#5"), (4, "E5"), (6, "A4")]}
    box = render_score([(bar * 8 + u, n, 0.55, 0.9) for bar, line in motif.items() for u, n in line], beat / 2, 64, music_box_note)
    tick = lambda f: bandpass(noise(0.04), f, 6) * env(0.04, 0.0005, 0.008) * 6
    ticks = np.zeros(len(bass_track))
    for b in range(32):
        place(ticks, tick(1300 if b % 2 else 900) * (0.6 if b % 2 else 0.35), (b * beat + (beat / 2 if b % 2 == 0 else 0)) * RATE)
    return bass_track * 0.8 + box + ticks * 0.25


# ------------------------------------------------------------------------------------------------ output

def write(name, x, peak=0.9, max_rms_db=-11.0, gritty=True, loop=False):
    """Peak-normalizes, then turns down anything denser than the existing sounds. One-shots get their DC removed, their
    silent tail trimmed and a short fade; loops are filtered circularly so the seam is untouched."""
    if loop:
        x = circular(lambda v: highpass(v, 25), x)
    else:
        x = highpass(x, 25)
        loud = np.nonzero(np.abs(x) > np.max(np.abs(x)) * 1e-3)[0]
        x = x[:loud[-1] + 1]
        fade = min(len(x), int(0.008 * RATE))
        x[-fade:] *= np.linspace(1, 0, fade)
    x = x / np.max(np.abs(x)) * peak
    rms_db = 20 * np.log10(np.sqrt(np.mean(x ** 2)))
    if rms_db > max_rms_db:
        x *= 10 ** ((max_rms_db - rms_db) / 20)
    if gritty:
        x = crush(x, bits=10, hold=1)
    data = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data)


SOUNDS = {
    "kid_yay_1": (lambda: kid_yay(1), {}), "kid_yay_2": (lambda: kid_yay(2), {}), "kid_yay_3": (lambda: kid_yay(3), {}),
    "kid_eww": (kid_eww, {}), "kid_cry": (kid_cry, {}), "kid_giggle": (kid_giggle, {}),
    "fat_kid_stomp": (fat_kid_stomp, {"max_rms_db": -10}), "fat_kid_burp": (burp, {}), "fat_kid_roar": (fat_kid_roar, {"max_rms_db": -10}),
    "fart_1": (lambda: fart(True), {}), "fart_2": (lambda: fart(False), {}),
    "gas_hiss_loop": (gas_hiss_loop, {"peak": 0.6, "max_rms_db": -22, "loop": True}), "cough": (cough, {}),
    "plop": (plop, {}), "shove": (shove, {}), "splat_face": (splat_face, {}), "scoop_shot": (scoop_shot, {}),
    "coin_burst": (coin_burst, {}), "coin_pickup": (coin_pickup, {"max_rms_db": -13}), "honk": (honk, {"max_rms_db": -10}),
    "siren_loop": (siren_loop, {"peak": 0.75, "max_rms_db": -13, "loop": True}), "whistle": (whistle, {"max_rms_db": -12}),
    "busted": (busted, {}), "ticket": (ticket, {}), "oof": (oof, {}), "tumble": (tumble, {}),
    "gate_open": (gate_open, {}), "vault_open": (vault_open, {}), "plate_click": (plate_click, {}),
    "tree_shake": (tree_shake, {}), "nut_drop": (nut_drop, {}), "mud_squelch": (mud_squelch, {}), "berry_pick": (berry_pick, {}),
    "coffee_grab": (coffee_grab, {}), "barista_hey": (barista_hey, {}), "churn_whir": (churn_whir, {}), "cone_grab": (cone_grab, {}),
    "refill": (refill, {}), "cash_register": (cash_register, {}), "stamp": (stamp, {"max_rms_db": -10}),
    "sad_trombone": (sad_trombone, {"max_rms_db": -13}), "fanfare": (fanfare, {"max_rms_db": -12}), "rooster": (rooster, {}),
    "dusk_chime": (dusk_chime, {"max_rms_db": -14}), "brain_freeze": (brain_freeze, {}),
    "birds_loop": (birds_loop, {"peak": 0.45, "max_rms_db": -28, "loop": True}),
    "crickets_loop": (crickets_loop, {"peak": 0.4, "max_rms_db": -26, "loop": True}),
    "music_greensleeves": (greensleeves, {"peak": 0.8, "max_rms_db": -14, "gritty": False, "loop": True}),
    "music_curfew_loop": (curfew, {"peak": 0.8, "max_rms_db": -14, "gritty": False, "loop": True}),
    "lesson_ding": (lesson_ding, {"max_rms_db": -14}),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name in sys.argv[1:] or SOUNDS:
        make, opts = SOUNDS[name]
        write(name, make(), **opts)
        print("wrote", name)


if __name__ == "__main__":
    main()
