@echo off
setlocal
REM Drop-in apply: copies patched startrek sources over tools\scummvm
REM Run from the st25-hires repo root (or Remaster Project if this folder lives there).

set "ROOT=%~dp0"
set "SRC=%ROOT%scummvm-patch\overlay\engines\startrek"
set "DST=%ROOT%tools\scummvm\engines\startrek"

if not exist "%SRC%\bridge.cpp" (
  echo ERROR: missing "%SRC%\bridge.cpp"
  echo Pull branch cursor/bridge-fidelity-7506 first.
  exit /b 1
)

if not exist "%DST%\bridge.cpp" (
  echo ERROR: missing ScummVM tree at "%DST%"
  echo Expected: tools\scummvm\engines\startrek
  exit /b 1
)

echo Copying patched startrek files to:
echo   %DST%
copy /Y "%SRC%\actors.cpp"   "%DST%\actors.cpp"   >nul
copy /Y "%SRC%\bridge.cpp"   "%DST%\bridge.cpp"   >nul
copy /Y "%SRC%\graphics.cpp" "%DST%\graphics.cpp" >nul
copy /Y "%SRC%\graphics.h"   "%DST%\graphics.h"   >nul
copy /Y "%SRC%\sound.cpp"    "%DST%\sound.cpp"    >nul
copy /Y "%SRC%\space.cpp"    "%DST%\space.cpp"    >nul
copy /Y "%SRC%\startrek.cpp" "%DST%\startrek.cpp" >nul
copy /Y "%SRC%\startrek.h"   "%DST%\startrek.h"   >nul
echo Done.
echo.
echo Next: rebuild scummvm.exe then Launch ScummVM Test.bat
exit /b 0
