# Hardware

Lucy is a Raspberry Pi and a dead phone in a stuffed animal. The animal is the sculpture. The Pi is the breath.

## Bill of materials (one Lucy)

| Part | Why | Notes |
| --- | --- | --- |
| Raspberry Pi 4 (2GB+) or Pi 5 | Live Chromium | Pi Zero 2W only if you accept `live_http` (no JS) |
| Official USB-C PSU | Don't starve Chromium | Cheap chargers reboot her at 2am |
| microSD 32GB (A2) | OS + slots | Keep a clone card labeled *previous* |
| Heatsink / small fan | Playwright cooks a Pi | |
| USB-C cable, short | Power in through a seam | Strain-relief inside the stuffing |
| Retired phone or cheap LCD | The face she stares at | Can be a dummy screen; the session does not need *this* panel |
| USB ethernet adapter (optional) | Skip home Wi‑Fi identity | |
| Stuffed animal, ~30–40cm | The body | Open a back seam, not the face |
| Needle, thread, velcro patch | Service hatch | You will open her again |
| Raspberry Pi OS (64-bit) | Bookworm or newer | Desktop image not required |

## Assembly

See [assembly.svg](assembly.svg). Short version:

1. Flash Raspberry Pi OS. Create user `pi`, enable SSH **on the LAN only**, then disable password SSH after keys work.
2. Open a back seam. Carve a pocket for the Pi so vents are not packed with wool.
3. Seat the phone/screen in the lap or against the chest, facing out. Dummy glass is fine.
4. Route USB-C out a back foot or a tagged "care label." Do not pierce the face.
5. Close with a velcro service hatch. Label the hatch internally: `lucy /opt/lucy`.
6. First boot on a desk, not inside the wool. Confirm `lucy-daemon` and a packet capture. Then dress her.

## Power and heat

Leave a thumb of air around the SoC. If she thermal-throttles, sessions look like a dying phone — which is almost on-theme, and also a crash loop. A tiny 5V fan in the hatch is allowed. It should not be louder than a household.

## Network

Default: home Wi‑Fi, MAC as-is. Optional: USB ethernet to a boring switch. Lucy's art is *ordinary* traffic. Do not put her on a VPN that makes her look like a datacenter.

## First software flash

On the Pi, after Raspberry Pi OS is up and on the LAN. This folder is the git root.

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/ghostinfosec/lucy-npc.git
cd lucy-npc
sudo ./pi/install.sh           # daemon on, auto-updates OFF
```

`install.sh` asks on a TTY. Non-interactive default is **no**. To consent at flash time:

```bash
sudo ./pi/install.sh --consent-auto-update --origin=ghostinfosec/lucy-npc
```

Or later:

```bash
sudo ./pi/consent-updates.sh ghostinfosec/lucy-npc
sudo ./pi/consent-updates.sh --off
```

Consent is git TOFU — the same trust as the clone. Signed GitHub releases are not wired yet. Updates replace `/opt/lucy/slots/*`. They do not replace `/etc/lucy` (persona, env).

Then: [RUNBOOK.md](RUNBOOK.md).

## Pi Zero variant

No Chromium. `LUCY_ENGINE=live_http`. Same allowlist, real TLS, thinner sculpture. Still live network. Still Lucy, quieter.
