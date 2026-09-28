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
    # An app that isn't on the store yet (the badges say "Coming soon"):
    ./new-app.py water --name Water --accent "#2e8dd9" \\
        --tagline "Log hydration in a single tap." \\
        --blurb "A friendly hydration tracker that keeps you on pace all day."

    # A live app (wires real App Store buttons):
    ./new-app.py tend --name Tend --accent "#109E8D" \\
        --appstore-id 6450000000 \\
        --tagline "Track symptoms and mood, written to Apple Health." \\
        --headline 'Your symptoms, <span>in one place.</span>'

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

After it runs: edit <slug>/index.html feature copy, add the icon at
assets/icons/<slug>.png and <slug>-512.png, three screenshots at
<slug>/assets/shots/{1,2,3}.webp, and a card for the app on the landing page.
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
    """Blend a hex colour toward white by `amt` (0..1): the accent's readable text tint."""
    r, g, b = hex_to_rgb(h)
    r = round(r + (255 - r) * amt)
    g = round(g + (255 - g) * amt)
    b = round(b + (255 - b) * amt)
    return f"#{r:02x}{g:02x}{b:02x}"


def on_colour(h: str) -> str:
    """Black or white, whichever reads better on `h` (WCAG relative luminance)."""
    def lin(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = hex_to_rgb(h)
    lum = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
    return "#000" if (lum + 0.05) / 0.05 > 1.05 / (lum + 0.05) else "#fff"


def theme_css(accent: str, accent_ink: str) -> str:
    """The three tokens assets/ludyem.css themes a page with (see its header)."""
    return (
        "\n    :root {\n"
        f"      --accent: {accent}; --accent-ink: {accent_ink}; --on-accent: {on_colour(accent)};\n"
        "    }\n  "
    )


APPLE_SVG = '<svg aria-hidden="true"><use href="/assets/sprite.svg#apple"/></svg>'


def download_buttons(app_id: str | None, free: bool = False) -> dict[str, str]:
    """Hero and closing App Store badges, and the top bar's pill: live or 'coming soon'.

    `free` opts in to the "free" wording on the pill. It is off by default because a
    paid app whose page says "free" is a false claim, not a typo. (Apple's badge itself
    never says it.)
    """
    if app_id:
        url = f"https://apps.apple.com/app/id{app_id}"
        badge = (
            f'<a class="store" href="{url}" target="_blank" rel="noopener" aria-label="Download on the App Store">'
            f"{APPLE_SVG}<span><small>Download on the</small>App Store</span></a>"
        )
        nav = f'<a class="get" href="{url}" target="_blank" rel="noopener">{"Get it free" if free else "Download"}</a>'
    else:
        badge = f'<span class="store is-soon">{APPLE_SVG}<span><small>Coming soon to the</small>App Store</span></span>'
        nav = '<span class="get is-soon">Coming soon</span>'
    return {"DOWNLOAD_PRIMARY": badge, "DOWNLOAD_CTA": badge, "DOWNLOAD_NAV": nav}


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
# have hand-edited labels worth keeping. The first three are the 2026 design (a
# "store" badge and a "get" pill); the rest match pages from the old design.
COMING_SOON_BADGE = re.compile(
    r'<span class="store is-soon">\s*<svg.*?</svg>\s*<span>.*?</span>\s*</span>', re.S)
COMING_SOON_PILL = re.compile(r'<span class="get is-soon">\s*Coming soon\s*</span>')
LIVE_HREF_NEW = re.compile(
    r'(<a class="(?:store|get)[^"]*" href=")https://apps\.apple\.com/app/id\d+(")')
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
    text, c = LIVE_HREF_NEW.subn(lambda m: f"{m.group(1)}{url}{m.group(2)}", text); n += c
    text, c = LIVE_HREF.subn(lambda m: f"{m.group(1)}{url}{m.group(2)}", text); n += c
    text, c = COMING_SOON_BADGE.subn(lambda _: buttons["DOWNLOAD_PRIMARY"], text); n += c
    text, c = COMING_SOON_PILL.subn(lambda _: buttons["DOWNLOAD_NAV"], text); n += c
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
    p.add_argument("--emoji", default="✨", help=argparse.SUPPRESS)  # unused since the 2026 design
    p.add_argument("--accent", default="#FF5A36", help="The app's accent hex, from its icon (default Ludyem orange)")
    p.add_argument("--accent-ink", default=None, help="Accent as text on black (default: the accent, lightened)")
    # The old design's extra colours. Still accepted so old commands run; ignored.
    p.add_argument("--accent2", default=None, help=argparse.SUPPRESS)
    p.add_argument("--grad-a", default=None, help=argparse.SUPPRESS)
    p.add_argument("--grad-b", default=None, help=argparse.SUPPRESS)
    p.add_argument("--tagline", default="A focused app from Ludyem.", help="Hero subtitle")
    p.add_argument("--headline", default=None,
                   help="Hero H1 HTML. Default builds one from --name. A <span>…</span> is the grey second half.")
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

    accent = a.accent
    accent_ink = getattr(a, "accent_ink") or lighten(accent, 0.45)
    headline = a.headline or f'{a.name}, <span>your way.</span>'
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
        "THEME_CSS": theme_css(accent, accent_ink),
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
    print(f"  1. Edit {slug}/index.html — replace the placeholder feature copy, and check every claim.")
    print(f"  2. Add the icon at assets/icons/{slug}.png (256px) and {slug}-512.png, and three raw")
    print(f"     screenshots at {slug}/assets/shots/1.webp, 2.webp, 3.webp (660px wide). The phones")
    print("     stay hidden until all three exist.")
    print(f"  3. Add an <article class=\"card app\"> for it to the landing page (index.html).")
    if not a.appstore_id:
        print(f"  4. When the app ships: ./new-app.py {slug} --appstore-id <id> --buttons-only")
        print("     (wires the real buttons and leaves every word you wrote alone).")
    print(f"  5. Commit & push — GitHub Pages will serve it at https://ludyem.dev/{slug}")


if __name__ == "__main__":
    main()
