Free42 (DM42 / DM42n stock firmware) NAVFULL with the screens of the C47 step 11 (branch struct-opt, Oct 2026)

Built from the release build/free42/NAVFULL.txt by  python3 tools/build_struct.py f42  (NAVFULL.txt and .raw).
Load it like the release, with the release Free42 NAVINIT_FULL / NAVINIT_FAST (build/free42/).

What changed (only what the C47 screens changed; Free42 keeps its own code for the rest):
  - the celestial equator every 6 deg on SKY and ANIM (60 dots) and every 9 deg on SPLIT and ALLSKY (40 dots), each
    dot 3 x 3 pixels as the C47 POINT (nine calls of the pixel routine N79 in place of four); CEQQ's cache rows
    follow (9 deg: rows 1-40, 6 deg: rows 121-180 of ALMQ);
  - ALLSKY's 58 stars exact (STR2 and CHCZ, as the C47 step 9 reads them from its cache) in place of the catalogue
    with a linear precession. Before the stars ALLSKY saves R07 R08 (the Sun from its CSUN call, two of STR2's
    inputs in the Free42 numbering) and calls CSUN again for the same time (a cache hit: STR2's inputs back); after
    them R07 R08 are given back.
Not needed on Free42: the structural steps, the matrix stars (the values agree with STR2 to 0.002'; no pixel
changes), ANIM's interpolation (no pixel changes) and its frame wait (Free42's ANIM has none).
NAVLITTLE: the C47 NAVLITTLE steps change no pixel, so the release Free42 NAVLITTLE stays as it is.

Checked: f42run against the C47 step 11 in the firmware PC simulator (NAVINIT_FULL), the menu, ALMANAC, SPLIT,
ALLSKY, INFO at 2026-10-04 25.2 N 55.2 E, 2031-03-15 33.5 S 18.25 E, 2004-06-21 60.1 N 24.55 E: 0 pixels different
on every screen (rebuilt after #64, which gave Free42 the firmware's fonts; before it the small differences of the
release pair remained). SKY and ANIM run until a key, so f42run takes no picture of them: they use the same equator
code as SPLIT and ALLSKY.
Size: 8475 steps, .raw 23542 bytes.
