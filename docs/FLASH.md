# Flashing Lucy onto an SD card

Two paths: **portal-first** (phone setup) or **terminal injection** (SSID/token at flash time). They work together — injection is optional; the portal is always the recovery path.

## Prerequisites

- Raspberry Pi OS **Lite (32-bit)** for Pi Zero W v1.1, or **Lite (64-bit)** for Pi 4+
- [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to write the OS image
- SD card mounted so you can see the **boot** partition (`/Volumes/bootfs` on macOS)

## Quick flash (portal only)

After Imager finishes writing the OS, **before ejecting the SD**:

```bash
cd lucy-npc
./pi/flash.sh --boot /Volumes/bootfs
```

Eject, boot the Pi on a desk. If she has no WiFi yet:

1. Join WiFi network **`Lucy-Setup`** from your phone (open network)
2. Captive portal opens — pick your home WiFi and password
3. Pi reboots onto your network, clones Lucy, runs `install.sh`

## Full flash (inject WiFi + token from terminal)

```bash
./pi/flash.sh --boot /Volumes/bootfs \
  --ssid "HomeWiFi" \
  --wifi-pass "your-wifi-password" \
  --wifi-country US \
  --hostname lucy-zero \
  --ssh-key ~/.ssh/id_ed25519.pub \
  --engine live_http \
  --lucy-token "$(openssl rand -hex 24)"
```

Or via environment:

```bash
LUCY_SSID=HomeWiFi LUCY_WIFI_PASS=secret ./pi/flash.sh --boot /Volumes/bootfs
```

The script prints a generated `LUCY_STATUS_TOKEN` if you did not pass one. Save it — that is the hatch admin passphrase for `:8787` on the LAN.

### Flags

| Flag | Purpose |
| --- | --- |
| `--boot PATH` | Mounted boot partition (required) |
| `--ssid` / `--wifi-pass` | Optional first-boot WiFi (skipped if omitted) |
| `--hostname` | Default `lucy-zero` |
| `--ssh-key` | Authorize your public key for `--user` (default `pi`) |
| `--engine live_http` | Pi Zero W (no Chromium) |
| `--engine live_public` | Pi 4+ with Playwright |
| `--no-wifi-portal` | Skip bundling portal stack |
| `--consent-auto-update` | Opt in to git pull updates on first install |

## What lands on the SD card

```
boot/lucy/
  lucy-flash.env           secrets + options (consumed on first boot)
  lucy-firstrun.sh          Pi one-shot hook
  first-boot.sh             clone + install orchestration
  install-wifi-portal.sh    NetworkManager + wifi-connect
  wifi-watch.sh             connectivity watchdog
  wifi-connect-rpi.tar.gz   offline portal binary (downloaded at flash time)
  *.service / *.timer       systemd units
boot/firstrun.sh            chains into lucy-firstrun.sh
```

## Portal recovery (steady state)

After install, `lucy-connect-watch.timer` runs every **45 seconds**. If connectivity fails **3 times in a row** (~2 minutes), **`Lucy-Setup`** comes back until you reconfigure WiFi.

Checks (in order): WiFi associated → IPv4 → default route → HTTP probe to Google connectivity check.

After the portal closes, a **5-minute cooldown** prevents flapping during router reboots.

## Pi Zero W v1.1 notes

- Flash **32-bit Lite** only
- Use `--engine live_http` (no Playwright/Chromium)
- First boot is slow on Zero W — allow several minutes

## Manual install (already on the LAN)

If you cloned the repo yourself instead of using `flash.sh`:

```bash
sudo ./pi/install.sh --wifi-portal --engine live_http --lucy-token "$(openssl rand -hex 24)"
```

## Troubleshooting

| Symptom | Check |
| --- | --- |
| No `Lucy-Setup` AP | `journalctl -u lucy-first-boot -b`; `systemctl status NetworkManager` |
| Portal never stops | Phone completed setup? `journalctl -u lucy-wifi-portal -b` |
| Lucy not installed | Needs internet to `git clone`; use portal or inject `--ssid` |
| Wrong engine | `/etc/lucy/env` → `LUCY_ENGINE=live_http`; `systemctl restart lucy` |

See also [HARDWARE.md](HARDWARE.md) and [RUNBOOK.md](RUNBOOK.md).
