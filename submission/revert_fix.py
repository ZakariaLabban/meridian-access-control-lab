#!/usr/bin/env python3
"""
Lab 3 — restore the vulnerable src/helpdesk/views/staff.py.

Run from the repository root:  python revert_fix.py
Restores staff.py from the backup apply_fix.py made, so you can capture the
'before' (attack working) screenshots again.
"""
import pathlib, shutil, sys

STAFF = pathlib.Path("src/helpdesk/views/staff.py")
bak = STAFF.with_suffix(".py.vuln.bak")
if not bak.exists():
    sys.exit("No backup found (%s). Nothing to revert." % bak)
shutil.copy(bak, STAFF)
print("Reverted staff.py to the vulnerable version. Wait a few seconds for gunicorn to reload.")
