# Almanac 47 and Zones 47 on the web

The Python reference of Almanac 47 (`python/nav.py`, `python/moon47.py`) in JavaScript (`nav.js`, line for line, the
same coefficients), with a one-page app, plus Zones 47's world time zones (github.com/valdesvj/zones47).

![The ALMANAC page](../docs/WEB_almanac.png)

## Run it

```bash
cd ~/opt/almanac47
google-chrome web/index.html          # or chromium / google-chrome-stable; it works as a file, no server needed
```
For a phone on the same network: `python3 -m http.server 8047 -d ~/opt/almanac47/web`, then `http://<the computer's
address>:8047`.

| Tab | |
|---|---|
| **Almanac** | the C47's ALMANAC page (ALMF): GHA Aries; the Sun and the brightest stars more than 10° high, GHA, Dec, Hc, Zn; nautical twilight, rise, meridian passage, set (UT and ZT), the Sun's SD; DAY / TWILIGHT / NIGHT; the Moon |
| **Sky** | the sky from the DR: zenith in the centre, north up, the 58 stars and the Sun (hover a star: Hc, Zn) |
| **Stars** | the 57 navigational stars and Polaris: SHA, GHA, Dec, Hc, Zn, brightness; sortable |
| **Sun** | GHA, Dec, SD, Hc, Zn now; the day's twilights, rise, meridian passage and set in UT and ZT |
| **Moon** | MOON47: the disc (northern or southern view), lit %, age, HP, SD, the next four phases in UT and ZT |
| **Zones** | ZONE47: the dot map in 24 columns of 15°, the 38 stops (the official offsets, −12 at sea), every stop's places with their local time and summer time now; your zone ▲; ← → the stop, ↑ ↓ the place |

The top: **Now** follows the clock (UT from the computer), or a date and a UT; ±1 h; the **DR** (`27 12.0N 049
42.0E` or `27.2 49.7`) and the **ZD** (zone description: ZT + ZD = UT; empty: from the DR's longitude).

## Data

`python3 tools/make_web_data.py [--zones ~/opt/zones47]` writes `web/data/navdata.js` from `python/navdata.py` and
`web/data/zones.js` from a Zones 47 checkout (its `python/zones.py`, IANA tzdata, and `python/worldmap.py`). The
places' local times and summer time come from the browser's own tz database (Intl), so they follow the rules in force.

## Checked

`python3 tests/test_web.py` (node): 150 random dates 1950-2100 and places against the Python: the Sun, the 58 stars
(1E-11°), 1050 events (1E-8 s), Hc / Zn, the ALMANAC page's text (the same, character for character), MOON47.

Not for navigation: check against the Nautical Almanac. By Victor Valdes, Master Mariner:
https://github.com/valdesvj/almanac47 and https://github.com/valdesvj/zones47
