# Almanac 47: working rules

- Work on a new branch; Victor creates and merges the PRs. Never force-push or rewrite history.
- Commit author: "Victor Valdes" <valdesvj@users.noreply.github.com>.
- Never commit binaries (tools/f42/f42run, the patched rejig). build/manuals/ is ignored.
- Leave tests/THANKS.txt untracked: don't commit, move or edit it.
- Manual PDFs go to build/manuals/; to docs/ only with --release, and only when asked.
- ATEXT and GRFNT are in the C47 firmware (Oct 2026): every C47 build (build/NAVFULL, dev/, build/dm42/)
  uses the T21 views (programs/atext/t21/): ATEXT in GRFNT 21, only the glyphs47 symbols drawn with AGRAPH.
  Free42 has no ATEXT: build_free42.py keeps its AGRAPH fonts (programs/PTXS, PTXT, PTXB); don't change it.
- Before changing a screen, compare it with the C47 simulator (python/c47sim.py); Free42 screens
  must match it pixel for pixel.
- Ask before anything that can't be undone.
- C47 commands come from the firmware on master, not from the web reference (it follows releases only):
  git -C ~/opt/c43 pull, then python3 tools/c47ref.py (docs/reference/C47_items_master.tsv) and
  python3 tests/test_c47ref.py. Use the latest rejig in ~/.local/bin.
