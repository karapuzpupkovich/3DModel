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
def layout(text: str, font: TTFont, upsize: float, size: float, spacing: float):
    """
    Позиции букв по X и вертикальное центрирование.

    Кернинг (GPOS) не применяется — буквы и так намеренно перекрываются
    множителем spacing, чтобы слово стало единым телом. Из-за этого ширина
    может на 1-3% отличаться от оригинала MakerWorld.
    """
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    glyphs = font.getGlyphSet()

    missing = sorted({c for c in text if ord(c) not in cmap})
    if missing:
        sys.exit(f"В шрифте нет символов: {' '.join(missing)}")

    mm = size / upsize  # мм на одну font-unit

    pen_x, xs_units, bounds = 0.0, [], []
    for ch in text:
        gname = cmap[ord(ch)]
        xs_units.append(pen_x * spacing)
        pen = BoundsPen(glyphs)
        glyphs[gname].draw(pen)
        bounds.append(pen.bounds)  # None у пробела
        pen_x += hmtx[gname][0]

    xs_mm = [u * mm for u in xs_units]
    ink_lo = min(xs_mm[i] + b[0] * mm for i, b in enumerate(bounds) if b)
    ink_hi = max(xs_mm[i] + b[2] * mm for i, b in enumerate(bounds) if b)
    y_lo = min(b[1] for b in bounds if b) * mm
    y_hi = max(b[3] for b in bounds if b) * mm

    center = (ink_lo + ink_hi) / 2
    x_pos = [round(v - center, 4) for v in xs_mm]
    return x_pos, round(-(y_lo + y_hi) / 2, 4), ink_hi - ink_lo


def heights(n: int, body_h: float, up: float, down: float, mode: str):
    if mode == "flat":
        return [body_h] * n
    return [body_h + up if i % 2 == 0 else body_h - down for i in range(n)]


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
def render(text: str, spacing: float, args, openscad: Path, font: TTFont,
           family: str, upsize: float, fn: int):
    """Собирает .scad под заданный spacing и возвращает (текст scad, треугольники)."""
    x_pos, y_off, _ = layout(text, font, upsize, args.size, spacing)
    hs = heights(len(text), args.height, args.up, args.down, args.mode)

    scad_body = TEMPLATE.read_text(encoding="utf-8")
    for token, value in {
        "{{LETTERS}}": scad_literal(list(text)),
        "{{XPOS}}": scad_literal(x_pos),
        "{{GROUPS}}": scad_literal(height_groups(hs)),
        "{{YOFF}}": scad_literal(y_off),
        "{{FONT}}": scad_literal(family),
        "{{SIZE}}": scad_literal(args.size),
        "{{BODY_H}}": scad_literal(args.height),
        "{{HOLE_D}}": scad_literal(args.hole),
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
        return scad_body, read_stl(stl_tmp)


def build_one(name: str, args, openscad: Path, font: TTFont, family: str,
              upsize: float, out_dir: Path) -> None:
    text = name if args.keep_case else name.upper()

    spacing = args.spacing

    # Подбор ведём на черновой сетке: она заведомо «тоньше» чистовой
    # (хорды срезают дуги внутрь), поэтому слипшееся на черновике
    # гарантированно слипнется и на чистовом $fn.
    if args.auto_fit:
        for attempt in range(args.fit_tries):
            _, draft = render(text, spacing, args, openscad, font, family,
                              upsize, args.fit_fn)
            shells = count_shells(draft)
            if shells == 1 or attempt == args.fit_tries - 1:
                break
            spacing = round(spacing - args.fit_step, 4)
            print(f"   {text}: {shells} тел — сжимаю до spacing {spacing}")

    scad_body, tris = render(text, spacing, args, openscad, font, family,
                             upsize, args.fn)
    shells = count_shells(tris)

    stem = f"{text}_{args.hole:g}"
    out_stl = out_dir / f"{stem}.stl"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_binary_stl(tris, out_stl)
    if args.keep_scad:
        (out_dir / f"{stem}.scad").write_text(scad_body, encoding="utf-8")

    lo, hi = bbox(tris)
    flag = "OK " if shells == 1 else "!! "
    print(
        f"{flag}{out_stl.name:<22} {hi[0]-lo[0]:6.2f} x {hi[1]-lo[1]:5.2f} x "
        f"{hi[2]-lo[2]:5.2f} мм   тр-ков {len(tris):6d}   тел {shells}   "
        f"spacing {spacing}"
    )
    if shells > 1:
        print(
            f"   ВНИМАНИЕ: буквы не соприкасаются ({shells} отдельных тел) даже "
            f"при spacing {spacing}. Задайте --spacing меньше вручную."
        )


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Генерация STL-насадок с именем на карандаш.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("names", nargs="*", help="имена (по одному аргументу)")
    ap.add_argument("--file", type=Path, help="файл со списком имён, по одному в строке")
    ap.add_argument("--hole", type=float, default=7.8, help="диаметр отверстия, мм")
    ap.add_argument("--size", type=float, default=12.0, help="размер шрифта")
    ap.add_argument("--height", type=float, default=10.0, help="базовая высота, мм")
    ap.add_argument("--up", type=float, default=0.9, help="прибавка высоты, зигзаг вверх")
    ap.add_argument("--down", type=float, default=0.25, help="убавка высоты, зигзаг вниз")
    ap.add_argument("--spacing", type=float, default=0.84,
                    help="множитель межбуквенного шага (<1 — буквы слипаются)")
    ap.add_argument("--mode", choices=("zigzag", "flat"), default="zigzag")
    ap.add_argument("--no-auto-fit", dest="auto_fit", action="store_false",
                    help="не подбирать spacing автоматически до единого тела")
    ap.add_argument("--fit-step", type=float, default=0.02,
                    help="шаг уменьшения spacing при автоподборе")
    ap.add_argument("--fit-tries", type=int, default=8,
                    help="сколько попыток автоподбора делать")
    ap.add_argument("--fit-fn", type=int, default=12,
                    help="$fn для черновых прогонов автоподбора")
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
