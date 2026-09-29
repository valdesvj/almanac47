# f42run: a headless Free42 for testing the Free42 build

`f42run` is the Free42 3.3.10 core (SwissMicros' fork, the core of the DM42/DM42n stock firmware) with
a small shell. It pastes program listings, runs them with scripted keys, captures the DM42's 400 × 240
graphics screen, and exports `.raw` files. It uses binary (double) arithmetic: the Intel decimal
library is replaced by the stubs in `bid_functions.h`.

    sh tools/f42/setup.sh                 # downloads the core sources, builds tools/f42/f42run
    tools/f42/f42run < commands.txt

Commands (one per line): `paste FILE`, `import FILE.raw`, `export FILE.raw`, `xeq NAME`,
`num 2026.0926` (keys a number and R/S), `key CODE` (GETKEY code 1–37), `qkey CODE MS [FILE]`
(a key while the program runs, after MS ms, capturing FILE first), `film PREFIX` / `stopfilm`
(a capture every 0.25 s while running), `shot FILE.pbm`, `msg` (the 131 × 16 text display),
`stack`, `regs A B`, `list N`.

Free42 is © Thomas Okken, GPL v2. This shell and the stubs: GPL v3 or later, like Almanac 47.
