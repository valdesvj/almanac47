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
- To merge (one commit each on main 1ca741d): moon-next (MOON47 of the next version), handoff-oct18 (this note).
      git fetch origin; git checkout main && git pull
      git merge --no-ff origin/moon-next -m "Merge moon-next: MOON47 of the next version"
      git merge --no-ff origin/handoff-oct18 -m "Merge handoff-oct18: hand-off notes"
      git push origin main
- Then delete the merged branches:
      git push origin --delete sim-flags c47sim-rclr-flags-lastx stack-keys moon-next handoff-oct18
      git fetch --prune; git branch -d <the ones that exist locally>

## The next version (build/dev/next/, from programs_struct/next/; v2.2.0 untouched)
- python3 tools/build_next.py -> ALMA47.txt, ALMA47.p47u (and ALMA47.p47 with rejig)
- Your stack (8 levels) and LASTx kept (LocR 09 at NAV's level, RCL L / STO L); NAV in R07-R98 only, cleared at the
  end with 7.92 R-CLR (R00-R06, R99 yours); keys 1-8 on ALMANAC / SPLIT end with Z text, Y Zn, X Hc (program PICK).
- Tested in python/c47sim.py only (tests/test_struct_src.py: ALL PASSED). Still to do:
  1. rejig --validate=r47 build/dev/next/ALMA47.txt and MOON47.txt (size in bytes)
  2. the firmware test (tests/test_fw_c47.py) for the 8-level stack, R-CLR, keys 1-8
  3. on the calculator: every view, keys 1-8, the stack after 0 / after a key

## MOON47 of the next version (branch moon-next)
- programs_struct/next/MOON47.txt -> build/dev/next/MOON47.txt, MOON47.p47u (python3 tools/build_next.py builds both
  ALMA47 and MOON47; build_struct_src.build_moon(NEXT) checks the block MOON_REGS and the R-CLR).
- LocR 09 at the start saves your stack (8 levels) and LASTx; the end gives them back instead of CLSTK.
- Registers moved + 4: v2.2.0 R03-R61 (incl. the two IND tables at base 54) -> R07-R65 (base 58), inside ALMA47's
  block; cleared at the end with R-CLR 7.59. R00-R06, R66-R99 yours. 1465 steps (v2.2.0 1436). Page and keys as v2.2.0.
- tests/test_struct_src.py moon_next: 16 dates / time zones, north and south, pixel for pixel v2.2.0, stack, LASTx,
  registers, M7 matrices: ALL PASSED. Simulator only: rejig, firmware test, calculator still to do.

## Updating rejig (CLAUDE.md: ~/opt/rpn read-only, build from a copy, install in ~/.local/bin)
The build line is not recorded in the repo: read the README of the copy (and write the line here once known).
      cd ~/opt/rpn && fossil update && fossil info | head -5 && fossil timeline -n 10
      rm -rf ~/build/rpn-rejig && mkdir -p ~/build && cp -a ~/opt/rpn ~/build/rpn-rejig && cd ~/build/rpn-rejig
      ls; cat README* rejig/README* 2>/dev/null | less          # the build instructions
      cp ~/.local/bin/rejig ~/.local/bin/rejig-0.34.1.bak       # keep the current one
      make (or the README's command); cp <new rejig> ~/.local/bin/rejig; rejig --version
- The patched rejig (CLAUDE.md): a fresh build has not the patch; apply it in the copy if still needed.
- Then: cd ~/almanac47 && python3 tools/build_next.py (with rejig it writes ALMA47.p47, MOON47.p47 and their bytes).

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
- moon-next: tests/test_struct_src.py ALL PASSED (8.5 min, with moon_next).
- tests/test_navhopt.py fails on main too (block not found once: ['STO "M7V"', 'CLSTK']): old, not from this work.
