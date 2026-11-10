#!/usr/bin/env python3
"""Code-drawn series character, rendered with Manim Community Edition.

The fixed faceless-series character as clean flat vector shapes:
round head, hair cap with fringe, round glasses, expressive face
(neutral / surprised / worried), simple teal-and-orange body.
A 5-second demo timeline (neutral -> surprised -> worried) is built in.

Render a transparent PNG sequence (what the pipeline composites over
generated scene images):

    manim render -t --format=png tools/char_anim.py CharAnimScene

Frames land under media/images/char_anim/CharAnimScene/.
"""

import numpy as np

from manim import *  # noqa: F401,F403  (Manim CE scene API)

config.pixel_width = 1080
config.pixel_height = 1920
config.frame_rate = 30
# Pin the camera frame explicitly: with only pixel sizes set, Manim keeps
# the default 14.22-unit frame width and stretches the frame height to
# ~25.3 units for the portrait aspect, shrinking the character to ~30%.
config.frame_width = 4.5
config.frame_height = 8.0

# --- series palette -------------------------------------------------------
OUTLINE = "#26303B"
SKIN = "#F4C491"
SKIN_SHADE = "#E0A878"
HAIR = "#3B3F46"
TEAL = "#17807E"        # shirt
TEAL_DARK = "#0F5E5C"   # sleeves / collar
PANTS = "#2E4057"
ORANGE = "#FF8C42"      # shoes / pocket accents
MOUTH_DARK = "#7C3A30"
TONGUE = "#C96A5E"
SWEAT = "#8FD8F8"
SWEAT_EDGE = "#3E7CB1"

HEAD_C = np.array([0.0, 1.75, 0.0])
HEAD_R = 1.02
EYE_L = np.array([-0.37, 1.62, 0.0])
EYE_R = np.array([0.37, 1.62, 0.0])
MOUTH_C = np.array([0.0, 1.28, 0.0])
SHOULDER_L = np.array([-0.72, 0.38, 0.0])
SHOULDER_R = np.array([0.72, 0.38, 0.0])
ARM_LEN = 1.5


def _cap_points(center, r, a0=162.0, a1=18.0, n=40):
    pts = []
    for a in np.linspace(a0, a1, n):
        th = np.deg2rad(a)
        pts.append(center + np.array([r * np.cos(th), r * np.sin(th), 0.0]))
    return pts


def build_hair():
    """Hair cap: the head circle's own arc closed by its chord + fringe."""
    pts = _cap_points(HEAD_C, HEAD_R + 0.012)
    cap = VMobject()
    cap.set_points_as_corners([*pts, pts[0]])
    cap.set_fill(HAIR, opacity=1)
    cap.set_stroke(OUTLINE, width=6)
    fringe = VGroup(*[
        Circle(radius=0.115, color=HAIR).set_fill(HAIR, opacity=1)
        .set_stroke(width=0).move_to(HEAD_C + np.array([x, 0.325, 0.0]))
        for x in (-0.55, 0.0, 0.55)
    ])
    return VGroup(cap, fringe)


def build_arm(shoulder, side):
    """One arm: thick sleeve line + skin hand. side=-1 left, +1 right."""
    ang = np.deg2rad(16)
    end = shoulder + np.array([side * np.sin(ang) * ARM_LEN,
                               -np.cos(ang) * ARM_LEN, 0.0])
    sleeve = Line(shoulder, end, color=TEAL_DARK, stroke_width=30)
    hand = (Circle(radius=0.14, color=OUTLINE)
            .set_fill(SKIN, opacity=1).set_stroke(OUTLINE, width=5)
            .move_to(end))
    return VGroup(sleeve, hand)


def build_mouth(kind):
    if kind == "smile":
        arc = Arc(radius=0.20, start_angle=215 * DEGREES, angle=110 * DEGREES,
                  color=OUTLINE, stroke_width=9)
        arc.move_to(MOUTH_C + np.array([0.0, 0.11, 0.0]))
        return VGroup(arc)
    if kind == "open":
        outer = (Ellipse(width=0.30, height=0.44, color=OUTLINE)
                 .set_fill(MOUTH_DARK, opacity=1).set_stroke(OUTLINE, width=6)
                 .move_to(MOUTH_C + np.array([0.0, -0.03, 0.0])))
        tongue = (Ellipse(width=0.17, height=0.12, color=TONGUE)
                  .set_fill(TONGUE, opacity=1).set_stroke(width=0)
                  .move_to(MOUTH_C + np.array([0.0, -0.16, 0.0])))
        return VGroup(outer, tongue)
    # worried: small wavy line
    pts = [MOUTH_C + np.array([dx, dy, 0.0]) for dx, dy in
           ((-0.22, 0.0), (-0.11, 0.055), (0.0, -0.055), (0.11, 0.055),
            (0.22, 0.0))]
    wave = VMobject(color=OUTLINE, stroke_width=9)
    wave.set_points_smoothly(pts)
    return VGroup(wave)


def build_sweat():
    top = Polygon(np.array([0.0, 0.17, 0.0]), np.array([-0.09, -0.03, 0.0]),
                  np.array([0.09, -0.03, 0.0]), color=SWEAT_EDGE)
    top.set_fill(SWEAT, opacity=1).set_stroke(SWEAT_EDGE, width=4)
    bulb = (Circle(radius=0.095, color=SWEAT_EDGE)
            .set_fill(SWEAT, opacity=1).set_stroke(SWEAT_EDGE, width=4)
            .move_to(np.array([0.0, -0.06, 0.0])))
    drop = VGroup(top, bulb).move_to(np.array([1.24, 2.42, 0.0]))
    drop.set_opacity(0)
    return drop


def build_character():
    """Return (whole VGroup, dict of named parts for animation)."""
    p = {}

    p["shadow"] = (Ellipse(width=2.6, height=0.35, color=BLACK)
                   .set_fill(BLACK, opacity=0.14).set_stroke(width=0)
                   .move_to(np.array([0.0, -3.66, 0.0])))

    legs = []
    shoes = []
    for sx in (-0.30, 0.30):
        legs.append(RoundedRectangle(corner_radius=0.10, width=0.52,
                                     height=1.85, color=OUTLINE)
                    .set_fill(PANTS, opacity=1).set_stroke(OUTLINE, width=6)
                    .move_to(np.array([sx, -2.47, 0.0])))
        shoes.append(RoundedRectangle(corner_radius=0.12, width=0.64,
                                      height=0.30, color=OUTLINE)
                     .set_fill(ORANGE, opacity=1).set_stroke(OUTLINE, width=6)
                     .move_to(np.array([sx + np.sign(sx) * 0.03, -3.47, 0.0])))
    p["legs"] = VGroup(*legs)
    p["shoes"] = VGroup(*shoes)

    p["arm_l"] = build_arm(SHOULDER_L, -1)
    p["arm_r"] = build_arm(SHOULDER_R, +1)

    p["neck"] = (Rectangle(width=0.42, height=0.38, color=OUTLINE)
                 .set_fill(SKIN, opacity=1).set_stroke(OUTLINE, width=5)
                 .move_to(np.array([0.0, 0.62, 0.0])))

    torso = (RoundedRectangle(corner_radius=0.18, width=1.56, height=2.16,
                              color=OUTLINE)
             .set_fill(TEAL, opacity=1).set_stroke(OUTLINE, width=7)
             .move_to(np.array([0.0, -0.52, 0.0])))
    collar = Polygon(np.array([-0.23, 0.56, 0.0]), np.array([0.23, 0.56, 0.0]),
                     np.array([0.0, 0.27, 0.0]), color=TEAL_DARK)
    collar.set_fill(TEAL_DARK, opacity=1).set_stroke(TEAL_DARK, width=3)
    pocket = (RoundedRectangle(corner_radius=0.04, width=0.22, height=0.22,
                               color=OUTLINE)
              .set_fill(ORANGE, opacity=1).set_stroke(OUTLINE, width=4)
              .move_to(np.array([0.44, -0.18, 0.0])))
    buttons = VGroup(*[Dot(point=np.array([0.0, y, 0.0]), radius=0.045,
                            color=OUTLINE) for y in (-0.55, -0.98)])
    p["torso"] = VGroup(torso, collar, pocket, buttons)

    # --- head group (tilts as one for the worried beat) ---
    ears = VGroup(*[
        Circle(radius=0.17, color=OUTLINE).set_fill(SKIN, opacity=1)
        .set_stroke(OUTLINE, width=5)
        .move_to(np.array([sx * 1.05, 1.68, 0.0])) for sx in (-1, 1)])
    head = (Circle(radius=HEAD_R, color=OUTLINE)
            .set_fill(SKIN, opacity=1).set_stroke(OUTLINE, width=8)
            .move_to(HEAD_C))
    nose = Polygon(np.array([-0.065, 1.585, 0.0]),
                   np.array([0.065, 1.585, 0.0]),
                   np.array([0.0, 1.455, 0.0]), color=OUTLINE)
    nose.set_fill(SKIN_SHADE, opacity=0.55).set_stroke(OUTLINE, width=5)

    whites, pupils = [], []
    for c in (EYE_L, EYE_R):
        whites.append(Circle(radius=0.115, color=OUTLINE)
                      .set_fill(WHITE, opacity=1).set_stroke(OUTLINE, width=5)
                      .move_to(c))
        pupils.append(Circle(radius=0.062, color=OUTLINE)
                      .set_fill(OUTLINE, opacity=1).set_stroke(width=0)
                      .move_to(c + np.array([0.0, 0.008, 0.0])))
    p["whites"] = VGroup(*whites)
    p["pupils"] = VGroup(*pupils)

    brow_l = Line(np.array([-0.63, 2.03, 0.0]), np.array([-0.15, 2.03, 0.0]),
                  color=OUTLINE, stroke_width=10)
    brow_r = Line(np.array([0.15, 2.03, 0.0]), np.array([0.63, 2.03, 0.0]),
                  color=OUTLINE, stroke_width=10)
    p["brow_l"], p["brow_r"] = brow_l, brow_r

    glass_l = (Circle(radius=0.335, color=OUTLINE).set_fill(opacity=0)
               .set_stroke(OUTLINE, width=7).move_to(EYE_L))
    glass_r = (Circle(radius=0.335, color=OUTLINE).set_fill(opacity=0)
               .set_stroke(OUTLINE, width=7).move_to(EYE_R))
    bridge = Line(np.array([-0.045, 1.67, 0.0]), np.array([0.045, 1.67, 0.0]),
                  color=OUTLINE, stroke_width=7)
    temple_l = Line(np.array([-0.70, 1.67, 0.0]), np.array([-1.0, 1.71, 0.0]),
                    color=OUTLINE, stroke_width=7)
    temple_r = Line(np.array([0.70, 1.67, 0.0]), np.array([1.0, 1.71, 0.0]),
                    color=OUTLINE, stroke_width=7)
    glasses = VGroup(glass_l, glass_r, bridge, temple_l, temple_r)

    p["mouth"] = build_mouth("smile")
    p["sweat"] = build_sweat()
    p["hair"] = build_hair()

    head_group = VGroup(ears, head, p["hair"], nose, p["whites"], p["pupils"],
                        p["brow_l"], p["brow_r"], glasses, p["mouth"],
                        p["sweat"])
    p["head_group"] = head_group

    char = VGroup(p["shadow"], p["legs"], p["shoes"], p["arm_l"], p["arm_r"],
                  p["neck"], p["torso"], head_group)
    return char, p


class CharAnimScene(Scene):
    """5s demo: neutral -> surprised -> worried, smooth transitions."""

    def construct(self):
        # NOTE: never animate `char` (the parent group) in the same play
        # as any of its descendants — the parent's transform overwrites
        # the children's points every frame and silently cancels their
        # animations (verified: arm rotations died when combined with a
        # char shift). Parent moves get their own plays.
        char, p = build_character()
        mouth = p["mouth"]
        self.add(char)

        # -- neutral hold with a gentle idle bob (0.0 - 1.3s) --
        self.play(char.animate.shift(UP * 0.05), run_time=0.65,
                  rate_func=smooth)
        self.play(char.animate.shift(DOWN * 0.05), run_time=0.65,
                  rate_func=smooth)

        # -- become surprised (1.3 - 1.85s): arms up, mouth open,
        #    brows raised, eyes wide, sweat drop appears --
        open_mouth = build_mouth("open")
        self.play(
            FadeTransform(mouth, open_mouth),
            p["arm_l"].animate.rotate(-140 * DEGREES,
                                      about_point=SHOULDER_L),
            p["arm_r"].animate.rotate(140 * DEGREES,
                                      about_point=SHOULDER_R),
            p["brow_l"].animate.shift(UP * 0.085),
            p["brow_r"].animate.shift(UP * 0.085),
            # scale each eye about its OWN center — scaling the whites
            # group about one eye displaces the other eye (verified).
            p["whites"][0].animate.scale(1.55, about_point=EYE_L),
            p["whites"][1].animate.scale(1.55, about_point=EYE_R),
            p["pupils"][0].animate.scale(1.15, about_point=EYE_L),
            p["pupils"][1].animate.scale(1.15, about_point=EYE_R),
            p["sweat"].animate.set_opacity(1),
            run_time=0.55, rate_func=smooth,
        )
        mouth = open_mouth

        # -- surprised hold (1.85 - 2.75s): sweat slides down, then a
        #    small settle bob (parent-only play) --
        self.play(p["sweat"].animate.shift(DOWN * 0.13), run_time=0.45,
                  rate_func=smooth)
        self.play(char.animate.shift(DOWN * 0.035), run_time=0.45,
                  rate_func=smooth)

        # -- become worried (2.75 - 3.25s): arms sink (asymmetric), wavy
        #    mouth, sideways glance, slanted brows, sweat drop goes --
        worry_mouth = build_mouth("worry")
        self.play(
            FadeTransform(mouth, worry_mouth),
            p["arm_l"].animate.rotate(130 * DEGREES,
                                      about_point=SHOULDER_L),
            p["arm_r"].animate.rotate(-130 * DEGREES,
                                      about_point=SHOULDER_R),
            p["brow_l"].animate.rotate(0.26, about_point=np.array(
                [-0.39, 2.03, 0.0])).shift(DOWN * 0.105),
            p["brow_r"].animate.rotate(-0.26, about_point=np.array(
                [0.39, 2.03, 0.0])).shift(DOWN * 0.105),
            p["whites"][0].animate.scale(1 / 1.55, about_point=EYE_L),
            p["whites"][1].animate.scale(1 / 1.55, about_point=EYE_R),
            p["pupils"][0].animate.scale(1 / 1.15, about_point=EYE_L),
            p["pupils"][1].animate.scale(1 / 1.15, about_point=EYE_R),
            p["pupils"].animate.shift(RIGHT * 0.085),
            p["sweat"].animate.set_opacity(0),
            run_time=0.5, rate_func=smooth,
        )
        mouth = worry_mouth

        # -- head tilt gets its own play: head_group is the parent of
        #    the face parts, so tilting it in the same play as theirs
        #    would clobber their animations (same rule as `char`) --
        self.play(p["head_group"].animate.rotate(-0.055,
                                                 about_point=HEAD_C),
                  run_time=0.25, rate_func=smooth)

        # -- worried hold (3.5 - 5.0s): glance left, glance back --
        self.play(p["pupils"].animate.shift(LEFT * 0.17), run_time=0.65,
                  rate_func=smooth)
        self.play(p["pupils"].animate.shift(RIGHT * 0.17), run_time=0.65,
                  rate_func=smooth)
        self.wait(0.2)
