"""
Air Guitar / Air Drum Kit
─────────────────────────
Webcam-based instrument that triggers sounds when your hand strikes virtual
zones.  Press  M  to toggle between Drum Kit and Guitar modes.
Press  Q  or  ESC  to quit.

Full MediaPipe hand-skeleton overlay is always visible.
"""

import os
import time
import collections
import cv2
import mediapipe as mp
import numpy as np
import pygame

import config

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def px(frac_x, frac_y, w, h):
    """Convert fractional coords to pixel coords."""
    return int(frac_x * w), int(frac_y * h)


def load_sounds(zone_dict, sounds_dir):
    """Pre-load every unique sound file referenced in zone_dict.
    Returns {filename: pygame.mixer.Sound}."""
    cache = {}
    for info in zone_dict.values():
        fname = info["sound"]
        if fname not in cache:
            path = os.path.join(sounds_dir, fname)
            if os.path.exists(path):
                cache[fname] = pygame.mixer.Sound(path)
            else:
                print(f"[WARN] Sound file not found: {path}")
                cache[fname] = None
    return cache


def zone_rect_px(rect_frac, w, h):
    """Return (x1, y1, x2, y2) in pixels for a fractional rect."""
    x1 = int(rect_frac[0] * w)
    y1 = int(rect_frac[1] * h)
    x2 = int((rect_frac[0] + rect_frac[2]) * w)
    y2 = int((rect_frac[1] + rect_frac[3]) * h)
    return x1, y1, x2, y2


def point_in_rect(px_coord, rect_px):
    x, y = px_coord
    x1, y1, x2, y2 = rect_px
    return x1 <= x <= x2 and y1 <= y <= y2


# ─────────────────────────────────────────────────────────────────────────────
# Drawing helpers
# ─────────────────────────────────────────────────────────────────────────────

# MediaPipe connection list mirrors mp.solutions.hands.HAND_CONNECTIONS
_MP_HANDS = mp.solutions.hands
_CONNECTIONS = _MP_HANDS.HAND_CONNECTIONS


def draw_skeleton(frame, hand_landmarks, color, w, h):
    """Draw all 21 landmarks + connection lines for one hand."""
    pts = []
    for lm in hand_landmarks.landmark:
        cx, cy = int(lm.x * w), int(lm.y * h)
        pts.append((cx, cy))

    # Connection lines
    for start_idx, end_idx in _CONNECTIONS:
        cv2.line(frame, pts[start_idx], pts[end_idx], color, 2, cv2.LINE_AA)

    # Landmark dots
    for i, (cx, cy) in enumerate(pts):
        r = 6 if i == 0 else 4
        cv2.circle(frame, (cx, cy), r, color, -1, cv2.LINE_AA)

    return pts


def draw_zones(frame, zones, hit_times, mode_color, w, h, now):
    """Render zone overlays with flash effect."""
    overlay = frame.copy()
    for label, info in zones.items():
        x1, y1, x2, y2 = zone_rect_px(info["rect"], w, h)
        last_hit = hit_times.get(label, 0)
        is_flashing = (now - last_hit) < config.ZONE_FLASH_DURATION

        fill_color = config.COLOR_ZONE_HIT if is_flashing else (40, 40, 40)
        cv2.rectangle(overlay, (x1, y1), (x2, y2), fill_color, -1)

    cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)

    for label, info in zones.items():
        x1, y1, x2, y2 = zone_rect_px(info["rect"], w, h)
        last_hit = hit_times.get(label, 0)
        is_flashing = (now - last_hit) < config.ZONE_FLASH_DURATION

        border_color = config.COLOR_ZONE_HIT if is_flashing else config.COLOR_ZONE_IDLE
        cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, 2)

        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.putText(frame, label, (cx - tw // 2, cy + th // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, border_color, 2, cv2.LINE_AA)


def draw_trail(frame, trail, color):
    """Draw fading motion trail dots."""
    n = len(trail)
    for i, pt in enumerate(trail):
        alpha = int(200 * (i + 1) / n)
        r = max(2, int(6 * (i + 1) / n))
        c = tuple(int(ch * alpha / 255) for ch in color)
        cv2.circle(frame, pt, r, c, -1, cv2.LINE_AA)


def draw_hud(frame, mode, hit_counts, chord_label, w, h):
    """Top-left status block."""
    lines = [
        f"MODE: {'DRUM KIT' if mode == 'drum' else 'GUITAR'}  [M]=switch  [Q]=quit",
        f"HITS: {sum(hit_counts.values())}",
    ]
    if chord_label:
        lines.append(f"CHORD: {chord_label}")

    for i, line in enumerate(lines):
        y = 28 + i * 26
        cv2.putText(frame, line, (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (220, 220, 220), 2, cv2.LINE_AA)


# ─────────────────────────────────────────────────────────────────────────────
# Strike detector
# ─────────────────────────────────────────────────────────────────────────────

class StrikeDetector:
    """Tracks per-zone cooldown and velocity gating."""

    def __init__(self, zones, velocity_axis="y"):
        self.zones = zones
        self.velocity_axis = velocity_axis   # "y" for drums, "x" for guitar
        self.last_hit_time = {z: 0.0 for z in zones}

    def check(self, tip_px, velocity, sound_cache, hit_counts, hit_times, now, w, h):
        """
        tip_px   : (x, y) pixel coord of the tracked point
        velocity : signed float (positive = down for drum, positive = right for guitar)
        Returns list of zone labels that were triggered.
        """
        triggered = []
        threshold = (config.DRUM_VELOCITY_THRESHOLD if self.velocity_axis == "y"
                     else config.GUITAR_VELOCITY_THRESHOLD)

        if abs(velocity) < threshold:
            return triggered

        for label, info in self.zones.items():
            rect = zone_rect_px(info["rect"], w, h)
            if not point_in_rect(tip_px, rect):
                continue
            cooldown_ok = (now - self.last_hit_time[label]) >= config.ZONE_COOLDOWN_SECONDS
            if not cooldown_ok:
                continue

            self.last_hit_time[label] = now
            hit_times[label] = now
            hit_counts[label] = hit_counts.get(label, 0) + 1

            snd = sound_cache.get(info["sound"])
            if snd:
                snd.play()

            triggered.append(label)

        return triggered


# ─────────────────────────────────────────────────────────────────────────────
# Guitar chord detector (left-hand y position)
# ─────────────────────────────────────────────────────────────────────────────

def get_chord_label(wrist_y_frac):
    for label, (y_min, y_max) in config.GUITAR_CHORD_ZONES.items():
        if y_min <= wrist_y_frac <= y_max:
            return label
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # ── Audio init ────────────────────────────────────────────────────────────
    pygame.mixer.pre_init(
        frequency=config.AUDIO_FREQUENCY,
        size=-16,
        channels=2,
        buffer=config.AUDIO_BUFFER,
    )
    pygame.mixer.init()
    pygame.mixer.set_num_channels(config.AUDIO_CHANNELS)

    sounds_dir = os.path.join(os.path.dirname(__file__), config.SOUNDS_DIR)
    drum_sounds   = load_sounds(config.DRUM_ZONES,    sounds_dir)
    guitar_sounds = load_sounds(config.GUITAR_STRINGS, sounds_dir)

    # ── MediaPipe ─────────────────────────────────────────────────────────────
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.5,
    )

    # ── Camera ────────────────────────────────────────────────────────────────
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera resolution: {w}x{h}")

    # ── State ─────────────────────────────────────────────────────────────────
    mode = "drum"   # "drum" or "guitar"

    drum_detector   = StrikeDetector(config.DRUM_ZONES,    velocity_axis="y")
    guitar_detector = StrikeDetector(config.GUITAR_STRINGS, velocity_axis="x")

    hit_counts = {}
    hit_times  = {}     # label -> time of last hit (for flash)

    # Per-hand trail deques  {handedness_label: deque}
    trails = collections.defaultdict(lambda: collections.deque(maxlen=config.TRAIL_LENGTH))

    # Previous fingertip positions for velocity calc  {handedness_label: (x,y)}
    prev_tip = {}

    chord_label = ""

    # ── Main loop ─────────────────────────────────────────────────────────────
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to read from camera.")
            break

        frame = cv2.flip(frame, 1)   # mirror so left/right feel natural
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        now = time.time()

        # ── Draw zones ────────────────────────────────────────────────────────
        zones = config.DRUM_ZONES if mode == "drum" else config.GUITAR_STRINGS
        detector = drum_detector if mode == "drum" else guitar_detector
        draw_zones(frame, zones, hit_times, config.COLOR_ZONE_IDLE, w, h, now)

        chord_label = ""

        # ── Process hands ─────────────────────────────────────────────────────
        if result.multi_hand_landmarks:
            for hand_lm, hand_info in zip(result.multi_hand_landmarks,
                                          result.multi_handedness):
                label = hand_info.classification[0].label   # "Left" or "Right"

                hand_color = (config.COLOR_RIGHT_HAND if label == "Right"
                              else config.COLOR_LEFT_HAND)

                # Draw full skeleton
                pts = draw_skeleton(frame, hand_lm, hand_color, w, h)

                # Index fingertip = landmark 8
                tip = pts[8]
                tip_frac_x = hand_lm.landmark[8].x
                tip_frac_y = hand_lm.landmark[8].y

                # Motion trail
                trails[label].append(tip)
                draw_trail(frame, trails[label], hand_color)

                # Highlighted tracked point
                cv2.circle(frame, tip, 10, config.COLOR_FINGERTIP, -1, cv2.LINE_AA)
                cv2.circle(frame, tip, 12, (255, 255, 255), 2, cv2.LINE_AA)

                # Velocity (signed pixels/frame)
                if label in prev_tip:
                    dx = tip[0] - prev_tip[label][0]
                    dy = tip[1] - prev_tip[label][1]
                else:
                    dx, dy = 0, 0
                prev_tip[label] = tip

                # Guitar: left hand determines chord, right hand strums
                if mode == "guitar":
                    if label == "Left":
                        wrist_y = hand_lm.landmark[0].y
                        chord_label = get_chord_label(wrist_y)
                    if label == "Right":
                        detector.check(tip, dx, guitar_sounds,
                                       hit_counts, hit_times, now, w, h)
                else:
                    # Drum: either hand can strike
                    detector.check(tip, dy, drum_sounds,
                                   hit_counts, hit_times, now, w, h)

                # Hand label badge
                cv2.putText(frame, label, (tip[0] + 14, tip[1]),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, hand_color, 2, cv2.LINE_AA)

        # ── HUD ───────────────────────────────────────────────────────────────
        draw_hud(frame, mode, hit_counts, chord_label, w, h)

        cv2.imshow("Air Instrument", frame)

        # ── Key handling ──────────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), 27):     # Q or ESC
            break
        elif key == ord('m'):
            mode = "guitar" if mode == "drum" else "drum"
            hit_times.clear()
            trails.clear()
            prev_tip.clear()
            print(f"Switched to {'GUITAR' if mode == 'guitar' else 'DRUM'} mode")

    cap.release()
    cv2.destroyAllWindows()
    hands.close()
    pygame.mixer.quit()


if __name__ == "__main__":
    main()
