# Hand-off: Oct 18, 2026 (cloud session -> terminal)

Details of each step: DEVELOPMENT_NOTES.md, sections "Oct 18, 2026 - Your stack and registers kept, keys 1-8 push a
body" and "Oct 18, 2026 - c47sim: R-CLR ranges, local flags, LASTx". The older hand-off (STRUCT source, forum files):
build/dev/struct_src/HANDOFF.md.

## Git state (main 1ca741d)
- Merged: v2.2.0 "Struct on Attack" (PR #72), the next version apart from v2.2.0 (stack-keys, 5839dab),
  PR #73 sim-flags (c47sim), PR #74 c47sim-rclr-flags-lastx.
- PR #74's commit (acbb25e) has no c47sim code: it added 14 files under tests/ (C64FX*, C64_ATXT, C64_DEBUG,
  FORUM_BUZZER, INDY*, MARCHA, MARIO*, WAKEUP_NEO) and tests/THANKS.txt, which CLAUDE.md says stays untracked.
  To untrack it (the file stays on disk), on a branch:
      git rm --cached tests/THANKS.txt      (and add tests/THANKS.txt to .gitignore)
  Decide whether the other 13 files belong in git.
- Remote branches already in main, can be deleted:
      git push origin --delete sim-flags c47sim-rclr-flags-lastx stack-keys
  (and handoff-oct18 once this note is merged)
- Locally: git checkout main && git pull && git fetch --prune; git branch -d <the merged branches>

## The next version (build/dev/next/, from programs_struct/next/; v2.2.0 untouched)
- python3 tools/build_next.py -> ALMA47.txt, ALMA47.p47u (and ALMA47.p47 with rejig)
- Your stack (8 levels) and LASTx kept (LocR 09 at NAV's level, RCL L / STO L); NAV in R07-R98 only, cleared at the
  end with 7.92 R-CLR (R00-R06, R99 yours); keys 1-8 on ALMANAC / SPLIT end with Z text, Y Zn, X Hc (program PICK).
- Tested in python/c47sim.py only (tests/test_struct_src.py: ALL PASSED). Still to do:
  1. rejig --validate=r47 build/dev/next/ALMA47.txt (size in bytes)
  2. the firmware test (tests/test_fw_c47.py) for the 8-level stack, R-CLR, keys 1-8
  3. on the calculator: every view, keys 1-8, the stack after 0 / after a key

## c47sim (python/c47sim.py, tests/test_c47sim.py)
- R-CLR as registers.c getRegParam: 0-99 sss + nn < 100 (0.99 = R00-R98, 1.99 error), nn = 0 to R99; 100-111
  X..K (108 = L = LASTx); 112+ local R.nn within the LocR; nn = 0 there an error (firmware runs past the range).
- Local flags SF CF FS? FC? FS?C FC?C .nn (or F.nn): from the level's first LocR (even LocR 00), dropped at RTN;
  without LocR an error in the sim (the firmware ignores them silently). FS?C / FC?C on global flags too.
- LASTx / LASTX push LASTx; RCL L / STO L.
- For Elements 47 (its python/elem47sim.py split() works around these): not checked from here (repo not in the
  cloud session's scope); check its flag spelling (.nn / F.nn) and that each level using local flags has a LocR.

## Tests (Oct 18)
- tests/test_c47sim.py, tests/test_struct.py (5.5 min), tests/test_struct_src.py (7 min): ALL PASSED.
- tests/test_navhopt.py fails on main too (block not found once: ['STO "M7V"', 'CLSTK']): old, not from this work.
