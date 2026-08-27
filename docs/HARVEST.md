# Harvest awareness

Lucy can see **when her browser phones a known ad/broker/analytics host**. She cannot see what was inside the ciphertext, who bought the profile, or what the site’s *servers* sent later.

That is the honest ceiling. It is still useful: most “data brokers capturing your browsing” on a phone is this device making HTTPS requests to identity graphs, pixels, and bid wrappers.

## What she notices

On each `live_public` beat, Chromium’s request log is classified against [`data/trackers.json`](../data/trackers.json):

| Kind | Examples |
| --- | --- |
| ad | DoubleClick, Criteo, The Trade Desk, Xandr |
| broker | LiveRamp (`rlcdn.com`), Comscore, Lotame, ID5 cookie sync |
| analytics | GA, GTM, Segment, Mixpanel |
| replay | Hotjar, FullStory, Clarity (session replay is harvest) |
| sync | ID5 and similar identity graphs |

Only the **host**, vendor, kind, and count are stored. Query strings are dropped (they often contain emails, click ids, `fbclid`). First-party hosts (same site she opened) are not tagged. CDNs are ignored.

The hatch **Who took a piece** is the last look. **All looks** is the diary total and top ten names/hosts. Same per-look numbers are in each JSONL event’s `extra.harvest`.

## What she will miss

| Miss | Why |
| --- | --- |
| Server-side Conversion API / CAPI | The site’s backend talks to Meta/Google. No request leaves *this* Chromium. |
| CNAME-cloaked pixels | `metrics.weather.com` → LiveRamp in DNS. We see weather.com, not the broker. Needs DNS, not HTTP. |
| First-party analytics | A pixel on the same eTLD+1 looks like the article. |
| Encrypted bodies | HTTPS. We do not MITM ourselves. |
| Tracker not in the list | `data/trackers.json` is high-signal, not EasyList. Unknown beacons increment `beacons` only if the resource type is `ping`/`beacon`. |
| `live_http` | No JavaScript. Almost no pixels. |

Pi-hole on the same LAN can catch **DNS** for the whole house, including CNAME tricks Lucy will miss. They stack: Lucy = this body’s browser; Pi-hole = the resolver. Lucy should not become a network tap.

## Not a blocklist

This is awareness, not an ad blocker. Blocking pixels would change the art (and the fingerprint). She watches. She does not starve the exchange unless you do that somewhere else.
