"""Tracker host classification. No live network."""

from lucy.harvest import HarvestWatch, classify_host, load_catalog, registrable


def test_registrable() -> None:
    assert registrable("www.weather.com") == "weather.com"
    assert registrable("secure.scorecardresearch.com") == "scorecardresearch.com"


def test_doubleclick_on_weather_is_harvest() -> None:
    catalog = load_catalog()
    hit = classify_host("stats.g.doubleclick.net", "weather.com", catalog)
    assert hit is not None
    assert hit["vendor"] == "Google"
    assert hit["kind"] == "ad"


def test_first_party_is_not_harvest() -> None:
    catalog = load_catalog()
    assert classify_host("weather.com", "www.weather.com", catalog) is None
    assert classify_host("s.w.org", "en.wikipedia.org", catalog) is None


def test_cdn_ignored() -> None:
    catalog = load_catalog()
    assert classify_host("www.gstatic.com", "weather.com", catalog) is None


def test_watch_drops_query_strings() -> None:
    watch = HarvestWatch("https://weather.com/")
    watch.see("https://pixel.facebook.com/tr?id=EMAIL_SHOULD_NEVER_BE_LOGGED&ev=PageView", "image")
    extra = watch.extra()
    assert extra["harvest_hits"] >= 1
    blob = str(extra)
    assert "EMAIL" not in blob
    assert "facebook.com" in extra["harvest"][0]["host"]


def test_liveramp_is_broker() -> None:
    catalog = load_catalog()
    hit = classify_host("idsync.rlcdn.com", "www.bbc.com", catalog)
    assert hit is not None
    assert hit["vendor"] == "LiveRamp"
    assert hit["kind"] == "broker"
