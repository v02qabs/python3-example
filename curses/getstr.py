import curses

def curses_main(args):
    w = curses.initscr()

    f = open('myfile.txt', 'w')
    curses.echo()
    while 1:
        w.addstr(0,0,">")
        w.clrtoeol()
        s = w.getstr()
        f.write(s)
        if s=="q":
            break
curses.wrapper(curses_main)
