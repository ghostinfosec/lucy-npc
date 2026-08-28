# Lucy OS image (pi-gen)

Official **Lucy Ghost Zero** Raspberry Pi OS images. Flash one file; boot; join **`Lucy-Setup`** from your phone if WiFi is not configured. No `git clone`, no apt on first boot.

## What is in the image

- Raspberry Pi OS Lite (Bookworm, armhf — Pi Zero W through Pi 3)
- NetworkManager + wifi-connect (pinned v4.4.6)
- Lucy preinstalled under `/opt/lucy` with `live_http` engine
- `lucy-connect-watch.timer` — opens **Lucy-Setup** after sustained connectivity loss
- SSH enabled (set password via Pi Imager advanced options, or use Imager SSH key)

## Flash (recommended)

1. Download **`lucy-zero-w.img.xz`** from [GitHub Releases](https://github.com/ghostinfosec/lucy-npc/releases)
2. Verify SHA256 checksum from the release notes
3. Raspberry Pi Imager → **Use custom** → select the `.img.xz`
4. Optional: Imager advanced options → hostname `lucy-zero`, SSH public key
5. Boot on a desk — **`Lucy-Setup`** within ~10–20 min if no WiFi was preconfigured

```bash
# CLI flash (macOS/Linux)
rpi-imager --cli custom lucy-zero-w.img.xz /dev/diskN
```

## Build the image (maintainers)

Images are built in GitHub Actions with [pi-gen](https://github.com/RPi-Distro/pi-gen) via [pi-gen-action](https://github.com/usimd/pi-gen-action).

**On tag `v*`** or **workflow dispatch** → `.github/workflows/build-image.yml`

Local build (requires Debian/Ubuntu + Docker, ~30–60 min):

```bash
git clone https://github.com/RPi-Distro/pi-gen.git
# armhf: pi-gen master branch
export LUCY_SRC="$(pwd)"
# Copy stage-lucy into pi-gen and append to STAGE_LIST — see workflow for exact flags.
```

### Layout

```
pi/image/
  chroot-install.sh       # runs inside pi-gen chroot; bakes Lucy + portal
  stage-lucy/               # pi-gen custom stage
    EXPORT_IMAGE
    00-pkg/00-packages      # NetworkManager, python3, …
    01-lucy/00-run.sh       # copy repo into rootfs
    01-lucy/01-run-chroot.sh
```

## vs `./pi/flash.sh`

| | **Lucy OS image** | **flash.sh on stock Pi OS** |
|---|---|---|
| Audience | Clone-realistic, stuffed animal | Developers, quick iteration |
| First boot | Portal-only, no apt | May need bundled debs / WiFi |
| Updates | `lucy-update` / re-flash image | `git pull` on Pi |

Both paths converge after onboarding: Lucy daemon + Lucy-Setup recovery.

See also [FLASH.md](../docs/FLASH.md) (stock SD + flash.sh) and [HARDWARE.md](../docs/HARDWARE.md).
