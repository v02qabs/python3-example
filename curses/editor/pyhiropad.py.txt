import curses

f = open("out.log", "w")

def log(msg):
    f.write(msg)
    f.flush()

stdscr = curses.initscr()

while True:
    #key = stdscr.getch()   # char or integer (keycode), native/Polish char OK
    key = stdscr.getstr()
