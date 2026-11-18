"""Original pose drawings in native pixels. Run from any directory with Pillow."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
EVIDENCE = ROOT / "evidence"
SIZE = 96
FLOOR = 78
ANCHOR = 44
TICK = 80

INK = "#201829"
DEEP = "#183843"
TEAL = "#27615f"
MINT = "#3d8981"
EDGE = "#75aea0"
HAIR = "#4b303a"
HAIR_LIGHT = "#704552"
SKIN = "#ffcd9c"
SHADE = "#d1846b"
BLUSH = "#eea382"
CREAM = "#f8e5b2"
CLOTH = "#b4a079"
PANTS = "#594250"
BOOT = "#694239"
SOLE = "#422831"
ORANGE = "#dd6237"
RUST = "#9b3a32"
PEACH = "#f8924b"
GOLD = "#ffc965"
BAG = "#a96236"

# Tuple order: pose label, hold in ticks, hip offset, head offset, near/far
# knee and foot (absolute canvas coordinates), near/far hand (relative to
# hip), scarf wave, and optional weapon/effect pose.
CLIPS = {
    "idle": (True, [
        ("Rest", 3, (0,0), (0,0), ((47,67),(49,77)), ((39,68),(38,77)), (9,-2), (13,-1), 0, ""),
        ("Inhale", 2, (0,0), (0,-1), ((47,67),(49,77)), ((39,68),(38,77)), (9,-3), (13,-1), 1, ""),
        ("Lift", 2, (0,-1), (0,-1), ((46,66),(49,77)), ((40,67),(38,77)), (8,-2), (13,0), 2, ""),
        ("Settle", 2, (-1,0), (0,-1), ((46,67),(49,77)), ((39,68),(38,77)), (9,-2), (13,-1), 1, ""),
        ("Blink", 1, (-1,0), (0,0), ((46,67),(49,77)), ((39,68),(38,77)), (9,-1), (13,-1), 0, ""),
        ("Exhale", 2, (0,0), (0,0), ((47,67),(49,77)), ((39,68),(38,77)), (10,-2), (13,0), -1, ""),
    ]),
    "run": (True, [
        ("Near contact", 1, (0,0), (4,0), ((53,65),(58,77)), ((35,64),(29,71)), (-12,-2), (17,-12), 2, ""),
        ("Near load", 1, (0,2), (4,0), ((52,69),(52,77)), ((36,65),(32,70)), (-10,-2), (15,-11), 0, ""),
        ("Pass", 1, (0,0), (4,-1), ((46,67),(45,77)), ((44,65),(35,67)), (-3,-3), (9,-8), -2, ""),
        ("Near push", 1, (0,-3), (4,0), ((39,65),(37,73)), ((55,61),(54,67)), (9,-8), (-3,-3), -1, ""),
        ("Far contact", 1, (0,0), (4,0), ((37,64),(32,69)), ((54,65),(57,77)), (15,-14), (-13,-4), 2, ""),
        ("Far load", 1, (0,2), (4,0), ((39,64),(34,68)), ((51,69),(51,77)), (14,-12), (-11,-2), 0, ""),
        ("Pass", 1, (0,0), (4,-1), ((44,65),(35,67)), ((46,67),(45,77)), (9,-8), (-3,-3), -2, ""),
        ("Far push", 1, (0,-3), (4,0), ((57,61),(57,66)), ((40,65),(37,74)), (-5,-4), (9,-8), -1, ""),
    ]),
    "jump": (False, [
        ("Ready", 2, (0,0), (0,0), ((47,67),(49,77)), ((39,68),(38,77)), (9,-2), (13,-1), 0, ""),
        ("Bend", 1, (-2,3), (1,0), ((50,69),(49,77)), ((42,70),(38,77)), (-4,-2), (12,-8), 0, ""),
        ("Crouch", 2, (-4,7), (3,1), ((51,70),(49,77)), ((43,70),(38,77)), (-9,-4), (11,-7), 1, ""),
        ("Takeoff", 1, (-1,-4), (3,-1), ((46,63),(47,77)), ((38,63),(36,74)), (10,-20), (13,-14), -2, ""),
        ("Rise", 1, (0,-13), (3,-2), ((52,53),(51,62)), ((37,54),(32,60)), (14,-22), (14,-15), -5, ""),
        ("Apex", 2, (2,-16), (2,0), ((56,48),(55,55)), ((41,50),(35,55)), (15,-17), (16,-13), -3, ""),
        ("Fall", 1, (3,-14), (2,1), ((54,54),(57,63)), ((42,55),(36,63)), (16,-13), (15,-9), 2, ""),
        ("Reach", 1, (3,-7), (1,0), ((52,60),(56,70)), ((42,61),(39,70)), (15,-6), (14,-5), 4, ""),
        ("Land", 1, (3,4), (2,1), ((56,69),(55,77)), ((46,70),(42,77)), (16,-4), (14,-7), 3, "dust"),
        ("Absorb", 2, (1,7), (2,1), ((55,70),(55,77)), ((46,70),(42,77)), (9,-4), (12,-5), 0, "dust2"),
        ("Recover", 3, (1,1), (0,0), ((50,67),(53,77)), ((41,68),(41,77)), (10,-2), (13,-1), -1, ""),
    ]),
    "attack": (False, [
        ("Ready", 2, (0,0), (0,0), ((47,67),(49,77)), ((39,68),(38,77)), (9,-2), (13,-1), 0, ""),
        ("Draw", 1, (-2,2), (0,0), ((47,68),(49,77)), ((39,68),(38,77)), (-4,-4), (13,-8), 1, "draw"),
        ("Wind up", 2, (-5,3), (1,0), ((46,68),(49,77)), ((38,69),(38,77)), (-11,-12), (14,-8), 2, "wind"),
        ("Swing", 1, (1,0), (3,0), ((53,65),(59,74)), ((38,68),(38,77)), (11,-20), (13,-5), 1, "swing"),
        ("Strike", 2, (5,3), (3,0), ((60,68),(61,77)), ((40,69),(38,77)), (20,-12), (3,-6), -2, "strike"),
        ("Follow through", 1, (5,4), (3,1), ((60,69),(61,77)), ((42,69),(38,77)), (18,-3), (3,-4), -3, "follow"),
        ("Hold", 1, (4,3), (2,0), ((59,69),(61,77)), ((43,70),(38,77)), (14,0), (7,-4), -1, "lower"),
        ("Sheathe", 2, (2,1), (1,0), ((55,68),(56,77)), ((41,68),(38,77)), (4,-4), (12,-4), 1, "draw"),
        ("Recover", 3, (0,0), (0,0), ((48,67),(49,77)), ((39,68),(38,77)), (10,-1), (13,-1), 0, ""),
    ]),
}


def render(action, pose):
    name, _hold, hip, head, near, far, hand, far_hand, wave, effect = pose
    x, y = (ANCHOR + hip[0], 59 + hip[1])
    hx, hy = (x + head[0], y - 24 + head[1])
    rush = 5 if action == "run" else 0
    image = Image.new("RGBA", (SIZE, SIZE))
    draw = ImageDraw.Draw(image)

    def polygon(points, fill, outline=None, origin=(0, 0)):
        ox, oy = origin
        draw.polygon([(ox + px, oy + py) for px, py in points], fill=fill, outline=outline)

    def body(points, fill, outline=None):
        polygon(points, fill, outline, (x, y))

    def face(points, fill, outline=None):
        polygon(points, fill, outline, (hx, hy))

    def line(points, color, width=1):
        draw.line(points, fill=color, width=width, joint="curve")

    def limb(points, fill, width):
        line(points, INK, width + 2)
        line(points, fill, width)

    def leg(data, front):
        knee, toe = data
        hip_joint = (x + (2 if front else -4), y)
        ankle = (toe[0] - 2, toe[1] - 3)
        limb([hip_joint, knee, ankle], PANTS if front else HAIR, 7)
        line([(knee[0] - 2, knee[1] - 1), (ankle[0] - 1, ankle[1])],
             "#7b5b5e" if front else PANTS, 2)
        tx, ty = toe
        polygon([(-6,-1),(-6,-6),(-3,-7),(0,-6),(0,-3),(4,-3),
                 (6,-1),(6,0),(-5,0)], BOOT if front else SOLE, INK, (tx, ty))
        polygon([(-5,-5),(-1,-5),(-1,-4),(-5,-4)], BAG if front else BOOT,
                origin=(tx, ty))
        line([(tx - 4, ty - 1), (tx + 4, ty - 1)], SOLE)

    def arm(offset, front):
        sx = x + (1 if front else 7) + head[0] // 2
        sy = y - 15 + head[1]
        px, py = x + offset[0], y + offset[1]
        ex = (sx + px) // 2 - (3 if front else 1)
        ey = (sy + py) // 2 + 2
        limb([(sx, sy), (ex, ey), (px, py)], SHADE if front else "#a47762", 4)
        limb([(sx, sy), (ex, ey)], CREAM if front else CLOTH, 6)
        polygon([(-3,-2), (1,-3), (3,-1), (3,2), (1,3), (-2,2)], BOOT, INK, (px, py))
        draw.point((px + 1, py + 1), fill=SKIN if front else SHADE)

    # Behind the limbs: the cloak's hem trails farther when running or rising.
    tail = -18 - rush
    lift = min(wave, 2)
    body([(1,-21),(-8,-23),(-14,-17),(tail,-12 + lift),(tail-2,-5 + lift),
          (tail+4,-8 + lift),(tail+9,-3 + lift),(-9,3),(-4,1),(7,-10)], DEEP, INK)
    body([(-7,-20),(-13,-16),(tail,-11 + lift),(tail-1,-7 + lift),(tail+6,-10 + lift),
          (-10,-8),(-3,-16)], TEAL)
    body([(-10,-16),(tail,-11 + lift),(tail-1,-9 + lift),(tail+6,-11 + lift),(-9,-15)], MINT)
    body([(-12,-9),(tail+8,-5 + lift),(-9,1),(-5,-2)], TEAL)
    leg(far, False)
    arm(far_hand, False)
    leg(near, True)

    body([(-6,-21),(4,-24),(10,-20),(12,-12),(8,-2),(11,3),(4,6),
          (0,4),(-7,6),(-10,2),(-8,-6),(-9,-14)], DEEP, INK)
    body([(-5,-19),(4,-21),(9,-17),(9,-9),(5,-6),(-6,-7),(-7,-13)], TEAL)
    body([(-6,-4),(6,-4),(8,2),(4,4),(0,1),(-5,4),(-8,2)], CLOTH)
    body([(-6,-2),(-3,-2),(-4,2),(-6,3)], CREAM)
    body([(-8,-7),(8,-8),(8,-5),(-8,-4)], BOOT, INK)
    body([(2,-8),(6,-8),(6,-5),(2,-5)], GOLD, BOOT)
    body([(3,-7),(5,-7),(5,-6),(3,-6)], INK)

    # Crossbody strap and the mail peeking through the satchel flap.
    body([(7,-20),(10,-18),(-5,0),(-9,-1)], BAG, INK)
    body([(7,-19),(-7,-1),(-7,-3),(6,-19)], GOLD)
    bob = 1 if action == "run" and hip[1] >= 2 else 0
    bx, by = x - 7, y - 3 + bob
    polygon([(-4,-7),(3,-8),(4,-2),(-4,-1)], CREAM, INK, (bx, by))
    line([(bx - 3, by - 6), (bx, by - 4), (bx + 2, by - 6)], BAG)
    polygon([(-7,-3),(-3,-5),(5,-4),(7,-1),(6,5),(3,7),
             (-5,7),(-8,4)], BAG, INK, (bx, by))
    polygon([(-6,-2),(-2,-4),(5,-3),(6,0),(3,2),(-5,1)], PEACH, SOLE, (bx, by))
    polygon([(-2,1),(2,1),(2,4),(-2,4)], GOLD, SOLE, (bx, by))
    draw.point((bx, by + 2), fill=GOLD)
    line([(bx - 6, by + 2), (bx - 5, by + 5), (bx - 2, by + 5)], RUST)

    # Scarf tails are individually posed behind the hood and knot.
    ox, oy = hx - 5, hy + 5
    reach = 4 if action == "run" else 0
    polygon([(0,-1),(-6,1),(-13-reach,-1+wave),(-18-reach,-1+wave),
             (-22-reach,3+wave),(-18-reach,3+wave),(-13-reach,2+wave),
             (-6,5),(1,3)], ORANGE, INK, (ox, oy))
    polygon([(-2,3),(-8,5),(-13-reach,5+wave),(-17-reach,9+wave),
             (-12-reach,8+wave),(-7,8),(0,5)], RUST, INK, (ox, oy))
    line([(ox - 20 - reach, oy + 2 + wave), (ox - 16 - reach, oy + wave),
          (ox - 12 - reach, oy + 1 + wave)], PEACH)

    face([(-13,-9),(-10,-14),(-5,-17),(3,-17),(9,-14),(12,-10),(13,-5),
          (12,1),(9,5),(5,7),(-5,6),(-12,3),(-15,-2),(-15,-6)], TEAL, INK)
    face([(-13,-8),(-9,-13),(-5,-16),(3,-16),(7,-14),(0,-14),
          (-5,-12),(-10,-7),(-11,-1),(-9,3),(-12,2),(-14,-2)], MINT)
    face([(-11,-9),(-7,-13),(-4,-14),(-3,-14),(-7,-11)], EDGE)
    face([(-10,1),(-7,3),(-2,4),(4,4),(6,6),(0,6),(-7,5),(-11,3)], DEEP)
    face([(-7,-7),(-5,-11),(0,-14),(5,-14),(9,-12),(11,-8),(11,0),
          (7,4),(0,5),(-5,2),(-8,-1)], HAIR, INK)
    face([(-6,-7),(-3,-11),(2,-13),(7,-12),(7,-11),(2,-11),
          (-1,-8),(-5,-6)], HAIR_LIGHT)
    face([(0,-8),(4,-10),(7,-10),(10,-7),(10,-4),(12,-2),(12,0),
          (10,0),(10,3),(8,5),(4,5),(1,3),(-1,2),(-3,0),(-3,-3),(-1,-4)], SKIN, INK)
    face([(-2,-2),(-1,0),(1,1),(4,3),(8,4),(9,3),(9,4),(8,5),
          (4,5),(0,3),(-2,1)], SHADE)
    face([(-1,-6),(1,-9),(4,-11),(7,-11),(6,-8),(3,-6),(2,-4),(0,-4)],
         HAIR, INK)
    face([(-3,-1),(-2,-2),(-1,-1),(-1,1),(-2,1)], BLUSH)
    line([(hx+5,hy-6),(hx+8,hy-6)], HAIR)
    if name == "Blink":
        line([(hx+5,hy-3),(hx+8,hy-3)], HAIR)
    else:
        draw.rectangle((hx+5,hy-4,hx+8,hy-2), fill="#fff1d8")
        draw.rectangle((hx+7,hy-4,hx+8,hy-2), fill=INK)
        draw.point((hx+7,hy-4), fill=EDGE)
    draw.point((hx + 4, hy), fill=BLUSH)
    line([(hx+7,hy+2),(hx+9,hy+2)], "#984939")

    face([(-8,3),(-2,4),(2,6),(8,5),(11,4),(11,8),(8,10),
          (2,9),(-4,8),(-9,7)], ORANGE, INK)
    face([(-7,4),(-2,5),(3,7),(5,7),(5,8),(1,8),(-5,6),(-8,6)], PEACH)
    face([(4,7),(7,7),(6,13),(2,15),(2,11)], RUST, INK)
    face([(4,7),(6,7),(5,11),(3,12)], ORANGE)
    face([(6,5),(8,5),(9,6),(9,8),(8,9),(6,9),(5,8),(5,6)], GOLD, BOOT)
    draw.point((hx + 6, hy + 6), fill=CREAM)

    if effect in {"draw", "wind", "swing", "strike", "follow", "lower"}:
        px, py = x + hand[0], y + hand[1]
        vectors = {"draw":(-11,5), "wind":(-14,-8), "swing":(11,-15),
                   "strike":(17,-2), "follow":(11,8), "lower":(8,12)}
        dx, dy = vectors[effect]
        base = (px + dx // 5, py + dy // 5)
        tip = (px + dx, py + dy)
        perp = (-1, 2) if abs(dx) > abs(dy) else (2, 1)
        bx2, by2 = base
        qx, qy = perp
        polygon([(bx2-qx, by2-qy),tip,(tip[0]+qx,tip[1]+qy),
                 (bx2+qx,by2+qy)], EDGE, INK)
        line([base,(tip[0],tip[1]+1)], "#ddf4dc")
        line([(px-qx*2,py-qy*2),(px+qx*2,py+qy*2)], INK, 3)
        line([(px-qx*2,py-qy*2),(px+qx*2,py+qy*2)], GOLD)
    arm(hand, True)

    if effect == "swing":
        polygon([(53,31),(61,26),(70,25),(79,28),(72,28),(65,30),(60,34)], EDGE)
        line([(63,27),(70,26),(76,27)], "#ddf4dc")
    elif effect == "strike":
        polygon([(78,35),(86,37),(91,42),(92,46),(87,43),(84,42),(80,41)], EDGE)
        line([(84,38),(89,41),(91,44)], "#ddf4dc")
        line([(85,49),(89,48)], GOLD)
        draw.point((92, 37), fill=CREAM)
    elif effect == "follow":
        polygon([(89,51),(91,50),(88,56),(81,60),(74,61),(80,58),(86,54)], MINT)
        draw.point((91, 54), fill=GOLD)
    elif effect == "dust":
        polygon([(36,77),(33,76),(34,73),(36,73),(38,77)], CLOTH)
        polygon([(62,77),(63,74),(66,73),(65,76),(67,77)], CLOTH)
    elif effect == "dust2":
        line([(32,75),(34,74)], CLOTH)
        draw.point((67, 74), fill=CLOTH)

    return image


def export():
    manifest = {
        "character": "Lark",
        "tickMs": TICK,
        "canvas": {"width": SIZE, "height": SIZE, "anchor": {"x": ANCHOR, "y": FLOOR}},
        "contactCoordinates": "Each listed x is a boot center. y is the line below the last sole pixel.",
        "comparison": "Shared time, clamped at each clip's final frame. Loop applies to the longest duration.",
        "clips": {},
    }
    previews = []
    contact = Image.new("RGB", (11*SIZE+48, 4*(SIZE+42)+22), "#10191a")
    labels = ImageDraw.Draw(contact)
    font = ImageFont.load_default(size=11)
    for row, (action, (loop, poses)) in enumerate(CLIPS.items()):
        sheet = Image.new("RGBA", (len(poses) * SIZE, SIZE))
        frames = []
        directory = ASSETS / "frames" / action
        directory.mkdir(parents=True, exist_ok=True)
        clip_images = []
        for index, pose in enumerate(poses):
            image = render(action, pose)
            name = f"frames/{action}/{index+1:02}.png"
            image.save(ASSETS / name, optimize=True)
            sheet.paste(image, (index * SIZE, 0))
            contacts = [{"x": leg_data[1][0], "y": FLOOR} for leg_data in pose[4:6]
                        if leg_data[1][1] == FLOOR - 1]
            frames.append({
                "name": pose[0], "file": name, "rect": [index * SIZE, 0, SIZE, SIZE],
                "hold": pose[1], "anchor": {"x": ANCHOR, "y": FLOOR},
                "bounds": list(image.getbbox()), "contacts": contacts,
            })
            clip_images.append(image)
        sheet_name = f"{action}.png"
        sheet.save(ASSETS / sheet_name, optimize=True)
        manifest["clips"][action] = {
            "label": action.title(), "sheet": sheet_name, "loop": loop, "frames": frames,
        }

        strip = Image.new("RGB", (len(poses)*SIZE+24, SIZE+58), "#10191a")
        strip_draw = ImageDraw.Draw(strip)
        strip_draw.text((12, 9), f"LARK  /  {action.upper()}  /  {sum(p[1] for p in poses)*TICK} MS",
                        fill="#9ae6cd", font=font)
        labels.text((24,row*(SIZE+42)+12), action.upper(), fill="#9ae6cd", font=font)
        for index, (image, pose) in enumerate(zip(clip_images, poses)):
            short_name = "Follow" if pose[0] == "Follow through" else pose[0]
            for target, painter, px, py in [(strip,strip_draw,12+index*SIZE,26),
                                           (contact,labels,24+index*SIZE,row*(SIZE+42)+29)]:
                painter.rectangle((px+1,py,px+SIZE-2,py+SIZE-1), fill="#213333")
                painter.line((px+4,py+FLOOR,px+SIZE-5,py+FLOOR), fill="#48635c")
                target.paste(image,(px,py),image)
                painter.text((px+3,py+SIZE+3), f"{index+1:02}  ·  {short_name}", fill="#eee3cc", font=font)
        strip.save(EVIDENCE / f"contact-{action}.png")

        for index, (image, pose) in enumerate(zip(clip_images, poses)):
            card = Image.new("RGB", (384, 320), "#172425")
            card.paste(image.resize((288,288), Image.Resampling.NEAREST), (48,5),
                       image.resize((288,288), Image.Resampling.NEAREST))
            caption = ImageDraw.Draw(card)
            caption.text((16,12), f"LARK / {action.upper()}", fill="#9ae6cd", font=font)
            caption.text((16,294), f"{index+1:02}/{len(poses):02}  {pose[0]}", fill="#eee3cc", font=font)
            previews.append((card, pose[1]*TICK + (400 if index == 0 else 0)))

    contact.save(EVIDENCE / "contact-sheets.png")
    images, holds = zip(*previews)
    images[0].save(EVIDENCE / "lark-playback.gif", save_all=True, append_images=images[1:],
                   duration=list(holds), loop=0, optimize=True)
    (ASSETS / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    export()
