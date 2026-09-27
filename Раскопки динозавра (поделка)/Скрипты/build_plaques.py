# -*- coding: utf-8 -*-
"""
Табличка «ОСТОРОЖНО! РАСКОПКИ» и карта раскопок — плоские пластины
с гравировкой.

Рисунок не печатается вторым цветом, а вырезается канавками глубиной
0.7–0.8 мм. Канавки заливают краской (акрил, гуашь, маркер) и стирают
излишки с поверхности влажной салфеткой — краска остаётся только в
углублениях. Для этого верх пластины печатается с глажкой (профиль A1
из соседнего проекта), чтобы краска не цеплялась за полоски слоёв.

Запуск (обычный Python, нужен OpenSCAD):
    python build_plaques.py
"""

from __future__ import annotations

import math
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import trimesh
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
OUT = PROJECT / "Готовые модели" / "Таблички"
sys.path.insert(0, str(HERE))
from drawings import dig_map, trex  # noqa: E402

OPENSCAD = Path(r"C:\Program Files\OpenSCAD\openscad.exe")
FONT_FILE = PROJECT.parent / "Насадка-имя на карандаш" / "fonts" / "ShantellSans-ExtraBold.ttf"
FONT = "Shantell Sans:style=ExtraBold"
UNITS_PER_SIZE = 720.0      # калибровка OpenSCAD для этого шрифта (см. проект с именами)

# ---- табличка: размеры сняты с образца в общем масштабе ×1.33 (см. README)
SIGN_W, SIGN_H, SIGN_T = 54.0, 44.0, 3.0
SIGN_R = 2.5                 # скругление углов
STAKE_W, STAKE_L = 6.0, 40.0  # колышек: ширина и длина ниже таблички
ENGRAVE = 0.8
BOLDER = 0.12                # утолщение букв, мм

# ---- карта
MAP_W, MAP_H, MAP_T = 60.0, 44.0, 2.4
MAP_ENGRAVE = 0.7


def ensure_font():
    """OpenSCAD ищет шрифты только через fontconfig — кладём копию в ~/.fonts."""
    dst = Path.home() / ".fonts" / FONT_FILE.name
    dst.parent.mkdir(exist_ok=True)
    if not dst.exists():
        shutil.copy2(FONT_FILE, dst)


def ink_width(text: str, size: float) -> float:
    """Ширина надписи по «чернилам», мм — чтобы вписать строку в табличку."""
    f = TTFont(FONT_FILE)
    cmap, gs, hm = f.getBestCmap(), f.getGlyphSet(), f["hmtx"]
    x, lo, hi = 0.0, math.inf, -math.inf
    for ch in text:
        g = cmap[ord(ch)]
        bp = BoundsPen(gs)
        gs[g].draw(bp)
        if bp.bounds:
            lo, hi = min(lo, x + bp.bounds[0]), max(hi, x + bp.bounds[2])
        x += hm[g][0]
    return (hi - lo) * size / UNITS_PER_SIZE


def run_openscad(src: str, out_stl: Path) -> trimesh.Trimesh:
    with tempfile.TemporaryDirectory(prefix="plaque_") as tmp:
        scad = Path(tmp) / "p.scad"
        stl = Path(tmp) / "p.stl"
        scad.write_text(src, encoding="utf-8")
        r = subprocess.run([str(OPENSCAD), "-o", str(stl), str(scad)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0 or not stl.exists():
            sys.exit("OpenSCAD упал:\n" + r.stderr[-2000:])
        m = trimesh.load(stl)
    m.export(out_stl)                      # бинарный STL
    return m


# --------------------------------------------------------------------------- #
#  Табличка
# --------------------------------------------------------------------------- #
def sign_scad(with_stake: bool) -> str:
    lines = ("ОСТОРОЖНО!", "РАСКОПКИ")
    margin = 3.8
    size = min(8.0, (SIGN_W - 2 * margin) / (ink_width(lines[0], 1.0)))
    cap = size * 700 / UNITS_PER_SIZE

    icon = trex()
    ix0, iy0, ix1, iy1 = icon.bounds()
    scale = 1.0
    icon_h = (iy1 - iy0) * scale
    gap1, gap2 = 2.3, 2.6
    block = cap + gap1 + cap + gap2 + icon_h
    y_base = STAKE_L if with_stake else 0.0
    top = y_base + SIGN_H - (SIGN_H - block) / 2
    b1 = top - cap
    b2 = b1 - gap1 - cap
    icon_bottom = b2 - gap2 - icon_h
    cx = SIGN_W / 2
    icon = icon.moved(cx - (ix0 + ix1) / 2 * scale, icon_bottom - iy0 * scale, scale)

    plate = (f"translate([{SIGN_R}, {y_base + SIGN_R}]) offset(r={SIGN_R}, $fn=32) "
             f"square([{SIGN_W - 2 * SIGN_R}, {SIGN_H - 2 * SIGN_R}]);")
    stake = ""
    if with_stake:
        x0, x1 = cx - STAKE_W / 2, cx + STAKE_W / 2
        stake = (f"translate([{x0}, 7]) square([{STAKE_W}, {STAKE_L - 7 + 3}]);\n"
                 f"    hull() {{ translate([{x0}, 7]) square([{STAKE_W}, 0.01]); "
                 f"translate([{cx}, 1.1]) circle(r=0.9, $fn=24); }}")
    # Буквы на BOLDER мм жирнее, чем в шрифте: штрих 0.76 -> ~1.0 мм. В такую
    # канавку заходит краска и не выковыривается при стирании. Просветы
    # в О, Р, А шире миллиметра — не зальются.
    text = "\n".join(
        f'    translate([{cx}, {b}]) offset(r={BOLDER}, $fn=16) text("{s}", font="{FONT}", '
        f'size={size:.3f}, halign="center", valign="baseline", $fn=24);'
        for s, b in zip(lines, (b1, b2)))
    return f"""// Табличка «ОСТОРОЖНО! РАСКОПКИ» — генерируется build_plaques.py
difference() {{
  linear_extrude({SIGN_T}) union() {{
    {plate}
    {stake}
  }}
  translate([0, 0, {SIGN_T - ENGRAVE}]) linear_extrude({ENGRAVE + 1}) union() {{
{text}
    {icon.scad()}
  }}
}}
""", size, cap


# --------------------------------------------------------------------------- #
#  Карта с рваными краями
# --------------------------------------------------------------------------- #
def torn_outline(w, h, seed=11):
    """
    Край листа «порван»: мелкая неровность по всему периметру и несколько
    надрывов. Глубина надрывов ограничена, чтобы до рамки рисунка
    (отступ 3.4 мм) оставалось не меньше 0.8 мм пластика.
    """
    rnd = random.Random(seed)
    pts = []
    corners = [(0, 0), (w, 0), (w, h), (0, h)]
    step = 1.1
    for (x0, y0), (x1, y1) in zip(corners, corners[1:] + corners[:1]):
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        nx, ny = -uy, ux                       # внутрь листа
        n = max(2, int(L / step))
        tear_at = {rnd.randrange(3, n - 3) for _ in range(2)}
        jit = 0.0
        for i in range(n):
            t = i * L / n
            jit = 0.6 * jit + 0.4 * rnd.uniform(0.0, 0.75)
            d = jit
            # углы листа чуть «обтрёпаны»
            if i == 0:
                d += 0.9
            if i in tear_at:
                d += rnd.uniform(1.1, 1.8)
            pts.append((x0 + ux * t + nx * d, y0 + uy * t + ny * d))
    return pts


def map_scad() -> str:
    outline = torn_outline(MAP_W, MAP_H)
    poly = "polygon(" + str([[round(x, 3), round(y, 3)] for x, y in outline]) + ");"
    drawing = dig_map(MAP_W, MAP_H)
    return f"""// Карта раскопок — генерируется build_plaques.py
difference() {{
  linear_extrude({MAP_T}) {poly}
  translate([0, 0, {MAP_T - MAP_ENGRAVE}]) linear_extrude({MAP_ENGRAVE + 1})
    {drawing.scad()}
}}
"""


def check(name, m: trimesh.Trimesh):
    bodies = len(m.split(only_watertight=False))
    lo, hi = m.bounds
    print(f"OK {name:32s} {hi[0]-lo[0]:6.2f} x {hi[1]-lo[1]:6.2f} x {hi[2]-lo[2]:4.2f} мм   "
          f"граней {len(m.faces):6d}   водонепр. {m.is_watertight}   тел {bodies}")
    if bodies != 1 or not m.is_watertight:
        print("   ВНИМАНИЕ: деталь не цельная")


def main():
    ensure_font()
    OUT.mkdir(parents=True, exist_ok=True)
    for stake, name in ((True, "табличка с колышком"), (False, "табличка без колышка")):
        src, size, cap = sign_scad(stake)
        (OUT / f"{name}.scad").write_text(src, encoding="utf-8")
        m = run_openscad(src, OUT / f"{name}.stl")
        check(name, m)
    print(f"   шрифт {size:.2f} (высота заглавных {cap:.2f} мм)")
    src = map_scad()
    (OUT / "карта раскопок.scad").write_text(src, encoding="utf-8")
    check("карта раскопок", run_openscad(src, OUT / "карта раскопок.stl"))


if __name__ == "__main__":
    main()
