"""
Minesweeper — curses, stdlib only

Controls:
  arrow keys / wasd   move cursor
  space / enter       reveal cell
  f                   flag / unflag
  r                   restart
  q / Esc             quit

Difficulties (chosen at start screen):
  e  Easy    9×9,   10 mines
  m  Medium  16×16, 40 mines
  h  Hard    16×30, 99 mines
"""

import curses
import random
import time

# ── Difficulty presets ────────────────────────────────────────────────────────

DIFFICULTIES = {
    'e': ("Easy",   9,  9,  10),
    'm': ("Medium", 16, 16, 40),
    'h': ("Hard",   16, 30, 99),
}

# ── Cell state flags ──────────────────────────────────────────────────────────

HIDDEN   = 0
REVEALED = 1
FLAGGED  = 2


# ── Board logic ───────────────────────────────────────────────────────────────

def make_board(rows, cols, mines, safe_r, safe_c):
    """
    Generate a board ensuring the first clicked cell and its
    neighbours are always safe.
    """
    safe = {(safe_r + dr, safe_c + dc)
            for dr in range(-1, 2) for dc in range(-1, 2)}

    candidates = [(r, c) for r in range(rows) for c in range(cols)
                  if (r, c) not in safe]
    mine_cells = set(random.sample(candidates, min(mines, len(candidates))))

    board = []
    for r in range(rows):
        row = []
        for c in range(cols):
            is_mine = (r, c) in mine_cells
            row.append({
                "mine":  is_mine,
                "state": HIDDEN,
                "adj":   0,
            })
        board.append(row)

    # Calculate adjacency numbers
    for r in range(rows):
        for c in range(cols):
            if not board[r][c]["mine"]:
                count = sum(
                    1 for dr in range(-1, 2) for dc in range(-1, 2)
                    if (dr or dc)
                    and 0 <= r + dr < rows
                    and 0 <= c + dc < cols
                    and board[r + dr][c + dc]["mine"]
                )
                board[r][c]["adj"] = count

    return board

def reveal(board, rows, cols, r, c):
    """Flood-fill reveal from (r, c)."""
    if not (0 <= r < rows and 0 <= c < cols):
        return
    cell = board[r][c]
    if cell["state"] != HIDDEN:
        return
    cell["state"] = REVEALED
    if cell["adj"] == 0 and not cell["mine"]:
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                if dr or dc:
                    reveal(board, rows, cols, r + dr, c + dc)

def count_flags(board, rows, cols):
    return sum(board[r][c]["state"] == FLAGGED
               for r in range(rows) for c in range(cols))

def check_win(board, rows, cols, mines):
    revealed = sum(board[r][c]["state"] == REVEALED
                   for r in range(rows) for c in range(cols))
    return revealed == rows * cols - mines


# ── Drawing ───────────────────────────────────────────────────────────────────

# Colour pair indices
C_DEFAULT  = 0
C_HIDDEN   = 1
C_FLAG     = 2
C_MINE     = 3
C_CURSOR   = 4
C_NUMBERS  = [0, 5, 6, 7, 8, 9, 10, 11, 12]  # index 0 unused, 1-8 → pairs 5-12

ADJ_CHARS = [' ', '1', '2', '3', '4', '5', '6', '7', '8']


def draw_board(stdscr, board, rows, cols, mines,
               cur_r, cur_c, state, elapsed, first_click):
    stdscr.erase()

    flags     = count_flags(board, rows, cols) if board else 0
    remaining = mines - flags

    # Status bar
    timer_str = f"{int(elapsed):03d}s" if not first_click else "---"
    try:
        stdscr.addstr(0, 0,
            f" Mines: {remaining:<4}  "
            f"{'[WON!]' if state == 'won' else '[DEAD]' if state == 'dead' else '      '}"
            f"  Time: {timer_str}",
            curses.A_BOLD)
        stdscr.addstr(1, 0,
            " arrows=move  space=reveal  f=flag  r=restart  q=quit")
    except curses.error:
        pass

    if board is None:
        return

    origin_r, origin_c = 2, 1

    for r in range(rows):
        for c in range(cols):
            cell    = board[r][c]
            s       = cell["state"]
            is_cur  = (r == cur_r and c == cur_c)
            sr      = origin_r + r
            sc      = origin_c + c * 2   # 2 chars wide per cell

            if is_cur:
                attr = curses.color_pair(C_CURSOR) | curses.A_BOLD
                ch   = '?'
                if s == FLAGGED:   ch = 'F'
                elif s == REVEALED:
                    if cell["mine"]: ch = '*'
                    else: ch = ADJ_CHARS[cell["adj"]]
            elif s == HIDDEN:
                attr = curses.color_pair(C_HIDDEN)
                ch   = '.'
            elif s == FLAGGED:
                attr = curses.color_pair(C_FLAG) | curses.A_BOLD
                ch   = 'F'
            elif s == REVEALED:
                if cell["mine"]:
                    attr = curses.color_pair(C_MINE) | curses.A_BOLD
                    ch   = '*'
                elif cell["adj"] == 0:
                    attr = curses.color_pair(C_DEFAULT)
                    ch   = ' '
                else:
                    pair = C_NUMBERS[cell["adj"]]
                    attr = curses.color_pair(pair) | curses.A_BOLD
                    ch   = ADJ_CHARS[cell["adj"]]
            else:
                attr = 0
                ch   = '?'

            try:
                stdscr.addstr(sr, sc, ch, attr)
                stdscr.addstr(sr, sc + 1, ' ')
            except curses.error:
                pass

    stdscr.refresh()


# ── Screens ───────────────────────────────────────────────────────────────────

def start_screen(stdscr):
    """Returns difficulty key ('e','m','h') or None to quit."""
    stdscr.nodelay(False)
    stdscr.keypad(True)
    lines = [
        "  ╔══════════════════════════╗",
        "  ║       MINESWEEPER        ║",
        "  ╠══════════════════════════╣",
        "  ║  e  Easy    9×9   10 💣  ║",
        "  ║  m  Medium 16×16  40 💣  ║",
        "  ║  h  Hard   16×30  99 💣  ║",
        "  ╠══════════════════════════╣",
        "  ║  q  quit                 ║",
        "  ╚══════════════════════════╝",
    ]
    while True:
        stdscr.erase()
        rows, cols = stdscr.getmaxyx()
        sr = max(0, rows // 2 - len(lines) // 2)
        for i, line in enumerate(lines):
            try:
                stdscr.addstr(sr + i,
                              max(0, (cols - len(line)) // 2),
                              line, curses.A_BOLD)
            except curses.error:
                pass
        stdscr.refresh()
        key = stdscr.getch()
        if key in (ord('e'), ord('E')): return 'e'
        if key in (ord('m'), ord('M')): return 'm'
        if key in (ord('h'), ord('H')): return 'h'
        if key in (ord('q'), ord('Q'), 27): return None


# ── Main ──────────────────────────────────────────────────────────────────────

def play(stdscr, diff_key):
    _, rows, cols, mines = DIFFICULTIES[diff_key]

    cur_r, cur_c = rows // 2, cols // 2
    board       = None          # built on first reveal
    state       = 'playing'     # 'playing' | 'won' | 'dead'
    first_click = True
    start_time  = None

    stdscr.nodelay(False)
    stdscr.keypad(True)
    curses.halfdelay(5)         # refresh timer display every 0.5 s

    while True:
        elapsed = (time.monotonic() - start_time) if start_time else 0
        draw_board(stdscr, board, rows, cols, mines,
                   cur_r, cur_c, state, elapsed, first_click)

        key = stdscr.getch()
        if key == curses.ERR:
            continue   # just a timer refresh

        # Quit / restart
        if key in (ord('q'), ord('Q'), 27):
            return False
        if key in (ord('r'), ord('R')):
            return True   # restart (caller shows start screen again)

        if state != 'playing':
            continue

        # Movement
        if   key in (curses.KEY_UP,    ord('w'), ord('W')): cur_r = max(0, cur_r - 1)
        elif key in (curses.KEY_DOWN,  ord('s'), ord('S')): cur_r = min(rows - 1, cur_r + 1)
        elif key in (curses.KEY_LEFT,  ord('a'), ord('A')): cur_c = max(0, cur_c - 1)
        elif key in (curses.KEY_RIGHT, ord('d'), ord('D')): cur_c = min(cols - 1, cur_c + 1)

        # Flag
        elif key in (ord('f'), ord('F')):
            if board:
                cell = board[cur_r][cur_c]
                if cell["state"] == HIDDEN:
                    cell["state"] = FLAGGED
                elif cell["state"] == FLAGGED:
                    cell["state"] = HIDDEN

        # Reveal
        elif key in (ord(' '), ord('\n'), curses.KEY_ENTER):
            # Build board on first reveal so first click is always safe
            if first_click:
                board       = make_board(rows, cols, mines, cur_r, cur_c)
                first_click = False
                start_time  = time.monotonic()

            cell = board[cur_r][cur_c]
            if cell["state"] == HIDDEN:
                if cell["mine"]:
                    cell["state"] = REVEALED
                    # Reveal all mines
                    for r in range(rows):
                        for c in range(cols):
                            if board[r][c]["mine"]:
                                board[r][c]["state"] = REVEALED
                    state = 'dead'
                else:
                    reveal(board, rows, cols, cur_r, cur_c)
                    if check_win(board, rows, cols, mines):
                        state = 'won'


def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(C_HIDDEN,  curses.COLOR_WHITE,   -1)
    curses.init_pair(C_FLAG,    curses.COLOR_YELLOW,  -1)
    curses.init_pair(C_MINE,    curses.COLOR_RED,     -1)
    curses.init_pair(C_CURSOR,  curses.COLOR_BLACK,   curses.COLOR_CYAN)
    # Number colours 1-8 → pairs 5-12
    number_colors = [
        curses.COLOR_BLUE,    # 1
        curses.COLOR_GREEN,   # 2
        curses.COLOR_RED,     # 3
        curses.COLOR_CYAN,    # 4
        curses.COLOR_MAGENTA, # 5
        curses.COLOR_YELLOW,  # 6
        curses.COLOR_WHITE,   # 7
        curses.COLOR_WHITE,   # 8
    ]
    for i, color in enumerate(number_colors, start=5):
        curses.init_pair(i, color, -1)

    while True:
        diff = start_screen(stdscr)
        if diff is None:
            return
        result = play(stdscr, diff)
        if not result:
            return   # quit


if __name__ == "__main__":
    curses.wrapper(main)