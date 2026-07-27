"""Build the mcporter --json payload string for the upload + share calls,
write each to a temp file, then exec mcporter with --json @file. mcporter
supports file-based JSON via the `--args @file` syntax for params; for the
--json flag itself we'll just construct the JSON in Python and pass it
directly via stdin or as a single literal token.

Actually simplest: build the full JSON object in Python, write it to a
short script that exec()s subprocess.run with mcporter --json <payload>.
"""
import json
import subprocess
import sys

FILE_PATH = r"D:\IBM Project\Open_Production\open-production-plan-copy.md"
FILE_NAME = "open-production-plan-copy.md"

upload_payload = {
    "selected_api": "GoogleDriveCLIAPI",
    "action": "file",
    "instructions": (
        "Upload the IBM Open Production plan markdown for sharing via "
        "public link. Preserve the .md extension; do NOT convert to "
        "Google Doc."
    ),
    "params": {
        "file": FILE_PATH,
        "convert": False,
        "new_name": FILE_NAME,
    },
    "output": "file id, name, webViewLink, webContentLink",
}

with open(r"D:\IBM Project\Open_Production\.tmp\upload_payload.json", "w") as f:
    json.dump(upload_payload, f)
print("wrote upload_payload.json", file=sys.stderr)
