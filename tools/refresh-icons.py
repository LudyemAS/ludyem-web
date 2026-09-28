#!/usr/bin/env python3
"""
refresh-icons.py: the site's app icons, straight from the App Store.

The icons in assets/icons/ drifted from the shipping ones more than once (Never Stall,
Tend and the Workouts family all showed an old icon in September 2026). This pulls the
icon each app's listing shows today, so the site shows what the store shows.

    tools/refresh-icons.py           # download every icon, write <slug>.png and <slug>-512.png
    tools/refresh-icons.py --check   # download nothing to disk; list icons that differ

Needs Pillow (python3 -m pip install pillow). Uses Apple's public lookup API, no key.
"""
from __future__ import annotations

import argparse, io, json, sys, urllib.request
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageStat
except ImportError:
    sys.exit("✗ needs Pillow: python3 -m pip install pillow")

ROOT = Path(__file__).resolve().parent.parent
ICONS = ROOT / "assets" / "icons"

# slug on this site -> App Store id. Add a line when an app ships.
APPS = {
    "rckit": 1544144499,
    "appglance": 6801786470,
    "storeglance": 6807185861,
    "vitaview": 6772708337,
    "tend": 6778921650,
    "never-stall": 6808904948,
    "runway": 6784426559,
    "pushups": 6447548662,
    "situps": 6449369495,
    "pullups": 6449373216,
    "squats": 6449372822,
}


def store_icon(app_id: int) -> Image.Image:
    with urllib.request.urlopen(f"https://itunes.apple.com/lookup?id={app_id}&country=us", timeout=20) as r:
        results = json.load(r).get("results", [])
    if not results:
        raise RuntimeError(f"no App Store listing for id {app_id}")
    url = results[0]["artworkUrl512"].rsplit("/", 1)[0] + "/1024x1024bb.png"
    with urllib.request.urlopen(url, timeout=30) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGB")


def differs(a: Image.Image, b: Image.Image) -> bool:
    """True when two icons are visibly different (small, blurred compare)."""
    a, b = (x.convert("RGB").resize((64, 64)) for x in (a, b))
    diff = ImageChops.difference(a, b).convert("L")
    return ImageStat.Stat(diff).mean[0] > 6


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--check", action="store_true", help="report icons that differ from the store; write nothing")
    a = p.parse_args()
    stale = 0
    for slug, app_id in APPS.items():
        try:
            icon = store_icon(app_id)
        except Exception as e:  # network, or a listing that is gone
            print(f"  ? {slug}: {e}")
            continue
        path = ICONS / f"{slug}.png"
        if a.check:
            if not path.exists() or differs(Image.open(path), icon):
                print(f"  ✗ {slug}: differs from the App Store")
                stale += 1
            else:
                print(f"  ✓ {slug}")
            continue
        icon.resize((256, 256), Image.LANCZOS).save(path, optimize=True)
        icon.resize((512, 512), Image.LANCZOS).save(ICONS / f"{slug}-512.png", optimize=True)
        print(f"  ✓ {slug}: written")
    if a.check and stale:
        sys.exit(f"\n{stale} icon(s) out of date. Run tools/refresh-icons.py to fix.")


if __name__ == "__main__":
    main()
