# 🥁 Air Guitar / Air Drum Kit

> Play a virtual instrument using only your hands and a webcam — no controller, no hardware.

A Python desktop app that uses **MediaPipe Hands** to track your hand skeleton in real time and triggers drum or guitar sounds whenever you "strike" a virtual zone with enough velocity. The full 21-point hand skeleton is always overlaid on the camera feed so you can see exactly what the tracker sees.

---

## Demo

| Drum Kit Mode | Guitar Mode |
|:---:|:---:|
| 3 × 2 pad grid (HI-HAT, SNARE, CRASH, KICK, TOM1, TOM2) | 6 vertical string bands (E2 → E4) |
| Downward strike triggers sound | Horizontal swipe triggers string |
| Both hands tracked simultaneously | Right hand strums, left hand sets chord label |

---

## Features

- **Full hand skeleton overlay** — all 21 MediaPipe landmarks connected with lines, drawn every frame (right hand = cyan, left hand = magenta)
- **Velocity-gated strike detection** — sound only fires on a genuine strike motion, not while hovering
- **Per-zone cooldown** — one physical strike cannot double-fire (configurable, default 180 ms)
- **Fading motion trail** — last 8 fingertip positions shown as shrinking dots
- **Two instrument modes** switchable live with **M**
- **Fully configurable** — zone layout, sound mappings, thresholds all in `config.py`
- **Placeholder sound generator** — ships with a script that synthesises WAV tones so it works out of the box without sample files

---

## Quick Start

### 1. Clone
```bash
git clone https://github.com/WATERFBG/Air-Guitar-Drums.git
cd Air-Guitar-Drums
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

> **Python 3.9 – 3.12** recommended. MediaPipe does not yet support 3.13+.

### 3. Generate placeholder sounds *(skip if you have real samples)*
```bash
python generate_sounds.py
```
This creates 12 short synthetic WAV tones in `sounds/` so the app is immediately playable.

### 4. Run
```bash
python main.py
```

---

## Controls

| Key | Action |
|-----|--------|
| **M** | Toggle Drum Kit ↔ Guitar mode |
| **Q** / **ESC** | Quit |

---

## How It Works

### Hand Tracking Pipeline
```
Webcam frame
    └─► MediaPipe Hands (up to 2 hands, 21 landmarks each)
            └─► Index fingertip (landmark 8) extracted as strike point
                    └─► Velocity calculated vs. previous frame
                            └─► Strike detector checks zone + velocity + cooldown
                                    └─► pygame plays sound on hit
```

### The Key Trick — Velocity Gating
Simply checking "is the hand inside a zone?" fires every frame the hand hovers there.  
Instead, the app:
1. Measures the **signed velocity** of the fingertip between consecutive frames
2. Only triggers if velocity exceeds a threshold (a real *strike* motion)
3. Enforces a **per-zone cooldown** to prevent one strike from double-firing

This is what makes it feel like an instrument rather than a noisy toy.

---

## Project Structure

```
Air-Guitar-Drums/
├── config.py               ← All settings: zones, sounds, thresholds, colours
├── main.py                 ← App: webcam loop, tracking, rendering, audio
├── generate_sounds.py      ← One-time helper: create synthetic placeholder WAVs
├── requirements.txt
├── README.md
└── sounds/
    ├── kick.wav
    ├── snare.wav
    ├── hihat.wav
    ├── crash.wav
    ├── tom1.wav
    ├── tom2.wav
    ├── string_e2.wav
    ├── string_a.wav
    ├── string_d.wav
    ├── string_g.wav
    ├── string_b.wav
    └── string_e4.wav
```

---

## Drum Kit Layout

```
┌────────────┬────────────┬────────────┐
│  HI-HAT    │   SNARE    │   CRASH    │
│            │            │            │
├────────────┼────────────┼────────────┤
│   KICK     │   TOM 1    │   TOM 2    │
│            │            │            │
└────────────┴────────────┴────────────┘
```
Strike any zone with a fast **downward** motion to trigger it.

## Guitar Layout

```
┌──────┬──────┬──────┬──────┬──────┬──────┐
│  E2  │  A   │  D   │  G   │  B   │  E4  │
│      │      │      │      │      │      │
│      │      │      │      │      │      │
└──────┴──────┴──────┴──────┴──────┴──────┘
```
Swipe your **right hand** horizontally across a band to strum it.  
Your **left hand** vertical position sets the chord label (Open / Power Chord / Barre).

---

## Using Real Sound Samples

Drop any `.wav` file into the `sounds/` folder and update the mapping in `config.py`:

```python
DRUM_ZONES = {
    "KICK": {"rect": (0.00, 0.50, 0.33, 0.50), "sound": "my_kick.wav"},
    ...
}
```

Free CC0 sample packs:
- [Freesound.org](https://freesound.org) — search "drum kit CC0"
- [OpenGameArt.org](https://opengameart.org) — many CC0 packs
- [SampleSwap](https://sampleswap.org)

---

## Configuration Reference (`config.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `CAMERA_INDEX` | `0` | Webcam device index |
| `FRAME_WIDTH / HEIGHT` | `640 × 480` | Capture resolution |
| `DRUM_VELOCITY_THRESHOLD` | `12` | Min downward px/frame for a drum hit |
| `GUITAR_VELOCITY_THRESHOLD` | `18` | Min horizontal px/frame for a strum |
| `ZONE_COOLDOWN_SECONDS` | `0.18` | Per-zone re-trigger lockout |
| `TRAIL_LENGTH` | `8` | Number of trail positions shown |
| `AUDIO_BUFFER` | `256` | pygame audio buffer (lower = less latency) |

### Adding a custom zone
```python
# In config.py → DRUM_ZONES
"COWBELL": {"rect": (0.85, 0.00, 0.15, 0.20), "sound": "cowbell.wav"},
# rect = (x_fraction, y_fraction, width_fraction, height_fraction)
```

---

## Performance Tips

- **Target ≥ 25 fps** — velocity detection degrades below ~20 fps
- If latency feels bad, lower `FRAME_WIDTH / FRAME_HEIGHT` in `config.py`
- On slower machines, change `max_num_hands=2` → `1` in `main.py` (~line 121) to halve MediaPipe CPU load
- If audio crackles, increase `AUDIO_BUFFER` from `256` to `512`

---

## Requirements

```
opencv-python >= 4.8
mediapipe     >= 0.10
pygame        >= 2.5
numpy         >= 1.24
```

---

## License

MIT — free to use, modify, and distribute.
