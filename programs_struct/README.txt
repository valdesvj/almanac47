programs_struct/ - the C47 NAVFULL written with the C47 STRUCT commands (C47 / R47 only)

One file per program. IF ELSE ENDIF, DO WHILE ENDDO, REPEAT UNTIL, indented two spaces per open structure (ELSE and
WHILE on their opener's column), without the partner numbers (the build writes them). Code only: no REM lines.
The comments are in a separate file, build/dev/struct_src/NAVFULL_COMMENTED.txt: the same listing, numbered and
indented, with REM lines (each program, each global label's original name and job, who calls each local routine,
the XEQ IND tables).
No GTO of any kind: decisions and loops are structures, a code end shared by several branches is a small routine they
call (XEQ nn, then RTN), a program reached by name is called (XEQ "Nxx"). The speed work of build/dev/struct steps
21-41 is in it (PIXEL line mode, the box in GRMOD 1, HCZ with 4 trig, the equator on whole columns with M.GETM /
M.PUTM, the star order as the matrix SBR, PTXS and small routines written in place, unrolled box loops ...).

Rules the build checks (as the firmware's VALID): a test right before IF, WHILE and UNTIL; none right before ELSE,
ENDIF, DO, ENDDO, REPEAT (the firmware never skips them); nothing open at END or across RTN + LBL; a DO has its WHILE.
A loop that only RTN leaves is REPEAT ... 0 X≠0? UNTIL.

The labels on the calculator: only NAV keeps its name, the others are N01, N02 ... (their original names and jobs:
LABELS in tools/build_struct_src.py, build/NAVFULL_LABELS.txt). Local labels are 01, 02 ... in the order they
appear; the ones XEQ IND reaches (star numbers, character codes, body numbers) keep their numbers.

  python3 tools/build_struct_src.py     -> build/dev/struct_src/NAVFULL.txt (the file for the calculator)
                                           build/dev/struct_src/NAVFULL_COMMENTED.txt (to read)
  python3 tools/build_forum.py          -> build/forum/NAV.p47u, NAVINIT.p47u (for the PROGRAMS folder of the C47
                                           release: '@' header, main label = file name, only the FAST matrices)
  python3 tests/test_struct_src.py      the pages pixel for pixel build/dev/struct/18_hourglass; the forum files

Free42 has no STRUCT: build_free42.py keeps its sources in programs/.
