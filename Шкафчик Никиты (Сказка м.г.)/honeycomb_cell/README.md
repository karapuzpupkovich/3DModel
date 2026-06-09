# Honeycomb Cell

This folder contains the isolated shoe-organizer cell geometry.

Rules:
- Do not change locked overall dimensions without explicit instruction.
- Modify groove, perforation, and safety details only in this module.
- Cabinet assembly scripts must import this module instead of copying geometry logic.

Primary entry points:
- honeycomb_cell/builder.py: geometry builder
- honeycomb_cell/export_single_cell.py: standalone FreeCAD export
- honeycomb_cell/tests/check_overlap.py: neighboring-cell regression check
