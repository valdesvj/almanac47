#!/bin/bash
# convert_all.sh - convert every C47 program .txt to .p47
# Run it inside the "programs" folder.
CONV="rejig"          # <- your converter's name or full path
mkdir -p p47
ok=0; bad=0
for f in *.txt; do
  out="p47/${f%.txt}.p47"
  if $CONV "$f" -o "$out" 2> "p47/${f%.txt}.err"; then
    rm -f "p47/${f%.txt}.err"; echo "OK   $f -> $out"; ok=$((ok+1))
  else
    echo "FAIL $f  (see p47/${f%.txt}.err)"; bad=$((bad+1))
  fi
done
echo "Done: $ok converted, $bad failed"
