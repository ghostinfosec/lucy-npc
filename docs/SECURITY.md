# Security and SDLC

Lucy should be **dumb if hacked** and **strict while honest**.

A compromised Lucy is a stuffed animal whose Chromium visits Wikipedia. That is the blast radius. She is not a pivot box, not a credential jar, not a remote-control fleet.

## Top 10 is not a program

OWASP Top 10 is **awareness**. It is the shared language for “what keeps showing up,” not a requirements list and not a test plan.

What 2026 web work actually uses:

| Layer | Thing | Job |
| --- | --- | --- |
| Awareness | [Top 10:2025](https://owasp.org/Top10/2025/) | Shared language. We map to it. We do not “implement the Top 10.” |
| Requirements | [ASVS 5.0](https://owasp.org/www-project-application-security-verification-standard/) **Level 1** | The checklist. Verifiable “must / must not.” |
| How to test | [WSTG](https://owasp.org/www-project-web-security-testing-guide/) | How a human or pipeline probes those requirements. |
| APIs | [API Top 10](https://owasp.org/API-Security/) | BOLA/BFLA, object IDs, function-level auth. Applies even to two routes. |
| Supply chain | [SLSA](https://slsa.dev/) + SBOM (CycloneDX/SPDX) + lockfiles | Now Top 10 **A03**. Highest incidence, worst CVE coverage. |
| How we cut releases | [NIST SSDF](https://csrc.nist.gov/projects/ssdf) | PR → test → signed tag. |
| Future holes | [LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/) | The unread API key. Treat as live the day it goes live. |

We do **not** take on SOC 2, PCI, full MASVS, or a WAF-as-product.

Tracked against this tree: [ASVS-L1.md](ASVS-L1.md). Update that table when code changes.

ASVS L2/L3 is for apps that hold other people’s money or medical records. Lucy holds a browsing diary of public URLs. L1 is the honest level. If `live_session` ever stores cookies, that slice jumps.

## Dumb if hacked (acceptance)

If someone owns the `lucy` OS user they can:

- Read JSONL of public URLs she already visited
- Drive Chromium at **allowlisted** hosts until you unplug her

They must **not** get:

- Logins (none in v0.1)
- A POST API that changes behavior
- RFC1918, link-local, or cloud metadata
- A push path to her sisters
- Root, by default

## Top 10:2025 mapped (awareness only)

SSRF sits under **broken access control**. Supply chain is a new #3. Fail-open is a new #10.

| 2025 | Name | Lucy |
| --- | --- | --- |
| A01 | Broken access control (incl. BOLA/BFLA/SSRF) | GET-only status. LAN bind needs a token. Allowlist is the SSRF control. No object IDs that mean “another Lucy.” |
| A02 | Security misconfiguration | No `0.0.0.0` without a token. `lucy` user, not root. Hatch: nosniff, DENY frame. Playwright extra is opt-in. |
| A03 | Software supply chain failures | Pin Python extras, Dependabot. Signed tags + SHA256 + cosign before a slot flip. GitHub Actions must not be a second origin. |
| A04 | Cryptographic failures | HTTPS-only fetches. No home-rolled crypto. Cosign, not a DIY JWT. |
| A05 | Injection | Persona JSON is data. URLs parsed before fetch. No `eval`, no shell-from-network. |
| A06 | Insecure design | The browser is a confused deputy on purpose. No command channel is the design. |
| A07 | Authentication failures | No user accounts. Token is a capability. |
| A08 | Software or data integrity | Dual slot. `/etc/lucy` is not overwritten. Integrity of *data* (persona, allowlist) is root-owned. |
| A09 | Logging and alerting failures | JSONL is the body. No tokens in logs. No off-box ship. Journald for crashes. |
| A10 | Mishandling exceptional conditions | Fail **closed**. Unknown origin → updater `--check` only. Redirect off-allowlist → drop the beat. Chromium crash → systemd restart, not a wider bind. |

## ASVS L1 — the slice that matters here

| Chapter (sense) | Must |
| --- | --- |
| Encoding / injection | No string-built shell, SQL, or browser script from untrusted input. |
| Validation | HTTPS, host allowlist, re-check after redirect. |
| Authorization | Status is read. Nothing is write. |
| Files | Persona/allowlist root-owned. Logs not world-writable. |
| Config | Loopback default. Secrets only in `/etc/lucy/env`, never in git. |
| Cryptography | TLS for live fetches and for origin pull. |
| Client | nosniff + DENY frame on the hatch. |
| API | Schema-small JSON. No mass assignment. 405 on POST. |
| Error handling | Fail closed (A10). Do not return stack traces to LAN. |

WSTG is how we test that: bootstrap misconfig, SSRF to metadata, verb tampering on `/status`, dependency confusion on the updater host pin.

## What Top 10 still doesn’t cover (and we still need)

1. **CI as an attacker** — `pull_request_target`, stolen `GITHUB_TOKEN`, unpinned Actions.
2. **Dependency confusion / typosquats** — lockfiles and hashed pins, not “latest.”
3. **MCP / LLM** — tool exfil, prompt injection. Stubs stay stubs until they have their own threat model.
4. **Privacy of the body log** — URL history stays on the Pi.
5. **Physical theft** — sculpture. SD is the credential the day `live_session` exists.
6. **Exception paths** — updater, Playwright crash, captive portal. Fail closed.

## Pi daemon

- Bind loopback unless a token is set.
- No POST except login/logout.
- Allowlist at load, at fetch, after redirect.
- `NoNewPrivileges`, `PrivateTmp`. Chromium blocks `ProtectSystem=strict`.

## SDLC (origin)

1. PR. Allowlist diffs are firewall diffs.
2. `pytest` on every PR. No live-network tests in CI.
3. Tag. CI + cosign + `SHA256SUMS`. SBOM when the origin repo is real.
4. Canary Pi one day. Then timers.
5. Private report until a signed tag. No silent host adds.

## Secrets

v0.1: none required. `LUCY_MODEL_API_KEY` is unread. If you paste one, the SD is a secret.

## Threats we accept

- The body is stealable.
- Public sites can fingerprint the Pi’s Chromium. Casual ad tags may bucket her as mobile Chrome. Fraud / FingerprintJS-class scripts usually will not. See [FINGERPRINT.md](FINGERPRINT.md).
- GitHub can vanish. Last slot remains.
