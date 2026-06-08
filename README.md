# ludyem.dev

One website, every Ludyem app. A single static site hosted on GitHub Pages at the
custom domain **ludyem.dev**, where each app lives at its own path:

| URL | Folder | What it is |
|-----|--------|------------|
| `ludyem.dev/` | `index.html` | Brand landing — the whole app constellation |
| `ludyem.dev/workouts` | `workouts/` | The four rep-counter apps (Push-Ups, Sit-Ups, Pull-Ups, Squats) |
| `ludyem.dev/workouts/privacy` · `/support` · `/terms` | `workouts/*.html` | Legal + help (App Store URLs point here) |
| `ludyem.dev/<app>` | `<app>/` | One folder per future app |

The trick that makes one domain serve every app: **GitHub Pages serves one repo at
the custom domain, and folders are the paths.** No build step, no framework — plain
HTML + one shared stylesheet, deployed straight from `main`.

## Reuse: how the apps stay consistent

* **`assets/ludyem.css`** is the shared design system. Every page links it. Change it
  once and every app updates.
* **Per-app theming** is just four CSS variables (`--accent1/2`, `--grad-a/b`) overridden
  in a small `<style>` block per page. Same components, different colours.
* **`_template/`** holds the page skeleton with `{{TOKENS}}`; **`new-app.py`** fills them in.

## Add a new app

```bash
# Not on the App Store yet → "Coming soon" buttons, no dead links:
./new-app.py water --name Water --emoji 💧 --accent "#2e8dd9" \
    --tagline "Log hydration in a single tap." \
    --blurb "A friendly hydration tracker that keeps you on pace all day."

# Live app → wires real App Store buttons:
./new-app.py tend --name Tend --emoji 🌿 --accent "#22c55e" --appstore-id 6450000000 \
    --tagline "Track symptoms and mood, written to Apple Health."
```

Then: edit the feature copy in `<slug>/index.html`, drop a hero image at
`<slug>/assets/hero.png`, add a card to the landing page (`index.html`), commit, push.
Run `./new-app.py --help` for all options. When a "coming soon" app ships, re-run with
`--appstore-id <id> --force` to wire the live buttons.

## Hosting (GitHub Pages)

* Repo: this one. **Settings → Pages → Build from `main` / root.**
* `CNAME` (already in the repo) sets the custom domain to `ludyem.dev`.
* Tick **Enforce HTTPS** once the certificate is issued (a few minutes after DNS resolves).

## DNS (Porkbun)

In Porkbun's DNS for `ludyem.dev`, remove the parking records and add:

| Type | Host | Answer |
|------|------|--------|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `ludyemas.github.io` |

> **`.dev` requires HTTPS** — it's on the HSTS preload list, so browsers refuse plain
> HTTP. GitHub Pages issues a free TLS certificate automatically; just don't panic during
> the few minutes between DNS resolving and the cert being ready.

Optional: set up **email forwarding** in Porkbun so `support@ludyem.dev` and
`hello@ludyem.dev` (used across the pages) reach your inbox.

## Notes

* The Workouts App Store IDs are the live ASC records from the app's `project.yml`.
  Confirm each listing is live before announcing — if one isn't ready, flip its card in
  `workouts/index.html` to the "coming soon" style.
* `vitaview.app` stays its own separate site; the landing page links out to it.
* Mascot art (Rocky) comes from `~/Developer/asset-gen/pushup-mascot/`.

© Ludyem AS
