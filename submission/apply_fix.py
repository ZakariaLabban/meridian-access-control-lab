#!/usr/bin/env python3
"""
Lab 3 — apply the four fixes to src/helpdesk/views/staff.py.

Run from the repository root:  python apply_fix.py
A backup (staff.py.vuln.bak) is written next to the file the first time, so
revert_fix.py can restore the vulnerable version for your 'before' captures.

src/ is mounted into the container and hot-reloads in a few seconds, so there
is no need to rebuild the image.
"""
import pathlib, shutil, sys

STAFF = pathlib.Path("src/helpdesk/views/staff.py")
if not STAFF.exists():
    sys.exit("Run this from the repo root (could not find %s)" % STAFF)

bak = STAFF.with_suffix(".py.vuln.bak")
if not bak.exists():
    shutil.copy(STAFF, bak)
    print("backup written:", bak)

s = STAFF.read_text(encoding="utf-8")

EDITS = [
    # A1 — view_ticket: add the object check
    ("""@helpdesk_staff_member_required
def view_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
""",
     """@helpdesk_staff_member_required
def view_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    ticket_perm_check(request, ticket)
"""),
    # A2 — promote_user: require admin, not merely staff
    ("""@helpdesk_staff_member_required
def promote_user(request):""",
     """@helpdesk_superuser_required
def promote_user(request):"""),
    # A3 — change_email: drop the CSRF exemption
    ("""@csrf_exempt
@helpdesk_staff_member_required
def change_email(request):""",
     """@helpdesk_staff_member_required
def change_email(request):"""),
    # B + finale — export_ticket: no shell, and add the object check
    ('''    import subprocess

    ticket = get_object_or_404(Ticket, id=ticket_id)
    label = request.GET.get("label", "")
    name = f"ticket-{ticket_id}" + (f"-{label}" if label else "")
    body = f"#{ticket.id} {ticket.title} [{ticket.get_status_display()}]\\\\n\\\\n{ticket.description or ''}\\\\n"

    command = f"mkdir -p /tmp/exports && printf %s {json.dumps(body)} > /tmp/exports/{name}.txt && cat /tmp/exports/{name}.txt"
    output = subprocess.check_output(
        command, shell=True, stderr=subprocess.STDOUT
    )
    return HttpResponse(output, content_type="text/plain")''',
     '''    import os

    ticket = get_object_or_404(Ticket, id=ticket_id)
    ticket_perm_check(request, ticket)
    label = request.GET.get("label", "")
    name = f"ticket-{ticket_id}" + (f"-{label}" if label else "")
    body = f"#{ticket.id} {ticket.title} [{ticket.get_status_display()}]\\\\n\\\\n{ticket.description or ''}\\\\n"

    # No shell: the label is only ever part of a filename, never a command.
    exports = "/tmp/exports"
    os.makedirs(exports, exist_ok=True)
    path = os.path.join(exports, os.path.basename(f"{name}.txt"))
    with open(path, "w") as handle:
        handle.write(body)
    with open(path) as handle:
        output = handle.read()
    return HttpResponse(output, content_type="text/plain")'''),
]

for i, (old, new) in enumerate(EDITS, 1):
    if new in s and old not in s:
        print(f"[{i}] already applied, skipping")
        continue
    if s.count(old) != 1:
        sys.exit(f"[{i}] expected exactly one match, found {s.count(old)} — aborting")
    s = s.replace(old, new)
    print(f"[{i}] applied")

STAFF.write_text(s, encoding="utf-8")
print("Done. staff.py fixed — give gunicorn a few seconds to reload, then re-run the attacks.")
