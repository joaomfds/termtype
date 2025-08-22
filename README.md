typeterm — Terminal typing test (Monkeytype‑like)

What it is
- A no‑GUI, curses‑based typing test you run in a terminal.
- Shows live WPM, accuracy, and time/words remaining.
- Modes: time (e.g., 60s) or words (e.g., 50 words).
- Pure Python, no dependencies.

Quick start
- Requirements: Python 3.10+ and a real terminal (TTY) with basic color support.
- From this folder, run:
  - Time mode: `python -m typeterm --mode time --seconds 60`
  - Words mode: `python -m typeterm --mode words --words 50`
  - Custom list: `python -m typeterm --wordlist wordlists/english_2000.txt`

Keys
- Start: begin typing any character
- Submit word: Space or Enter
- Backspace: delete within current word
- Restart: Tab
- Quit: Esc

Stats
- WPM: correct characters / 5, per minute of elapsed time
- Accuracy: correct characters / (correct + incorrect)

Notes
- The timer starts on your first keypress.
- In words mode, the test ends when you submit the last word.
- In time mode, words stream continuously until the countdown ends.
 - You can load your own list with `--wordlist` (one word per line). If provided, it is used for both modes and for infinite extension in time mode.

Troubleshooting
- If you see a message about requiring a real TTY, run it directly in your OS terminal (e.g., xterm, GNOME Terminal, iTerm2, Windows Terminal). Some embedded environments or consoles don’t support curses.

Windows one-file EXE
- Local build (on Windows):
  - Install Python 3.10+.
  - From the repo root, run `scripts\build_windows.bat`.
  - The executable appears at `dist\typeterm.exe` (single file). Share that file.
- CI build (GitHub Actions):
  - Push to `main`/`master` or run the `build-windows` workflow manually.
  - Download `typeterm.exe` from the workflow artifacts.
- Notes:
  - The app uses `curses`; on Windows this is provided by `windows-curses` and is bundled by PyInstaller.
  - Run it directly in a real terminal (e.g., Windows Terminal).

Linux one-file binary
- Local build (on Linux):
  - Ensure Python 3.10+ is installed.
  - From the repo root, run `scripts/build_linux.sh`.
  - The executable appears at `dist/typeterm`. Share that single file.
  - Run: `./dist/typeterm --mode time --seconds 60`
- CI build (GitHub Actions):
  - Push to `main`/`master` or run the `build-linux` workflow manually.
  - Download `typeterm` from the workflow artifacts.
- Notes:
  - Linux uses the built-in `curses` module; no extra runtime deps are required.
  - Run it in a real terminal (e.g., GNOME Terminal, xterm, KDE Konsole).

Command-line options (Windows and Linux)
- `--mode {time,words}`: Test mode (default: `time`).
- `--seconds INT`: Duration for time mode (default: `60`).
- `--words INT`: Number of words for words mode (default: `50`).
- `--seed INT`: Random seed for repeatable word sequences (optional).
- `--wordlist PATH`: Custom word list file (one word per line). If provided, it is used for both modes and for infinite extension in time mode.

Examples
- Time mode 60s: `typeterm --mode time --seconds 60`
- Words mode 50 words: `typeterm --mode words --words 50`
- Custom list with fixed seed: `typeterm --wordlist ./my_words.txt --seed 123`
