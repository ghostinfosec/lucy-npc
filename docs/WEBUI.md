# The hatch

Bound with the daemon, laptop or Pi. [http://127.0.0.1:8787/](http://127.0.0.1:8787/)

```bash
# while she runs (default):
# http://127.0.0.1:8787/

# hatch only, no looks:
lucy-daemon --ui-only
```

On a laptop, loopback with an empty `LUCY_STATUS_TOKEN` has no login. On the LAN: `LUCY_STATUS_HOST=0.0.0.0` **and** a long `LUCY_STATUS_TOKEN` (the phrase). Cookie is HttpOnly + SameSite=Strict. POST is `/login` and `/logout` only. Anything else POST is 405.

The glass shows the last look from the diary. `looking` means Chromium is in the loop. `still` means the hatch is up and she is not mid-look.

## Numbers

| Card | Meaning |
| --- | --- |
| Fetches | Browser requests during **this look** |
| Taken | Requests to hosts in `data/trackers.json` on **this look** |
| Weight | Sum of `Content-Length` on **this look** when the server sent one |

**Who took a piece** is this look. **All looks** is the diary: total taken, top ten vendors, top ten hosts.

A weather.com open can be dozens of fetches. Harvest is host-only. [HARVEST.md](HARVEST.md).
