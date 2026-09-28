# ludyem.dev

One website, every Ludyem app. A static site on GitHub Pages at **ludyem.dev**, where
each app that has no domain of its own lives at its own path. No build step and no
framework: plain HTML, one shared stylesheet, deployed straight from `main`.

| URL | Folder | What it is |
|-----|--------|------------|
| `ludyem.dev/` | `index.html` | The studio: every app, grouped (developer tools, health, money) |
| `ludyem.dev/workouts` | `workouts/` | The four rep trainers (Push-Ups, Sit-Ups, Pull-Ups, Squats) |
| `ludyem.dev/tend` | `tend/` | Tend, mood and symptom diary |
| `ludyem.dev/storeglance` | `storeglance/` | StoreGlance, plus its free check, guides and press kit |
| `ludyem.dev/never-stall` | `never-stall/` | Never Stall, in the app's own skin (`never-stall/assets/never-stall.css`) |
| `ludyem.dev/lungday/privacy` · `/support` | `lungday/` | Lungday's legal pages, ahead of its release |
| `ludyem.dev/runway/*` | `runway/` | Redirect stubs to runwayfire.com. Leave them: old links still arrive |
| `ludyem.dev/<app>/privacy` · `/support` · `/terms` | per app | Legal and help; App Store Connect points here |

RCKit (rckit.app), AppGlance (appglance.app), VitaView (vitaview.app) and Runway
(runwayfire.com) have their own sites; the landing page links out to them.

## The design

The look follows rckit.app: a black page, system type set big and tight, headlines in
two tones (white, then a grey `<span>`), real screens in CSS-drawn iPhones, and colour
that comes from light (a glow behind the phones, a tint in a card) rather than from
gradient text. `assets/ludyem.css` explains itself at the top; the short version:

* **Theming is three tokens**, set in a small inline `<style>` after the stylesheet:
  `--accent` (the app's colour, from its icon), `--accent-ink` (the same hue, light
  enough to read as text on black) and `--on-accent` (text on an accent fill).
* **Components**: `.topbar`, `.hero` with `.stage` (three phones), `.iphone` (the drawn
  device around an `<img>`), `.bento` / `.card` (tinted by `--tint`), `.plats` (short
  feature list), `.close`, `.foot`. Documents keep their old class names
  (`.doc-main`, `.doc-body`, `.faq-list`, …), restyled.
* **Cards side by side line up** with CSS subgrid (`.bento.pair.align`,
  `.bento.three.align`, `.bento.four.align`): name, headline, text, buttons and phone
  each share a row with the next card.
* **The mark** is `assets/ludyem-icon.svg`: an L made of three app tiles, with an orange
  dot in the empty slot for the next app. PNG sizes are in `assets/icons/ludyem*.png`
  (`ludyem-180.png` is full-bleed, for iOS to round). Social cards are in `assets/og/`.

## Screens and icons

* **Screens are raw simulator captures**, never App Store composites: 1320×2868 from an
  iPhone 17 Pro Max, status bar at 9:41, resized to **660px wide WebP** (about 45 KB).
  Each app's screenshot mode is how they were made (Tend `ASC_SCREENSHOT_MODE=1`,
  VitaView `VV_SCREENSHOT_MODE=1`, Workouts `-SeedWorkouts -debug.proUnlocked YES`,
  Never Stall `make shots`); see each repo.
* **Icons come from the App Store**, so the site shows what the store shows:

  ```bash
  tools/refresh-icons.py --check   # which icons differ from the listings
  tools/refresh-icons.py           # pull them all (256px and 512px)
  ```

## Add a new app

```bash
# Not on the App Store yet: the badges say "Coming soon":
./new-app.py myapp --name MyApp --accent "#2e8dd9" \
    --tagline "One clear sentence about what it does." \
    --blurb "A slightly longer sentence for search and social cards."

# When it ships, wire the real App Store buttons and touch nothing else:
./new-app.py myapp --appstore-id 6450000000 --buttons-only
```

Then write the feature copy in `<slug>/index.html` (and check every claim against the
app), add the icon (`tools/refresh-icons.py` once it is live, by hand before that),
three screens at `<slug>/assets/shots/1.webp`, `2.webp`, `3.webp`, and a card on the
landing page. `./new-app.py --help` has every option.

## Hosting

* GitHub Pages, **Settings → Pages → Build from `main` / root**. `CNAME` sets the domain.
* DNS is at Porkbun: four `A` records for `@` (185.199.108–111.153) and a `CNAME` for
  `www` to `ludyemas.github.io`. `.dev` is HSTS-preloaded, so HTTPS only.
* `support@ludyem.dev` is the one public contact address on every page.
* Pages are served extensionless by GitHub Pages (`/tend/privacy` is `tend/privacy.html`).
  Python's `http.server` does not do that locally, so preview with the `.html`.

## Notes

* Workouts carries **no mascot**, on purpose. Tend's Sprout and Runway's Pip stay.
* Never Stall's page follows the app's DESIGN.md (flat panels, 1px borders, no glows,
  cyan for progress and violet for a ceiling). Keep new colours out of it.

© Ludyem AS
