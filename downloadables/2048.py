"""
2048 — curses, stdlib only

Controls:  arrow keys to slide   q / Esc to quit
"""

import curses
import random

# ── Tile colours ─────────────────────────────────────────────────────────────
# pair index → (fg, bg) — we only have 8 basic colours, so we cycle
TILE_COLORS = {
    0:    1,
    2:    2,
    4:    3,
    8:    4,
    16:   5,
    32:   6,
    64:   7,
    128:  8,
    256:  2,
    512:  3,
    1024: 4,
    2048: 5,
}

CELL_W = 7   # width of each cell in characters
CELL_H = 3   # height of each cell in lines


# ── Game logic ────────────────────────────────────────────────────────────────

def empty_board():
    return [[0] * 4 for _ in range(4)]

def add_tile(board):
    empty = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]
    if empty:
        r, c = random.choice(empty)
        board[r][c] = 4 if random.random() < 0.1 else 2

def slide_left(row):
    """Slide and merge one row to the left. Returns (new_row, score_gained)."""
    tiles  = [x for x in row if x != 0]
    merged = []
    score  = 0
    i = 0
    while i < len(tiles):
        if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
            val = tiles[i] * 2
            merged.append(val)
            score += val
            i += 2
        else:
            merged.append(tiles[i])
            i += 1
    merged += [0] * (4 - len(merged))
    return merged, score

def move(board, direction):
    """
    Apply a move. direction: 'left','right','up','down'
    Returns (new_board, score_gained, moved: bool)
    """
    score = 0
    b = [row[:] for row in board]

    # Rotate board so we always slide left
    if direction == 'right':
        b = [row[::-1] for row in b]
    elif direction == 'up':
        b = [list(col) for col in zip(*b)]
    elif direction == 'down':
        b = [list(col) for col in zip(*b)]
        b = [row[::-1] for row in b]

    new_b = []
    for row in b:
        new_row, s = slide_left(row)
        new_b.append(new_row)
        score += s

    # Rotate back
    if direction == 'right':
        new_b = [row[::-1] for row in new_b]
    elif direction == 'up':
        new_b = [list(col) for col in zip(*new_b)]
    elif direction == 'down':
        new_b = [row[::-1] for row in new_b]
        new_b = [list(col) for col in zip(*new_b)]

    moved = new_b != board
    return new_b, score, moved

def is_game_over(board):
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                return False
            if c < 3 and board[r][c] == board[r][c + 1]:
                return False
            if r < 3 and board[r][c] == board[r + 1][c]:
                return False
    return True

def has_won(board):
    return any(board[r][c] == 2048 for r in range(4) for c in range(4))


# ── Drawing ───────────────────────────────────────────────────────────────────

def draw(stdscr, board, score, best, message=""):
    stdscr.erase()

    # Header
    try:
        stdscr.addstr(0, 0, f" 2048", curses.A_BOLD)
        stdscr.addstr(0, 10, f"Score: {score:<8}", curses.A_BOLD)
        stdscr.addstr(0, 28, f"Best: {best:<8}", curses.A_BOLD)
        stdscr.addstr(1, 0, " arrows = move   q = quit   n = new game")
    except curses.error:
        pass

    origin_r = 3
    origin_c = 1

    board_w = 4 * CELL_W + 1
    board_h = 4 * CELL_H + 1

    # Draw grid lines
    for r in range(5):
        row = origin_r + r * CELL_H
        for c in range(board_w):
            try:
                stdscr.addch(row, origin_c + c, curses.ACS_HLINE)
            except curses.error:
                pass
    for c in range(5):
        col = origin_c + c * CELL_W
        for r in range(board_h):
            try:
                stdscr.addch(origin_r + r, col, curses.ACS_VLINE)
            except curses.error:
                pass
    # Corners / intersections (simple +)
    for r in range(5):
        for c in range(5):
            try:
                stdscr.addch(origin_r + r * CELL_H,
                             origin_c + c * CELL_W, '+')
            except curses.error:
                pass

    # Draw tiles
    for r in range(4):
        for c in range(4):
            val  = board[r][c]
            pair = TILE_COLORS.get(val, 1)
            attr = curses.color_pair(pair) | curses.A_BOLD

            cell_r = origin_r + r * CELL_H + 1
            cell_c = origin_c + c * CELL_W + 1

            # Fill cell background rows
            for dr in range(CELL_H - 1):
                try:
                    stdscr.addstr(cell_r + dr, cell_c,
                                  ' ' * (CELL_W - 1), attr)
                except curses.error:
                    pass

            # Centre the number on the middle row
            text = str(val) if val else '·'
            pad  = (CELL_W - 1 - len(text)) // 2
            try:
                stdscr.addstr(cell_r, cell_c + pad, text, attr)
            except curses.error:
                pass

    if message:
        try:
            stdscr.addstr(origin_r + board_h + 1, 1,
                          message, curses.A_BOLD | curses.A_BLINK)
        except curses.error:
            pass

    stdscr.refresh()


# ── Screens ───────────────────────────────────────────────────────────────────

def start_screen(stdscr):
    stdscr.nodelay(False)
    lines = [
        "  ╔══════════════════════╗",
        "  ║   2  0  4  8         ║",
        "  ╠══════════════════════╣",
        "  ║  Slide tiles to      ║",
        "  ║  combine them.       ║",
        "  ║  Reach 2048 to win!  ║",
        "  ╠══════════════════════╣",
        "  ║  SPACE / ENTER start ║",
        "  ║  q           quit    ║",
        "  ╚══════════════════════╝",
    ]
    while True:
        stdscr.erase()
        rows, cols = stdscr.getmaxyx()
        sr = max(0, rows // 2 - len(lines) // 2)
        for i, line in enumerate(lines):
            try:
                stdscr.addstr(sr + i, max(0, (cols - len(line)) // 2),
                              line, curses.A_BOLD)
            except curses.error:
                pass
        stdscr.refresh()
        key = stdscr.getch()
        if key in (ord(' '), ord('\n'), curses.KEY_ENTER):
            return True
        if key in (ord('q'), ord('Q'), 27):
            return False


# ── Main ──────────────────────────────────────────────────────────────────────

def game(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    pairs = [
        (curses.COLOR_WHITE,   -1),  # 1 empty
        (curses.COLOR_GREEN,   -1),  # 2
        (curses.COLOR_CYAN,    -1),  # 3
        (curses.COLOR_BLUE,    -1),  # 4
        (curses.COLOR_MAGENTA, -1),  # 5
        (curses.COLOR_RED,     -1),  # 6
        (curses.COLOR_YELLOW,  -1),  # 7
        (curses.COLOR_WHITE,   -1),  # 8
    ]
    for i, (fg, bg) in enumerate(pairs, start=1):
        curses.init_pair(i, fg, bg)

    best = 0

    while True:
        if not start_screen(stdscr):
            return

        board = empty_board()
        add_tile(board)
        add_tile(board)
        score   = 0
        won     = False
        message = ""

        stdscr.nodelay(False)
        stdscr.keypad(True)

        while True:
            draw(stdscr, board, score, best, message)
            key = stdscr.getch()

            direction = None
            if key == curses.KEY_LEFT:   direction = 'left'
            elif key == curses.KEY_RIGHT: direction = 'right'
            elif key == curses.KEY_UP:    direction = 'up'
            elif key == curses.KEY_DOWN:  direction = 'down'
            elif key in (ord('n'), ord('N')):
                break   # new game
            elif key in (ord('q'), ord('Q'), 27):
                return  # quit

            if direction:
                message = ""
                new_board, gained, moved = move(board, direction)
                if moved:
                    board  = new_board
                    score += gained
                    best   = max(best, score)
                    add_tile(board)

                if not won and has_won(board):
                    won     = True
                    message = "  🎉  You reached 2048!  Press any key…"
                    draw(stdscr, board, score, best, message)
                    stdscr.getch()
                    message = "  Keep going! (n=new game)"

                if is_game_over(board):
                    message = f"  Game over! Score {score}  —  n=new  q=quit"
                    draw(stdscr, board, score, best, message)
                    while True:
                        k = stdscr.getch()
                        if k in (ord('n'), ord('N')):
                            break
                        if k in (ord('q'), ord('Q'), 27):
                            return
                    break  # new game


if __name__ == "__main__":
    curses.wrapper(game)