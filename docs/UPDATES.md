# Updates — pull only

Many bodies. They do not report to a mothership. They **pull**.

If an operator can push shell to a hundred stuffed animals, that is a botnet. Origin is a GitHub repo. Each body, on a jittered timer, asks whether there is a new tag it was allowed to take. If yes: fetch, flip a slot, keep its own memory.

See [fleet.svg](fleet.svg).

## Disk

```
/opt/lucy/current          -> slots/v0.2.0
/opt/lucy/slots/v0.1.0/
/opt/lucy/slots/v0.2.0/
/opt/lucy/.venv/
/etc/lucy/env              local, never replaced by an update
/etc/lucy/persona.json     local tastes
/etc/lucy/allowlist.json   copied from release; root-owned
/opt/lucy/logs/            body log
```

Core in the slot. Identity in `/etc/lucy`.

## Channel

| Channel | Who | What v0.1 actually does |
| --- | --- | --- |
| `git` | if you consented | TOFU `git fetch` of `v*` tags. Same trust as clone. |
| `signed` | not implemented | Fail closed. Cosign is not wired. |

`LUCY_UPDATE_ORIGIN=owner/repo` in `/etc/lucy/env`. Empty origin or `LUCY_AUTO_UPDATE=off`: the timer, if enabled, only logs status. v0.1 default. Consent: `sudo ./pi/consent-updates.sh owner/repo`.

## At 04:17 (plus jitter)

Consent **off**: log current slot, exit.

Consent **git** (`LUCY_AUTO_UPDATE=git`):

1. `git fetch` `https://github.com/<origin>.git` into `/var/lib/lucy/origin` (host pinned).
2. Check out the latest `v*` tag, or `LUCY_UPDATE_REF` if you extra-consented to a floating branch.
3. Copy into `/opt/lucy/slots/<tag>` after writing `SOURCE.json` + `SHA256SUMS`.
4. Flip `/opt/lucy/current`. Do **not** touch `/etc/lucy`.
5. Restart `lucy` yourself, or on next reboot. v0.1 does not `systemctl restart` from the updater.

Consent **signed**: fail closed. Cosign is not implemented.

`lucy-update --from-dir` is first flash / tests. `--from-git` pulls when a human runs it.

Origin cannot ask a Lucy to visit a URL, dump logs, or wake. Status HTTP is GET-only and local.

## If GitHub is gone

Keep a mirror. Change `LUCY_UPDATE_ORIGIN` on the bodies you still hold. Bodies you do not hold keep their last slot.

## Maintainer

1. PR to the origin repo.
2. Tests, allowlist review, no new private-range hosts.
3. Tag `v*`. That is what consented bodies fetch.
4. Watch a canary Pi for a day.
5. Then let the timer do the rest.

Cosign / GitHub Release artifacts are the next integrity step, not this one.
