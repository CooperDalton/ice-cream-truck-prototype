from pathlib import Path
import math
import struct
import wave

output = Path(__file__).resolve().parents[2] / 'Ice Cream Truck Prototype/Assets/Audio/Tycoon'
output.mkdir(parents=True, exist_ok=True)
rate = 22050
for name, notes, duration in [
    ('Sale', [659, 988, 1318], .30),
    ('Scoop', [220, 330], .15),
    ('Deposit', [440, 660], .12),
    ('Upgrade', [523, 659, 784, 1046], .60),
    ('Day', [523, 659, 784, 659, 1046], .85),
]:
    samples = []
    length = duration / len(notes)
    for index in range(int(rate * duration)):
        t = index / rate
        note_index = min(int(t / length), len(notes) - 1)
        local = t - note_index * length
        envelope = min(1, local / .008) * math.exp(-local * 8 / length)
        frequency = notes[note_index]
        value = math.sin(t * frequency * math.tau) + .15 * math.sin(t * frequency * math.tau * 2)
        samples.append(struct.pack('<h', int(value * envelope * 15000)))
    with wave.open(str(output / (name + '.wav')), 'wb') as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(b''.join(samples))
