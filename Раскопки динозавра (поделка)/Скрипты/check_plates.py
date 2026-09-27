# -*- coding: utf-8 -*-
"""
Проверка плит слайсером: CLI Bambu Studio режет каждый проект так же,
как перед отправкой на принтер, и по его отчёту (result.json) видно
главное — нарезалось ли, есть ли поддержки, время, расход по пруткам,
число смен прутка и предупреждения.

    python check_plates.py                 # все плиты из «Готовые модели/Плиты»
    python check_plates.py номерки цифры   # только плиты с такими словами в имени

После записи отчёта CLI иногда не завершается сам (на этой машине так
висела третья плита): процесс снимается через 20 секунд после появления
result.json.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

EXE = Path(r"C:\Program Files\Bambu Studio\bambu-studio.exe")
PLATES = Path(__file__).resolve().parent.parent / "Готовые модели" / "Плиты"


def fmt_time(s: float) -> str:
    s = int(round(s))
    h, m = divmod(s // 60, 60)
    return f"{h} ч {m:02d} мин" if h else f"{m} мин {s % 60:02d} с"


def slice_one(project: Path, timeout: float = 900.0) -> dict | None:
    with tempfile.TemporaryDirectory(prefix="slice_") as tmp:
        tmp = Path(tmp)
        p3 = tmp / "p.3mf"
        shutil.copy2(project, p3)
        proc = subprocess.Popen([str(EXE), "--slice", "0", "--outputdir", str(tmp), str(p3)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        res, t0, seen = tmp / "result.json", time.time(), None
        while proc.poll() is None:
            time.sleep(1)
            if seen is None and res.exists():
                seen = time.time()
            if (seen and time.time() - seen > 20) or time.time() - t0 > timeout:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                               capture_output=True)
                break
        if not res.exists():
            return None
        time.sleep(0.5)
        return json.loads(res.read_text(encoding="utf-8"))


def report(name: str, r: dict | None) -> bool:
    if r is None:
        print(f"{name:<28} НЕ НАРЕЗАЛОСЬ: отчёта нет")
        return False
    if not r.get("sliced_plates"):
        print(f"{name:<28} {r.get('error_string')} (код {r.get('return_code')})")
        return False
    p = r["sliced_plates"][0]
    ftt = p.get("feature_type_times", {})
    support = sum(v for k, v in ftt.items() if "upport" in k)
    fil = " + ".join(f"{f['total_used_g']:.2f}" for f in p.get("filaments", []))
    warn = p.get("warning_message") or "нет"
    changes = p.get("filament_change_times", 0)
    print(f"{name:<28} {r.get('error_string')}  деталей {len(p.get('objects', [])):2d} | "
          f"поддержки {support:.0f} с | {fmt_time(p.get('total_predication', 0)):>12} | "
          f"{fil} г | смен прутка {changes} | предупр.: {warn}")
    return r.get("return_code") == 0 and support == 0 and warn == "нет"


def main() -> None:
    only = sys.argv[1:]
    ok = True
    for project in sorted(PLATES.glob("*/*.3mf")):
        if only and not any(s in project.stem for s in only):
            continue
        ok &= report(project.stem, slice_one(project))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
