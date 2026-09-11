#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор насадок-имён на карандаш (аналог конструктора MakerWorld #2374615).

Что делает:
  1. считает раскладку букв по метрикам TTF (fontTools);
  2. подставляет её в name_pencil_template.scad;
  3. вызывает OpenSCAD и получает STL;
  4. проверяет, что модель — единое связное тело (иначе буквы не слиплись
     и деталь распадётся на куски при печати).

Примеры:
    python generate_names.py ДИМА
    python generate_names.py ДИМА ИЛЬЯ ЯСМИНА --hole 7.8
    python generate_names.py --file names.txt --mode flat

Зачем «зигзаг» — это чередование ВЫСОТЫ букв (body_h + up / body_h - down),
буквы стоят на общем дне Z = 0. Проверено обмером эталона ДИМА_7.8.stl.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
FONTS_DIR = PROJECT_DIR / "fonts"
TEMPLATE = SCRIPT_DIR / "name_pencil_template.scad"
CALIB_FILE = SCRIPT_DIR / ".font_calibration.json"

DEFAULT_FONT = "ShantellSans-ExtraBold.ttf"

OPENSCAD_CANDIDATES = [
    Path(r"C:\Program Files\OpenSCAD\openscad.exe"),
    Path(r"C:\Program Files (x86)\OpenSCAD\openscad.exe"),
    Path("/usr/bin/openscad"),
    Path("/usr/local/bin/openscad"),
]


# --------------------------------------------------------------------------- #
#  Инфраструктура: OpenSCAD и шрифты
# --------------------------------------------------------------------------- #
def find_openscad() -> Path:
    env = os.environ.get("OPENSCAD")
    if env and Path(env).exists():
        return Path(env)
    for p in OPENSCAD_CANDIDATES:
        if p.exists():
            return p
    found = shutil.which("openscad")
    if found:
        return Path(found)
    sys.exit("OpenSCAD не найден. Укажите путь через переменную окружения OPENSCAD.")


def ensure_font_visible(ttf: Path) -> None:
    """
    OpenSCAD ищет шрифты через fontconfig: C:\\Windows\\Fonts, %LOCALAPPDATA%\\fonts
    и ~/.fonts. Папку проекта он не смотрит и OPENSCADPATH для шрифтов не
    использует, поэтому кладём копию в ~/.fonts (без прав администратора и без
    записи в реестр).
    """
    target_dir = Path.home() / ".fonts"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / ttf.name
    if not target.exists() or target.stat().st_size != ttf.stat().st_size:
        shutil.copy2(ttf, target)
        print(f"  шрифт скопирован в {target}")


def font_family_name(font: TTFont) -> str:
    """
    Имя для text(font=...) в формате fontconfig: "Семейство:style=Начертание".
    Явный стиль нужен, чтобы при нескольких установленных начертаниях
    (Regular / Bold / ExtraBold) выбиралось именно нужное.
    """
    names = font["name"]
    family = names.getDebugName(16) or names.getDebugName(1)
    style = names.getDebugName(17) or names.getDebugName(2)
    if style and style.lower() != "regular":
        return f"{family}:style={style}"
    return family


# --------------------------------------------------------------------------- #
#  Чтение STL (OpenSCAD пишет ASCII, эталоны — бинарные)
# --------------------------------------------------------------------------- #
def read_stl(path: Path):
    """Возвращает массив треугольников формы (n, 3, 3) как список кортежей."""
    raw = path.read_bytes()
    if raw[:5] == b"solid" and b"facet" in raw[:2048]:
        text = raw.decode("utf-8", "replace")
        nums = [
            (float(a), float(b), float(c))
            for a, b, c in re.findall(
                r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", text
            )
        ]
        return [tuple(nums[i:i + 3]) for i in range(0, len(nums), 3)]
    count = struct.unpack("<I", raw[80:84])[0]
    tris = []
    off = 84
    for _ in range(count):
        vals = struct.unpack("<12fH", raw[off:off + 50])
        tris.append((vals[3:6], vals[6:9], vals[9:12]))
        off += 50
    return tris


def write_binary_stl(tris, path: Path, header: bytes = b"pencil-name") -> None:
    with path.open("wb") as fh:
        fh.write(header.ljust(80, b"\0")[:80])
        fh.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            ux, uy, uz = (b[i] - a[i] for i in range(3))
            vx, vy, vz = (c[i] - a[i] for i in range(3))
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            ln = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
            fh.write(struct.pack("<3f", nx / ln, ny / ln, nz / ln))
            for v in (a, b, c):
                fh.write(struct.pack("<3f", *v))
            fh.write(b"\0\0")


def bbox(tris):
    xs = [v[0] for t in tris for v in t]
    ys = [v[1] for t in tris for v in t]
    zs = [v[2] for t in tris for v in t]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def count_shells(tris) -> int:
    """
    Число связных компонент меша. Больше одной — буквы не соприкасаются,
    деталь развалится. Вершины «свариваем» округлением до 1e-4 мм.
    """
    parent: dict[int, int] = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    key_to_id: dict[tuple, int] = {}
    for tri in tris:
        ids = []
        for v in tri:
            key = (round(v[0], 4), round(v[1], 4), round(v[2], 4))
            if key not in key_to_id:
                key_to_id[key] = len(key_to_id)
                parent[key_to_id[key]] = key_to_id[key]
            ids.append(key_to_id[key])
        union(ids[0], ids[1])
        union(ids[1], ids[2])
    return len({find(i) for i in parent})


# --------------------------------------------------------------------------- #
#  Калибровка масштаба шрифта
# --------------------------------------------------------------------------- #
def units_per_size(openscad: Path, font: TTFont, family: str, fn: int = 32) -> float:
    """
    OpenSCAD трактует text(size=N) НЕ как размер em: для Shantell Sans при
    size=100 глиф получается ровно в 720 font-units. Коэффициент зависит от
    шрифта, поэтому измеряем его один раз рендером эталонного глифа и кешируем.

    Возвращает число font-units, которым соответствует одна единица size.
    """
    cache = {}
    if CALIB_FILE.exists():
        cache = json.loads(CALIB_FILE.read_text(encoding="utf-8"))
    if family in cache:
        return cache[family]

    cmap = font.getBestCmap()
    probe = next((c for c in "HXOНО" if ord(c) in cmap), None)
    if probe is None:
        raise SystemExit(f"В шрифте {family} нет ни одного калибровочного глифа.")

    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[cmap[ord(probe)]].draw(pen)
    unit_h = pen.bounds[3] - pen.bounds[1]

    with tempfile.TemporaryDirectory(prefix="scadcal_") as tmp:
        scad = Path(tmp) / "cal.scad"
        stl = Path(tmp) / "cal.stl"
        scad.write_text(
            f'$fn={fn};\n'
            f'linear_extrude(1) text("{probe}", font="{family}", size=100,'
            f' halign="left", valign="baseline");\n',
            encoding="utf-8",
        )
        run_openscad(openscad, scad, stl)
        tris = read_stl(stl)
        lo, hi = bbox(tris)
        rendered_h = hi[1] - lo[1]

    upsize = unit_h / (rendered_h / 100.0)
    cache[family] = upsize
    CALIB_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"  калибровка {family}: 1 ед. size = {upsize:.1f} font-units")
    return upsize


def run_openscad(openscad: Path, scad: Path, stl: Path) -> None:
    res = subprocess.run(
        [str(openscad), "-o", str(stl), str(scad)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if res.returncode != 0 or not stl.exists():
        sys.exit(f"OpenSCAD упал на {scad.name}:\n{res.stderr}")
    for line in (res.stderr or "").splitlines():
        if "WARNING" in line or "ERROR" in line:
            print(f"  OpenSCAD: {line.strip()}")


# --------------------------------------------------------------------------- #
#  Раскладка
# --------------------------------------------------------------------------- #
def layout(text: str, font: TTFont, upsize: float, size: float, factors):
    """
    Позиции букв по X и вертикальное центрирование.

    `factors` — множитель шага для каждого стыка (len(text) - 1 штук) либо
    одно число на все стыки. Отдельный множитель на стык нужен потому, что
    пары вроде «ТО» в рукописном шрифте расходятся сильнее прочих: ужимать
    ради них всё слово — значит слепить остальные буквы в кашу.

    Кернинг (GPOS) не применяется — буквы и так намеренно перекрываются,
    чтобы слово стало единым телом. Из-за этого ширина может на 1-3%
    отличаться от оригинала MakerWorld.
    """
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    glyphs = font.getGlyphSet()

    missing = sorted({c for c in text if ord(c) not in cmap})
    if missing:
        sys.exit(f"В шрифте нет символов: {' '.join(missing)}")

    if not isinstance(factors, (list, tuple)):
        factors = [factors] * max(0, len(text) - 1)

    mm = size / upsize  # мм на одну font-unit

    pen_x, xs_units, bounds = 0.0, [], []
    for i, ch in enumerate(text):
        gname = cmap[ord(ch)]
        xs_units.append(pen_x)
        pen = BoundsPen(glyphs)
        glyphs[gname].draw(pen)
        bounds.append(pen.bounds)  # None у пробела
        pen_x += hmtx[gname][0] * (factors[i] if i < len(factors) else 1.0)

    xs_mm = [u * mm for u in xs_units]
    ink_lo = min(xs_mm[i] + b[0] * mm for i, b in enumerate(bounds) if b)
    ink_hi = max(xs_mm[i] + b[2] * mm for i, b in enumerate(bounds) if b)

    # По вертикали канал ставится в ОБЩУЮ ПОЛОСУ всех букв: от самого
    # высокого низа до самого низкого верха. Только так у каждой буквы
    # под каналом и над ним остаётся одинаковый запас.
    #
    # Считать по общему габариту нельзя, и это два разных бага:
    #  * бревис Й задирает верх — центр уезжает вверх, канал вылезает
    #    над буквами и вскрывает их сверху (лечится исключением диакритики);
    #  * хвост Д опускает низ на 3.3 мм — центр уезжает вниз, и у всех
    #    ОСТАЛЬНЫХ букв под каналом остаётся 0.5-0.7 мм вместо 2.1
    #    (ДИМА и АЛЕКСАНДР ломались именно так).
    # Хвост Д и бревис Й просто торчат за полосу — это лишний материал,
    # он ничему не мешает.
    body_y = []
    for ch, b in zip(text, bounds):
        if b is None:
            continue
        blo, bhi, _ = floating_parts(font, ch, mm)
        body_y.append((b[1] * mm, b[3] * mm) if blo is None else (blo, bhi))
    y_lo = max(v[0] for v in body_y)
    y_hi = min(v[1] for v in body_y)

    center = (ink_lo + ink_hi) / 2
    x_pos = [round(v - center, 4) for v in xs_mm]
    return x_pos, round(-(y_lo + y_hi) / 2, 4), ink_hi - ink_lo, y_hi - y_lo


def heights(n: int, body_h: float, up: float, down: float, mode: str):
    if mode == "flat":
        return [body_h] * n
    return [body_h + up if i % 2 == 0 else body_h - down for i in range(n)]


def glyph_contours(glyphs, gname: str, mm: float):
    """
    Контуры глифа как ломаные (кривые распрямлены), в мм.
    Возвращает [(габарит [x0, y0, x1, y1], [точки]), ...].
    """
    pen = RecordingPen()
    glyphs[gname].draw(pen)
    out, pts, prev = [], [], None
    for op, args in pen.value:
        if op == "moveTo":
            prev = args[0]
            pts = [prev]
        elif op == "lineTo":
            prev = args[0]
            pts.append(prev)
        elif op in ("qCurveTo", "curveTo"):
            ctrl = list(args)
            # TrueType: цепочка квадратичных с неявными серединами
            for i in range(len(ctrl) - 1):
                c = ctrl[i]
                nxt = ctrl[i + 1]
                end = nxt if i + 2 == len(ctrl) else ((c[0] + nxt[0]) / 2, (c[1] + nxt[1]) / 2)
                for k in range(1, 7):
                    t = k / 6
                    pts.append(((1 - t) ** 2 * prev[0] + 2 * (1 - t) * t * c[0] + t * t * end[0],
                                (1 - t) ** 2 * prev[1] + 2 * (1 - t) * t * c[1] + t * t * end[1]))
                prev = end
        elif op in ("closePath", "endPath"):
            if pts:
                xs = [p[0] * mm for p in pts]
                ys = [p[1] * mm for p in pts]
                out.append(([min(xs), min(ys), max(xs), max(ys)],
                            [(x, y) for x, y in zip(xs, ys)]))
            pts = []
    return out


def contour_boxes(glyphs, gname: str, mm: float) -> list[list[float]]:
    """Габарит каждого отдельного контура глифа, в мм."""
    return [box for box, _ in glyph_contours(glyphs, gname, mm)]


def floating_parts(font: TTFont, ch: str, mm: float):
    """
    Делит контуры глифа на тело и «висящие» части (точки Ё, бревис Й).

    Тело наращивается транзитивно от самого крупного контура по пересечению
    диапазонов Y. Возвращает (низ тела, верх тела, [габариты висящих частей]);
    если висящих нет — (None, None, []).
    """
    contours = glyph_contours(font.getGlyphSet(), font.getBestCmap()[ord(ch)], mm)
    if len(contours) < 2:
        return None, None, []
    boxes = [c[0] for c in contours]
    body = [max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))]
    rest = [b for b in boxes if b is not body[0]]
    grew = True
    while grew:
        grew = False
        lo = min(b[1] for b in body)
        hi = max(b[3] for b in body)
        for b in list(rest):
            if b[1] <= hi and b[3] >= lo:
                body.append(b)
                rest.remove(b)
                grew = True
    if not rest:
        return None, None, []
    return min(b[1] for b in body), max(b[3] for b in body), rest


def body_top_profile(font: TTFont, ch: str, mm: float, step: float = 0.25):
    """
    Верх тела буквы по X: {x_bin: max Y тела в этом столбце}. Нужен, чтобы
    ставить перемычки под диакритикой туда, где под ней есть штрих, а не
    пустота между штрихами.
    """
    contours = glyph_contours(font.getGlyphSet(), font.getBestCmap()[ord(ch)], mm)
    _, _, floats = floating_parts(font, ch, mm)
    float_ids = {id(b) for b in floats}
    prof: dict[int, float] = {}
    for box, pts in contours:
        if any(box == fb for fb in floats):
            continue
        for x, y in pts:
            k = int(round(x / step))
            if y > prof.get(k, -1e9):
                prof[k] = y
    return prof


def _profile(pts, step: float, top: bool) -> dict[int, float]:
    """Огибающая ломаной по столбцам X: верх (top=True) или низ."""
    prof: dict[int, float] = {}
    for x, y in pts:
        k = int(round(x / step))
        if k not in prof or (y > prof[k] if top else y < prof[k]):
            prof[k] = y
    return prof


def diacritic_bridges(text: str, font: TTFont, mm: float, width_frac: float = 0.6,
                      min_width: float = 1.5, bite: float = 1.0,
                      step: float = 0.25) -> list[list]:
    """
    Перемычки под «висящими» частями букв.

    Точки у Ё и бревис у Й — отдельные контуры глифа. После выдавливания они
    становятся самостоятельными столбиками: к букве не крепятся и на печати
    просто остаются лежать на столе.

    Перемычку мало поставить под диакритикой — под ней должно быть ТЕЛО.
    У Й бревис висит над просветом между двумя штрихами И, и перемычка по
    центру цепляла их только уголками: связность формально была, держалось
    на двух точках и отваливалось при снятии со стола. Поэтому ищем столбцы,
    где тело доходит до своего верха (там штрих), и ставим перемычку на
    каждый такой штрих под диакритикой. У Й их выходит две — по концам
    бревиса, у Ё по одной под каждой точкой на перекладине Е.

    Верх перемычки — по огибающей низа диакритики над ней (у бревиса низ
    в середине ниже, чем по краям), низ — с заходом в штрих на `bite`.

    Возвращает [[индекс буквы, x0, y0, x1, y1], ...] в мм от начала буквы.
    """
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    out = []
    for i, ch in enumerate(text):
        _, top, floats = floating_parts(font, ch, mm)
        if top is None:
            continue
        contours = glyph_contours(glyphs, cmap[ord(ch)], mm)
        body_pts = [p for box, pts in contours if box not in floats for p in pts]
        body_top = _profile(body_pts, step, top=True)

        # штрихи: кластеры столбцов, где тело поднимается почти до верха
        high = sorted(k for k, y in body_top.items() if y >= top - 1.5)
        clusters: list[list[int]] = []
        for k in high:
            if clusters and k - clusters[-1][-1] <= 2:
                clusters[-1].append(k)
            else:
                clusters.append([k])
        strokes = [(c[0] * step - step / 2, c[-1] * step + step / 2) for c in clusters]

        for box, pts in contours:
            if box not in floats:
                continue
            fx0, fy0, fx1, _ = box
            float_bot = _profile(pts, step, top=False)
            hits = [(max(a, fx0 - 0.3), min(b, fx1 + 0.3)) for a, b in strokes
                    if b >= fx0 - 0.3 and a <= fx1 + 0.3]
            if not hits:
                # под диакритикой ни один штрих не доходит до верха —
                # опускаемся к тому телу, что есть под её серединой
                hits = [((fx0 + fx1) / 2 - 0.5, (fx0 + fx1) / 2 + 0.5)]
            for a, b in hits:
                cx = (a + b) / 2
                w = max(min_width, min(2.5, b - a))
                x0, x1 = cx - w / 2, cx + w / 2
                ks = [k for k in body_top if x0 - 0.3 <= k * step <= x1 + 0.3]
                y_body = max(body_top[k] for k in ks) if ks else top
                ks_f = [k for k in float_bot if x0 <= k * step <= x1]
                y_float = max(float_bot[k] for k in ks_f) if ks_f else fy0
                out.append([i, round(x0, 4), round(y_body - bite, 4),
                            round(x1, 4), round(y_float + 0.3, 4)])
    return out


FLOOR_DEFAULT = 1.1   # пол под каналом; печатается на столе, тонким быть может


def bore_axis(args) -> float:
    """
    Высота оси канала. По умолчанию — так, чтобы под каналом остался пол
    FLOOR_DEFAULT, а весь остальной запас высоты ушёл наверх: снизу деталь
    лежит на столе и тонкий пол там не мешает, а сверху нужно место под
    конёк и слои над ним.
    """
    return args.hole / 2 + FLOOR_DEFAULT if args.bore_z is None else args.bore_z


MIN_ROOF = 1.0        # сколько материала обязательно оставить над коньком


def bore_relief(args) -> float:
    """
    Подъём конька. По умолчанию берётся максимум, который влезает:
    полный «домик» на 45° (скаты из точек, где касательная к кругу идёт
    под 45°, сходятся на высоте r * sqrt(2)) — если над ним остаётся
    хотя бы MIN_ROOF материала. Не влезает полный — ставится урезанный,
    не влезает никакой — ноль, и канал остаётся обычным кругом.

    Полный конёк убирает горизонтальный мост совсем, урезанный оставляет
    площадку шириной 2 * (full - relief) — провисает, но заметно меньше.
    """
    if args.bore_relief is not None:
        return args.bore_relief
    full = args.hole / 2 * (2 ** 0.5 - 1)
    lowest = args.height if args.mode == "flat" else args.height - args.down
    room = lowest - (bore_axis(args) + args.hole / 2) - MIN_ROOF
    return max(0.0, min(full, room))


def floor_under_hole(args) -> float:
    """Материал от стола до низа канала."""
    return bore_axis(args) - args.hole / 2


def roof_over_hole(args) -> float:
    """
    Толщина «свода» — материала над каналом у самых низких букв, с учётом
    конька. Это единственный навес в детали: он печатается мостом, поэтому
    от него зависит, нужны ли поддержки и ровным ли выйдет верх.
    """
    lowest = args.height if args.mode == "flat" else args.height - args.down
    return lowest - (bore_axis(args) + args.hole / 2 + bore_relief(args))


def height_groups(hs):
    """[[высота, [индексы]], ...] — буквы одной высоты выдавливаются разом."""
    out: dict[float, list[int]] = {}
    for i, h in enumerate(hs):
        out.setdefault(round(h, 4), []).append(i)
    return [[h, idx] for h, idx in sorted(out.items())]


def scad_literal(value) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ", ".join(scad_literal(v) for v in value) + "]"
    return repr(round(value, 4) if isinstance(value, float) else value)


# --------------------------------------------------------------------------- #
#  Основной сценарий
# --------------------------------------------------------------------------- #
def pair_joint_ok(pair: str, factor: float, erode: float, args, openscad: Path,
                  font: TTFont, family: str, upsize: float) -> bool:
    """
    Достаточно ли толстый перешеек между двумя соседними буквами.

    Меряем эрозией ОБЪЕДИНЕНИЯ пары: `offset(r = -erode)` съедает по `erode`
    со всех сторон, и если после этого пара осталась единым непустым телом,
    значит самое узкое место шире `2 * erode`. Именно там деталь и рвётся —
    ломается не пересечение букв, а самая тонкая перемычка их объединения.

    При `erode = 0` это вырождается в обычную проверку «слиплось или нет».
    """
    mm = args.size / upsize
    adv = font["hmtx"][font.getBestCmap()[ord(pair[0])]][0] * mm * factor

    parts = []
    for i, ch in enumerate(pair):
        dx = adv if i else 0.0
        glyph = (f'text("{ch}", font="{family}", size={args.size}, '
                 f'halign="left", valign="baseline")')
        # Диакритику из теста выбрасываем: галочка над Й и точки над Ё к
        # соседней букве не крепятся, а их тонкие места ломают замер —
        # эрозия находит самое узкое место где угодно, а нам нужен стык.
        _, top, _ = floating_parts(font, ch, mm)
        if top is not None:
            glyph = (f'intersection() {{ {glyph}; '
                     f'translate([-500, -500]) square([1000, {500 + top:.4f}]); }}')
        parts.append(f'translate([{dx:.4f}, 0]) {glyph};')
    shape = "union() {\n" + "\n".join(parts) + "\n}"
    if erode > 0:
        shape = f"offset(r = -{erode:.4f}) {shape}"
    body = f"$fn={args.fit_fn};\nlinear_extrude(2) {shape}\n"

    with tempfile.TemporaryDirectory(prefix="scadpair_") as tmp:
        scad, stl = Path(tmp) / "p.scad", Path(tmp) / "p.stl"
        scad.write_text(body, encoding="utf-8")
        res = subprocess.run([str(openscad), "-o", str(stl), str(scad)],
                             capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        if res.returncode != 0 or not stl.exists():
            return False           # пустой результат — эрозия съела всё
        tris = read_stl(stl)
        return bool(tris) and count_shells(tris) == 1


def check_diacritics(text: str, args, openscad: Path, font: TTFont, family: str,
                     upsize: float) -> list[str]:
    """
    Держится ли диакритика на перемычках: буква с перемычками после эрозии
    на weld/2 должна остаться одним телом. Ровно этот тест поймал бы
    бревис Й, висевший на уголках.
    """
    mm = args.size / upsize
    bad = []
    for ch in sorted(set(text)):
        _, top, floats = floating_parts(font, ch, mm)
        if top is None or args.no_bridges:
            continue
        parts = [f'text("{ch}", font="{family}", size={args.size}, '
                 f'halign="left", valign="baseline");']
        for b in diacritic_bridges(ch, font, mm, min_width=args.bridge_width):
            parts.append(f'translate([{b[1]:.4f}, {b[2]:.4f}]) '
                         f'square([{b[3]-b[1]:.4f}, {b[4]-b[2]:.4f}]);')
        shape = (f"offset(r = -{args.weld / 2:.4f}) union() {{\n"
                 + "\n".join(parts) + "\n}")
        body = f"$fn={args.fit_fn};\nlinear_extrude(2) {shape}\n"
        with tempfile.TemporaryDirectory(prefix="scaddia_") as tmp:
            scad, stl = Path(tmp) / "d.scad", Path(tmp) / "d.stl"
            scad.write_text(body, encoding="utf-8")
            res = subprocess.run([str(openscad), "-o", str(stl), str(scad)],
                                 capture_output=True)
            ok = res.returncode == 0 and stl.exists()
            if ok:
                tris = read_stl(stl)
                ok = bool(tris) and count_shells(tris) == 1
        if not ok:
            bad.append(ch)
    return bad


def largest_passing(test, lo: float, hi: float, steps: int = 6):
    """
    Наибольший множитель в [lo, hi], проходящий тест, или None.

    Тест монотонен: чем меньше множитель, тем плотнее буквы и тем толще
    перешеек, поэтому годится обычный двоичный поиск.
    """
    if test(hi):
        return hi
    if not test(lo):
        return None
    for _ in range(steps):
        mid = (lo + hi) / 2
        if test(mid):
            lo = mid
        else:
            hi = mid
    return round(lo, 3)


def fit_gaps(text: str, args, openscad: Path, font: TTFont, family: str,
             upsize: float) -> list[float]:
    """
    Подбирает множитель шага отдельно для каждого стыка букв.

    Критерий — не «слиплось», а «перешеек не тоньше --weld». Разница
    существенная: просто соприкоснуться буквы могут по касательной, и такой
    стык отломится. Проверка идёт на паре букв и на черновом $fn — дёшево,
    а тессиляция там срезает дуги внутрь, так что результат консервативен.
    """
    erode = args.weld / 2
    factors, weak = [], []

    for i in range(len(text) - 1):
        pair = text[i:i + 2]

        def test(f, e=erode, p=pair):
            return pair_joint_ok(p, f, e, args, openscad, font, family, upsize)

        f = largest_passing(test, args.min_spacing, args.spacing)
        if f is None:
            # Нужную толщину не дать при любом шаге — отступаем к «лишь бы
            # слиплось», но говорим об этом вслух.
            f = largest_passing(lambda v, p=pair: pair_joint_ok(
                p, v, 0.0, args, openscad, font, family, upsize),
                args.min_spacing, args.spacing)
            weak.append(pair)
            if f is None:
                f = args.min_spacing
        factors.append(f)

    if any(f < args.spacing for f in factors):
        print("   стыки: " + " · ".join(
            f"{text[i:i + 2]} {f}" + ("←" if f < args.spacing else "")
            for i, f in enumerate(factors)))
    if weak:
        print(f"   ВНИМАНИЕ: стыки {', '.join('«' + p + '»' for p in weak)} тоньше "
              f"{args.weld} мм при любом шаге — держатся, но это слабое место")
    return factors


def render(text: str, spacing, args, openscad: Path, font: TTFont,
           family: str, upsize: float, fn: int):
    """Собирает .scad под заданный spacing и возвращает (текст scad, треугольники)."""
    x_pos, y_off, _, body_span = layout(text, font, upsize, args.size, spacing)
    hs = heights(len(text), args.height, args.up, args.down, args.mode)
    bridges = [] if args.no_bridges else diacritic_bridges(
        text, font, args.size / upsize, min_width=args.bridge_width)

    scad_body = TEMPLATE.read_text(encoding="utf-8")
    for token, value in {
        "{{LETTERS}}": scad_literal(list(text)),
        "{{XPOS}}": scad_literal(x_pos),
        "{{GROUPS}}": scad_literal(height_groups(hs)),
        "{{BRIDGES}}": scad_literal(bridges),
        "{{YOFF}}": scad_literal(y_off),
        "{{FONT}}": scad_literal(family),
        "{{SIZE}}": scad_literal(args.size),
        "{{BODY_H}}": scad_literal(args.height),
        "{{HOLE_D}}": scad_literal(args.hole),
        "{{RELIEF}}": scad_literal(round(bore_relief(args), 4)),
        "{{BORE_Z}}": scad_literal(bore_axis(args)),
        "{{FN}}": scad_literal(fn),
    }.items():
        scad_body = scad_body.replace(token, value)

    # OpenSCAD запускаем в ASCII-каталоге: на Windows кириллица в путях
    # к .scad/.stl отрабатывает не на всех сборках.
    with tempfile.TemporaryDirectory(prefix="scadjob_") as tmp:
        scad_tmp = Path(tmp) / "job.scad"
        stl_tmp = Path(tmp) / "job.stl"
        scad_tmp.write_text(scad_body, encoding="utf-8")
        run_openscad(openscad, scad_tmp, stl_tmp)
        return scad_body, read_stl(stl_tmp), body_span


def build_one(name: str, args, openscad: Path, font: TTFont, family: str,
              upsize: float, out_dir: Path) -> None:
    text = name if args.keep_case else name.upper()

    spacing = (fit_gaps(text, args, openscad, font, family, upsize)
               if args.auto_fit else args.spacing)
    loose = check_diacritics(text, args, openscad, font, family, upsize)
    if loose:
        print(f"   ВНИМАНИЕ: диакритика у {', '.join(loose)} держится тоньше "
              f"{args.weld} мм — отвалится при снятии со стола")

    scad_body, tris, body_span = render(text, spacing, args, openscad, font,
                                        family, upsize, args.fn)
    shells = count_shells(tris)

    stem = f"{text}_{args.hole:g}"
    out_stl = out_dir / f"{stem}.stl"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_binary_stl(tris, out_stl)
    if args.keep_scad:
        (out_dir / f"{stem}.scad").write_text(scad_body, encoding="utf-8")

    lo, hi = bbox(tris)
    flag = "OK " if shells == 1 else "!! "
    n_bridges = 0 if args.no_bridges else len(
        diacritic_bridges(text, font, args.size / upsize, min_width=args.bridge_width))
    tightest = min(spacing) if isinstance(spacing, list) and spacing else args.spacing
    print(
        f"{flag}{out_stl.name:<22} {hi[0]-lo[0]:6.2f} x {hi[1]-lo[1]:5.2f} x "
        f"{hi[2]-lo[2]:5.2f} мм   тр-ков {len(tris):6d}   тел {shells}   "
        f"шаг {args.spacing}/{tightest}   пол {floor_under_hole(args):.2f}"
        f" / свод {roof_over_hole(args):.2f}"
        f" / стенка {body_span / 2 - args.hole / 2:.2f} мм"
        + (f"   перемычек {n_bridges}" if n_bridges else "")
    )
    if shells > 1:
        print(
            f"   ВНИМАНИЕ: буквы не соприкасаются ({shells} отдельных тел). "
            f"Уменьшите --min-spacing или задайте --spacing вручную."
        )
    wall = body_span / 2 - args.hole / 2
    if wall < 1.0:
        print(f"   ВНИМАНИЕ: сбоку от канала всего {wall:.2f} мм — канал"
              f" вскрывает буквы. Уменьшите --hole или увеличьте --size.")
    for what, value in (("пол под каналом", floor_under_hole(args)),
                        ("свод над каналом", roof_over_hole(args))):
        if value < 1.0:
            print(f"   ВНИМАНИЕ: {what} всего {value:.2f} мм "
                  f"({value / 0.2:.0f} слоёв по 0.2) — тонко для печати. "
                  f"Увеличьте --height.")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Генерация STL-насадок с именем на карандаш.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("names", nargs="*", help="имена (по одному аргументу)")
    ap.add_argument("--file", type=Path, help="файл со списком имён, по одному в строке")
    ap.add_argument("--hole", type=float, default=7.8, help="диаметр отверстия, мм")
    ap.add_argument("--size", type=float, default=12.0, help="размер шрифта")
    ap.add_argument("--height", type=float, default=10.5, help="базовая высота, мм")
    ap.add_argument("--up", type=float, default=0.9, help="прибавка высоты, зигзаг вверх")
    ap.add_argument("--down", type=float, default=0.25, help="убавка высоты, зигзаг вниз")
    ap.add_argument("--spacing", type=float, default=0.84,
                    help="множитель межбуквенного шага (<1 — буквы слипаются)")
    ap.add_argument("--mode", choices=("zigzag", "flat"), default="zigzag")
    ap.add_argument("--no-auto-fit", dest="auto_fit", action="store_false",
                    help="не подбирать spacing автоматически до единого тела")
    ap.add_argument("--min-spacing", type=float, default=0.5,
                    help="ниже этого множитель шага стыка не опускается")
    ap.add_argument("--weld", type=float, default=1.2,
                    help="минимальная толщина перешейка на стыке букв, мм")
    ap.add_argument("--fit-fn", type=int, default=12,
                    help="$fn для черновых прогонов автоподбора")
    ap.add_argument("--no-bridges", action="store_true",
                    help="не подставлять перемычки под точки Ё и бревис Й")
    ap.add_argument("--bridge-width", type=float, default=1.5,
                    help="минимальная ширина перемычки под диакритикой, мм")
    ap.add_argument("--bore-relief", type=float, default=None,
                    help="конёк над каналом, мм (по умолчанию полный домик на 45°)")
    ap.add_argument("--bore-z", type=float, default=None,
                    help="высота оси канала, мм (по умолчанию середина тела)")
    ap.add_argument("--font", default=DEFAULT_FONT, help="имя файла шрифта в fonts/")
    ap.add_argument("--fn", type=int, default=64,
                    help="$fn контуров букв (у эталона MakerWorld примерно 64)")
    ap.add_argument("--out", type=Path, default=PROJECT_DIR / "Готовые модели")
    ap.add_argument("--keep-case", action="store_true",
                    help="не переводить имя в ВЕРХНИЙ РЕГИСТР")
    ap.add_argument("--keep-scad", action="store_true",
                    help="сохранить сгенерированный .scad рядом с STL")
    args = ap.parse_args()

    names = list(args.names)
    if args.file:
        names += [
            ln.strip()
            for ln in args.file.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")
        ]
    if not names:
        ap.error("не задано ни одного имени (аргументы или --file)")

    ttf = FONTS_DIR / args.font
    if not ttf.exists():
        sys.exit(f"Шрифт не найден: {ttf}")

    openscad = find_openscad()
    ensure_font_visible(ttf)
    font = TTFont(ttf)
    family = font_family_name(font)
    upsize = units_per_size(openscad, font, family)

    print(f"Шрифт: {family}   отверстие Ø{args.hole:g}   режим {args.mode}\n")
    for name in names:
        build_one(name, args, openscad, font, family, upsize, args.out)


if __name__ == "__main__":
    main()
