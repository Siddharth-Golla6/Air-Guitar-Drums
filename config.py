# ─────────────────────────────────────────────────────────────────────────────
# Air Instrument — Configuration
# Edit this file to remap zones, sounds, and detection thresholds without
# touching the main application code.
# ─────────────────────────────────────────────────────────────────────────────

# ── Camera ────────────────────────────────────────────────────────────────────
CAMERA_INDEX = 0          # 0 = default webcam
FRAME_WIDTH  = 640
FRAME_HEIGHT = 480

# ── Strike detection ──────────────────────────────────────────────────────────
# Downward velocity threshold (pixels per frame) to count as a drum "hit".
# Higher = requires a more forceful downward motion.
DRUM_VELOCITY_THRESHOLD = 12

# Horizontal velocity threshold (pixels per frame) for a guitar "strum".
GUITAR_VELOCITY_THRESHOLD = 18

# Per-zone cooldown in seconds — prevents a single strike from firing twice.
ZONE_COOLDOWN_SECONDS = 0.18

# Number of past fingertip positions to show as a motion trail.
TRAIL_LENGTH = 8

# ── Hand skeleton colours ─────────────────────────────────────────────────────
# BGR tuples used by OpenCV
COLOR_RIGHT_HAND     = (0, 255, 255)   # cyan
COLOR_LEFT_HAND      = (255, 0, 255)   # magenta
COLOR_FINGERTIP      = (0, 255, 0)     # bright green circle on tracked point
COLOR_ZONE_IDLE      = (255, 255, 255) # white border when zone is inactive
COLOR_ZONE_HIT       = (0, 200, 255)   # orange-yellow flash on hit
ZONE_FLASH_DURATION  = 0.15            # seconds a zone stays lit after a hit

# ── Drum kit layout ───────────────────────────────────────────────────────────
# Each zone is defined as a fraction of frame dimensions so it's
# resolution-independent.  Format:
#   "LABEL": {
#       "rect":  (x_frac, y_frac, w_frac, h_frac),   # top-left + size
#       "sound": "filename_inside_sounds/",
#   }
#
# The grid below is a 3 × 2 arrangement:
#   [ HI-HAT ]  [ SNARE  ]  [ CRASH  ]
#   [  KICK  ]  [  TOM1  ]  [  TOM2  ]

DRUM_ZONES = {
    "HI-HAT": {"rect": (0.00, 0.00, 0.33, 0.50), "sound": "hihat.wav"},
    "SNARE":  {"rect": (0.33, 0.00, 0.34, 0.50), "sound": "snare.wav"},
    "CRASH":  {"rect": (0.67, 0.00, 0.33, 0.50), "sound": "crash.wav"},
    "KICK":   {"rect": (0.00, 0.50, 0.33, 0.50), "sound": "kick.wav"},
    "TOM1":   {"rect": (0.33, 0.50, 0.34, 0.50), "sound": "tom1.wav"},
    "TOM2":   {"rect": (0.67, 0.50, 0.33, 0.50), "sound": "tom2.wav"},
}

# ── Guitar layout ─────────────────────────────────────────────────────────────
# Six vertical "string" bands, full-height.
# A horizontal swipe (right→left or left→right) crossing a band triggers it.
# The optional second dict "chord_zones" maps left-hand position to chord label
# (pure visual/label — the same sample plays, label is shown on screen).

GUITAR_STRINGS = {
    "E2":  {"rect": (0.00, 0.00, 0.165, 1.00), "sound": "string_e2.wav"},
    "A":   {"rect": (0.165, 0.00, 0.165, 1.00), "sound": "string_a.wav"},
    "D":   {"rect": (0.33, 0.00, 0.165, 1.00), "sound": "string_d.wav"},
    "G":   {"rect": (0.495, 0.00, 0.165, 1.00), "sound": "string_g.wav"},
    "B":   {"rect": (0.66, 0.00, 0.165, 1.00), "sound": "string_b.wav"},
    "E4":  {"rect": (0.825, 0.00, 0.175, 1.00), "sound": "string_e4.wav"},
}

# Left-hand vertical position → chord label (purely cosmetic label overlay)
GUITAR_CHORD_ZONES = {
    "Open":        (0.00, 0.33),   # top third   → y_frac range
    "Power Chord": (0.33, 0.66),
    "Barre":       (0.66, 1.00),
}

# ── Audio ─────────────────────────────────────────────────────────────────────
SOUNDS_DIR = "sounds"   # relative to main.py
AUDIO_FREQUENCY  = 44100
AUDIO_BUFFER     = 256   # smaller = lower latency; increase if you get glitches
AUDIO_CHANNELS   = 8     # simultaneous sound channels (polyphony)
