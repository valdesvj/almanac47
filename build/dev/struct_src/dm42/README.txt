STRUCT builds for the old DM42 with the C47 firmware - NOT RELEASED
===================================================================

NAVLITTLE.txt (the program ALMA47), NAVINIT_LITTLE.txt (NAVINIT) and MOON47.txt: the v2.2.0 STRUCT programs for
the old DM42 (64 KiB), written within the limit of the old-DM42 firmware builds that have STRUCT: at most 10 IF,
10 DO and 10 REPEAT in each program and 10 structures open at once (src/c47/programming/structured.h).

They are not in v2.2.0: the C47 firmware published for the old DM42 has ATEXT and GRFNT but NO STRUCT.

  firmware                                           ATEXT  GRFNT  STRUCT
  00.109.05.00a0.ALPHA or later, C47 / R47, DM42n     in     in     in (255 a series per program, 63 open)
  the same release, old DM42: pkg4 (the only one      in     in     OUT
    published; the CI builds DMCP_PACKAGE 4)
  old DM42 packages 1-3 (built from the sources,      in     in     in, 10 a series per program, 10 open
    not published)
  00.109.04.00b0 and older (every calculator)         out    out    out

Checked 2026-10-11 in the firmware sources (src/c47/defines.h of the release branch 00.109.05.00a0.ALPHA and of
master 9fb8f6316: package 4 #undef OPTION_STRUCTURED_PGM; OPTION_ATEXT and OPTION_ATEXT_FONTS in the block common to
packages 1-4) and in the published file c47-dmcp-pkg4-00.109.05.00a0.ALPHA.zip (C47.pgm holds the GRFNT font names,
code built only with OPTION_ATEXT_FONTS, which needs OPTION_ATEXT). Master of 8 Oct (b160a7b60) had ATEXT, GRFNT
and STRUCT off for the old DM42; master of 10 Oct has them as in the release.

Old-DM42 users: the NAVLITTLE without STRUCT (build/dm42/, and the "DM42 with the C47 firmware" zip of v2.0.0) needs
only ATEXT and GRFNT. These STRUCT builds are ready for a DM42 firmware with STRUCT: tests/test_struct_src.py checks
them pixel for pixel (NAVLITTLE against build/dm42/, MOON47 against the main MOON47) and tests/test_fw_c47.py runs them
in the firmware simulator (which has STRUCT).

  NAVLITTLE  programs_struct/little/NAVLITTLE.txt (tools/build_little_struct.py, once from build/dm42/NAVLITTLE.txt);
             largest program 6 IF, 2 DO, 1 REPEAT; search work -57 %; 7 302 bytes
  MOON47     tools/build_release_c47.moon_dm42: the STRUCT MOON47 with 7 of its 17 IF as test + XEQ of a routine:
             10 IF, 5 DO, 6 REPEAT; 4 487 bytes
Built by python3 tools/build_release_c47.py.
