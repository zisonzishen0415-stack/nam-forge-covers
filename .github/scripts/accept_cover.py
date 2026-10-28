#!/usr/bin/env python3
"""Accept a NAM FORGE cover submitted through a prefilled GitHub issue.

The app opens a new issue whose body contains a hidden marker:

    <!-- NAMFORGE-COVER:<base64url payload> -->

The payload is a compact JSON object (gzip-compressed when the browser
supports CompressionStream). This script validates it, writes the design
JSON + 128x64 PNG, updates library.json, and commits. No token is ever
entered by the user; the workflow's GITHUB_TOKEN is used server-side.
"""
import base64
import datetime as dt
import gzip
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COVERS = ROOT / "covers"
LIBRARY = ROOT / "library.json"

MARKER = re.compile(r"<!--\s*NAMFORGE-COVER:([A-Za-z0-9_-]+)\s*-->")
LICENSES = {"CC-BY-4.0", "CC0-1.0", "CC-BY-SA-4.0", "MIT"}
PNG_SIG = b"\x89PNG\r\n\x1a\n"


class Invalid(Exception):
    pass


def b64url_decode(text):
    if not isinstance(text, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", text or ""):
        raise Invalid("payload is not base64url")
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def expand_base(packed):
    if len(packed) != 1024:
        raise Invalid("packed cover must be 1,024 bytes")
    pixels = bytearray(8192)
    for yx in range(8):
        for x in range(128):
            v = packed[yx * 128 + x]
            for z in range(8):
                pixels[(yx * 8 + z) * 128 + x] = (v >> z) & 1
    return bytes(pixels)


def clean_text(value, field, limit, required=True):
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise Invalid(f"{field} must be text")
    value = value.strip()
    if required and not value:
        raise Invalid(f"{field} is required")
    if len(value) > limit:
        raise Invalid(f"{field} is longer than {limit} characters")
    return value


def clean_int(value, field, lo, hi, default=0):
    if value is None:
        value = default
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Invalid(f"{field} must be a number")
    value = int(value)
    if not lo <= value <= hi:
        raise Invalid(f"{field} is out of range")
    return value


def clean_bool(value):
    return bool(value)


def validate_design(design):
    if not isinstance(design, dict):
        raise Invalid("design is missing")
    area = design.get("area")
    scale = design.get("scale")
    if not isinstance(area, list) or len(area) != 4:
        raise Invalid("area must have four values")
    if not isinstance(scale, list) or len(scale) != 2:
        raise Invalid("scale must have two values")
    area = [clean_int(v, "area", 0, 128) for v in area]
    scale = [max(1, min(8, clean_int(v, "scale", 1, 8))) for v in scale]
    text_fill = design.get("textFill") if design.get("textFill") in ("solid", "dither") else "solid"
    text_size = "large" if design.get("textSize") == "large" else "small"
    return {
        "preset": clean_text(design.get("preset"), "preset", 32, required=False) or "custom",
        "textInk": 1 if design.get("textInk") else 0,
        "area": area,
        "scale": scale,
        "plate": clean_bool(design.get("plate")),
        "halo": clean_bool(design.get("halo")),
        "showName": design.get("showName") is not False,
        "textFill": text_fill,
        "textSize": text_size,
        "textX": clean_int(design.get("textX"), "textX", -128, 128),
        "textY": clean_int(design.get("textY"), "textY", -128, 128),
    }


def validate_png(data):
    if len(data) > 64 * 1024:
        raise Invalid("preview PNG is too large")
    if not data.startswith(PNG_SIG) or len(data) < 33:
        raise Invalid("preview is not a PNG")
    if data[12:16] != b"IHDR":
        raise Invalid("preview PNG has no IHDR")
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    if (width, height) != (128, 64):
        raise Invalid("preview PNG must be 128x64")
    return data


def slugify(name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:32]
    return slug


def find_id(name, number):
    base = slugify(name) or f"cover-{number}"
    candidate = base
    n = 2
    while (COVERS / f"{candidate}.json").exists():
        candidate = f"{base}-{n}"
        n += 1
        if n > 99:
            raise Invalid("too many covers with the same name")
    return candidate


def parse_payload(body):
    match = MARKER.search(body or "")
    if not match:
        return None
    raw = b64url_decode(match.group(1))
    if len(raw) > 256 * 1024:
        raise Invalid("payload is too large")
    # The enc field is inside the compressed blob, so sniff the gzip magic.
    if raw.startswith(b"\x1f\x8b"):
        raw = gzip.decompress(raw)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise Invalid("payload is not valid JSON")
    if not isinstance(payload, dict) or payload.get("v") != 1:
        raise Invalid("unsupported payload version")
    if payload.get("format") != 1 or payload.get("engine") != "0.26":
        raise Invalid("unsupported design format")
    name = clean_text(payload.get("name"), "name", 40)
    author = clean_text(payload.get("author"), "author", 60)
    license_name = clean_text(payload.get("license"), "license", 40)
    if license_name not in LICENSES:
        raise Invalid("unsupported license")
    source = clean_text(payload.get("source"), "source", 140, required=False) or "original"
    preview_name = clean_text(payload.get("previewName"), "previewName", 16, required=False)
    design = validate_design(payload.get("design"))
    packed = b64url_decode(payload.get("basePacked"))
    pixels = expand_base(packed)
    png = validate_png(b64url_decode(payload.get("png")))
    return {
        "name": name,
        "author": author,
        "license": license_name,
        "source": source,
        "previewName": preview_name,
        "design": design,
        "pixels": pixels,
        "png": png,
    }


def write_cover(entry, issue_number):
    COVERS.mkdir(exist_ok=True)
    cover_id = find_id(entry["name"], issue_number)
    design_json = {
        "app": "NAM FORGE",
        "format": 1,
        "engine": "0.26",
        "previewName": entry["previewName"],
        "design": {
            **entry["design"],
            "base": base64.b64encode(entry["pixels"]).decode("ascii"),
        },
    }
    # Keep base second, matching the app's export order.
    ordered = {"preset": entry["design"]["preset"], "base": design_json["design"]["base"]}
    for key, value in design_json["design"].items():
        if key not in ordered:
            ordered[key] = value
    design_json["design"] = ordered
    (COVERS / f"{cover_id}.json").write_text(
        json.dumps(design_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (COVERS / f"{cover_id}.png").write_bytes(entry["png"])
    library = json.loads(LIBRARY.read_text(encoding="utf-8"))
    today = dt.date.today().isoformat()
    library["updated"] = today
    library.setdefault("covers", []).append(
        {
            "id": cover_id,
            "name": entry["name"],
            "author": entry["author"],
            "license": entry["license"],
            "source": entry["source"],
            "preview": f"covers/{cover_id}.png",
            "design": f"covers/{cover_id}.json",
            "tags": ["shared"],
            "added": today,
            "issue": issue_number,
        }
    )
    LIBRARY.write_text(
        json.dumps(library, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return cover_id


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)


def commit_and_push(cover_id):
    git("add", "covers", "library.json")
    if not subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=ROOT
    ).returncode:
        return False
    git(
        "-c",
        "user.name=NAM FORGE",
        "-c",
        "user.email=actions@users.noreply.github.com",
        "commit",
        "-m",
        f"Add shared cover {cover_id}",
    )
    for attempt in range(3):
        try:
            git("push")
            return True
        except subprocess.CalledProcessError:
            if attempt == 2:
                raise
            git("pull", "--rebase", "--autostash")
    return True


def main():
    dry_run = "--dry-run" in sys.argv
    no_commit = "--no-commit" in sys.argv
    body = os.environ.get("ISSUE_BODY", "")
    number = int(os.environ.get("ISSUE_NUMBER") or 0)
    result = {"status": "ignored", "message": "no NAM FORGE payload"}
    try:
        entry = parse_payload(body)
        if entry is None:
            result = {"status": "ignored", "message": "no NAM FORGE payload"}
        else:
            if dry_run:
                result = {
                    "status": "accepted",
                    "message": f"dry run: {entry['name']}",
                    "id": slugify(entry["name"]) or f"cover-{number}",
                }
            else:
                cover_id = write_cover(entry, number)
                if not no_commit:
                    commit_and_push(cover_id)
                result = {
                    "status": "accepted",
                    "message": f"已收录「{entry['name']}」：https://zisonzishen0415-stack.github.io/nam-forge-covers/",
                    "id": cover_id,
                }
    except Invalid as exc:
        result = {"status": "invalid", "message": str(exc)}
    except Exception as exc:  # noqa: BLE001 - report unexpected failures to the issue
        result = {"status": "error", "message": f"处理失败：{exc}"}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
