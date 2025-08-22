@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Build a one-file Windows executable for typeterm using PyInstaller.
REM Creates .venv (local), installs deps, and outputs dist/typeterm.exe

if not exist .venv (
  echo Creating virtual environment...
  py -3 -m venv .venv
)

call .venv\Scripts\activate

echo Upgrading pip...
python -m pip install --upgrade pip >nul

echo Installing build dependencies...
REM windows-curses provides the curses module on Windows; required at runtime.
python -m pip install pyinstaller windows-curses -r requirements.txt || goto :error

echo Building one-file executable...
pyinstaller --onefile --name typeterm typeterm\__main__.py || goto :error

echo.
echo Build complete: dist\typeterm.exe
echo You can now distribute dist\typeterm.exe to friends.
goto :eof

:error
echo Build failed. See output above for details.
exit /b 1

