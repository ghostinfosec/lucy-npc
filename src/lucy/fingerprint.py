"""What Lucy *claims* to be versus what a tracker can still see. No I/O."""

from __future__ import annotations

from lucy.models import Persona


def chromium_context_kwargs(persona: Persona) -> dict:
    """Playwright browser.new_context kwargs. Phone-shaped, not undetectable."""
    lang = persona.locale.replace("_", "-")
    short = lang.split("-")[0]
    return {
        "user_agent": persona.user_agent,
        "locale": persona.locale,
        "viewport": {
            "width": persona.viewport_width,
            "height": persona.viewport_height,
        },
        "timezone_id": persona.timezone,
        "is_mobile": True,
        "has_touch": True,
        "device_scale_factor": persona.device_scale_factor,
        "color_scheme": persona.color_scheme,
        "extra_http_headers": {
            "Accept-Language": f"{lang},{short};q=0.9",
            "Upgrade-Insecure-Requests": "1",
        },
    }


def chromium_launch_kwargs(headless: bool) -> dict:
    """Launch flags. Drops the obvious --enable-automation banner. Not stealth."""
    return {
        "headless": headless,
        "args": ["--disable-blink-features=AutomationControlled"],
        "ignore_default_args": ["--enable-automation"],
    }


def describe(persona: Persona, engine: str) -> dict:
    """Costume copy for the hatch. No I/O."""
    mobile = "Mobile" in persona.user_agent or "Android" in persona.user_agent
    if engine == "live_http":
        bucket = "a GET client. Not a phone."
        casual = "No. httpx is not Chrome. Ads see a bot or empty JS."
        fraud = "Yes, immediately."
    elif engine == "local":
        bucket = "rehearsal. Nothing left the machine."
        casual = "No costume. No weather."
        fraud = "n/a"
    else:
        bucket = "a tired phone. Chrome costume." if mobile else "desktop Chrome"
        casual = "Most tags stop at the costume."
        fraud = (
            "The ones that look harder see Linux Chromium in wool — JA3, Client Hints, SwiftShader. "
            "They will not think this is a Pixel."
        )
    return {
        "engine": engine,
        "presents_as": bucket,
        "user_agent": persona.user_agent,
        "viewport": f"{persona.viewport_width}x{persona.viewport_height}@{persona.device_scale_factor}dpr",
        "timezone": persona.timezone,
        "locale": persona.locale,
        "casual_ad_tags": casual,
        "fingerprint_and_fraud": fraud,
        "ip_note": "Home IP keeps the story. A VPS ends it.",
        "not_packets": "Looks are fetches the browser made. Not packets. Not radio.",
    }
