"""
Drive upload + public-share orchestrator, v2.

mcporter's --json/--args expects the *tool's own argument object*, not the
full MCP envelope. The tool name is positional. selected_api / action /
instructions / output are top-level parameters on the underlying
execute_zapier_write_action tool — they go as flags, not nested under args.

This script:
  1. Calls zapier.execute_zapier_write_action with selected_api=GoogleDriveCLIAPI,
     action=file, and --args {params: {file, convert, new_name}}.
  2. Parses the Zapier response to extract the uploaded file's id + webViewLink.
  3. Calls zapier.execute_zapier_write_action with selected_api=GoogleDriveCLIAPI,
     action=share_file, and --args {params: {file_id, permission: public_link_view}}.
  4. Reports the final webViewLink (or, if public-link-view is rejected, falls
     back to a Drive link construction from the file id).
"""
import json
import re
import subprocess
import sys

MCPORTER_JS = r"C:\Users\karti\AppData\Roaming\npm\node_modules\mcporter\dist\cli.js"

FILE_PATH = r"D:\IBM Project\Open_Production\open-production-plan-copy.md"
FILE_NAME = "open-production-plan-copy.md"


def run_mcporter(tool: str, args_dict: dict, *, label: str,
                 extra_flags: list[str] | None = None) -> dict:
    """Invoke a Zapier write action with --args <json>."""
    args_json = json.dumps(args_dict)
    cmd = [
        "node", MCPORTER_JS, "call", tool,
        "--args", args_json,
        "--output", "json",
    ]
    if extra_flags:
        cmd.extend(extra_flags)
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        shell=False,
        timeout=180,
    )
    sys.stderr.write(f"\n=== {label} (exit {proc.returncode}) ===\n")
    sys.stderr.write(f"stderr: {proc.stderr[:500]}\n")
    sys.stderr.write(f"stdout (first 800): {proc.stdout[:800]}\n\n")
    if proc.returncode != 0:
        return {"_error": True, "stderr": proc.stderr, "stdout": proc.stdout}
    raw = proc.stdout.strip()
    if not raw:
        return {"_error": True, "stderr": "empty stdout"}
    # Strip [mcporter] banner lines from stdout before parsing
    cleaned = "\n".join(
        line for line in raw.splitlines()
        if not line.lstrip().startswith("[mcporter]")
    ).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"_raw": raw}


def extract_file_id(blob) -> str | None:
    """Zapier returns whatever the action's output string contains. The file
    id is a Drive-style id: ~33 chars of alphanumerics, dashes, underscores."""
    s = json.dumps(blob) if blob else ""
    # Try a Google Drive id pattern first
    m = re.search(r'([A-Za-z0-9_-]{25,44})', s)
    if m:
        return m.group(0)
    return None


def extract_url(blob, pattern: str) -> str | None:
    s = json.dumps(blob) if blob else ""
    m = re.search(pattern, s)
    return m.group(0) if m else None


def main():
    # ---- Step 1: upload ----
    upload_args = {
        "selected_api": "GoogleDriveCLIAPI",
        "action": "file",
        "instructions": (
            "Upload the IBM Open Production plan markdown to Drive. "
            "Preserve the .md extension; do NOT convert to Google Doc."
        ),
        "params": {
            "file": FILE_PATH,
            "convert": False,
            "new_name": FILE_NAME,
        },
        "output": "file id, name, webViewLink, webContentLink",
    }
    upload = run_mcporter("zapier.execute_zapier_write_action",
                          upload_args, label="UPLOAD")

    file_id = extract_file_id(upload)
    if not file_id:
        sys.stderr.write("Could not extract file id from upload result.\n")
        print(json.dumps({"stage": "upload", "upload": upload}, indent=2))
        return 1

    sys.stderr.write(f"file_id: {file_id}\n")

    # ---- Step 2: share ----
    share_args = {
        "selected_api": "GoogleDriveCLIAPI",
        "action": "share_file",
        "instructions": (
            "Make this file viewable by anyone with the link. "
            "View-only — no edit, no comment."
        ),
        "params": {
            "file_id": file_id,
            "permission": "public_link_view",
        },
        "output": "file id, name, webViewLink, webContentLink, permissionId",
    }
    share = run_mcporter("zapier.execute_zapier_write_action",
                         share_args, label="SHARE")

    # Build the canonical public view URL (works even if share action failed)
    canonical_view = f"https://drive.google.com/file/d/{file_id}/view?usp=drivesdk"
    canonical_dl   = f"https://drive.google.com/uc?export=download&id={file_id}"

    web_view = extract_url(upload, r'https://drive\.google\.com/file/d/[^"\s]+') \
        or extract_url(share,  r'https://drive\.google\.com/file/d/[^"\s]+') \
        or canonical_view
    web_dl   = extract_url(upload, r'https://drive\.google\.com/uc\?export=download&id=[^"\s]+') \
        or extract_url(share,  r'https://drive\.google\.com/uc\?export=download&id=[^"\s]+') \
        or canonical_dl

    print(json.dumps({
        "stage": "done",
        "file_id": file_id,
        "view_link": web_view,
        "download_link": web_dl,
        "upload": upload,
        "share": share,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
