# ludyem-waitlist (Cloudflare Worker)

Backs the "notify me at launch" email signup form on the Runway page
(`ludyem.dev/runway`), and any future app's waitlist form on this site. A `POST
/subscribe` with `{ app, email, wantsAndroid?, company? }` writes an entry to
the `WAITLIST` KV namespace, keyed `<app>:<email>`. Requests are rejected
unless they come from an allowed `Origin` (`ludyem.dev` / `www.ludyem.dev`),
rate-limited per IP via the `SUBSCRIBE_RL` binding, and a hidden `company`
field acts as a bot honeypot.

## Deploy

```bash
wrangler deploy
```

Run from this folder. Requires being logged into the Cloudflare account
**`f28dk74ky8@privaterelay.appleid.com`** (account id
`d151ea2f999ea12422270f34ae26f915`), the same account the rest of the
Ludyem apps use. Check with `wrangler whoami`; log in with `wrangler login`
if needed.

There is no build step and no npm dependencies checked in, this is a single
`src/index.js` file plus `wrangler.jsonc`. If `wrangler` isn't installed
globally, run it via `npx wrangler deploy` instead.

## Bindings

`wrangler.jsonc` declares:
- `WAITLIST`: KV namespace storing signups.
- `SUBSCRIBE_RL`: rate limit binding (5 requests / 60s per key).

Both already exist on the account; this config just re-attaches to them by
id/name, it does not create them.
