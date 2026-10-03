C47 COMMAND REFERENCE

C47_items_master.tsv: every C47 item (2,800+ commands, functions, characters, menus) as the firmware
on master defines it, made by tools/c47ref.py from a local clone of gitlab.com/rpncalculators/c43
(src/c47/items.c, items.h, fonts.h). This is the reference for the programs here: the web reference
(47calc.com) follows the official releases only, and master is ahead of it (GRMOD, ATEXT, GRFNT came
there first). The second line of the file names the commit it was made from.
  Columns: item number, ITM_ name, catalog name and softmenu label (the firmware's own code points:
  x² is stored as xⅢ), function, parameter, TAM range, category, programmable (PTP_DISABLED = not
  allowed in programs), stack lift, and the name, bytes and aliases rejig uses for the item (blank when
  the installed rejig cannot write it).
  Data parsed from GPL-3.0-only source.

Keep it current:
  git -C ~/opt/c43 pull                    the firmware source (C43_DIR=... for another clone)
  python3 tools/c47ref.py                  rewrites the table, prints what changed
  python3 tools/c47check.py                every C47 listing: rejig reads it, each command must exist on
                                           master and be allowed in programs; renamed commands as notes
  python3 tests/test_c47ref.py             both, and the item numbers of tools/rejig47_atext.py

C47_Full_index.txt: text of "C47_Full_index" (04/08/2026, 180 pages), the official index of the release
00.109.04.00b0 with the descriptions of the commands, menus, settings and reserved variables. It has no
GRMOD, ATEXT or GRFNT; use it for the descriptions, C47_items_master.tsv for what exists now.
Copyright (c) 2026 The C47/R47 Development Team, GNU Free Documentation License (gnu.org).
Original documents: https://47calc.com/doc/C47/
The project's own reference tables, with descriptions (RefDB47): docs/refdb47/ in the c43 clone.

Graphics entries used by this project: PIXEL, POINT, AGRAPH, CLLCD, CLLCDxy, PAUSE, GRMOD / GRMOD#
(AGRAPH mode: 0 OR, 1 SET, 2 OFF, 3 XOR; reserved variable GRAMOD), ATEXT, GRFNT / GRFNT#.
