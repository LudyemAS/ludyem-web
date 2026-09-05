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
        --appstore-id 6450000000 --free \\
        --tagline "Track symptoms and mood, written to Apple Health." \\
        --headline 'Your symptoms,<br><span class="grad">in one place.</span>'

    # An app that already shipped and whose pages are hand-written — wire the real
    # App Store buttons WITHOUT touching a word of the prose:
    ./new-app.py never-stall --appstore-id 6808904948 --buttons-only

Editing an app that already exists
----------------------------------
--force no longer overwrites hand-written pages. It re-renders only the pages that
still look exactly like template output; if a page has been edited it stops and tells
you which ones. --overwrite-content is the deliberate "yes, throw my edits away".
Neither ever deletes the folder, so assets/, guides/ and blog/ survive.

Wording note: the download buttons only claim the app is free when you pass --free.
Never add it for an app without a free tier — that claim is a legal one.

After it runs: edit <slug>/index.html feature copy, drop a hero image at
<slug>/assets/hero.png, and add a card for the app to the landing page (index.html).
"""
from __future__ import annotations
import argparse, datetime, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "_template"
PAGES = ["index.html", "privacy.html", "support.html", "terms.html"]

# Pages whose URL can also be served the directory way (privacy/index.html). The
# scaffolder only ever writes the flat form, so an app using the directory form must
# not be scaffolded over — both copies would sit there and the stale one may win.
DIR_FORM = ["privacy", "support", "terms"]

# Formats accepted by --date. Deliberately no slashed forms: 05/09/2026 is 5 September
# in Oslo and 9 May in Cupertino, and guessing wrong puts a wrong date in a legal page.
DATE_FORMATS = [
    "%Y-%m-%d",       # 2026-09-05
    "%d %B %Y",       # 5 September 2026   (what this script itself prints)
    "%d %b %Y",       # 5 Sep 2026
    "%B %d, %Y",      # September 5, 2026
    "%b %d, %Y",      # Sep 5, 2026
    "%B %d %Y",       # September 5 2026
    "%b %d %Y",       # Sep 5 2026
    "%d.%m.%Y",       # 05.09.2026
]


def parse_date(s: str) -> datetime.date | None:
    """Read a human or ISO date. None if it isn't one — the caller decides how loud."""
    for fmt in DATE_FORMATS:
        try:
            return datetime.datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None


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


def download_buttons(app_id: str | None, free: bool = False) -> dict[str, str]:
    """Primary (hero), CTA, and nav download buttons — live or 'coming soon'.

    `free` opts in to the "Free" wording. It is off by default because a paid app
    whose page says "Free" is a false claim, not a typo.
    """
    if app_id:
        url = f"https://apps.apple.com/app/id{app_id}"
        cta_label = "Download on App Store — Free" if free else "Download on App Store"
        nav_label = "Download Free" if free else "Download"
        primary = (
            f'<a href="{url}" class="btn-primary" target="_blank" rel="noopener">{APPLE_SVG} '
            "Download on App Store</a>"
        )
        cta = (
            f'<a href="{url}" class="btn-primary" style="display:inline-flex;" target="_blank" rel="noopener">{APPLE_SVG} '
            f"{cta_label}</a>"
        )
        nav = f'<a href="{url}" class="btn-nav" target="_blank" rel="noopener">{nav_label}</a>'
    else:
        primary = '<span class="btn-primary" style="opacity:.6;cursor:default;">Coming soon</span>'
        cta = '<span class="btn-primary" style="display:inline-flex;opacity:.6;cursor:default;">Coming soon</span>'
        nav = '<span class="btn-nav" style="opacity:.6;cursor:default;">Coming soon</span>'
    return {"DOWNLOAD_PRIMARY": primary, "DOWNLOAD_CTA": cta, "DOWNLOAD_NAV": nav}


def is_pristine(page_text: str, template_text: str) -> bool:
    """True if `page_text` could have come straight out of `template_text`.

    Compares the literal stretches between {{TOKEN}} slots and lets the slots hold
    anything, so a page still counts as pristine whatever name/date/App Store ID was
    substituted into it. One word changed in the prose and it doesn't.
    """
    chunks = re.split(r"\{\{[A-Z_]+\}\}", template_text)
    pos = 0
    for i, chunk in enumerate(chunks):
        if not chunk:
            continue
        if i == 0:
            if not page_text.startswith(chunk):
                return False
            pos = len(chunk)
            continue
        found = page_text.find(chunk, pos)
        if found == -1:
            return False
        pos = found + len(chunk)
    return chunks[-1] == "" or page_text.endswith(chunks[-1])


# --- --buttons-only surgery -------------------------------------------------------
# Matches the button elements by structure, never by their label, because live pages
# have hand-edited labels ("Download on the App Store") worth keeping.
COMING_SOON_CTA = re.compile(
    r'<span class="btn-primary"[^>]*display:inline-flex[^>]*>\s*Coming soon\s*</span>')
COMING_SOON_PRIMARY = re.compile(
    r'<span class="btn-primary"[^>]*>\s*Coming soon\s*</span>')
COMING_SOON_NAV = re.compile(
    r'<span class="btn-nav"[^>]*>\s*Coming soon\s*</span>')
# An already-live button: swap the id in the href, leave the label alone. Scoped to
# btn-primary/btn-nav so a page listing several apps (workouts) is left untouched.
LIVE_HREF = re.compile(
    r'(<a href=")https://apps\.apple\.com/app/id\d+(" class="btn-(?:primary|nav)")')


def rewrite_buttons(text: str, buttons: dict[str, str], url: str) -> tuple[str, int]:
    """Replace only the App Store button markup. Returns (new_text, n_changed)."""
    n = 0
    # Re-point already-live buttons first, so the anchors written just below aren't
    # then matched by LIVE_HREF and counted a second time.
    text, c = LIVE_HREF.subn(lambda m: f"{m.group(1)}{url}{m.group(2)}", text); n += c
    text, c = COMING_SOON_CTA.subn(lambda _: buttons["DOWNLOAD_CTA"], text); n += c
    text, c = COMING_SOON_PRIMARY.subn(lambda _: buttons["DOWNLOAD_PRIMARY"], text); n += c
    text, c = COMING_SOON_NAV.subn(lambda _: buttons["DOWNLOAD_NAV"], text); n += c
    return text, n


def app_pages(dest: Path) -> list[Path]:
    """Every page of an app, in whichever layout it uses (flat or directory form)."""
    found = [dest / p for p in PAGES if (dest / p).is_file()]
    found += [dest / n / "index.html" for n in DIR_FORM if (dest / n / "index.html").is_file()]
    return found


def run_buttons_only(dest: Path, slug: str, app_id: str, free: bool) -> None:
    pages = app_pages(dest)
    if not pages:
        sys.exit(f"✗ no pages found under {dest} — nothing to wire up.")
    url = f"https://apps.apple.com/app/id{app_id}"
    buttons = download_buttons(app_id, free)
    total = 0
    for page in pages:
        text = page.read_text(encoding="utf-8")
        new_text, n = rewrite_buttons(text, buttons, url)
        rel = page.relative_to(ROOT)
        if n:
            page.write_text(new_text, encoding="utf-8")
            print(f"  ✓ {rel} — {n} button{'s' if n != 1 else ''} wired to id {app_id}")
            total += n
        else:
            print(f"  · {rel} — no App Store buttons, left alone")
    if not total:
        sys.exit(
            f"\n✗ Found no button markup to rewrite in {slug}/.\n"
            "  The buttons must have been hand-written into a different shape — wire\n"
            "  them by hand; nothing was changed."
        )
    print(f"\n✓ Wired {total} button(s) for ludyem.dev/{slug} — prose untouched.")
    if not free:
        print("  Buttons do not claim the app is free. Pass --free if it has a free tier.")
    leftovers = []
    for page in pages:
        for i, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
            if "coming soon" in line.lower():
                leftovers.append(f"{page.relative_to(ROOT)}:{i}")
    print("\nStill to do by hand:")
    if leftovers:
        print(f"  1. 'Coming soon' still appears at: {', '.join(leftovers)}")
    else:
        print("  1. No 'Coming soon' wording left on these pages.")
    print("  2. Check the landing page card (index.html) points at the live app.")


def main() -> None:
    p = argparse.ArgumentParser(
        description="Scaffold a new app page under ludyem.dev from _template/.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("slug", help="URL path / folder name, e.g. 'water' -> ludyem.dev/water")
    p.add_argument("--name", help="Display name, e.g. 'Water' (required unless --buttons-only)")
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
    p.add_argument("--free", action="store_true",
                   help="Say the app is free on the download buttons. Only for apps with a free tier.")
    p.add_argument("--support-email", default="support@ludyem.dev", help="Support/contact email")
    p.add_argument("--date", default=None, help="'Last updated' date for legal pages (default: today)")
    p.add_argument("--year", default=None,
                   help="Copyright year for footers (default: the year of --date, else this year)")
    p.add_argument("--force", action="store_true",
                   help="Re-render an app that already exists. Stops if any page was hand-edited.")
    p.add_argument("--overwrite-content", action="store_true",
                   help="With --force: re-render hand-edited pages too, throwing those edits away.")
    p.add_argument("--buttons-only", action="store_true",
                   help="Rewrite just the App Store button markup in an existing app. Touches no prose.")
    a = p.parse_args()

    slug = a.slug.strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        sys.exit(f"✗ slug must be url-safe (lowercase letters, digits, hyphens): got '{a.slug}'")
    if slug in {"assets", "_template"}:
        sys.exit(f"✗ '{slug}' is reserved.")

    dest = ROOT / slug

    # --- buttons-only: a completely separate, non-destructive path -----------------
    if a.buttons_only:
        if a.force or a.overwrite_content:
            sys.exit("✗ --buttons-only rewrites nothing but buttons; drop --force/--overwrite-content.")
        if not a.appstore_id:
            sys.exit("✗ --buttons-only needs --appstore-id <id> — that's the whole point of it.")
        if not dest.is_dir():
            sys.exit(f"✗ {dest} doesn't exist. Scaffold it first (without --buttons-only).")
        run_buttons_only(dest, slug, a.appstore_id, a.free)
        return

    if a.overwrite_content and not a.force:
        sys.exit("✗ --overwrite-content only means something with --force.")

    if dest.exists() and not a.force:
        sys.exit(
            f"✗ {dest} already exists.\n"
            "  To wire up App Store buttons on a shipped app, use --buttons-only.\n"
            "  To re-render the pages from the template, use --force."
        )

    # --- guard an app that already exists -----------------------------------------
    if dest.exists():
        dir_pages = [f"{n}/index.html" for n in DIR_FORM if (dest / n / "index.html").is_file()]
        if dir_pages:
            sys.exit(
                f"✗ {slug}/ serves its pages the directory way ({', '.join(dir_pages)}).\n"
                f"  Scaffolding writes {'/'.join(PAGES[1:2])} etc. beside those, leaving two copies of\n"
                "  every page with no say in which one wins.\n"
                "  Use --buttons-only to wire App Store buttons, or move the pages by hand first."
            )
        edited = []
        for page in PAGES:
            path = dest / page
            if path.is_file() and not is_pristine(
                    path.read_text(encoding="utf-8"),
                    (TEMPLATE / page).read_text(encoding="utf-8")):
                edited.append(page)
        if edited and not a.overwrite_content:
            sys.exit(
                f"✗ {slug}/ has hand-written pages: {', '.join(edited)}\n"
                "  --force would replace them with template copy, including claims the\n"
                "  template makes that may not be true of this app.\n"
                "  Use --buttons-only to wire App Store buttons and touch nothing else,\n"
                "  or --overwrite-content to throw those edits away on purpose."
            )
        if edited:
            print(f"  ⚠ overwriting hand-written pages: {', '.join(edited)}\n")

    if not a.name:
        sys.exit("✗ --name is required when scaffolding.")

    accent1 = a.accent
    accent2 = a.accent2 or lighten(accent1, 0.25)
    grad_a = getattr(a, "grad_a") or lighten(accent1, 0.45)
    grad_b = getattr(a, "grad_b") or lighten(accent2, 0.45)
    headline = a.headline or f'{a.name},<br><span class="grad">your way.</span>'
    blurb = a.blurb or a.tagline
    today = datetime.date.today()

    # The date shown on legal pages is whatever was asked for, verbatim. The copyright
    # year is derived from it — never sliced off the front of it, which is how footers
    # ended up reading "© 5 Se Ludyem AS".
    date = a.date or today.strftime("%-d %B %Y")
    if a.year:
        if not re.fullmatch(r"[0-9]{4}", a.year):
            sys.exit(f"✗ --year must be a 4-digit year: got '{a.year}'")
        year = a.year
    elif a.date:
        parsed = parse_date(a.date)
        if parsed is None:
            sys.exit(
                f"✗ can't read a year out of --date '{a.date}'.\n"
                "  Accepted: 2026-09-05, 5 September 2026, 5 Sep 2026, September 5, 2026,\n"
                "  05.09.2026. For any other wording, pass --year 2026 alongside it."
            )
        year = str(parsed.year)
    else:
        year = str(today.year)

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
        **download_buttons(a.appstore_id, a.free),
    }

    # Only ever writes the four pages. The folder is never deleted, so assets/, guides/
    # and anything else hand-made stays put.
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "assets").mkdir(exist_ok=True)

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
    print(f"\n✓ Scaffolded ludyem.dev/{slug} — {status} — © {year}\n")
    print("Next steps:")
    print(f"  1. Edit {slug}/index.html — replace the placeholder feature copy.")
    print(f"  2. Add a hero image at {slug}/assets/hero.png (or it auto-hides).")
    print(f"  3. Add an <a class=\"app-card\" href=\"/{slug}\"> card to the landing page (index.html).")
    if not a.appstore_id:
        print(f"  4. When the app ships: ./new-app.py {slug} --appstore-id <id> --buttons-only")
        print("     (wires the real buttons and leaves every word you wrote alone).")
    print(f"  5. Commit & push — GitHub Pages will serve it at https://ludyem.dev/{slug}")


if __name__ == "__main__":
    main()
