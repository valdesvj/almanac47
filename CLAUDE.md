# Almanac 47: working rules

- Work on a new branch; Victor creates and merges the PRs. Never force-push or rewrite history.
- Commit author: "Victor Valdes" <valdesvj@users.noreply.github.com>.
- Never commit binaries (tools/f42/f42run, the patched rejig). build/manuals/ is ignored.
- Leave tests/THANKS.txt untracked: don't commit, move or edit it.
- Manual PDFs go to build/manuals/; to docs/ only with --release, and only when asked.
- The C47 T21/GRFNT builds (build/atext/NAVFULL_T21, NAVLITTLE_PH) stay EXPERIMENTAL until the
  GRFNT firmware is released. Don't change the main C47 builds.
- Before changing a screen, compare it with the C47 simulator (python/c47sim.py); Free42 screens
  must match it pixel for pixel.
- Ask before anything that can't be undone.
