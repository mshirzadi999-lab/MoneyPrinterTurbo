"""THE character - single source of truth. DO NOT redesign from scratch.

Canonical Shorts character (approved by Mehdi, 2026-11-10): warm-red filled
torso whose SLEEVES ARE the upper arms (same red, one piece), white forearms
and round hands, navy legs, round white head, soft ground shadow.
Design notes + rules: see CHARACTER.md in this folder.
Extracted verbatim from the original hybrid test (make_hybrid.py) that Mehdi
approved. Extend THIS code (new phases/poses) - never redraw the character
in another style or tool unless Mehdi explicitly approves a new design.
"""
#!/usr/bin/env python3

import math, os
from PIL import Image, ImageDraw

W, H = 720, 1280
FPS, DUR = 24, 5
N = FPS * DUR
SS = 2  # supersample for smooth lines
# NOTE (2026-11-10): the original's background-loading scaffolding was removed
# when extracting this module - draw_character only draws the character layer
# and never used the background. Drawing code below is otherwise verbatim.

BLACK = (20, 20, 20, 255)
WHITE = (255, 255, 255, 255)
SHIRT = (196, 58, 44, 255)     # warm red
PANTS = (38, 44, 66, 255)      # dark navy
SKIN = WHITE

def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

def lerp(a, b, t):
    return a + (b - a) * t

def draw_character(t):
    """Return RGBA layer (supersampled then downscaled) with shadow + character."""
    s = SS
    layer = Image.new("RGBA", (W * s, H * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # timeline phases
    shock = 0.0
    if t < 1.5:
        phase = "idle"
    elif t < 2.2:
        phase = "notice"; shock = ease((t - 1.5) / 0.7) * 0.4
    elif t < 3.5:
        phase = "shock"; shock = 0.4 + 0.6 * ease((t - 2.2) / 0.35)
        if t > 3.1: shock = 1.0 - 0.45 * ease((t - 3.1) / 0.4)
    else:
        phase = "worried"; shock = 0.55

    cx = W // 2
    ground = 1135
    bob = 4 * math.sin(t * 2.2) if phase == "idle" else 0
    hop = 0
    if phase == "shock" and 2.2 <= t < 3.1:
        hop = -26 * math.sin(math.pi * min(1.0, (t - 2.2) / 0.5)) if t < 2.7 else 0
    lean = -6 * shock  # lean back a bit
    feet_y = ground + bob + hop

    # soft shadow
    sh_w = 150 - abs(hop) * 0.8
    d.ellipse([(cx - sh_w) * s, (ground + 8) * s, (cx + sh_w) * s, (ground + 34) * s],
              fill=(0, 0, 0, 110))

    hip_y = feet_y - 150
    shoulder_y = hip_y - 150 + bob * 0.4
    head_r = 78
    head_cx = cx + lean
    head_cy = shoulder_y - head_r - 12

    lw = 17 * s  # limb width
    # legs
    spread = 46
    d.line([(cx - 12) * s, hip_y * s, (cx - spread) * s, feet_y * s], fill=PANTS, width=lw, joint="curve")
    d.line([(cx + 12) * s, hip_y * s, (cx + spread) * s, feet_y * s], fill=PANTS, width=lw, joint="curve")
    # shoes
    for sx in (cx - spread, cx + spread):
        d.ellipse([(sx - 26) * s, (feet_y - 8) * s, (sx + 30) * s, (feet_y + 14) * s], fill=BLACK)
    # torso (shirt) as thick line + rounded body
    d.line([(cx) * s, hip_y * s, (cx + lean * 0.5) * s, shoulder_y * s], fill=SHIRT, width=64 * s, joint="curve")
    d.ellipse([(cx + lean * 0.5 - 34) * s, (shoulder_y - 12) * s, (cx + lean * 0.5 + 34) * s, (shoulder_y + 22) * s], fill=SHIRT)
    d.rectangle([(cx - 34) * s, (hip_y - 26) * s, (cx + 34) * s, (hip_y + 8) * s], fill=PANTS)

    # arms: idle down; shock up
    arm_drop = lerp(120, -105, shock)   # hand y offset relative to shoulder
    arm_out = lerp(58, 105, shock)
    sh_x, sh_y = cx + lean * 0.5, shoulder_y + 8
    for side in (-1, 1):
        hx = sh_x + side * arm_out
        hy = sh_y + arm_drop + (6 * math.sin(t * 2.2 + side) if phase == "idle" else 0)
        ex = sh_x + side * (arm_out * 0.55)
        ey = sh_y + arm_drop * 0.45 + 18
        d.line([sh_x * s, sh_y * s, ex * s, ey * s], fill=SHIRT, width=26 * s, joint="curve")
        d.line([ex * s, ey * s, hx * s, hy * s], fill=SKIN, width=15 * s, joint="curve")
        d.ellipse([(hx - 13) * s, (hy - 13) * s, (hx + 13) * s, (hy + 13) * s], fill=WHITE, outline=BLACK, width=3 * s)

    # head
    d.ellipse([(head_cx - head_r) * s, (head_cy - head_r) * s, (head_cx + head_r) * s, (head_cy + head_r) * s],
              fill=WHITE, outline=BLACK, width=6 * s)
    # eyes
    look = 0
    if phase == "notice": look = -10
    if phase in ("shock", "worried"): look = -6
    eye_y = head_cy - 10
    eye_r = lerp(7, 11, shock)
    for side in (-1, 1):
        ex = head_cx + side * 30 + look
        if phase == "idle" and (t % 2.6) > 2.42:  # blink
            d.line([(ex - 9) * s, eye_y * s, (ex + 9) * s, eye_y * s], fill=BLACK, width=4 * s)
        else:
            d.ellipse([(ex - eye_r) * s, (eye_y - eye_r) * s, (ex + eye_r) * s, (eye_y + eye_r) * s], fill=BLACK)
    # brows
    brow_raise = lerp(0, 12, shock)
    for side in (-1, 1):
        bx = head_cx + side * 30 + look
        by = eye_y - 26 - brow_raise
        tilt = -6 * side if phase == "worried" else 0
        d.line([(bx - 13) * s, (by + tilt) * s, (bx + 13) * s, (by - tilt) * s], fill=BLACK, width=5 * s)
    # mouth
    m_y = head_cy + 34
    if phase == "idle":
        d.arc([(head_cx - 20 + look) * s, (m_y - 12) * s, (head_cx + 20 + look) * s, (m_y + 16) * s], 15, 165, fill=BLACK, width=5 * s)
    elif phase == "shock" and shock > 0.6:
        d.ellipse([(head_cx - 13 + look) * s, (m_y - 4) * s, (head_cx + 13 + look) * s, (m_y + 26) * s], fill=BLACK)
        # sweat drop
        sxp, syp = head_cx + head_r - 6, head_cy - 26
        d.ellipse([(sxp - 8) * s, (syp - 12) * s, (sxp + 8) * s, (syp + 10) * s], fill=(90, 180, 255, 255))
        d.polygon([(sxp - 7) * s, (syp - 6) * s, (sxp + 7) * s, (syp - 6) * s, sxp * s, (syp - 24) * s], fill=(90, 180, 255, 255))
    else:
        d.arc([(head_cx - 16 + look) * s, (m_y + 2) * s, (head_cx + 16 + look) * s, (m_y + 24) * s], 195, 345, fill=BLACK, width=5 * s)

    return layer.resize((W, H), Image.LANCZOS)

# ---------------------------------------------------------------------------
# Convenience API (added 2026-11-10; drawing logic above is UNCHANGED)
# Representative timeline timestamps per beat, from the original 5s test.
PHASE_T = {"idle": 0.8, "shock": 2.5, "worried": 4.2}

def character_layer(phase="idle"):
    """Return the RGBA character layer for a named beat."""
    return draw_character(PHASE_T[phase])
