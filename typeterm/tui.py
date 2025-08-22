from __future__ import annotations

import argparse
import curses
import random
import time
from dataclasses import dataclass

from .wordlist import generate_words, load_words_from_file, WORDS as DEFAULT_WORDS


@dataclass
class Config:
    mode: str = "time"  # "time" or "words"
    seconds: int = 60
    words: int = 50
    seed: int | None = None
    wordlist_path: str | None = None


@dataclass
class WordState:
    target: str
    typed: str = ""

    @property
    def correct_prefix_length(self) -> int:
        n = 0
        for a, b in zip(self.typed, self.target):
            if a == b:
                n += 1
            else:
                break
        return n

    @property
    def extra_count(self) -> int:
        return max(0, len(self.typed) - len(self.target))

    @property
    def is_complete(self) -> bool:
        # complete when user pressed space or reached exact length and pressed space/enter handled by app
        return False


class TypingSession:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        nwords = max(cfg.words, 200) if cfg.mode == "time" else cfg.words
        # choose word pool
        if cfg.wordlist_path:
            pool = load_words_from_file(cfg.wordlist_path)
        else:
            pool = DEFAULT_WORDS
        self.words: list[WordState] = [WordState(w) for w in generate_words(nwords, seed=cfg.seed, word_source=pool)]
        self.index = 0
        self.view_start = 0  # index of first visible word for layout/scrolling
        self.started_at: float | None = None
        self.ended_at: float | None = None
        self.total_keystrokes = 0  # includes backspace and spaces
        self.correct_chars = 0
        self.incorrect_chars = 0
        self.completed_words = 0

    # Metrics
    def elapsed(self) -> float:
        if self.started_at is None:
            return 0.0
        end = self.ended_at if self.ended_at is not None else time.time()
        return max(0.0, end - self.started_at)

    def is_running(self) -> bool:
        return self.started_at is not None and self.ended_at is None

    def is_finished(self) -> bool:
        return self.ended_at is not None

    def remaining_seconds(self) -> int:
        if self.cfg.mode != "time":
            return 0
        secs = self.cfg.seconds - int(self.elapsed())
        return max(0, secs)

    def current_word(self) -> WordState:
        return self.words[self.index]

    def handle_key(self, ch: int) -> None:
        if self.is_finished():
            return
        if self.started_at is None:
            self.started_at = time.time()
        # printable range
        if ch in (curses.KEY_BACKSPACE, 127, 8):
            if self.current_word().typed:
                self.current_word().typed = self.current_word().typed[:-1]
                self.total_keystrokes += 1
            return
        if ch in (10, 13, ord(' ')):
            self._submit_word()
            return
        if 32 <= ch <= 126:
            # ascii
            self.current_word().typed += chr(ch)
            self.total_keystrokes += 1
            return

    def _submit_word(self) -> None:
        target = self.current_word().target
        typed = self.current_word().typed
        # count correct and incorrect chars for this word
        for i, c in enumerate(typed):
            if i < len(target) and c == target[i]:
                self.correct_chars += 1
            else:
                self.incorrect_chars += 1
        # count missed characters as incorrect if typed shorter than target (on submission)
        if len(typed) < len(target):
            self.incorrect_chars += (len(target) - len(typed))
        self.completed_words += 1
        # move index
        self.index += 1
        if self.cfg.mode == "words" and self.completed_words >= self.cfg.words:
            self.ended_at = time.time()
        elif self.index >= len(self.words):
            # extend for time mode so there's always more words
            self._extend_words()

    def _extend_words(self):
        # Extend from same source (either external wordlist or default)
        pool = load_words_from_file(self.cfg.wordlist_path) if self.cfg.wordlist_path else DEFAULT_WORDS
        more = generate_words(100, seed=None, word_source=pool)
        self.words.extend(WordState(w) for w in more)

    def tick(self):
        if self.cfg.mode == "time" and self.is_running():
            if self.elapsed() >= self.cfg.seconds:
                self.ended_at = time.time()

    def wpm(self) -> float:
        elapsed = max(self.elapsed(), 1e-9)
        return (self.correct_chars / 5.0) / (elapsed / 60.0)

    def accuracy(self) -> float:
        total_chars = self.correct_chars + self.incorrect_chars
        if total_chars == 0:
            return 100.0
        return (self.correct_chars / total_chars) * 100.0


def draw_centered(stdscr, y: int, text: str, attr=0):
    h, w = stdscr.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    stdscr.addnstr(y, x, text, max(0, w - x), attr)


def render(session: TypingSession, stdscr):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    # Colors
    try:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)  # correct
        curses.init_pair(2, curses.COLOR_RED, -1)    # wrong
        curses.init_pair(3, curses.COLOR_CYAN, -1)   # highlight
    except curses.error:
        pass

    # Header
    mode_text = f"Mode: {session.cfg.mode.upper()}"
    if session.cfg.mode == "time":
        hdr = f"{mode_text} | {session.remaining_seconds():02d}s left | ESC quit, TAB restart"
    else:
        remaining_words = max(0, session.cfg.words - session.completed_words)
        hdr = f"{mode_text} | {remaining_words} words left | ESC quit, TAB restart"
    stdscr.addnstr(0, 1, hdr, w - 2, curses.A_BOLD)

    # Stats line
    stats = f"WPM: {session.wpm():.1f} | Acc: {session.accuracy():.0f}% | Time: {int(session.elapsed()):02d}s"
    stdscr.addnstr(1, 1, stats, w - 2)

    # Instructions if not started
    if session.started_at is None:
        draw_centered(stdscr, h // 2, "Start typing to begin...", curses.A_DIM)
    elif session.is_finished():
        # Results screen
        draw_centered(stdscr, h // 2 - 1, f"Results — WPM {session.wpm():.1f} | Acc {session.accuracy():.0f}%", curses.A_BOLD)
        draw_centered(stdscr, h // 2 + 1, "Press TAB to restart or ESC to quit", curses.A_DIM)
    else:
        # Typing area
        draw_words_area(session, stdscr, start_y=3, height=h - 4, width=w - 2, x=1)

    stdscr.refresh()


def draw_words_area(session: TypingSession, stdscr, start_y: int, height: int, width: int, x: int):
    # We keep previous words visible and only scroll when the current word would move beyond the view.

    def layout(start_idx: int):
        positions: list[tuple[int, int, int]] = []  # (word_index, y, x)
        y = 0
        x0 = 0
        idx = start_idx
        current_line = None
        while y < height and idx < len(session.words):
            w = session.words[idx].target
            need_space = 1 if x0 > 0 else 0
            if x0 + need_space + len(w) > width:
                y += 1
                x0 = 0
                if y >= height:
                    break
                need_space = 0
            if need_space:
                x0 += 1
            positions.append((idx, y, x0))
            if idx == session.index:
                current_line = y
            x0 += len(w)
            idx += 1
        return positions, current_line

    # Adjust view_start so that the current word is within the visible area.
    start_idx = session.view_start
    for _ in range(1000):
        positions, cur_line = layout(start_idx)
        if cur_line is not None and cur_line < height:
            break
        start_idx += 1
    session.view_start = start_idx

    # Draw the positioned words
    positions, _ = layout(session.view_start)
    for idx, rel_y, rel_x in positions:
        word = session.words[idx]
        abs_y = start_y + rel_y
        abs_x = x + rel_x
        if idx == session.index:
            draw_word_with_progress(stdscr, abs_y, abs_x, word)
        else:
            if idx < session.index and word.typed:
                draw_word_result(stdscr, abs_y, abs_x, word)
            else:
                stdscr.addnstr(abs_y, abs_x, word.target, max(0, x + width - abs_x))


def draw_word_with_progress(stdscr, y: int, x: int, word: WordState):
    correct_attr = curses.color_pair(1)
    wrong_attr = curses.color_pair(2)
    cur_attr = curses.A_UNDERLINE | curses.color_pair(3)
    # draw each char
    for i, ch in enumerate(word.target):
        if i < len(word.typed):
            if word.typed[i] == ch:
                stdscr.addch(y, x + i, ord(ch), correct_attr)
            else:
                stdscr.addch(y, x + i, ord(ch), wrong_attr)
        else:
            stdscr.addch(y, x + i, ord(ch), cur_attr)
    # Extra typed chars beyond target
    extra = word.extra_count
    for j in range(extra):
        ch = word.typed[len(word.target) + j]
        stdscr.addch(y, x + len(word.target) + j, ord(ch), wrong_attr)


def draw_word_result(stdscr, y: int, x: int, word: WordState):
    correct_attr = curses.color_pair(1)
    wrong_attr = curses.color_pair(2)
    # draw target with correct/incorrect based on what was typed when submitted
    typed = word.typed
    for i, ch in enumerate(word.target):
        if i < len(typed) and typed[i] == ch:
            stdscr.addch(y, x + i, ord(ch), correct_attr)
        elif i < len(typed):
            stdscr.addch(y, x + i, ord(ch), wrong_attr)
        else:
            stdscr.addch(y, x + i, ord(ch))
    # extra typed characters
    if len(typed) > len(word.target):
        for j in range(len(typed) - len(word.target)):
            ch = typed[len(word.target) + j]
            stdscr.addch(y, x + len(word.target) + j, ord(ch), wrong_attr)


def run_curses(cfg: Config):
    def _main(stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(50)  # refresh every 50ms for timer
        session = TypingSession(cfg)

        while True:
            render(session, stdscr)
            try:
                ch = stdscr.getch()
            except KeyboardInterrupt:
                break
            if ch == -1:
                # periodic tick for timer
                session.tick()
                continue

            if ch in (27,):
                # ESC to quit
                break
            if ch in (9,):
                # TAB to restart
                session = TypingSession(cfg)
                continue

            if not session.is_finished():
                session.handle_key(ch)
                session.tick()
            else:
                # allow quick restart with any key except ESC
                if ch not in (27,):
                    session = TypingSession(cfg)

    try:
        curses.wrapper(_main)
    except curses.error:
        # Likely not a real TTY or terminal doesn't support curses in this environment.
        print("This app requires a real TTY with curses support.")
        print("Try running from your system terminal (e.g., xterm, iTerm, Windows Terminal).")
        return


def parse_args(argv: list[str] | None = None) -> Config:
    p = argparse.ArgumentParser(
        prog="typeterm",
        description="Terminal typing test (Monkeytype-like)",
    )
    p.add_argument("--mode", choices=["time", "words"], default="time", help="Test mode")
    p.add_argument("--seconds", type=int, default=60, help="Seconds for time mode")
    p.add_argument("--words", type=int, default=50, help="Word count for words mode")
    p.add_argument("--seed", type=int, default=None, help="Random seed for repeatable word sequences")
    p.add_argument("--wordlist", type=str, default=None, help="Path to a custom wordlist (one word per line)")
    args = p.parse_args(argv)
    return Config(mode=args.mode, seconds=args.seconds, words=args.words, seed=args.seed, wordlist_path=args.wordlist)


def main(argv: list[str] | None = None):
    cfg = parse_args(argv)
    run_curses(cfg)
