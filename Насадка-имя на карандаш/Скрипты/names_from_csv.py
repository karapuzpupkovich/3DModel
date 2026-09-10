#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Достаёт имена из списка группы (CSV «Фамилия, имя, отчество;Дата рождения»).

Берётся второй токен ФИО и переводится в ВЕРХНИЙ РЕГИСТР. Одинаковые имена
схлопываются в один STL — но печатать его нужно столько раз, сколько детей
с этим именем, поэтому скрипт считает и выводит количество копий.

    python names_from_csv.py "дети.csv"
    python names_from_csv.py "дети.csv" --out "Скрипты/names.txt" --skip ИЛЬЯ ЯСМИНА
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path


def read_names(path: Path) -> list[tuple[str, str]]:
    """Возвращает пары (полное ФИО, имя в верхнем регистре)."""
    out = []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.reader(fh, delimiter=";"):
            if not row or not row[0].strip():
                continue
            fio = row[0].strip()
            # Строка заголовка: «Фамилия, имя, отчество» — токены с запятыми.
            if fio.split()[0].strip(",.").lower() == "фамилия":
                continue
            parts = fio.split()
            if len(parts) < 2:
                print(f"  пропущено (нет имени): {fio}")
                continue
            out.append((fio, parts[1].upper()))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Имена детей из CSV в список для генератора.")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, help="куда записать список имён")
    ap.add_argument("--skip", nargs="*", default=[], metavar="ИМЯ",
                    help="имена, которые уже сделаны")
    ap.add_argument("--checklist", type=Path,
                    help="куда записать чек-лист печати (Markdown)")
    ap.add_argument("--rename", nargs="*", default=[], metavar="БЫЛО=СТАЛО",
                    help="замена имени, например ДМИТРИЙ=ДИМА")
    args = ap.parse_args()

    if not args.csv.exists():
        sys.exit(f"Нет файла: {args.csv}")

    people = read_names(args.csv)

    # Замены вида ДМИТРИЙ=ДИМА: в списке группы полное имя, а печатаем то,
    # как ребёнка зовут на самом деле.
    swaps = {}
    for item in args.rename:
        if "=" not in item:
            sys.exit(f"Ожидался формат БЫЛО=СТАЛО, получено: {item}")
        was, now = item.split("=", 1)
        swaps[was.strip().upper()] = now.strip().upper()
    if swaps:
        people = [(fio, swaps.get(name, name)) for fio, name in people]

    counts = Counter(name for _, name in people)
    skip = {s.upper() for s in args.skip}

    print(f"Детей в списке: {len(people)}   разных имён: {len(counts)}\n")

    todo = []
    for name in sorted(counts):
        who = [fio for fio, n in people if n == name]
        mark = "уже есть" if name in skip else "нужно"
        if name not in skip:
            todo.append(name)
        copies = f"× {counts[name]}" if counts[name] > 1 else "    "
        print(f"  {name:<12} {copies}  {mark:<9} {'; '.join(who)}")

    dup = {n: c for n, c in counts.items() if c > 1}
    if dup:
        print("\nОдинаковые имена — STL один, печатать по числу детей:")
        for n, c in sorted(dup.items()):
            print(f"  {n} — {c} шт.")

    print(f"\nК генерации: {len(todo)} имён")

    if args.checklist:
        rows = ["# Чек-лист печати", "",
                f"Детей: {len(people)}. Разных имён (файлов): {len(counts)}. "
                f"Всего насадок к печати: {len(people)}.", "",
                "| ✓ | Ребёнок | Имя на насадке | Файл |", "|---|---|---|---|"]
        for fio, name in sorted(people, key=lambda p: p[0]):
            rows.append(f"|   | {fio} | {name} | `{name}_7.8.3mf` |")
        dup_rows = [f"- **{n}** — {c} шт." for n, c in sorted(counts.items()) if c > 1]
        if dup_rows:
            rows += ["", "## Печатать по несколько копий", ""] + dup_rows
        args.checklist.write_text("\n".join(rows) + "\n", encoding="utf-8")
        print(f"Чек-лист записан: {args.checklist}")

    if args.out:
        args.out.write_text(
            "# Сгенерировано из " + args.csv.name + "\n" + "\n".join(todo) + "\n",
            encoding="utf-8",
        )
        print(f"Список записан: {args.out}")


if __name__ == "__main__":
    main()
