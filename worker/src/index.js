const ALLOWED_ORIGINS = new Set([
  "https://ludyem.dev",
  "https://www.ludyem.dev",
]);
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MAX_EMAIL_LEN = 254;
const MAX_APP_LEN = 40;

function corsHeaders(origin) {
  const allow = ALLOWED_ORIGINS.has(origin) ? origin : "";
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

function json(data, status, origin) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders(origin) },
  });
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }
    if (url.pathname !== "/subscribe" || request.method !== "POST") {
      return json({ ok: false, error: "not_found" }, 404, origin);
    }
    if (!ALLOWED_ORIGINS.has(origin)) {
      return json({ ok: false, error: "forbidden_origin" }, 403, origin);
    }

    // Only real /subscribe hits from an allowed origin reach here, so this is
    // the actual abuse surface (scripted spam, KV-write flooding), not the
    // background bot noise that 404s above.
    const ip = request.headers.get("CF-Connecting-IP") || "unknown";
    const { success } = await env.SUBSCRIBE_RL.limit({ key: ip });
    if (!success) {
      return json({ ok: false, error: "rate_limited" }, 429, origin);
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return json({ ok: false, error: "invalid_json" }, 400, origin);
    }

    const app = String(body?.app || "").trim().toLowerCase();
    const email = String(body?.email || "").trim().toLowerCase();
    const wantsAndroid = Boolean(body?.wantsAndroid);
    const company = String(body?.company || "").trim();
    if (company) {
      // Honeypot: bots that fill every field get a fake success, humans never see it.
      return json({ ok: true }, 200, origin);
    }
    if (!app || app.length > MAX_APP_LEN || !/^[a-z0-9-]+$/.test(app)) {
      return json({ ok: false, error: "invalid_app" }, 400, origin);
    }
    if (!email || email.length > MAX_EMAIL_LEN || !EMAIL_RE.test(email)) {
      return json({ ok: false, error: "invalid_email" }, 400, origin);
    }

    const key = `${app}:${email}`;
    const existing = await env.WAITLIST.get(key, "json");
    const record = {
      email,
      app,
      wantsAndroid,
      createdAt: existing?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    await env.WAITLIST.put(key, JSON.stringify(record));
    return json({ ok: true }, 200, origin);
  },
};
