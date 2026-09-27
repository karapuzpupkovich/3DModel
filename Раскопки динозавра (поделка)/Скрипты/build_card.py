# -*- coding: utf-8 -*-
"""
Карточка «Расшифровка находок» для печати на фотобумаге 10×15 см.

Рядом с каждой находкой в песке стоит номерок, а на карточке — что под
каким номером: «фото» находки на песке, название и один короткий факт.
Нумерация та же, что на схеме раскладки: 1 — череп … 9 — коготь.

Картинка 2400×3600 точек — это 4×6 дюймов при 600 dpi, стандартный лист
фотобумаги 10×15 (101.6×152.4 мм). Всё важное — не ближе 7 мм к краю:
при печати без полей принтер немного обрезает края.

    python build_card.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
OUT = PROJECT / "Готовые модели" / "Расшифровка"
sys.path.insert(0, str(HERE))
from build_plaques import FONT_FILE  # noqa: E402
from raster import Camera, render, value_noise  # noqa: E402
from scenes import BONE, ORDER, SAND, obj, placed  # noqa: E402

DPI = 600
PX_W, PX_H = 2400, 3600
MM = DPI / 25.4                      # точек на миллиметр

FONTS = Path(r"C:\Windows\Fonts")
BODY = FONTS / "candara.ttf"         # гуманистический гротеск с кириллицей
BODY_I = FONTS / "candarai.ttf"

PAPER = np.array([238, 226, 198]) / 255
INK = (64, 42, 24)
INK_SOFT = (128, 98, 66)
YELLOW = (244, 238, 42)              # как у номерков: Bambu PLA Basic Yellow
BLACK = (22, 20, 18)

TITLE = "РАСШИФРОВКА НАХОДОК"
SUBTITLE = "Найди номерок рядом с находкой — и узнай, что нашёл!"

# (название, уточнение, факт) — в порядке номеров, как ORDER в scenes.py
ENTRIES = [
    ("Череп", "", "В черепе были «окна» — так голова становилась легче."),
    ("Позвоночник и рёбра", "", "Рёбра, как клетка, защищали сердце и лёгкие."),
    ("Хвост", "", "Тяжёлый хвост уравновешивал большую голову, как качели."),
    ("Передняя лапа", "", "У тираннозавра передние лапы короткие, всего с двумя пальцами."),
    ("Задняя лапа", "вытянутая", "Хищные динозавры ходили на двух сильных задних ногах."),
    ("Задняя лапа", "согнутая", "Ходили на пальцах, как птицы. По следам узнают, как быстро они шли."),
    ("Косточка", "", "За миллионы лет кость превратилась в камень — это окаменелость."),
    ("Позвонок", "", "По цепочке позвонков учёные узнают длину динозавра."),
    ("Коготь", "", "Живой коготь был ещё длиннее: его покрывал роговой чехол, как ноготь."),
]

# ---- разметка, мм
FRAME = (4.0, 5.0)                   # двойная рамка: отступы линий от края
CONTENT = 7.0                        # поле для содержимого
ROWS_TOP, ROWS_BOTTOM = 25.0, 145.4
BADGE_X, BADGE_D = 12.0, 9.6         # центр и диаметр кружка с номером
THUMB_X0, THUMB_X1 = 18.5, 44.5      # «фото» находки
TEXT_X = 47.0


def mm(v: float) -> int:
    return int(round(v * MM))


def font(path, size_mm):
    return ImageFont.truetype(str(path), max(8, mm(size_mm)))


# --------------------------------------------------------------------------- #
#  «Фото» находки на песке
# --------------------------------------------------------------------------- #
def find_photo(name: str, w: int, h: int) -> Image.Image:
    """
    Деталь в той же позе, что на схеме, камера спереди-сверху. Расстояние
    и прицел подбираются по проекции вершин: деталь занимает ~80% кадра.
    """
    m = placed(name)
    V = m.vertices
    lo, hi = V.min(axis=0), V.max(axis=0)
    target = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, 0.0])
    size = float(np.max(hi - lo))
    fov, elev = 22.0, 58.0
    cam = Camera(tuple(target), size * 3, elev, -90, fov, w, h)
    for _ in range(3):                       # подгонка масштаба и центра кадра
        x, y, _ = cam.project(V)
        k = max((x.max() - x.min()) / (0.84 * w), (y.max() - y.min()) / (0.78 * h))
        dx, dy = (x.max() + x.min()) / 2 - w / 2, (y.max() + y.min()) / 2 - h / 2
        zc = float(np.median((V - cam.pos) @ cam.f))
        target = target + (dx * cam.r - dy * cam.u) * zc / cam.fpx
        cam = Camera(tuple(target), cam.dist * k, elev, -90, fov, w, h)
    img = render([obj(m, BONE, 0.2)], cam, ground={"z": 0, "color": SAND},
                 ss=2, shadow_res=max(0.03, size / 400))
    return Image.fromarray((np.clip(img, 0, 1) ** (1 / 1.05) * 255).astype(np.uint8))


# --------------------------------------------------------------------------- #
#  Бумага и рамка
# --------------------------------------------------------------------------- #
def parchment() -> Image.Image:
    # шум плавный — считаем в половинном разрешении, памяти вчетверо меньше
    ys, xs = np.mgrid[0:PX_H // 2, 0:PX_W // 2].astype(np.float32)
    x, y = xs * 2 / MM, ys * 2 / MM                           # в миллиметрах
    blot = 0.6 * value_noise(x, y, 18.0, 21) + 0.4 * value_noise(x, y, 6.0, 22)
    grain = value_noise(x, y, 0.35, 23)
    # край листа чуть темнее — как у старой бумаги
    ex = np.minimum(x, PX_W / MM - x)
    ey = np.minimum(y, PX_H / MM - y)
    edge = np.clip(1 - np.minimum(ex, ey) / 14.0, 0, 1) ** 2
    shade = 0.93 + 0.09 * blot + 0.035 * grain - 0.10 * edge
    rgb = PAPER[None, None, :] * shade[..., None]
    im = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    return im.resize((PX_W, PX_H), Image.BICUBIC)


def wobbly_rect(dr, inset, width, rng):
    """Рамка «от руки»: прямоугольник из коротких отрезков с дрожанием."""
    x0, y0, x1, y1 = mm(inset), mm(inset), PX_W - mm(inset), PX_H - mm(inset)
    pts = []
    for (ax, ay), (bx, by) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                               ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        n = max(2, int(abs(bx - ax + by - ay) / mm(6)))
        for i in range(n):
            t = i / n
            pts.append((ax + (bx - ax) * t + rng.normal(0, 2.2),
                        ay + (by - ay) * t + rng.normal(0, 2.2)))
    pts.append(pts[0])
    dr.line(pts, fill=INK, width=width, joint="curve")


def wrap(text: str, f, width: int, draw) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


# --------------------------------------------------------------------------- #
#  Карточка
# --------------------------------------------------------------------------- #
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    card = parchment()
    dr = ImageDraw.Draw(card)
    rng = np.random.default_rng(5)
    wobbly_rect(dr, FRAME[0], mm(0.55), rng)
    wobbly_rect(dr, FRAME[1], mm(0.25), rng)

    # ---- заголовок: по ширине поля, но не выше 6.5 мм заглавных
    width = PX_W - 2 * mm(CONTENT + 1.5)
    size = 9.0
    while True:
        tf = font(FONT_FILE, size)
        if dr.textlength(TITLE, font=tf) <= width:
            break
        size -= 0.1
    dr.text((PX_W / 2, mm(9.0)), TITLE, font=tf, fill=INK, anchor="mt")
    sf = font(BODY_I, 3.5)
    dr.text((PX_W / 2, mm(9.0 + size * 0.78 + 1.6)), SUBTITLE, font=sf, fill=INK_SOFT, anchor="mt")
    # пунктир, как тропа на карте
    yl = mm(ROWS_TOP - 1.6)
    for x in range(mm(CONTENT + 2), PX_W - mm(CONTENT + 2), mm(3.2)):
        dr.line([(x, yl), (x + mm(1.8), yl)], fill=INK_SOFT, width=mm(0.35))

    # ---- строки
    row_h = (ROWS_BOTTOM - ROWS_TOP) / len(ENTRIES)
    text_w = PX_W - mm(CONTENT + 0.8) - mm(TEXT_X)
    note_f = font(BODY_I, 3.2)
    # один кегль названий на все строки: самый крупный, при котором и
    # «Позвоночник и рёбра», и «Задняя лапа (вытянутая)» влезают в колонку
    ns = 4.3
    while ns > 3.0:
        name_f = font(FONT_FILE, ns)
        if all(dr.textlength(t, font=name_f)
               + (mm(1.4) + dr.textlength(f"({n})", font=note_f) if n else 0) <= text_w
               for t, n, _ in ENTRIES):
            break
        ns -= 0.05
    # один кегль факта на все строки: самый крупный, при котором каждый
    # факт укладывается в две строки
    fs = 3.4
    while fs > 2.4:
        ff = font(BODY, fs)
        if all(len(wrap(fact, ff, text_w, dr)) <= 2 for _, _, fact in ENTRIES):
            break
        fs -= 0.05
    ff = font(BODY, fs)
    badge_f = font(FONT_FILE, 7.4)

    thumb_w, thumb_h = mm(THUMB_X1 - THUMB_X0), mm(row_h - 1.6)
    for i, (name, (title, note, fact)) in enumerate(zip(ORDER, ENTRIES), start=1):
        top = ROWS_TOP + (i - 1) * row_h
        cy = mm(top + row_h / 2)
        # разделитель между строками
        if i > 1:
            y = mm(top)
            for x in range(mm(TEXT_X - 28.5), PX_W - mm(CONTENT + 1), mm(2.4)):
                dr.line([(x, y), (x + mm(1.1), y)], fill=(170, 140, 100), width=mm(0.18))
        # кружок с номером — как номерок: жёлтый, цифра чёрная
        r = mm(BADGE_D / 2)
        bx = mm(BADGE_X)
        dr.ellipse([bx - r, cy - r, bx + r, cy + r], fill=YELLOW, outline=BLACK, width=mm(0.5))
        dr.text((bx, cy + mm(0.2)), str(i), font=badge_f, fill=BLACK, anchor="mm")
        # «фото» находки: рамка-паспарту и тень
        photo = find_photo(name, thumb_w * 2, thumb_h * 2).resize((thumb_w, thumb_h), Image.LANCZOS)
        px0, py0 = mm(THUMB_X0), cy - thumb_h // 2
        shadow = Image.new("L", (thumb_w + mm(3), thumb_h + mm(3)), 0)
        ImageDraw.Draw(shadow).rounded_rectangle([mm(1.5), mm(1.5), thumb_w + mm(1.5), thumb_h + mm(1.5)],
                                                 radius=mm(1.2), fill=110)
        shadow = shadow.filter(ImageFilter.GaussianBlur(mm(0.7)))
        card.paste((90, 60, 30), (px0 - mm(1.1), py0 - mm(1.1)), shadow)
        mask = Image.new("L", (thumb_w, thumb_h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, thumb_w - 1, thumb_h - 1], radius=mm(1.2), fill=255)
        card.paste(photo, (px0, py0), mask)
        dr.rounded_rectangle([px0, py0, px0 + thumb_w, py0 + thumb_h], radius=mm(1.2),
                             outline=(250, 244, 228), width=mm(0.45))
        # название (+ уточнение) и факт
        lines = wrap(fact, ff, text_w, dr)
        line_h = fs * 1.13
        block = ns * 0.9 + 0.9 + line_h * len(lines)
        ty = mm(top + row_h / 2 - block / 2)
        tx = mm(TEXT_X)
        dr.text((tx, ty), title, font=name_f, fill=INK, anchor="lt")
        if note:
            nx = tx + dr.textlength(title, font=name_f) + mm(1.4)
            dr.text((nx, ty + mm(0.9)), f"({note})", font=note_f, fill=INK_SOFT, anchor="lt")
        y = ty + mm(ns * 0.9 + 0.9)
        for ln in lines:
            dr.text((tx, y), ln, font=ff, fill=INK, anchor="lt")
            y += mm(line_h)
        print(f"{i}: {title:<20} факт в {len(lines)} стр.")

    path = OUT / "расшифровка находок 10x15.jpg"
    card.save(path, quality=95, dpi=(DPI, DPI), subsampling=0)
    print(f"кегль: названия {ns:.2f} мм, факты {fs:.2f} мм ({fs / 0.3528:.1f} pt), заголовок {size:.1f} мм")
    print(f"готово: {path}  {card.size[0]}x{card.size[1]}")


if __name__ == "__main__":
    main()
