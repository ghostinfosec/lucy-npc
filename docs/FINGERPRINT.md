# Device signatures — will ads think she is a phone?

Short answer: **casual tags often will; fingerprinting and fraud systems often will not.**

Lucy sets a Pixel-shaped story: Android Chrome UA, 412×915 viewport, touch, DPR, timezone, `Accept-Language`. That is enough for a lot of ad pixels that only read UA + screen. It is not enough for anyone who looks at the actual client.

| Signal | What we send | What they can still see |
| --- | --- | --- |
| User-Agent | Pixel 8 / Chrome Mobile | Fine, if they stop here |
| Viewport + touch | Phone | Fine |
| Client Hints | We do not fully control `sec-ch-ua-platform` | Chromium-on-Linux often says Linux, not Android |
| TLS JA3/JA4 | — | Linux Chromium, **not** iOS Safari, not Android Chrome Play |
| WebGL / GPU | — | SwiftShader, V4L, or a Pi GPU — not Adreno/Mali-as-Pixel |
| `navigator.webdriver` | We drop `--enable-automation` | Playwright is still a known fingerprint |
| IP / ASN | Home Wi‑Fi | Helps. Cloud/VPS ends the costume |
| `live_http` | Same UA string on httpx | **Not a browser.** No JS, no ads-as-phone |

Casual tags often bucket her as mobile Chrome on home Wi‑Fi. A fraud vendor, a bank, or FingerprintJS will treat her as **headless Chromium on a small Linux board**. That mismatch is expected. Do not promise invisibility.

`live_http` (Pi Zero) should never be described as a phone to an ad system. It is a GET client.

Hatch shows UA and viewport. JA3 and GPU live on `/api/fingerprint`. [WEBUI.md](WEBUI.md).
