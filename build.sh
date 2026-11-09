#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
CC="${CC:-i686-w64-mingw32-gcc}"
WINDRES="${WINDRES:-i686-w64-mingw32-windres}"
mkdir -p .build release
(cd resources && "$WINDRES" -i app.rc -o ../.build/app.res.o --output-format=coff)
"$CC" -std=c11 -Os -Wall -Wextra -Werror -municode -mwindows -static -s \
  -Wl,--no-insert-timestamp -Wl,--nxcompat -Wl,--dynamicbase \
  src/patcher.c .build/app.res.o -lcomdlg32 -lbcrypt -luser32 \
  -o release/Domex-Windows10-Patch.exe
python3 package_release.py
