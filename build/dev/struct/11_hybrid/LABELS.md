# NAVFULL step 11: numbered labels used by every program

Build: `build/dev/struct/11_hybrid/NAVFULL.txt` (C47 / R47, the winner of the struct-opt work, Oct 2026).
Names from `build/NAVFULL_LABELS.txt`; N95 / N97 / N98 / N99 are new in step 8–11.

- 35 programs, **544 numbered local labels**, 76 global labels (35 program entries + 41 inside programs).
- **No letter labels** (A–L, a–l) anywhere.
- The numbers 00–99 count **per program**; the most used in one program is 58 of 100 (SBRT and SNMU: one label per
  star, reached by `GTO IND`). Every program has room left.

| Prog | Name | Steps | Labels | Numbers used | Also global labels inside |
|---|---|---:|---:|---|---|
| NAV | NAV | 1148 | 48 | 01-03 05-15 20-23 25-26 28-30 40-43 46-48 50-54 61-66 93-99 | |
| N50 | PTXS | 382 | 30 | 01-02 05-08 11-22 25 48-57 99 | PTNT PDMS PDTS PHMS PINS PTTY PHLS PZNS PF1S |
| N61 | HANIM | 401 | 24 | 01-03 08-10 13-14 23 29 44 48 65 68 70-79 | |
| N82 | PSYS | 195 | 15 | 01-02 40 42 60-64 94-99 | |
| N32 | HCZ | 94 | 1 | 02 | HCZR HCZI HCZQ |
| N64 | CSUN | 794 | 41 | 01 09-10 20-22 30-33 40-45 47-49 78-99 | CEQR CSQK CHCZ CSTR CNTA CPLN CALC CMOO CRIS CTRN CSET CNTP CEQQ CPHA |
| N24 | MOON | 516 | 6 | 20 22 96-99 | MOO2 MOOQ |
| N83 | HDR | 67 | 2 | 01-02 | |
| N62 | ALLSKY | 251 | 26 | 08-10 13-17 20-25 29 44 48 61-63 65 68 71-74 | |
| N04 | HORZ | 646 | 53 | 29 34-40 42-45 47-57 59 62-67 70-79 81-88 91-94 99 | |
| N38 | RISE | 110 | 7 | 20-22 24-25 29 99 | SET TRAN NTWA NTWP |
| N28 | PLN2 | 585 | 22 | 11-14 26-28 30-33 48-50 60-64 97-99 | PLN3 |
| N81 | PSYB | 367 | 38 | 01-02 38 40 42 48-55 60-64 80-99 | |
| N01 | ALMF | 474 | 41 | 16-19 22-24 26-29 35-36 48-55 60-61 63-66 71-74 82-85 91-94 98-99 | |
| N15 | SUNA | 406 | 4 | 14-15 45 99 | SER SUNG SUNF SERT NUT |
| N46 | PHA2 | 183 | 6 | 40-44 46 | |
| N06 | HALMH | 539 | 39 | 12-13 15-19 21-24 27 29-32 49 51-52 57 60-61 63-66 71-74 82-85 91-94 99 | |
| N22 | STR2 | 161 | 0 | | SQK |
| N47 | SBRT | 178 | 58 | 01-58 (one per star, `GTO IND`) | |
| N48 | SNMU | 178 | 58 | 01-58 (one per star name) | |
| N49 | TGET | 194 | 13 | 09 12-13 20-26 28-30 | |
| N63 | WPLS | 23 | 1 | 01 | |
| N84 | CMN | 22 | 0 | | |
| N85 | CMS | 22 | 0 | | |
| N86–N94 | OUT1–OUT9 | 8–63 each | 0 | (shared step sequences, no jumps) | |
| N95 | MSTAR (the star matrices per time) | 406 | 11 | 02 10-13 20 30 40 71-73 | |
| N97 | STANG (one star's angles) | 206 | 0 | | N98 (ALLSKY: a star without values), N99 (all 58 at once) |

## What the firmware does with them (c43 master, read 2026-10-07)

- One table `labelList` (manage.c `scanLabelsAndPrograms`) with every LBL: program, step, the label's **address in
  RAM**, the next step's address. About 16 bytes of RAM per label on the calculator: ~9.9 KB for these 620 labels.
  It is rebuilt whenever programs are loaded or edited.
- `GTO nn` / `XEQ nn` (numbers, letters): integer compares in the table, then a jump **to the stored address** — no
  walk; distance does not matter (TSTRUCT R21 ≈ R22).
- `XEQ "NAME"` and `XEQ :NAME:`: the names of the labels compared as text, then a **walk from the start of the
  program** to the label (goToGlobalStep).
- `RTN`: a **walk from the start of the caller's program** to the step after the XEQ (fnReturn → defineCurrentStep).

So: numbered labels inside **small** programs, global labels at the top of each program (step 11). One program for
everything (v2.2.0, 12_compact, with letters too) is 2–4× slower: every return walks thousands of steps.

## Candidates if more speed is wanted

The programs with many global labels inside, where a call walks from the program's top to the routine:
CSUN (14 cache routines), PTXS (9 text routines), SUNA (5), RISE (4), HCZ (3). Splitting the hot ones into their own
small programs would shorten those walks a little (step 3 already moved the most called ones up).
