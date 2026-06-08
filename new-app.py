#!/usr/bin/env python3
"""
new-app.py — scaffold a new app page under ludyem.dev from _template/.

Each Ludyem app gets its own folder (the folder name IS the URL path):
    ludyem.dev/<slug>            -> <slug>/index.html
    ludyem.dev/<slug>/privacy    -> <slug>/privacy.html
    ludyem.dev/<slug>/support    -> <slug>/support.html
    ludyem.dev/<slug>/terms      -> <slug>/terms.html

This copies _template/, fills in the per-app identity + theme + App Store links,
and leaves the (editable) feature copy in place. Everything visual is reused from
assets/ludyem.css, so apps stay consistent automatically.

Examples
--------
    # An app that isn't on the store yet (download buttons say "Coming soon"):
    ./new-app.py water --name Water --emoji 💧 --accent "#2e8dd9" \\
        --tagline "Log hydration in a single tap." \\
        --blurb "A friendly hydration tracker that keeps you on pace all day."

    # A live app (wires real App Store buttons):
    ./new-app.py tend --name Tend --emoji 🌿 --accent "#22c55e" --accent2 "#0ea5e9" \\
        --appstore-id 6450000000 \\
        --tagline "Track symptoms and mood, written to Apple Health." \\
        --headline 'Your symptoms,<br><span class="grad">in one place.</span>'

After it runs: edit <slug>/index.html feature copy, drop a hero image at
<slug>/assets/hero.png, and add a card for the app to the landing page (index.html).
"""
from __future__ import annotations
import argparse, datetime, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "_template"
PAGES = ["index.html", "privacy.html", "support.html", "terms.html"]


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        sys.exit(f"✗ not a valid hex colour: #{h}")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore


def lighten(h: str, amt: float) -> str:
    """Blend a hex colour toward white by `amt` (0..1) — used for gradient text."""
    r, g, b = hex_to_rgb(h)
    r = round(r + (255 - r) * amt)
    g = round(g + (255 - g) * amt)
    b = round(b + (255 - b) * amt)
    return f"#{r:02x}{g:02x}{b:02x}"


def theme_css(accent1: str, accent2: str, grad_a: str, grad_b: str) -> str:
    r, g, b = hex_to_rgb(accent1)
    return (
        "\n    :root {\n"
        f"      --accent1: {accent1}; --accent2: {accent2};\n"
        f"      --grad-a: {grad_a}; --grad-b: {grad_b};\n"
        f"      --accent-soft: rgba({r},{g},{b},0.14); --accent-line: rgba({r},{g},{b},0.32);\n"
        "    }\n  "
    )


APPLE_SVG = (
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">'
    '<path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>'
)


def download_buttons(app_id: str | None) -> dict[str, str]:
    """Primary (hero), CTA, and nav download buttons — live or 'coming soon'."""
    if app_id:
        url = f"https://apps.apple.com/app/id{app_id}"
        primary = (
            f'<a href="{url}" class="btn-primary" target="_blank" rel="noopener">{APPLE_SVG} '
            "Download on App Store</a>"
        )
        cta = (
            f'<a href="{url}" class="btn-primary" style="display:inline-flex;" target="_blank" rel="noopener">{APPLE_SVG} '
            "Download on App Store — Free</a>"
        )
        nav = f'<a href="{url}" class="btn-nav" target="_blank" rel="noopener">Download Free</a>'
    else:
        primary = '<span class="btn-primary" style="opacity:.6;cursor:default;">Coming soon</span>'
        cta = '<span class="btn-primary" style="display:inline-flex;opacity:.6;cursor:default;">Coming soon</span>'
        nav = '<span class="btn-nav" style="opacity:.6;cursor:default;">Coming soon</span>'
    return {"DOWNLOAD_PRIMARY": primary, "DOWNLOAD_CTA": cta, "DOWNLOAD_NAV": nav}


def main() -> None:
    p = argparse.ArgumentParser(
        description="Scaffold a new app page under ludyem.dev from _template/.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("slug", help="URL path / folder name, e.g. 'water' -> ludyem.dev/water")
    p.add_argument("--name", required=True, help="Display name, e.g. 'Water'")
    p.add_argument("--emoji", default="✨", help="Icon emoji used in the hero/cards")
    p.add_argument("--accent", default="#6d6cff", help="Primary accent hex (default Ludyem indigo)")
    p.add_argument("--accent2", default=None, help="Secondary accent hex (default: a lighter accent)")
    p.add_argument("--grad-a", default=None, help="Gradient text start (default: lightened accent)")
    p.add_argument("--grad-b", default=None, help="Gradient text end (default: lightened accent2)")
    p.add_argument("--tagline", default="A focused app from Ludyem.", help="Hero subtitle")
    p.add_argument("--headline", default=None,
                   help="Hero H1 HTML. Default builds one from --name. Use <span class=\"grad\">…</span> to highlight.")
    p.add_argument("--blurb", default=None, help="One-line description for meta tags (default: tagline)")
    p.add_argument("--appstore-id", default=None,
                   help="Numeric App Store ID. Omit for a 'Coming soon' page with no live links.")
    p.add_argument("--support-email", default="support@ludyem.dev", help="Support/contact email")
    p.add_argument("--date", default=None, help="'Last updated' date for legal pages (default: today)")
    p.add_argument("--force", action="store_true", help="Overwrite the folder if it already exists")
    a = p.parse_args()

    slug = a.slug.strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        sys.exit(f"✗ slug must be url-safe (lowercase letters, digits, hyphens): got '{a.slug}'")
    if slug in {"assets", "_template"}:
        sys.exit(f"✗ '{slug}' is reserved.")

    dest = ROOT / slug
    if dest.exists() and not a.force:
        sys.exit(f"✗ {dest} already exists. Re-run with --force to overwrite.")

    accent1 = a.accent
    accent2 = a.accent2 or lighten(accent1, 0.25)
    grad_a = getattr(a, "grad_a") or lighten(accent1, 0.45)
    grad_b = getattr(a, "grad_b") or lighten(accent2, 0.45)
    headline = a.headline or f'{a.name},<br><span class="grad">your way.</span>'
    blurb = a.blurb or a.tagline
    date = a.date or datetime.date.today().strftime("%-d %B %Y")
    year = (a.date or datetime.date.today().isoformat())[:4]

    tokens = {
        "APP_NAME": a.name,
        "APP_SLUG": slug,
        "APP_EMOJI": a.emoji,
        "APP_HEADLINE": headline,
        "APP_TAGLINE": a.tagline,
        "APP_BLURB": blurb,
        "THEME_CSS": theme_css(accent1, accent2, grad_a, grad_b),
        "SUPPORT_EMAIL": a.support_email,
        "DATE": date,
        "YEAR": year,
        **download_buttons(a.appstore_id),
    }

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    (dest / "assets").mkdir()

    for page in PAGES:
        text = (TEMPLATE / page).read_text(encoding="utf-8")
        for key, val in tokens.items():
            text = text.replace("{{" + key + "}}", val)
        leftover = re.findall(r"\{\{[A-Z_]+\}\}", text)
        if leftover:
            print(f"  ⚠ {page}: unreplaced tokens {sorted(set(leftover))}")
        (dest / page).write_text(text, encoding="utf-8")
        print(f"  ✓ {slug}/{page}")

    status = f"live (id {a.appstore_id})" if a.appstore_id else "COMING SOON (no live links)"
    print(f"\n✓ Scaffolded ludyem.dev/{slug} — {status}\n")
    print("Next steps:")
    print(f"  1. Edit {slug}/index.html — replace the placeholder feature copy.")
    print(f"  2. Add a hero image at {slug}/assets/hero.png (or it auto-hides).")
    print(f"  3. Add an <a class=\"app-card\" href=\"/{slug}\"> card to the landing page (index.html).")
    if not a.appstore_id:
        print("  4. When the app ships, re-run with --appstore-id <id> --force to wire real buttons.")
    print(f"  5. Commit & push — GitHub Pages will serve it at https://ludyem.dev/{slug}")


if __name__ == "__main__":
    main()
