@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%~dp0start_pp.py" %*
  goto finished
)
where python >nul 2>nul
if not errorlevel 1 (
  python "%~dp0start_pp.py" %*
  goto finished
)
echo Python ontbreekt. Installeer Python 3.11 of hoger en probeer opnieuw.
:finished
if errorlevel 1 echo P.P. is niet gestart. Lees de melding hierboven.
pause
endlocal
