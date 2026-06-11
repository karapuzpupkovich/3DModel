# Honeycomb Cell

This folder contains the isolated shoe-organizer cell geometry.

Rules:
- Do not change locked overall dimensions without explicit instruction.
- Modify groove, perforation, and safety details only in this module.
- Cabinet assembly scripts must import this module instead of copying geometry logic.

Primary entry points:
- Стандартная_ячейка/builder.py: geometry builder
- Стандартная_ячейка/export_single_cell.py: standalone FreeCAD export
- Стандартная_ячейка/tests/check_overlap.py: neighboring-cell regression check
