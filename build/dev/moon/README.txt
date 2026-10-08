MOON47 for the C47 / R47 with the label rules of build/dev/struct (Oct 2026). C47 only; Free42 and the DM42 file
are not changed. Build again with:  python3 tools/build_moon47_struct.py

  0_speed/MOON47.txt    the input: build/MOON47.txt of the branch moon47-speed (59d01b4: the disc routine first, the
                        elongation of now computed once, -17 % CPU against v2.1.0, pages identical). Three programs:
                        MOON47, M7TX (text printers), M7SY (phase symbols). 4844 bytes.
  1_labels/MOON47.txt   + the three blocks no jump can reach removed (M7TX's LBL 14 15 19: NAV printers MOON47 does
                        not use, 11 steps); labels 01, 02 ... in order in each program; the XEQ IND tables keep
                        their numbers (MOON47 60-67 phase names, 90-97 symbol codes, M7TX 48-57 digits, M7SY 48-55
                        symbols). 4820 bytes.
  2_compact/MOON47.txt  + ONE program, only MOON47 in the XEQ menu: M7TX and M7SY after the page; their entries are
                        letters (M7TX=a M7IN=b M7F1=c M7HM=d M7DT=e M7HL=f M7SY=g), every other label a number;
                        M7TX's digit table moved to 70-79 (70 + digit) so it does not meet M7SY's 48-55. It takes
                        ALL 124 local labels of a program (00-99, a-l, A-L): no room for one more. Ends with CLSTK
                        as before (MOON47 keeps no registers of yours, no CLREGS). 4646 bytes.

Checked in the C47 firmware PC simulator (clock pinned to the date in a test copy, the key wait -> PAUSE 1 SNAP;
~/almanac47-fwtest/moon/moonfw.py): 7 dates 2000-2050, north and south (+/- key): every screen pixel for pixel
the same in 0, 1 and 2; X = Y = 0 at the end, no error.
CPU (best of 3, minus the sim start 0.046 s per run, sum of 7 dates): 0_speed 0.794 s, 1_labels 0.798 s,
2_compact 0.859 s (+8 %): the calls by name were cheap already (M7TX and M7SY are short programs with their entry
labels near the top), and in one program the returns from the printers and symbols walk from the program start
past the page's 1100 steps (fnReturn -> defineCurrentStep).
