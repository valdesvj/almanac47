# Hand-off: branch c47-struct-src (Oct 10-11, 2026)

For the next session (terminal). Details of every step: DEVELOPMENT_NOTES.md, the sections from
"Oct 10, 2026 - STRUCT: the C47's IF / DO / REPEAT in NAVFULL" on.

## Branches
- c47-struct - the step builds build/dev/struct/19_struct ... 41_layout (GTO -> STRUCT by the converter, then the
  speed steps). tests/test_struct.py. Kept as the record; not to be merged as is.
- c47-struct-src - THE ONE TO CONTINUE: the STRUCT source and the forum files. Last commit: see git log.
- claude/task-htdu76 - one unrelated commit (build/dev/moon moved into build/dev/struct/moon): can be dropped.
- Nothing merged; Victor opens the PRs. Git state on Oct 11: nothing uncommitted, every branch pushed;
  c47-struct-src is 16 commits ahead of main (c47-struct's 8 + 8), c47-struct 8, claude/task-htdu76 1.
  To drop claude/task-htdu76:  git push origin --delete claude/task-htdu76;  git branch -D claude/task-htdu76

## To continue in the terminal
```
git fetch origin c47-struct-src
git checkout -b c47-struct-src origin/c47-struct-src     (or: git checkout c47-struct-src; git pull)
python3 tools/build_struct_src.py    # NAVFULL + MOON47 from programs_struct/
python3 tools/build_forum.py         # build/forum/ALMA47.p47u, NAVINIT.p47u, MOON47.p47u
python3 tests/test_struct_src.py     # all the checks
```

## What is on c47-struct-src
- programs_struct/ - the C47 source in STRUCT, code only (no REM), indented, no partner numbers, no GTO:
  26 NAV programs (ORDER in tools/build_struct_src.py) + MOON47.txt (one program, LBL "MOON47" the only global).
  NAV: 18_hourglass converted without copies + the speed steps 21-41 + layout; 8859 steps, 126 structures.
  MOON47: 1436 steps (1540 in 3 programs), search work -28 %.
- tools/build_struct_src.py -> build/dev/struct_src/NAVFULL.txt, NAVFULL_COMMENTED.txt, MOON47.txt,
  MOON47_COMMENTED.txt (comments only in the *_COMMENTED files; LABELS / MOON_LABELS hold the names).
- tools/build_forum.py -> build/forum/ALMA47.p47u (NAV's main label named ALMA47), NAVINIT.p47u (INIT named
  NAVINIT, FAST matrices only; the header says NAVINIT_FULL and TBL exist but need more memory), MOON47.p47u.
  Format of the C47 release's res/PROGRAMS (BUILD.md there): '@ Index:' header, file name = main label.
- build/forum/C64FX.p47u - Victor's buzzer demo, written by hand (not built): his original code (GTO loops),
  the '@' header and '#' comments from C64FX_rem.
- tests/test_struct_src.py - the source rules, every NAV page pixel for pixel 18_hourglass (3 places, menu keys,
  16 random dates and places), MOON47 pixel for pixel build/dev/moon/1_labels and python/moon47.py (16 dates,
  north and south), the forum files' headers and steps. ALL PASSED at the last commit.
- tools/build_struct.py: pixel_lines and star_order also take the source's shapes (test_struct.py still passes).

## Pending (Victor)
1. rejig every forum file (no rejig in the cloud session): cd build/forum; rejig ALMA47.p47u (also NAVINIT,
   MOON47, C64FX). Check: the "..." quotes (the release examples use '...'), the '#' comment lines, the
   STRUCT numbers ("IF 01"), and the sizes in bytes (python3 tools/build_struct_src.py prints them with rejig).
2. On the calculator: ALMA47 + NAVINIT (FAST) - every view, the arrows, timing against 18_hourglass / 41_layout;
   MOON47; C64FX (its '@ Tested:' line is computed: about 15 s, 8.6 + 3 + 3.4).
3. The firmware test (tests/test_fw.py on T47) for the new NAVFULL and MOON47.
4. Check the forum headers: '@ Version: 2.2' and '@ Source:' (the GitHub link) are guesses; Author Victor Valdes.
5. Ask jaymos whether he takes them (line counts: ALMA47 8948, NAVINIT 6564, MOON47 1457, C64FX 282).
6. PR from c47-struct-src into main when it is checked; decide about claude/task-htdu76.

## Open ideas, not done
- Comments for the local routines of NAV (the commented listing names only the global labels and the callers).
- MOON47: inlining the two small routines c47struct.inline finds (+5 steps, -3 % search): left out (compact).
- Mbrot.p47u (a forum program by someone else, not in the repo): STRUCT would NOT make it faster (the inner loop
  becomes DO ... WHILE ... WHILE ENDDO: 11 steps a round instead of 10, ENDDO searches twice). What would:
  (a) skip the main cardioid and the period-2 bulb before iterating - 58 % of the inner rounds for its settings
  (400 x 240, 25 rounds, bound sqrt 2), the same image (no escaping pixel inside them: all 96000 checked);
  only when -1.25 <= x <= 0.375; (b) dx = Xrange / SXMax and the row's imaginary part once (per run / per row) in
  local registers, not six named recalls a pixel. About 8 M -> 5 M steps a screen (estimate, not run: the sim has
  no TICKS / COMPLEX). Optional (c): mirror rows - its rows are one pixel off symmetric, so the image moves a row.
