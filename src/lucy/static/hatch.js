const $ = (id) => document.getElementById(id);

async function api(path) {
  const res = await fetch(path, { credentials: "same-origin" });
  return { res, data: await res.json().catch(() => ({})) };
}

function fmtBytes(n) {
  if (!n) return "0";
  if (n < 1024) return n + " B";
  if (n < 1048576) return (n / 1024).toFixed(1) + " KB";
  return (n / 1048576).toFixed(1) + " MB";
}

function hostOf(url) {
  if (!url) return "";
  try { return new URL(url).hostname.replace(/^www\./, ""); }
  catch { return url; }
}

function ago(ts) {
  const ms = Date.parse(ts);
  if (!Number.isFinite(ms)) return "";
  const min = Math.max(0, Math.round((Date.now() - ms) / 60000));
  if (min < 2) return "just now";
  if (min < 60) return min + " minutes ago";
  const hr = Math.round(min / 60);
  if (hr === 1) return "an hour ago";
  if (hr < 36) return hr + " hours ago";
  const days = Math.round(hr / 24);
  if (days === 1) return "a day ago";
  return days + " days ago";
}

function clock(ts) {
  return (ts || "").replace("T", " ").replace("Z", " UTC");
}

function glass(place, fetches, taken) {
  $("glass-place").textContent = place || "";
  if (!place) {
    $("glass-stats").textContent = "";
    return;
  }
  const bits = [];
  if (fetches) bits.push(fetches + " fetches");
  if (taken) bits.push(taken + " taken");
  $("glass-stats").textContent = bits.join(" · ");
}

async function paint() {
  const status = await api("/api/status");
  if (status.res.status === 401) {
    $("login").classList.remove("hidden");
    $("dash").classList.add("hidden");
    glass("", 0, 0);
    return;
  }
  $("login").classList.add("hidden");
  $("dash").classList.remove("hidden");
  const metrics = await api("/api/metrics");
  const events = await api("/api/events");
  const fp = await api("/api/fingerprint");
  const s = status.data;
  const m = metrics.data;
  const list = events.data.events || [];
  const diaryLive = !!(m.live_capture || (m.http_requests || 0) > 0 ||
    list.some((e) => String(e.engine || "").startsWith("live")));
  const looking = !!s.awake;
  const last = m.last_open || list.filter((e) => e.action === "open" && e.url).slice(-1)[0] || null;
  const persona = s.persona || "lucy";
  $("who").textContent = persona + (looking ? " · looking" : " · still");

  const fetches = last
    ? (last.http_requests || (last.extra && last.extra.http_requests) || m.http_requests || 0)
    : (m.http_requests || 0);
  const taken = last
    ? (last.harvest_hits || (last.extra && last.extra.harvest_hits) || m.harvest_hits || 0)
    : (m.harvest_hits || 0);
  glass(last ? (hostOf(last.url) || last.url) : "", fetches, taken);

  const harvest = (last && (last.harvest || (last.extra && last.extra.harvest))) || [];
  const lookBytes = last
    ? (last.http_bytes || last.bytes || (last.extra && last.extra.http_bytes) || 0)
    : (m.http_bytes ?? 0);

  const tape = $("tape");
  tape.classList.remove("hidden");
  if (diaryLive && last) {
    const place = hostOf(last.url) || last.url;
    const when = looking ? "now" : ago(last.ts);
    tape.textContent = [place, when, fetches + " fetches", taken ? taken + " taken" : null]
      .filter(Boolean).join(" · ");
  } else if (!list.length) {
    tape.textContent = "No looks yet.";
  } else {
    tape.textContent = looking ? "looking" : "still";
  }

  const liveCards = diaryLive
    ? [["Fetches", fetches], ["Taken", taken], ["Weight", fmtBytes(lookBytes)]]
    : [["Looks", m.beats ?? 0], ["Taken", m.harvest_hits ?? 0], ["Weight", fmtBytes(m.http_bytes ?? 0)]];
  $("cards").innerHTML = liveCards.map(([k, v]) => `<div class="card"><span>${k}</span><b>${v}</b></div>`).join("");
  $("unit").textContent = diaryLive
    ? (fetches + " fetches. " + taken + " taken.")
    : (m.unit || "No looks yet.");
  $("rows").innerHTML = list.slice().reverse().map((e) => {
    const cls = e.ok ? "ok" : "fail";
    const extra = e.extra || {};
    const rowFetches = extra.http_requests;
    const rowTaken = extra.harvest_hits;
    let act = e.action === "sleep" ? "asleep" : (e.action || "");
    if (e.action === "open" && rowFetches) act = "looked";
    let capture = "";
    if (rowFetches) capture = rowFetches + " fetches" + (rowTaken ? " · " + rowTaken + " taken" : "");
    else if (e.engine && String(e.engine).startsWith("live")) capture = e.engine;
    return `<tr><td>${clock(e.ts)}</td><td>${act}</td><td class="url">${e.url || "—"}</td><td class="${cls}">${e.ok ? capture : "miss"}</td></tr>`;
  }).join("");
  const byVendor = {};
  const byHost = {};
  for (const hit of harvest) {
    const vendor = hit.vendor || "unknown";
    const host = hit.host || "";
    const n = hit.count || 1;
    byVendor[vendor] = (byVendor[vendor] || 0) + n;
    if (host) byHost[host] = (byHost[host] || 0) + n;
  }
  const vendorRows = Object.entries(byVendor).sort((a, b) => b[1] - a[1]);
  const hostRows = Object.entries(byHost).sort((a, b) => b[1] - a[1]);
  $("vendors").innerHTML = vendorRows.map(([name, n]) => `<tr><td>${name}</td><td>${n}</td></tr>`).join("")
    || "<tr><td colspan='2'>Nobody on the list took a piece this look.</td></tr>";
  $("brokers").innerHTML = hostRows.map(([host, n]) => `<tr><td class="url">${host}</td><td>${n}</td></tr>`).join("");
  const pileTaken = m.harvest_hits ?? 0;
  $("pile").textContent = pileTaken + " taken.";
  $("pile-vendors").innerHTML = (m.vendors || []).slice(0, 10).map((v) => `<tr><td>${v.vendor}</td><td>${v.hits}</td></tr>`).join("")
    || "<tr><td colspan='2'>—</td></tr>";
  $("pile-hosts").innerHTML = (m.broker_hosts || []).slice(0, 10).map((h) => `<tr><td class="url">${h.host}</td><td>${h.hits}</td></tr>`).join("");
  const f = fp.data;
  $("fp-present").textContent = f.presents_as || "";
  $("fp-ua").textContent = (f.user_agent || "") + " · " + (f.viewport || "");
}

$("login-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const body = new URLSearchParams({ token: $("token").value });
  const res = await fetch("/login", { method: "POST", credentials: "same-origin", body });
  if (!res.ok) { $("err").textContent = "that is not the phrase"; return; }
  $("err").textContent = "";
  paint();
});
$("logout-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  await fetch("/logout", { method: "POST", credentials: "same-origin" });
  paint();
});
paint();
setInterval(paint, 15000);
