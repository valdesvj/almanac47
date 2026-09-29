#!/bin/sh
# setup.sh - build f42run, a headless Free42 (SwissMicros core, binary math) with the DM42
# 400 x 240 graphics, to test the Free42 build of Almanac 47 (tools/build_free42.py).
#   sh tools/f42/setup.sh        -> tools/f42/f42run
set -e
D=$(cd "$(dirname "$0")" && pwd)
W="$D/src"
mkdir -p "$W/common" "$W/windows"
U=https://raw.githubusercontent.com/swissmicros/free42/master
for f in core_aux.cc core_aux.h core_commands1.cc core_commands1.h core_commands2.cc core_commands2.h \
         core_commands3.cc core_commands3.h core_commands4.cc core_commands4.h core_commands5.cc core_commands5.h \
         core_commands6.cc core_commands6.h core_commands7.cc core_commands7.h core_display.cc core_display.h \
         core_globals.cc core_globals.h core_helpers.cc core_helpers.h core_keydown.cc core_keydown.h \
         core_linalg1.cc core_linalg1.h core_linalg2.cc core_linalg2.h core_main.cc core_main.h \
         core_math1.cc core_math1.h core_math2.cc core_math2.h core_phloat.cc core_phloat.h \
         core_sto_rcl.cc core_sto_rcl.h core_tables.cc core_tables.h core_variables.cc core_variables.h \
         free42.h shell.h shell_spool.cc shell_spool.h; do
  [ -f "$W/common/$f" ] || curl -sSf -o "$W/common/$f" "$U/common/$f"
done
[ -f "$W/windows/VERSION.h" ] || curl -sSf -o "$W/windows/VERSION.h" "$U/windows/VERSION.h"
cp "$D/bid_conf.h" "$D/bid_functions.h" "$W/common/"
cd "$W/common"
# the DM42 graphics (GrMod, 400 x 240, AGRAPH modes) without the rest of the ARM build
for f in core_aux.cc core_display.cc core_commands7.cc shell.h; do
  sed -i 's/#ifdef ARM$/#if defined(ARM) || defined(F42GR)/; s/#if defined(ARM)$/#if defined(ARM) || defined(F42GR)/; s/#ifndef ARM$/#if !defined(ARM) \&\& !defined(F42GR)/' $f
done
n=$(grep -n 'cmdnam2buf(buf, len, &bufptr, cmdspec->name' core_display.cc | cut -d: -f1)
sed -i "$((n-1))s/.*/#ifdef ARM/" core_display.cc
g++ -std=c++11 -w -O2 -DF42GR -include ctype.h -include core_variables.h -I. *.cc "$D/f42run.cc" -o "$D/f42run" -lm
echo "built $D/f42run"
