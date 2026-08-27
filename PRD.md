# Lucy — PRD

**Version:** 0.1.0  
**Host:** Raspberry Pi  
**Surface:** GitHub + LAN hatch (`:8787`)  
**Status:** laptop MVP. Pi overnight unproven. Art project; experimental only.

## One sentence

Lucy is a stuffed animal that goes online so a real person does not have to look like they went dark.

## The art

Live network. Real TLS. Real CDNs. Real scroll against public pages billions of phones already touch.

A local simulator is a rehearsal. If the packets never leave the Pi, she is a prop.

## Impersonation

A lifestyle, not a victim.

| Yes | No |
| --- | --- |
| One persona. One household. One Pi. | Account farms, stolen names, engagement-as-a-service |
| Boring human-shaped sessions on the public internet | Mass-follow, mass-comment, political astroturf |
| Optional later: the operator's own logged-in profile | Creating fake identities at scale |
| Looks like someone left a phone playing | Looks like a botnet |

v0.1 is public HTTPS only. Logged-in mode is a stub: a Playwright `storage_state.json` the operator exports from their own browser.

## Problem

Empty accounts and silent devices are a signature. Lucy fills ordinary hours with ordinary garbage. The stuffed animal faces the cracked phone. The phone is working.

## Goals

1. Run unattended on a Raspberry Pi 4/5 under systemd.
2. Circadian live page opens, scrolls, and dwells.
3. JSONL of every action.
4. LAN hatch so a phone on the house network can see she is awake.
5. Typed holes for an API key and MCP. Do not call models in v0.1.

## Non-goals

- Multi-agent societies, million-user sims.
- Auto-creating platform accounts.
- Headless posting, liking, following, DMs.
- Selling cover as a service.
- A public marketing site.

## Users

| Who | Need |
| --- | --- |
| Operator | Install on a Pi, pick a persona, leave her running |
| Stranger | Clone, run on a laptop, read the hatch |

## Engines

| Engine | Where | Network | Notes |
| --- | --- | --- | --- |
| `local` | laptop, CI | none | Rehearsal. Same planner, fake fetches. |
| `live_public` | Pi (art) | yes | Playwright Chromium, phone viewport, public URLs. |
| `live_http` | Pi Zero | yes | httpx GET/HEAD, real TLS, no JS. |
| `live_session` | later | yes | Playwright + `storage_state.json`. Stub. |

Action space: `wake`, `open`, `scroll`, `dwell`, `skip`, `idle`, `sleep`.  
Stubbed: `like`, `follow`, `comment`, `login`.

## Surfaces

Public pages. Default mix is ordinary: weather, Wikipedia, a YouTube search that plays the first result, Reddit listings, a recipe site, a news homepage. The allowlist is a shape, not a moral filter.

## Constraints

- Pi 4/5, Raspberry Pi OS, Python 3.11+, Playwright Chromium. Pi Zero 2W is `live_http`.
- No secrets in git. `.env.template` only.
- Outbound live mode needs network. That is intended.

## Success

- Overnight on a Pi: sleep gaps, clustered evening scroll.
- Hatch at `:8787` says awake or asleep truthfully.
- A packet capture on the LAN shows SNI/CDN names that match the plan.
- Grep for `OPENAI_API_KEY` finds a stub, not a call.

## Open

Whether YouTube consent walls still stall a look after “Accept all.”
