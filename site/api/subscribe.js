// POST {email, website (honeypot), src} → GHL contact tagged LIBRARY_TAG (default free-library) + <tag>-src-<src>.
// Your GHL welcome workflow triggers on LIBRARY_TAG. Env (Vercel project settings): GHL_API_KEY, GHL_LOCATION_ID, LIBRARY_TAG.
// Upsert by email only, then add tags with the tags endpoint, so existing contacts keep their tags.
const GHL = "https://services.leadconnectorhq.com";
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const TAG = process.env.LIBRARY_TAG || "free-library";

module.exports = async (req, res) => {
  if (req.method !== "POST") return res.status(405).end();
  const { email, website, src } = req.body || {};

  if (typeof website === "string" && website.trim()) return res.json({ ok: true }); // bot

  const e = typeof email === "string" ? email.trim() : "";
  if (!e || e.length > 254 || !EMAIL_RE.test(e)) {
    return res.status(400).json({ error: "That email doesn't look right. Mind checking it?" });
  }
  const s = (typeof src === "string" ? src : "").toLowerCase().replace(/[^a-z0-9.-]/g, "").slice(0, 40) || "direct";

  const headers = {
    Authorization: `Bearer ${process.env.GHL_API_KEY}`,
    Version: "2021-07-28",
    "Content-Type": "application/json",
  };
  const call = (path, body) =>
    fetch(GHL + path, { method: "POST", headers, body: JSON.stringify(body), signal: AbortSignal.timeout(10_000) });

  try {
    const up = await call("/contacts/upsert", { locationId: process.env.GHL_LOCATION_ID, email: e });
    const id = up.ok && (await up.json()).contact?.id;
    if (!id) throw new Error(`upsert ${up.status}`);
    const tg = await call(`/contacts/${encodeURIComponent(id)}/tags`, { tags: [TAG, `${TAG}-src-${s}`] });
    if (!tg.ok) throw new Error(`tags ${tg.status}`);
    return res.json({ ok: true });
  } catch (err) {
    console.error(`subscribe: GHL failed (${err.message})`); // status only, never token or body
    return res.status(502).json({ error: "saved-failed" });
  }
};
