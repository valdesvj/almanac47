# Generators

Python scripts that wrote most of the calculator program files. They are kept as the
source of the generated programs. They were run in the original work folder, so the
input and output paths inside them (e.g. `/home/claude/ALMF.txt`) must be changed
before running them again.

| Script | Writes |
|---|---|
| `gen.py`, `gen2.py`, `addsym.py` | PTXB / PTXT fonts (AGRAPH glyphs) and the planet/Moon symbols |
| `genf.py` | ALMF |
| `genv.py` | HALMV |
| `genh2.py` | HORZ and HORZS |
| `genalmt.py` | ALMT |
| `gencache.py` | CACHE (sky cache for the NAV builds: views read matrix ALMC) |
| `genstxt.py` | STXT (number to text) |
| `genmp2.py` | MOON and PLAN (uses `mconst.json`, `pcounts.json`) |
| `annot.py` | `listings/*_doc.txt` and `programs_rem/` (REM comments) |
| `build_manual.py` | the user manual PDF (with `manual_head.py`, `manual_results.json`; images from the work folder) |

After regenerating a program, run `tests/test_parity.py` and keep the native Python
version (`python/native/c47screen.py`) in step.
