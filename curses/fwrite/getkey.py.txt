import curses

f = open("out.log", "w")

def log(msg):
    f.write(msg)
    f.flush()

stdscr = curses.initscr()
curses.echo()
curses.cbreak()
stdscr.keypad(True)

while True:
    stdscr.refresh()
    key = stdscr.getkey()
    log(key)
    if key == "KEY_RESIZE":
        log("{} {}".format(curses.LINES, curses.COLS))
    if key == "q":
        break
  
curses.echo()
curses.endwin()

f.close()
