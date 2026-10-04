KEYWAIT - the key wait of a graphics program on the C47 and in the PC simulator (Oct 2026)

Load KEYWAIT (rejig KEYWAIT.txt, or python3 tools/rejig47_atext.py tests/calc_keywait/KEYWAIT.txt), then:

  XEQ "KTK"   waits with a bare KEY? loop:        LBL 01 / KEY? 39 / GTO 01
  XEQ "KTP"   waits with PAUSE 50 and KEY?:       LBL 01 / PAUSE 50 / KEY? 39 / GTO 01

Both draw a screen; + (or any other key) is ignored, 1 draws the screen again, 0 ends (stack cleared).
"THIS SCREEN MUST STAY AS IT IS": after +, the screen must not change.

Unpatched PC simulator (master b8707a818): KTK gets the stack and the softkeys over its screen when the key is
RELEASED (btnReleased -> refreshScreen(117) while the program runs); KTP keeps its screen. The calculator never
calls btnReleased while a program runs (the run loop reads the keys), so both keep the screen there.

Why KTP works on both (firmware source, input.c / keyboard.c):
  C47      a key during PAUSE: pauseKeyExit sets the key code (KEY? reads it) and waits for the release.
  PC sim   a key during PAUSE: PGM_KEY_PRESSED_WHILE_PAUSED; PAUSE goes on until the release, which only
           sets PGM_RESUMING and returns: no repaint. KEY? then reads the key code.
Not PAUSE 99: on the C47 the end of PAUSE 99 sets SCRUPD_AUTO and repaints the normal screen (refresh 1201).
PAUSE 50 waits up to 5 s; with no key the loop starts the next PAUSE.

The dev NAV and MOON47 (build/dev/opt, C47) wait this way (tools/build_navopt.keywait). Tested in the unpatched
simulator on a headless display (sway + Xwayland, xdotool key down 150 ms / up, screenshots): NAV menu, ALMANAC,
CHART, SPLIT, the arrows and +, the same screens as the patched simulator; the release NAV gets the stack over
the menu on every ignored key. Still to check on the calculator: KTK and KTP, then NAV.
