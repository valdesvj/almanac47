# C47_nav

Celestial navigation for the SwissMicros C47 / R47 calculator (RPN), with a PC
version and the base for a phone app (**Almanac 47**).

- **Install and run:** `QUICKSTART.txt` (load NAVFULL + NAVINIT, XEQ "INIT", delete the
  INIT program, XEQ "NAV"). NAV asks date, UT and DR once, computes the sky, then a
  graphic menu: 1 ALMANAC, 2 SPLIT, 3 SKY, 4 ANIM, 5 ALLSKY, 6 INFO, 0 END (+ back,
  ↑↓ ±1 hour, 9 SNAP). NAV uses the numbered registers and clears R00–R99 when it ends (v2.2.0; up to
  v2.1.0 they were saved and given back). NAVFULL is one program: NAV is its only global label, the routines
  are local labels with their names (`build/NAVFULL_LABELS.txt`, section 7 of the manual).
- **v2.1.0 "Supercharger", what changed inside:** `docs/OPTIMIZATIONS.md` (v2.0.0: Horner, n-vectors, the loops
  on ISG, the registers renumbered and kept; v2.1.0, section 7: the firmware's matrix and complex functions,
  the series' cos and sin by one complex eˣ, Hc Zn from the direction vectors, smaller code; MOON47 too).
- **Text on the graphics screen:** `programs/FONTS.txt` - PTXT (3x5), PTXB (5x7) and
  PTXS (the C47 status-bar font), with number printers; usable on their own.
- **Calculator programs:** `programs/` (start with `NAV`), commented versions in
  `programs_rem/` and `listings/`. See `README.txt` and `PROGRAM_MAP.txt`.
- **PC, native Python:** `python/native/c47pc.py` v1.5 (GTK window, PNG, text): the views
  ALMANAC CHART TEXT SKY SPLIT ANIM ALLSKY MOON, drawn as the C47 screens of Oct 2026 (MOON,
  the Moon phases, is on the PC only).
- **PC, reference viewer:** `python/c47view.py` runs the real calculator programs.
- **Firmware:** the C47 builds (`build/`, `build/dm42/`) need C47 / R47 firmware **00.109.05.00a0.ALPHA**
  (5 Oct 2026) or later, or one built from master on or after 30 Sep 2026 (ATEXT and GRFNT). For the
  older public firmware 00.109.04.00b0 use `Almanac47_C47_R47_fw0400b0_v1.1.0.zip` from the v1.1.0
  release. The Free42 builds (`build/free42/`) run on the stock DM42 / DM42n firmware.
- **MOON47, the Moon phase on its own:** one program, no NAV and no INIT: the phase as a disc, % lit,
  age, HP, SD and the next four phases (UT), from the clock. `build/MOON47` (C47 / R47),
  `build/dm42/MOON47` (DM42 with the C47 firmware), `build/free42/MOON47.raw` (Free42),
  `python/numworks/moon47.py`, `python/hpprime/moon47.py`; the PC: `python3 python/moon47.py`.
  The same formulas everywhere (`tools/build_moon47.py` writes them all from `python/moon47.py`):
  phases within 4 minutes, HP 0.03'. Each manual has a MOON47 section.
- **Calculator files:** `build/` (C47 / R47 with a firmware that has ATEXT and GRFNT: NAVFULL,
  NAVINIT_FULL / _FAST, TBL; the text written with ATEXT, only the body symbols drawn; NAVTXT is
  not in v2.x),
  `build/dm42/` (C47 on the old DM42: NAVLITTLE, Sun and stars), `build/free42/` (DM42 /
  DM42n stock Free42 firmware: NAVFULL, NAVLITTLE and their INITs, the screens of Oct 2026 with
  AGRAPH fonts); other builds in the
  `dev/` folders. Other calculators: `python/numworks/`,
  `python/hpprime/`. How the C47 and Free42 update the screen: `README.txt`, SCREEN UPDATE.
- **Manuals of the other calculators:** `docs/Almanac47_Free42_Manual.pdf`,
  `docs/Almanac47_NumWorks_Manual.pdf`, `docs/Almanac47_HPPrime_Manual.pdf`.
- **Manual:** `docs/C47_Nav_User_Manual.pdf` (part 1: NAV and the views, the map of the
  N01, N02 ... labels; part 2: each program with worked results).
- **C47 command reference:** `docs/reference/C47_Full_index.txt` (C47 team, GFDL).
- **Test:** `python3 tests/test_parity.py` and `tests/test_parity21.py` (native Python =
  calculator, pixel for pixel); `tests/test_f42_little.py` (Free42 = C47, needs `tools/f42`).
- **Notes for further work:** `DEVELOPMENT_NOTES.md`.
- **AI assistance transparency:** `AI_ASSISTANCE.md` describes how AI was used and the validation process.

Sun, Moon, planets and the 57 navigational stars (+ Polaris): GHA, Dec, Hc, Zn,
twilight, sunrise/sunset, meridian passage, Moon phase; almanac pages and horizon
charts drawn on the calculator screen.

## Author

By Victor Valdes (valdes.vj@gmail.com),

Thank you To the C43/C47 firmware developers and SwissMicros, and to @tangent for rejig, which made converting the .txt programs to .p47 easy. With the C47, the sky is the limit - literally. Written with the help of AI. See `AI_ASSISTANCE.md` for the responsible-use statement.

## Licence

GNU General Public License v3.0 or later (`LICENSE`), for the whole project. Exceptions:
`docs/reference/C47_Full_index.txt` (C47 team, GFDL) and the PTXS glyph bitmaps from the C47
firmware (GPL-3.0, `programs/LICENSE-PTXS.txt`). See `NOTICE`.

**Does not replace the Nautical Almanac.**
