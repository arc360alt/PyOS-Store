# Note to self: Broken on linux, rewrite this at some point!
#!/usr/bin/env python3
"""
ARC Notes - A TUI notes application with proper error handling
Saves files with .arc extension

Usage: python arc_notes.py [filename.arc]

Needed PIP pkg's
WINDOWS: install windows-curses from pip
Linux: No need to install anything

Key bindings:
    Ctrl+S: Save file
    Ctrl+X: Exit
    Ctrl+L: Load file (opens file selector)
"""

import os
import sys
import subprocess
import tempfile

# Try to import curses, with a fallback option
try:
    import curses
    from curses import wrapper

    CURSES_AVAILABLE = True
except ImportError:
    CURSES_AVAILABLE = False
    print("Curses module not available. Installing fallback mode...")

# Try to import tkinter for file dialog (if not available, we'll use fallback methods)
try:
    import tkinter as tk
    from tkinter import filedialog

    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False


class ArcNotesFallback:
    """Fallback version when curses is not available"""

    def __init__(self, filename=None):
        self.filename = filename if filename else "untitled.arc"
        self.content = []

        # Load file if provided
        if filename and os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    self.content = f.read().split('\n')
                print(f"Loaded {filename}")
            except Exception as e:
                self.content = []
                print(f"Error loading file: {str(e)}")
        else:
            self.content = []
            if filename:
                print(f"New file: {filename}")
            else:
                print("New file")

    def display_content(self):
        """Clear the screen and display current content"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n".join(self.content))
        print("\n" + "-" * 40)
        print(f"File: {self.filename} | Lines: {len(self.content)}")
        print("Commands: :w (save), :q (quit), :wq (save and quit), :l (load)")
        print("> ", end="", flush=True)

    def save_file(self):
        """Save content to file"""
        try:
            with open(self.filename, 'w') as f:
                f.write('\n'.join(self.content))
            print(f"Saved {self.filename}")
            return True
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            return False

    def load_file(self):
        """Load a file"""
        print("\nEnter filename to load: ", end="", flush=True)
        filename = input()
        if filename and os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    self.content = f.read().split('\n')
                self.filename = filename
                print(f"Loaded {filename}")
            except Exception as e:
                print(f"Error loading file: {str(e)}")
        else:
            print(f"File not found: {filename}")
        input("Press Enter to continue...")

    def run(self):
        """Main editor loop"""
        while True:
            self.display_content()
            user_input = input()

            # Handle commands
            if user_input == ":q":
                break
            elif user_input == ":w":
                self.save_file()
            elif user_input == ":wq":
                self.save_file()
                break
            elif user_input == ":l":
                self.load_file()
            else:
                # Add the line to content
                self.content.append(user_input)


class ArcNotesCurses:
    """Curses-based version of the editor"""

    def __init__(self, stdscr, filename=None):
        self.stdscr = stdscr
        self.filename = filename if filename else "untitled.arc"
        self.content = []
        self.current_line = 0
        self.current_col = 0
        self.scroll_y = 0
        self.scroll_x = 0
        self.status_message = ""
        self.status_timer = 0

        # Initialize colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Status bar
        curses.init_pair(2, curses.COLOR_YELLOW, -1)  # Highlighted text

        # Load file if provided
        if filename and os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    self.content = f.read().split('\n')
                self.set_status(f"Loaded {filename}")
            except Exception as e:
                self.content = [""]
                self.set_status(f"Error loading file: {str(e)}")
        else:
            self.content = [""]
            if filename:
                self.set_status(f"New file: {filename}")
            else:
                self.set_status("New file")

    def set_status(self, message):
        self.status_message = message
        self.status_timer = 50  # Display for about 5 seconds

    def save_file(self):
        try:
            with open(self.filename, 'w') as f:
                f.write('\n'.join(self.content))
            self.set_status(f"Saved {self.filename}")
        except Exception as e:
            self.set_status(f"Error saving file: {str(e)}")

    def open_file_dialog(self):
        """Open a file selection dialog and load the selected file"""
        # Exit curses temporarily
        curses.endwin()

        new_filename = None

        # Choose file selection method based on availability
        if TKINTER_AVAILABLE:
            # Use tkinter file dialog
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            new_filename = filedialog.askopenfilename(
                title="Open File",
                filetypes=[("ARC Files", "*.arc"), ("All Files", "*.*")]
            )
            root.destroy()
        else:
            # Try using system-specific file selectors as fallback
            if os.name == 'nt':  # Windows
                try:
                    # PowerShell command to open file dialog
                    cmd = '''powershell -command "Add-Type -AssemblyName System.Windows.Forms;
                    $f = New-Object System.Windows.Forms.OpenFileDialog;
                    $f.Filter = 'ARC Files (*.arc)|*.arc|All Files (*.*)|*.*';
                    $f.ShowDialog() | Out-Null;
                    $f.FileName"'''
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0 and result.stdout.strip():
                        new_filename = result.stdout.strip()
                except Exception:
                    print("Could not open file dialog.")
            else:  # Linux/Mac
                try:
                    # Try using zenity if available
                    cmd = 'zenity --file-selection --title="Select File" --file-filter="*.arc"'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0 and result.stdout.strip():
                        new_filename = result.stdout.strip()
                except Exception:
                    print("Could not open file dialog.")

        # If no file selection method worked, show a message
        if new_filename is None or new_filename == '':
            print("No file selected or file dialog not available.")
            print("Press Enter to continue...")
            input()
        else:
            # Load the selected file
            try:
                with open(new_filename, 'r') as f:
                    self.content = f.read().split('\n')
                self.filename = new_filename
                self.current_line = 0
                self.current_col = 0
                self.scroll_x = 0
                self.scroll_y = 0
                self.set_status(f"Loaded {new_filename}")
            except Exception as e:
                print(f"Error loading file: {str(e)}")
                print("Press Enter to continue...")
                input()

        # Return to curses mode
        self.stdscr.refresh()

    def handle_key(self, key):
        height, width = self.stdscr.getmaxyx()

        # Ctrl+S: Save
        if key == 19:  # Ctrl+S
            self.save_file()
            return True

        # Ctrl+X: Exit
        elif key == 24:  # Ctrl+X
            return False

        # Ctrl+L: Load file
        elif key == 12:  # Ctrl+L
            self.open_file_dialog()
            return True

        # Enter key
        elif key == 10:  # Enter
            # Split the current line at cursor position
            current_line = self.content[self.current_line]
            self.content[self.current_line] = current_line[:self.current_col]
            self.content.insert(self.current_line + 1, current_line[self.current_col:])
            self.current_line += 1
            self.current_col = 0

        # Backspace
        elif key == 127 or key == curses.KEY_BACKSPACE:
            if self.current_col > 0:
                current_line = self.content[self.current_line]
                self.content[self.current_line] = current_line[:self.current_col - 1] + current_line[self.current_col:]
                self.current_col -= 1
            elif self.current_line > 0:
                # Join with the previous line
                self.current_col = len(self.content[self.current_line - 1])
                self.content[self.current_line - 1] += self.content[self.current_line]
                self.content.pop(self.current_line)
                self.current_line -= 1

        # Delete
        elif key == curses.KEY_DC:
            current_line = self.content[self.current_line]
            if self.current_col < len(current_line):
                self.content[self.current_line] = current_line[:self.current_col] + current_line[self.current_col + 1:]
            elif self.current_line < len(self.content) - 1:
                # Join with the next line
                self.content[self.current_line] += self.content[self.current_line + 1]
                self.content.pop(self.current_line + 1)

        # Arrow keys
        elif key == curses.KEY_UP:
            if self.current_line > 0:
                self.current_line -= 1
                self.current_col = min(self.current_col, len(self.content[self.current_line]))

        elif key == curses.KEY_DOWN:
            if self.current_line < len(self.content) - 1:
                self.current_line += 1
                self.current_col = min(self.current_col, len(self.content[self.current_line]))

        elif key == curses.KEY_LEFT:
            if self.current_col > 0:
                self.current_col -= 1
            elif self.current_line > 0:
                self.current_line -= 1
                self.current_col = len(self.content[self.current_line])

        elif key == curses.KEY_RIGHT:
            if self.current_col < len(self.content[self.current_line]):
                self.current_col += 1
            elif self.current_line < len(self.content) - 1:
                self.current_line += 1
                self.current_col = 0

        # Regular character
        elif 32 <= key <= 126:  # Printable ASCII
            current_line = self.content[self.current_line]
            self.content[self.current_line] = current_line[:self.current_col] + chr(key) + current_line[
                                                                                           self.current_col:]
            self.current_col += 1

        # Handle scrolling
        if self.current_line < self.scroll_y:
            self.scroll_y = self.current_line
        elif self.current_line >= self.scroll_y + height - 2:
            self.scroll_y = self.current_line - height + 3

        if self.current_col < self.scroll_x:
            self.scroll_x = self.current_col
        elif self.current_col >= self.scroll_x + width - 5:
            self.scroll_x = self.current_col - width + 6

        return True

    def render(self):
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()

        # Draw content
        for y in range(height - 2):
            line_num = y + self.scroll_y
            if line_num < len(self.content):
                line = self.content[line_num]
                line_to_draw = line[self.scroll_x:self.scroll_x + width - 1]
                self.stdscr.addstr(y, 0, line_to_draw)

        # Draw status bar
        status_line = f" {self.filename} | Line: {self.current_line + 1}/{len(self.content)} | Col: {self.current_col + 1} "
        if self.status_timer > 0:
            status_line += f"| {self.status_message}"
            self.status_timer -= 1

        status_line = status_line.ljust(width)
        self.stdscr.attron(curses.color_pair(1))
        self.stdscr.addstr(height - 1, 0, status_line[:width - 1])
        self.stdscr.attroff(curses.color_pair(1))

        # Draw shortcuts
        help_text = " ^S Save | ^L Load | ^X Exit "
        self.stdscr.addstr(height - 2, 0, help_text)

        # Position cursor
        cursor_y = self.current_line - self.scroll_y
        cursor_x = self.current_col - self.scroll_x
        self.stdscr.move(cursor_y, cursor_x)

        self.stdscr.refresh()

    def run(self):
        curses.curs_set(1)  # Show cursor

        running = True
        while running:
            self.render()
            key = self.stdscr.getch()
            running = self.handle_key(key)


def main_curses(stdscr):
    """Main function for curses version"""
    curses.cbreak()
    curses.noecho()
    stdscr.keypad(True)

    filename = sys.argv[1] if len(sys.argv) > 1 else None
    # Ensure filename has .arc extension
    if filename and not filename.endswith('.arc'):
        filename += '.arc'

    app = ArcNotesCurses(stdscr, filename)
    app.run()


def main():
    """Entry point that decides which version to run"""
    # Get filename from command line arguments
    filename = sys.argv[1] if len(sys.argv) > 1 else None

    # Ensure filename has .arc extension
    if filename and not filename.endswith('.arc'):
        filename += '.arc'

    if CURSES_AVAILABLE:
        try:
            wrapper(main_curses)
        except Exception as e:
            print(f"Error in curses mode: {str(e)}")
            print("Falling back to simple mode...")
            editor = ArcNotesFallback(filename)
            editor.run()
    else:
        print("Running in simple mode (curses not available)")
        editor = ArcNotesFallback(filename)
        editor.run()


if __name__ == "__main__":
    main()
