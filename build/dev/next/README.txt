Almanac 47 - the next version (after v2.2.0, not released). C47 / R47 only.
============================================================================

The v2.2.0 release (build/c47/, build/forum/, programs_struct/) is not changed. This version is built from
programs_struct/next/ by tools/build_next.py:

  ALMA47.txt    the programs that stay on the calculator (convert with rejig to ALMA47.p47)
  ALMA47.p47u   the same as a rejig source: the '@' header and a ';' comment on each global label
  MOON47.txt    MOON47 on its own (convert with rejig to MOON47.p47)
  MOON47.p47u   the same as a rejig source, with the comments of the v2.2.0 MOON47.p47u

NAVINIT is that of v2.2.0 (build/c47/NAVINIT_FAST.txt / NAVINIT_FULL.txt).

New, compared with v2.2.0:
  - Your stack (X Y Z T, and A B C D with the 8-level stack) and LASTx are as before XEQ "ALMA47" when it ends.
  - ALMA47 uses the registers R07-R98 and clears only those when it ends (R-CLR 7.92): R00-R06 and R99 stay yours.
    The numbers in R43-R98 and the DR (R13 longitude, R14 latitude) as in v2.2.0, for the routines you can call
    after leaving with EXIT.
  - On ALMANAC and SPLIT a key 1-8 picks a body of the table (1 the Sun, 2-8 the next rows; a body below the
    horizon too). ALMA47 ends and pushes on your stack: Z its text (e.g. SUN Zn 216.7 Hc 54 11.6), Y its Zn,
    X its Hc, in decimal degrees.
  The other keys as v2.2.0. 9006 steps (v2.2.0: 8734).

MOON47, new compared with v2.2.0 (the same page and keys):
  - Your stack (X Y Z T, and A B C D with the 8-level stack) and LASTx are as before XEQ "MOON47" when it ends
    (v2.2.0 ended with a clear stack).
  - MOON47 uses the registers R07-R65 (v2.2.0: R03-R61, not cleared) and clears only those when it ends
    (R-CLR 7.59): R00-R06 and R66-R99 stay yours. 1465 steps (v2.2.0: 1436).

Tested in the C47 simulator only (tests/test_struct_src.py next_version): every page pixel for pixel v2.2.0, the
stack (4 levels in the simulator), LASTx and the registers, the keys 1-8 against the PC almanac (python/native);
MOON47 (tests/test_struct_src.py moon_next) its page pixel for pixel v2.2.0, the stack, LASTx and the registers.
Still to do: rejig, the firmware simulator, the calculator.

DOES NOT REPLACE THE NAUTICAL ALMANAC.
