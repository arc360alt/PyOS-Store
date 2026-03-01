#!/usr/bin/env python3
"""
FastType - A terminal typing speed trainer inspired by MonkeyType
"""

import curses
import time
import json
import os
import urllib.request
import urllib.error
import random
import textwrap
import threading
from datetime import datetime
from pathlib import Path

# ─── Config & Paths ───────────────────────────────────────────────────────────
DATA_DIR = Path.home() / ".fasttype"
SCORES_FILE = DATA_DIR / "scores.json"
CONFIG_FILE = DATA_DIR / "config.json"

DATA_DIR.mkdir(exist_ok=True)

DEFAULT_CONFIG = {
    "word_count": 25,
    "quote_min_length": 100,
    "quote_max_length": 300,
    "zen_duration": 60,
    "theme": "default",
    "show_wpm_live": True,
    "word_source": "random_words",
    "difficulty": "medium",
}

# ─── Word lists by difficulty ─────────────────────────────────────────────────
# Easy: 2-4 letter common words, zero thinking required
WORDS_EASY = [
    "the","and","for","are","but","not","you","all","can","her","was","one","our",
    "out","day","get","has","him","his","how","its","may","new","now","old","see",
    "two","way","who","boy","did","man","too","use","dad","mom","cat","dog","run",
    "fun","sun","big","red","top","end","far","let","set","try","put","yes","no",
    "go","do","it","is","in","on","of","to","at","be","by","or","an","up","so",
    "we","me","my","he","she","they","them","then","than","that","this","with",
    "from","into","just","like","only","also","back","good","time","well","work",
    "life","when","over","such","make","your","know","take","come","more","long",
    "even","most","tell","much","keep","give","last","left","help","home","read",
    "look","move","live","said","hand","part","feel","food","few","say","here",
]

# Medium: 4-7 letter everyday words — what MonkeyType "normal" feels like
WORDS_MEDIUM = [
    "about","after","again","along","began","being","below","bring","build","carry",
    "catch","cause","check","china","claim","class","clean","clear","climb","close",
    "coast","color","comes","could","cover","cross","dance","death","doing","doors",
    "doubt","dream","drink","drive","early","earth","eight","email","enter","event",
    "every","exact","exist","extra","faith","false","family","field","final","first",
    "focus","force","found","frame","fresh","front","funny","given","glass","going",
    "grace","grand","grant","great","green","group","guess","guide","happy","heart",
    "heavy","hello","horse","hotel","house","human","image","index","inner","input",
    "issue","joint","judge","juice","jump","keeps","large","laugh","layer","learn",
    "leave","level","light","limit","lived","local","logic","lucky","magic","major",
    "maker","match","mayor","means","media","metal","might","model","money","month",
    "moral","mount","mouse","mouth","movie","music","never","night","noise","north",
    "noted","novel","ocean","offer","often","order","other","outer","owner","paint",
    "paper","party","peace","phone","photo","piece","pilot","place","plain","plane",
    "plant","plate","plaza","point","power","press","price","pride","prime","print",
    "prize","proof","proud","prove","queen","quick","quiet","quite","quote","radio",
    "raise","range","reach","ready","reply","right","river","robin","robot","round",
    "route","royal","ruler","rural","scale","scene","score","sense","serve","seven",
    "share","sharp","shift","shirt","shock","short","shown","sight","since","skill",
    "sleep","slide","small","smart","smile","smoke","solid","solve","south","space",
    "speak","speed","spend","spoke","sport","staff","stage","stand","start","state",
    "steel","still","stock","stone","story","study","style","sugar","super","sweet",
    "table","teach","teeth","thank","their","theme","thick","thing","think","third",
    "throw","tight","tired","today","token","topic","total","touch","tough","tower",
    "track","trade","train","treat","trend","trial","trick","tried","trust","truth",
    "under","union","until","upper","urban","using","usual","valid","value","video",
    "visit","voice","voter","watch","water","weird","where","which","while","white",
    "whole","whose","width","world","worry","worse","worth","would","write","young",
]

# Hard: longer, complex, or less common but real words you'd actually encounter
WORDS_HARD = [
    "abandon","ability","absence","absolute","abstract","academic","accident","account",
    "achieve","acquire","address","advance","against","agenda","airline","already",
    "although","ancient","another","anxiety","apparent","arrange","article","assembly",
    "attempt","attract","balance","barrier","because","between","billion","bizarre",
    "blossom","bracket","breathe","brother","cabinet","capture","catalog","century",
    "certain","chapter","climate","cluster","collect","combine","comment","complex",
    "concept","concern","conduct","confirm","connect","consider","consist","consume",
    "contain","content","context","control","convert","correct","counter","courage",
    "culture","current","customer","damage","declare","default","defense","deliver",
    "depend","describe","despite","develop","digital","discuss","display","dispute",
    "distant","dynamic","ecology","economy","element","embrace","emerge","emotion",
    "emphasis","enhance","ensure","exclude","execute","exhaust","explain","exploit",
    "explore","express","extreme","failure","feature","finance","foreign","forever",
    "forward","freedom","further","general","gesture","glimpse","gravity","harmony",
    "improve","include","initial","install","involve","isolate","journal","justice",
    "kingdom","language","laughter","liberty","logical","machine","maximum","measure",
    "memory","mention","mission","monitor","movement","mystery","natural","network",
    "nothing","observe","obvious","opinion","opposed","organic","outline","outside",
    "pathway","perfect","perform","perhaps","physics","picture","popular","portion",
    "precise","primary","problem","process","produce","profile","project","protect",
    "provide","quality","quarter","radical","reality","receive","recover","reflect",
    "release","remain","replace","request","require","research","resolve","respond",
    "restore","revenue","reverse","section","segment","serious","service","similar",
    "society","someone","source","standard","station","strange","strategy","structure",
    "subject","succeed","suggest","support","surface","survive","system","tangible",
    "tension","through","transfer","transform","travel","trouble","typical","unique",
    "various","version","vibrant","violent","visible","welcome","whether","without",
    "working","written","courage","history","imagine","journey","kingdom","library",
]

# ─── Colors ───────────────────────────────────────────────────────────────────
C_NORMAL     = 1
C_CORRECT    = 2
C_WRONG      = 3
C_DIM        = 4
C_ACCENT     = 5
C_HEADER     = 6
C_CURSOR     = 7
C_TITLE      = 8
C_GOOD       = 9
C_BAD        = 10
C_SUBTLE     = 11

# ─── Data persistence ─────────────────────────────────────────────────────────

def load_scores():
    if SCORES_FILE.exists():
        try:
            return json.loads(SCORES_FILE.read_text())
        except Exception:
            return []
    return []

def save_score(entry: dict):
    scores = load_scores()
    scores.append(entry)
    SCORES_FILE.write_text(json.dumps(scores, indent=2))

def load_config():
    cfg = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            saved = json.loads(CONFIG_FILE.read_text())
            cfg.update(saved)
        except Exception:
            pass
    return cfg

def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

# ─── API Fetchers ─────────────────────────────────────────────────────────────

def get_word_list(difficulty: str) -> list:
    """Return the cumulative word pool for a given difficulty.
    Easy   → easy only
    Medium → easy + medium (so medium mixes in familiar words)
    Hard   → easy + medium + hard (full range, harder words dominate via weighting)
    """
    if difficulty == "easy":
        return WORDS_EASY
    elif difficulty == "hard":
        # Weight so hard words appear most, but easy/medium still show up
        return WORDS_EASY * 1 + WORDS_MEDIUM * 2 + WORDS_HARD * 4
    else:  # medium
        return WORDS_EASY * 1 + WORDS_MEDIUM * 3

def fetch_random_words(count: int = 25, difficulty: str = "medium") -> str:
    """Pick random words from the curated difficulty-based word list."""
    pool = get_word_list(difficulty)
    chosen = random.choices(pool, k=count)
    return " ".join(chosen)

def fetch_quote(difficulty: str = "medium") -> tuple[str, str]:
    """Fetch a random quote filtered by difficulty. Returns (text, author)."""
    length_ranges = {
        "easy":   (50,  120),
        "medium": (100, 220),
        "hard":   (180, 400),
    }
    min_len, max_len = length_ranges.get(difficulty, (100, 220))

    # Try quotable.io — supports length filters
    try:
        url = f"https://api.quotable.io/random?minLength={min_len}&maxLength={max_len}"
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read().decode())
            quote = data["content"]
            author = data.get("author", "Unknown")
            if difficulty == "easy":
                words = quote.split()
                avg_word_len = sum(len(w.strip(".,!?;:\"'")) for w in words) / max(len(words), 1)
                if avg_word_len > 5.5:
                    raise ValueError("quote too complex for easy mode")
            return quote, author
    except Exception:
        pass

    # Fallback: DummyJSON
    try:
        url = "https://dummyjson.com/quotes/random"
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read().decode())
            quote = data["quote"]
            if min_len <= len(quote) <= max_len:
                return quote, data.get("author", "Unknown")
    except Exception:
        pass

    # Final tiered fallback
    easy_fb = [
        ("Do what you love.", "Steve Jobs"),
        ("Stay curious.", "Anonymous"),
        ("Be kind always.", "Anonymous"),
        ("Keep it simple.", "Leonardo da Vinci"),
    ]
    medium_fb = [
        ("The only way to do great work is to love what you do.", "Steve Jobs"),
        ("In the middle of difficulty lies opportunity.", "Albert Einstein"),
        ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
        ("Life is what happens when you're busy making other plans.", "John Lennon"),
        ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
    ]
    hard_fb = [
        ("It is not the strongest of the species that survives, nor the most intelligent, but the one most responsive to change.", "Charles Darwin"),
        ("The measure of intelligence is the ability to change. An unexamined life is not worth living, and wisdom begins in wonder.", "Albert Einstein"),
        ("We are what we repeatedly do. Excellence then is not an act but a habit. The purpose of our lives is to be happy and to contribute.", "Aristotle"),
        ("Logic will get you from A to Z but imagination will get you everywhere. The true sign of intelligence is not knowledge but imagination.", "Albert Einstein"),
        ("In three words I can sum up everything I have learned about life: it goes on. What lies behind us and before us are tiny matters compared to what lies within.", "Robert Frost"),
    ]
    pools = {"easy": easy_fb, "medium": medium_fb, "hard": hard_fb}
    return random.choice(pools.get(difficulty, medium_fb))

# ─── Color helpers ─────────────────────────────────────────────────────────────

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    # pair: (id, fg, bg)
    curses.init_pair(C_NORMAL,  curses.COLOR_WHITE,   -1)
    curses.init_pair(C_CORRECT, curses.COLOR_GREEN,   -1)
    curses.init_pair(C_WRONG,   curses.COLOR_RED,     -1)
    curses.init_pair(C_DIM,     8,                    -1)   # dark gray
    curses.init_pair(C_ACCENT,  curses.COLOR_CYAN,    -1)
    curses.init_pair(C_HEADER,  curses.COLOR_YELLOW,  -1)
    curses.init_pair(C_CURSOR,  curses.COLOR_BLACK,   curses.COLOR_WHITE)
    curses.init_pair(C_TITLE,   curses.COLOR_CYAN,    -1)
    curses.init_pair(C_GOOD,    curses.COLOR_GREEN,   -1)
    curses.init_pair(C_BAD,     curses.COLOR_RED,     -1)
    curses.init_pair(C_SUBTLE,  curses.COLOR_WHITE,   -1)

def cp(pair): return curses.color_pair(pair)

# ─── Drawing helpers ──────────────────────────────────────────────────────────

def safe_addstr(win, y, x, s, attr=0):
    h, w = win.getmaxyx()
    if y < 0 or y >= h: return
    if x < 0: 
        s = s[-x:]; x = 0
    if x >= w: return
    max_len = w - x - 1
    if len(s) > max_len:
        s = s[:max_len]
    try:
        win.addstr(y, x, s, attr)
    except curses.error:
        pass

def draw_box(win, y, x, h, w, title="", color=None):
    attr = cp(C_ACCENT) if color is None else color
    try:
        win.attron(attr)
        win.addch(y, x, curses.ACS_ULCORNER)
        win.hline(y, x+1, curses.ACS_HLINE, w-2)
        win.addch(y, x+w-1, curses.ACS_URCORNER)
        for row in range(y+1, y+h-1):
            win.addch(row, x, curses.ACS_VLINE)
            win.addch(row, x+w-1, curses.ACS_VLINE)
        win.addch(y+h-1, x, curses.ACS_LLCORNER)
        win.hline(y+h-1, x+1, curses.ACS_HLINE, w-2)
        try:
            win.addch(y+h-1, x+w-1, curses.ACS_LRCORNER)
        except curses.error:
            pass
        win.attroff(attr)
        if title:
            t = f" {title} "
            safe_addstr(win, y, x+2, t, attr | curses.A_BOLD)
    except curses.error:
        pass

def center_str(win, y, s, attr=0):
    _, w = win.getmaxyx()
    x = max(0, (w - len(s)) // 2)
    safe_addstr(win, y, x, s, attr)

# ─── Loading screen ───────────────────────────────────────────────────────────

def loading_screen(stdscr, message="Fetching content..."):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    for i in range(30):
        stdscr.clear()
        spinner = frames[i % len(frames)]
        center_str(stdscr, h//2 - 1, "FastType", cp(C_TITLE) | curses.A_BOLD)
        center_str(stdscr, h//2 + 1, f"{spinner}  {message}", cp(C_DIM))
        stdscr.refresh()
        time.sleep(0.08)

# ─── Stats calculation ────────────────────────────────────────────────────────

def calc_stats(target: str, typed: str, elapsed: float):
    if elapsed <= 0:
        elapsed = 0.001
    minutes = elapsed / 60

    correct_chars = sum(1 for a, b in zip(target, typed) if a == b)
    total_typed = len(typed)
    errors = sum(1 for a, b in zip(target, typed) if a != b)
    errors += abs(len(target) - len(typed))

    # WPM: correct chars / 5 / minutes
    wpm = (correct_chars / 5) / minutes if minutes > 0 else 0
    raw_wpm = (total_typed / 5) / minutes if minutes > 0 else 0

    accuracy = (correct_chars / max(len(target), 1)) * 100

    return {
        "wpm": round(wpm, 1),
        "raw_wpm": round(raw_wpm, 1),
        "accuracy": round(accuracy, 1),
        "correct_chars": correct_chars,
        "errors": errors,
        "elapsed": round(elapsed, 2),
        "chars_typed": total_typed,
    }

# ─── Typing test core ─────────────────────────────────────────────────────────

def run_typing_test(stdscr, text: str, mode: str, zen_mode=False, author="", difficulty="medium"):
    """Core typing engine. Returns stats dict or None if quit."""
    h, w = stdscr.getmaxyx()
    curses.cbreak()
    stdscr.nodelay(True)
    stdscr.keypad(True)

    typed = []
    start_time = None
    end_time = None
    done = False
    blink_state = True
    last_blink = time.time()

    # Wrap text to fit screen width (leave margins)
    margin = 8
    wrap_w = min(80, w - margin * 2)
    lines = textwrap.wrap(text, wrap_w)
    # Flatten back to track position
    flat = text  # original for comparison
    target = text

    # Pre-compute display lines and char offsets
    display_lines = lines
    line_starts = []
    pos = 0
    for line in display_lines:
        line_starts.append(pos)
        pos += len(line) + 1  # +1 for space between words that wrap

    # total height needed
    text_area_top = 5
    text_area_height = len(display_lines) + 2

    live_wpm = 0.0
    live_acc = 100.0

    while not done:
        h, w = stdscr.getmaxyx()
        now = time.time()

        # Cursor blink
        if now - last_blink > 0.5:
            blink_state = not blink_state
            last_blink = now

        stdscr.clear()

        # ── Header ──
        title = "FastType"
        diff_icons = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
        diff_label = f" {difficulty.upper()}" if mode not in ("zen", "custom") else ""
        mode_label = f"[{mode.upper()}{diff_label}]"
        if zen_mode:
            mode_label = "[ZEN]"
        safe_addstr(stdscr, 0, 2, title, cp(C_TITLE) | curses.A_BOLD)
        safe_addstr(stdscr, 0, w - len(mode_label) - 2, mode_label, cp(C_ACCENT))
        stdscr.hline(1, 0, curses.ACS_HLINE, w)

        # ── Live stats ──
        if start_time and not end_time:
            elapsed = now - start_time
            stats = calc_stats(target, "".join(typed), elapsed)
            live_wpm = stats["wpm"]
            live_acc = stats["accuracy"]

        progress = len(typed) / max(len(target), 1) * 100

        if not zen_mode:
            wpm_str  = f"WPM: {live_wpm:.0f}"
            acc_str  = f"ACC: {live_acc:.0f}%"
            prog_str = f"Progress: {progress:.0f}%"
            safe_addstr(stdscr, 2, 2, wpm_str,  cp(C_ACCENT) | curses.A_BOLD)
            safe_addstr(stdscr, 2, 14, acc_str, cp(C_HEADER) | curses.A_BOLD)
            safe_addstr(stdscr, 2, 26, prog_str, cp(C_DIM))

        # ── Text display ──
        typed_len = len(typed)
        cursor_pos = typed_len

        text_x = (w - wrap_w) // 2
        if text_x < 2: text_x = 2

        if author:
            safe_addstr(stdscr, text_area_top - 1, text_x, f'"{display_lines[0][:4]}..." — {author}', cp(C_DIM))

        for li, line in enumerate(display_lines):
            row = text_area_top + li
            if row >= h - 2: break
            line_start = line_starts[li]
            for ci, ch in enumerate(line):
                global_pos = line_start + ci
                col = text_x + ci
                if col >= w - 1: break

                if global_pos < typed_len:
                    # Already typed
                    typed_ch = typed[global_pos]
                    if typed_ch == ch:
                        attr = cp(C_CORRECT)
                    else:
                        attr = cp(C_WRONG) | curses.A_UNDERLINE
                elif global_pos == cursor_pos:
                    # Cursor position
                    if blink_state:
                        attr = cp(C_CURSOR)
                    else:
                        attr = cp(C_DIM)
                else:
                    # Not yet typed — grayed out
                    attr = cp(C_DIM)

                try:
                    stdscr.addch(row, col, ch, attr)
                except curses.error:
                    pass

        # ── Footer hint ──
        hint = "ESC: quit  |  TAB: restart"
        safe_addstr(stdscr, h-1, 2, hint, cp(C_DIM))

        stdscr.refresh()

        # ── Input ──
        try:
            key = stdscr.getch()
        except Exception:
            key = -1

        if key == 27:  # ESC
            return None
        elif key == 9:  # TAB → restart
            return "restart"
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if typed:
                typed.pop()
        elif key == curses.KEY_RESIZE:
            stdscr.clear()
        elif 32 <= key <= 126:
            ch = chr(key)
            if start_time is None:
                start_time = time.time()
            typed.append(ch)

            # Check completion
            if len(typed) >= len(target):
                end_time = time.time()
                done = True

        time.sleep(0.016)

    # ── Final stats ──
    elapsed = end_time - start_time if start_time else 0
    stats = calc_stats(target, "".join(typed), elapsed)
    stats["mode"] = mode
    stats["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    if author:
        stats["author"] = author
    return stats

# ─── Results screen ───────────────────────────────────────────────────────────

def show_results(stdscr, stats: dict):
    stdscr.nodelay(False)
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    bx = max(2, w//2 - 28)
    bw = min(56, w - 4)
    by = max(1, h//2 - 9)
    bh = 18

    draw_box(stdscr, by, bx, bh, bw, "Results", cp(C_ACCENT))

    cx = bx + bw // 2

    safe_addstr(stdscr, by+2, cx - 7, "─── FastType ───", cp(C_TITLE) | curses.A_BOLD)

    wpm  = stats.get("wpm", 0)
    raw  = stats.get("raw_wpm", 0)
    acc  = stats.get("accuracy", 0)
    err  = stats.get("errors", 0)
    sec  = stats.get("elapsed", 0)
    mode = stats.get("mode", "?")
    date = stats.get("date", "")

    # WPM big display
    wpm_str = f"{wpm:.0f} WPM"
    safe_addstr(stdscr, by+4, cx - len(wpm_str)//2, wpm_str,
                cp(C_GOOD) | curses.A_BOLD)

    diff = stats.get("difficulty", "")
    diff_display = diff.title() if diff else "—"
    rows = [
        ("Raw WPM",    f"{raw:.0f}"),
        ("Accuracy",   f"{acc:.1f}%"),
        ("Errors",     f"{err}"),
        ("Time",       f"{sec:.1f}s"),
        ("Mode",       mode.title()),
        ("Difficulty", diff_display),
        ("Date",       date),
    ]

    for i, (label, val) in enumerate(rows):
        lx = bx + 4
        vx = bx + bw - len(val) - 4
        safe_addstr(stdscr, by+6+i, lx, label, cp(C_DIM))
        color = cp(C_GOOD) if label in ("Accuracy", "WPM") and float(val.replace('%','')) > 90 else cp(C_NORMAL)
        safe_addstr(stdscr, by+6+i, vx, val, color | curses.A_BOLD)

    safe_addstr(stdscr, by+bh-3, cx-17, "Press ENTER to continue  |  TAB to retry", cp(C_DIM))

    stdscr.refresh()

    while True:
        key = stdscr.getch()
        if key in (10, 13):  # ENTER
            return "menu"
        elif key == 9:  # TAB
            return "retry"
        elif key == 27:
            return "menu"

# ─── History screen ───────────────────────────────────────────────────────────

def show_history(stdscr):
    scores = load_scores()
    stdscr.nodelay(False)
    offset = 0
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        safe_addstr(stdscr, 0, 2, "FastType", cp(C_TITLE) | curses.A_BOLD)
        safe_addstr(stdscr, 0, w-14, "[HISTORY]", cp(C_ACCENT))
        stdscr.hline(1, 0, curses.ACS_HLINE, w)

        if not scores:
            center_str(stdscr, h//2, "No scores yet. Go type something!", cp(C_DIM))
        else:
            # Stats summary
            wpms = [s.get("wpm",0) for s in scores]
            accs = [s.get("accuracy",0) for s in scores]
            best_wpm = max(wpms)
            avg_wpm  = sum(wpms)/len(wpms)
            avg_acc  = sum(accs)/len(accs)
            runs     = len(scores)

            header_y = 2
            safe_addstr(stdscr, header_y, 2,
                        f"Runs: {runs}   Best WPM: {best_wpm:.0f}   Avg WPM: {avg_wpm:.0f}   Avg Acc: {avg_acc:.1f}%",
                        cp(C_HEADER) | curses.A_BOLD)
            stdscr.hline(header_y+1, 0, curses.ACS_HLINE, w)

            # Column headers
            col_y = header_y + 2
            safe_addstr(stdscr, col_y, 2,  "Date",       cp(C_ACCENT) | curses.A_BOLD)
            safe_addstr(stdscr, col_y, 22, "Mode",       cp(C_ACCENT) | curses.A_BOLD)
            safe_addstr(stdscr, col_y, 32, "Diff",       cp(C_ACCENT) | curses.A_BOLD)
            safe_addstr(stdscr, col_y, 40, "WPM",        cp(C_ACCENT) | curses.A_BOLD)
            safe_addstr(stdscr, col_y, 48, "Raw",        cp(C_ACCENT) | curses.A_BOLD)
            safe_addstr(stdscr, col_y, 56, "Accuracy",   cp(C_ACCENT) | curses.A_BOLD)
            safe_addstr(stdscr, col_y, 68, "Errors",     cp(C_ACCENT) | curses.A_BOLD)
            stdscr.hline(col_y+1, 0, curses.ACS_HLINE, w)

            list_top = col_y + 2
            visible_rows = h - list_top - 3
            visible_scores = list(reversed(scores))  # newest first
            for i, s in enumerate(visible_scores[offset:offset+visible_rows]):
                row = list_top + i
                date = s.get("date", "")[:16]
                mode = s.get("mode", "?")[:8]
                diff = s.get("difficulty", "—")[:6]
                wpm  = f"{s.get('wpm',0):.0f}"
                raw  = f"{s.get('raw_wpm',0):.0f}"
                acc  = f"{s.get('accuracy',0):.1f}%"
                err  = str(s.get("errors",0))

                wpm_c = cp(C_GOOD) if s.get("wpm",0) >= best_wpm * 0.9 else cp(C_NORMAL)
                diff_colors = {"easy": C_GOOD, "medium": C_HEADER, "hard": C_BAD}
                diff_c = cp(diff_colors.get(diff, C_DIM))

                safe_addstr(stdscr, row, 2,  date, cp(C_DIM))
                safe_addstr(stdscr, row, 22, mode, cp(C_NORMAL))
                safe_addstr(stdscr, row, 32, diff, diff_c | curses.A_BOLD)
                safe_addstr(stdscr, row, 40, wpm,  wpm_c | curses.A_BOLD)
                safe_addstr(stdscr, row, 48, raw,  cp(C_DIM))
                safe_addstr(stdscr, row, 56, acc,  cp(C_GOOD) if float(acc[:-1]) >= 95 else cp(C_NORMAL))
                safe_addstr(stdscr, row, 68, err,  cp(C_BAD) if int(err) > 5 else cp(C_DIM))

        safe_addstr(stdscr, h-1, 2, "↑↓: scroll   ESC/Q: back", cp(C_DIM))
        stdscr.refresh()

        key = stdscr.getch()
        if key in (27, ord('q'), ord('Q')):
            return
        elif key == curses.KEY_UP and offset > 0:
            offset -= 1
        elif key == curses.KEY_DOWN:
            offset += 1

# ─── Settings screen ──────────────────────────────────────────────────────────

def show_settings(stdscr, cfg: dict):
    stdscr.nodelay(False)
    options = [
        ("difficulty",        "Difficulty",        ["easy", "medium", "hard"]),
        ("word_count",        "Word Count",        [10, 15, 25, 50, 100]),
        ("zen_duration",      "Zen Duration (s)",  [30, 60, 90, 120, 180]),
        ("show_wpm_live",     "Show Live WPM",     [True, False]),
    ]
    selected = 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        safe_addstr(stdscr, 0, 2, "FastType", cp(C_TITLE) | curses.A_BOLD)
        safe_addstr(stdscr, 0, w-14, "[SETTINGS]", cp(C_ACCENT))
        stdscr.hline(1, 0, curses.ACS_HLINE, w)

        for i, (key, label, values) in enumerate(options):
            row = 3 + i * 2
            is_sel = i == selected
            cur_val = cfg.get(key)
            try:
                vi = values.index(cur_val)
            except ValueError:
                vi = 0

            bullet = "▶" if is_sel else " "
            attr = cp(C_ACCENT) | curses.A_BOLD if is_sel else cp(C_NORMAL)

            safe_addstr(stdscr, row, 2, f"{bullet} {label}", attr)

            # Show values as a selector
            vx = 30
            for j, v in enumerate(values):
                vs = str(v)
                if j == vi:
                    val_attr = cp(C_GOOD) | curses.A_REVERSE if is_sel else cp(C_ACCENT) | curses.A_BOLD
                else:
                    val_attr = cp(C_DIM)
                safe_addstr(stdscr, row, vx, vs, val_attr)
                vx += len(vs) + 3

        safe_addstr(stdscr, h-1, 2,
                    "↑↓: select   ←→: change value   ESC/Q: save & back",
                    cp(C_DIM))
        stdscr.refresh()

        key_input = stdscr.getch()
        if key_input in (27, ord('q'), ord('Q')):
            save_config(cfg)
            return
        elif key_input == curses.KEY_UP:
            selected = (selected - 1) % len(options)
        elif key_input == curses.KEY_DOWN:
            selected = (selected + 1) % len(options)
        elif key_input in (curses.KEY_LEFT, curses.KEY_RIGHT):
            opt_key, _, values = options[selected]
            cur = cfg.get(opt_key)
            try:
                vi = values.index(cur)
            except ValueError:
                vi = 0
            if key_input == curses.KEY_RIGHT:
                vi = (vi + 1) % len(values)
            else:
                vi = (vi - 1) % len(values)
            cfg[opt_key] = values[vi]


# ─── Difficulty picker ────────────────────────────────────────────────────────

DIFFICULTY_INFO = {
    "easy":   ("Easy",   "Short common words & brief quotes",    "2-4 letter everyday words"),
    "medium": ("Medium", "Everyday words & standard quotes",     "4-7 letter common words"),
    "hard":   ("Hard",   "Longer complex words & long quotes",   "7-12 letter advanced words"),
}

def pick_difficulty(stdscr, current: str) -> str:
    """Show a difficulty selection screen. Returns chosen difficulty or current."""
    levels = ["easy", "medium", "hard"]
    try:
        sel = levels.index(current)
    except ValueError:
        sel = 1

    stdscr.nodelay(False)

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        safe_addstr(stdscr, 0, 2, "FastType", cp(C_TITLE) | curses.A_BOLD)
        safe_addstr(stdscr, 0, w - 16, "[DIFFICULTY]", cp(C_ACCENT))
        stdscr.hline(1, 0, curses.ACS_HLINE, w)
        center_str(stdscr, 3, "Choose a difficulty level", cp(C_HEADER) | curses.A_BOLD)

        box_w = min(52, w - 4)
        bx = max(2, (w - box_w) // 2)

        level_colors = {"easy": C_GOOD, "medium": C_HEADER, "hard": C_BAD}

        for i, lvl in enumerate(levels):
            name, tagline, word_desc = DIFFICULTY_INFO[lvl]
            row = 5 + i * 4
            is_sel = i == sel
            lc = level_colors[lvl]

            if is_sel:
                draw_box(stdscr, row, bx, 3, box_w, color=cp(lc))
                bullet = "▶"
                name_attr   = cp(lc) | curses.A_BOLD
                desc_attr   = cp(C_NORMAL)
            else:
                # dim unfocused box
                try:
                    stdscr.attron(cp(C_DIM))
                    stdscr.addch(row,     bx,          curses.ACS_ULCORNER)
                    stdscr.hline(row,     bx+1,        curses.ACS_HLINE, box_w-2)
                    stdscr.addch(row,     bx+box_w-1,  curses.ACS_URCORNER)
                    stdscr.addch(row+1,   bx,          curses.ACS_VLINE)
                    stdscr.addch(row+1,   bx+box_w-1,  curses.ACS_VLINE)
                    stdscr.addch(row+2,   bx,          curses.ACS_LLCORNER)
                    stdscr.hline(row+2,   bx+1,        curses.ACS_HLINE, box_w-2)
                    try:
                        stdscr.addch(row+2, bx+box_w-1, curses.ACS_LRCORNER)
                    except curses.error:
                        pass
                    stdscr.attroff(cp(C_DIM))
                except curses.error:
                    pass
                bullet = " "
                name_attr = cp(C_DIM) | curses.A_BOLD
                desc_attr = cp(C_DIM)

            safe_addstr(stdscr, row+1, bx+2, f"{bullet} {name:<8}  {tagline}", name_attr)
            safe_addstr(stdscr, row+1, bx + box_w - len(word_desc) - 3, word_desc, desc_attr)

        # Current saved indicator
        saved_row = 5 + len(levels) * 4 + 1
        saved_label = f"(saved: {current})"
        center_str(stdscr, saved_row, saved_label, cp(C_DIM))

        safe_addstr(stdscr, h-1, 2, "↑↓: select   ENTER: confirm   ESC: cancel", cp(C_DIM))
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP:
            sel = (sel - 1) % len(levels)
        elif key == curses.KEY_DOWN:
            sel = (sel + 1) % len(levels)
        elif key in (10, 13, curses.KEY_ENTER):
            return levels[sel]
        elif key == 27:
            return current

# ─── Custom text input ────────────────────────────────────────────────────────

def get_custom_text(stdscr) -> str | None:
    stdscr.nodelay(False)
    curses.echo()
    curses.curs_set(1)
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    safe_addstr(stdscr, 0, 2, "FastType", cp(C_TITLE) | curses.A_BOLD)
    safe_addstr(stdscr, 0, w-14, "[CUSTOM]", cp(C_ACCENT))
    stdscr.hline(1, 0, curses.ACS_HLINE, w)
    center_str(stdscr, 3, "Enter your custom text below:", cp(C_HEADER) | curses.A_BOLD)
    safe_addstr(stdscr, 4, 2, "(Press ENTER twice or ESC when done)", cp(C_DIM))
    stdscr.hline(5, 0, curses.ACS_HLINE, w)

    lines = []
    row = 7
    input_w = min(80, w - 4)
    bx = (w - input_w) // 2

    safe_addstr(stdscr, row - 1, bx, "▼ Type here (empty line to finish):", cp(C_ACCENT))

    text_lines = []
    while True:
        try:
            safe_addstr(stdscr, row + len(text_lines), bx, "> ", cp(C_ACCENT))
            stdscr.refresh()
            line_bytes = stdscr.getstr(row + len(text_lines), bx + 2, input_w - 2)
            line = line_bytes.decode("utf-8", errors="ignore").strip()
        except Exception:
            break
        if not line:
            break
        text_lines.append(line)

    curses.noecho()
    curses.curs_set(0)

    result = " ".join(text_lines).strip()
    if len(result) < 5:
        return None
    return result

# ─── Main menu ────────────────────────────────────────────────────────────────

MENU_ITEMS = [
    ("Words",   "words",   "Type a set of random words"),
    ("Quote",   "quote",   "Type a famous quote"),
    ("Zen",     "zen",     "Unlimited free typing — no pressure"),
    ("Custom",  "custom",  "Type your own text"),
    ("History", "history", "View your past scores & stats"),
    ("Settings","settings","Configure FastType"),
    ("Quit",    "quit",    "Exit FastType"),
]

def draw_menu(stdscr, selected: int):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    # Title art
    title_lines = [
        "  ███████╗ █████╗ ███████╗████████╗████████╗██╗   ██╗██████╗ ███████╗",
        "  ██╔════╝██╔══██╗██╔════╝╚══██╔══╝╚══██╔══╝╚██╗ ██╔╝██╔══██╗██╔════╝",
        "  █████╗  ███████║███████╗   ██║      ██║    ╚████╔╝ ██████╔╝█████╗  ",
        "  ██╔══╝  ██╔══██║╚════██║   ██║      ██║     ╚██╔╝  ██╔═══╝ ██╔══╝  ",
        "  ██║     ██║  ██║███████║   ██║      ██║      ██║   ██║     ███████╗",
        "  ╚═╝     ╚═╝  ╚═╝╚══════╝   ╚═╝      ╚═╝      ╚═╝   ╚═╝     ╚══════╝",
    ]
    title_top = max(1, h//2 - len(MENU_ITEMS) - len(title_lines) - 1)
    for i, line in enumerate(title_lines):
        if title_top + i < h:
            x = max(0, (w - len(line)) // 2)
            safe_addstr(stdscr, title_top + i, x, line,
                        cp(C_TITLE) | curses.A_BOLD)

    subtitle = "A terminal typing speed trainer"
    center_str(stdscr, title_top + len(title_lines) + 1, subtitle, cp(C_DIM))

    menu_top = title_top + len(title_lines) + 3
    menu_w   = 42
    mx       = max(0, (w - menu_w) // 2)

    for i, (label, _, desc) in enumerate(MENU_ITEMS):
        row = menu_top + i * 2
        if row >= h - 1: break
        if i == selected:
            safe_addstr(stdscr, row, mx, f"  ▶  {label:<12}  {desc}", cp(C_ACCENT) | curses.A_BOLD)
        else:
            safe_addstr(stdscr, row, mx, f"     {label:<12}  {desc}", cp(C_DIM))

    safe_addstr(stdscr, h-1, 2, "↑↓: navigate   ENTER: select", cp(C_DIM))
    stdscr.refresh()

# ─── App entry ────────────────────────────────────────────────────────────────

def run_app(stdscr):
    init_colors()
    curses.curs_set(0)

    cfg = load_config()
    selected = 0

    pending_mode = None  # if we want to auto-start after restart
    last_text    = None
    last_author  = ""
    last_mode    = None

    while True:
        if pending_mode:
            mode = pending_mode
            pending_mode = None
        else:
            # Main menu
            stdscr.nodelay(False)
            while True:
                draw_menu(stdscr, selected)
                key = stdscr.getch()
                if key == curses.KEY_UP:
                    selected = (selected - 1) % len(MENU_ITEMS)
                elif key == curses.KEY_DOWN:
                    selected = (selected + 1) % len(MENU_ITEMS)
                elif key in (10, 13, curses.KEY_ENTER):
                    mode = MENU_ITEMS[selected][1]
                    break
                elif key == ord('q') or key == ord('Q'):
                    mode = "quit"
                    break
                # Quick shortcuts
                elif key == ord('w'): mode = "words"; break
                elif key == ord('z'): mode = "zen"; break
                elif key == ord('c'): mode = "custom"; break
                elif key == ord('h'): mode = "history"; break
                elif key == ord('s'): mode = "settings"; break

        if mode == "quit":
            break

        elif mode == "history":
            show_history(stdscr)

        elif mode == "settings":
            show_settings(stdscr, cfg)

        elif mode in ("words", "quote", "zen", "custom"):
            # Difficulty picker for words and quote modes
            if mode in ("words", "quote"):
                diff = pick_difficulty(stdscr, cfg.get("difficulty", "medium"))
                cfg["difficulty"] = diff
                save_config(cfg)
            else:
                diff = cfg.get("difficulty", "medium")

            # Fetch / prepare text
            if mode == "words":
                loading_screen(stdscr, f"Fetching {diff} words...")
                text   = fetch_random_words(cfg.get("word_count", 25), difficulty=diff)
                author = ""
                zen    = False

            elif mode == "quote":
                loading_screen(stdscr, f"Fetching a {diff} quote...")
                text, author = fetch_quote(difficulty=diff)
                zen = False

            elif mode == "zen":
                loading_screen(stdscr, "Fetching words for Zen mode...")
                text   = fetch_random_words(200, difficulty=cfg.get("difficulty", "medium"))
                author = ""
                zen    = True

            elif mode == "custom":
                text = get_custom_text(stdscr)
                if not text:
                    continue
                author = ""
                zen    = False

            last_text   = text
            last_author = author
            last_mode   = mode

            result = run_typing_test(stdscr, text, mode, zen_mode=zen, author=author, difficulty=diff)

            if result is None:
                continue  # ESC → back to menu
            elif result == "restart":
                pending_mode = mode
                continue
            else:
                # Save score
                save_score(result)
                action = show_results(stdscr, result)
                if action == "retry":
                    pending_mode = mode

def main():
    try:
        curses.wrapper(run_app)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()