# Lucy

A stuffed animal that goes online.

She sits on a table facing a cracked phone. The phone looks: weather, a recipe, a YouTube search. Ordinary hours, so a real silence is not a hole.

The body is a Raspberry Pi. One persona. Public HTTPS. Not a farm.

This directory **is** the repo. Clone it, stay here. Python **3.11+**. A terminal and internet are required. This is not a one-click app.

```bash
git clone https://github.com/ghostinfosec/lucy-npc.git
cd lucy-npc
```

The hatch is [http://127.0.0.1:8787/](http://127.0.0.1:8787/). That is the only page.

## Laptop

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[live]"
playwright install chromium        # downloads a browser
cp .env.template .env              # lucy-daemon reads .env from this folder
lucy-daemon
```

Open [http://127.0.0.1:8787/](http://127.0.0.1:8787/). Loopback with an empty token has no login.

She looks **7–9, 11–13, and 17–23** in `America/Detroit`. Outside those hours she is still; the hatch stays up. `--force-open` looks anyway.

```bash
make verify
```

pytest, a checksummed slot flip, LAN-bind refusal. Not a Pi.

## Pi

A second step: flash Raspberry Pi OS, sew a body, systemd. Not a first Linux project. [docs/HARDWARE.md](docs/HARDWARE.md).

From this directory, on the Pi:

```bash
sudo ./pi/install.sh
```

Auto-updates stay off until you say yes. Overnight on hardware is unproven. Cosign is not wired. CI on a public origin has not run.

See [docs/RUNBOOK.md](docs/RUNBOOK.md), [docs/ASVS-L1.md](docs/ASVS-L1.md).

## Docs

- [PRD](PRD.md)
- [Hardware](docs/HARDWARE.md)
- [Runbook](docs/RUNBOOK.md)
- [Hatch](docs/WEBUI.md)
- [Harvest](docs/HARVEST.md)
- [Costume](docs/FINGERPRINT.md)
- [Updates](docs/UPDATES.md)
- [Security](docs/SECURITY.md)
- [ASVS L1](docs/ASVS-L1.md)

## Holes (v0.1)

| Hole | Where |
| --- | --- |
| Logged-in session | `src/lucy/engines/live_session.py` |
| Model key | `LUCY_MODEL_API_KEY` — unread |
| MCP | `LUCY_MCP_ENABLED=false` |

## Disclaimer

Lucy is an **art project**, for **experimental purposes only**. Not a product, not cover you can rely on, not advice. Live looks hit real sites from your network; that traffic is yours. Do not use this to run a farm.

## License

MIT. Copyright (c) 2026 Northern Void, LLC.
