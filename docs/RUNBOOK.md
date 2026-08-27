# Runbook

Operate one Lucy. For a hundred, still operate *one at a time*. There is no fleet console on purpose.

Laptop (this directory, no systemd): [README.md](../README.md). Tastes: `data/personas/wool.json` and `data/allowlist.json`. Restart the daemon after edits.

The rest of this page is a Pi after `sudo ./pi/install.sh`.

## Daily

```bash
systemctl is-active lucy
curl -s http://127.0.0.1:8787/status
journalctl -u lucy -n 50 --no-pager
tail -n 20 /opt/lucy/logs/lucy.jsonl
```

Healthy: `awake: true` during her windows (7–9, 11–13, 17–23 in the persona timezone), `sleep` beats at 3am, recent `ok: true` opens to allowlisted hosts.

## First hour after install

1. Desk, not wool.
2. `sudo systemctl status lucy`
3. Open [http://127.0.0.1:8787/](http://127.0.0.1:8787/). The glass should show a look during her windows.
4. Confirm the JSONL URL host is on `/etc/lucy/allowlist.json`.
5. Then assemble. [HARDWARE.md](HARDWARE.md)

## She's quiet

| Symptom | Likely | Do |
| --- | --- | --- |
| inactive unit | crash loop | `journalctl -u lucy -b` |
| Chromium OOM | Pi 3 / 1GB | drop to `live_http` or a Pi 4 |
| all `ok: false` | no DNS / captive portal | fix Wi‑Fi; Lucy will not click "I agree" |
| asleep at noon | timezone / windows | persona `timezone` and `windows`; `--force-open` looks anyway |
| status 401 | LAN token | `Authorization: Bearer …` from `/etc/lucy/env` |

## Sleep her (art / houseguest)

```bash
sudo systemctl stop lucy
```

She is a stuffed animal again. Start with `sudo systemctl start lucy`.

## Change tastes

Edit `/etc/lucy/persona.json`. Hosts still have to pass `/etc/lucy/allowlist.json` (copied from the release). Restart `lucy`. Updates will not overwrite this file.

YouTube: a `/results?search_query=` URL means she searches, opens the first watch result, and tries to play. A `/watch?v=` URL still just opens that video. `live_http` only GETs the search page.

## Auto-updates (opt-in)

Off after `install.sh`. To consent, use **this** GitHub repo (`owner/name`):

```bash
sudo /opt/lucy/current/pi/consent-updates.sh ghostinfosec/lucy-npc
```

That is a **git** pull of tagged releases, same trust as clone, not cosign. Turn off with `--off`. New Python dependencies are not auto-`pip installed`; a human re-runs `pip install -e .[live]` or `install.sh` if `pyproject.toml` grew.

## LAN status

Default bind is `127.0.0.1`. Open [http://127.0.0.1:8787/](http://127.0.0.1:8787/) for the hatch. Loopback with an empty `LUCY_STATUS_TOKEN` skips the login. To see her from the couch, set `LUCY_STATUS_HOST=0.0.0.0` **and** a long `LUCY_STATUS_TOKEN` (that is the phrase). The process will refuse a public bind with an empty token. POST is login/logout only. Lucy does not take orders over HTTP.

See [WEBUI.md](WEBUI.md) and [FINGERPRINT.md](FINGERPRINT.md).

## Rollback

```bash
ls /opt/lucy/slots
sudo ln -sfn /opt/lucy/slots/<old-tag> /opt/lucy/current
sudo systemctl restart lucy
```

Persona and env stay in `/etc/lucy`.

## Decommission

```bash
sudo systemctl disable --now lucy lucy-update.timer
sudo rm -rf /opt/lucy /etc/lucy /var/lib/lucy
# shred the SD if she ever held live_session cookies
```

v0.1 holds no logins. If you later enable `live_session`, treat the SD as a credential.

## Do not

- Do not expose `:8787` to the internet.
- Do not put API keys in persona JSON.
- Do not point surfaces at RFC1918, metadata IPs, or `http://`.
- Do not run the daemon as root.
