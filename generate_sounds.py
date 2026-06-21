"""
generate_sounds.py — creates synthetic placeholder WAV files in sounds/.

Run this once if you don't have real drum samples yet.  Each file is a short
sine-wave tone at a distinct pitch so you can hear which zone was hit.
Replace any file with a real sample at any time.
"""

import os
import struct
import math

SOUNDS_DIR = os.path.join(os.path.dirname(__file__), "sounds")

# (filename, frequency_hz, duration_ms, decay)
PATCHES = [
    # Drums
    ("kick.wav",   60,  300, True),
    ("snare.wav",  220, 120, True),
    ("hihat.wav",  8000, 60, True),
    ("crash.wav",  3000, 500, True),
    ("tom1.wav",   150, 200, True),
    ("tom2.wav",   120, 200, True),
    # Guitar strings (open notes: E2 A2 D3 G3 B3 E4)
    ("string_e2.wav",  82,  600, True),
    ("string_a.wav",   110, 600, True),
    ("string_d.wav",   147, 600, True),
    ("string_g.wav",   196, 600, True),
    ("string_b.wav",   247, 600, True),
    ("string_e4.wav",  330, 600, True),
]

SAMPLE_RATE = 44100


def write_wav(path, samples, rate=SAMPLE_RATE):
    n = len(samples)
    data_size = n * 2  # 16-bit mono

    with open(path, "wb") as f:
        # RIFF header
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + data_size))
        f.write(b"WAVE")
        # fmt chunk
        f.write(b"fmt ")
        f.write(struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16))
        # data chunk
        f.write(b"data")
        f.write(struct.pack("<I", data_size))
        for s in samples:
            clamped = max(-32768, min(32767, int(s)))
            f.write(struct.pack("<h", clamped))


def make_tone(freq, duration_ms, decay=True, rate=SAMPLE_RATE):
    n = int(rate * duration_ms / 1000)
    samples = []
    for i in range(n):
        t = i / rate
        amp = 32000
        if decay:
            amp *= math.exp(-5 * t / (duration_ms / 1000))
        samples.append(amp * math.sin(2 * math.pi * freq * t))
    return samples


def main():
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    for fname, freq, dur, decay in PATCHES:
        path = os.path.join(SOUNDS_DIR, fname)
        if os.path.exists(path):
            print(f"  skip (exists): {fname}")
            continue
        samples = make_tone(freq, dur, decay)
        write_wav(path, samples)
        print(f"  created: {fname}  ({freq}Hz, {dur}ms)")
    print("Done.  Replace any file with a real sample to improve sound quality.")


if __name__ == "__main__":
    main()
