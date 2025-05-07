import curses

def main(stdscr):
    # キー入力がすぐに返されるように設定
    stdscr.nodelay(True)
    # 入力されたキーを画面に表示しない
    curses.noecho()
    # カーソルを非表示にする
    curses.curs_set(0)
    # 特殊キーを有効にする
    stdscr.keypad(True)

    try:
        # 画面の高さと幅を取得
        height, width = stdscr.getmaxyx()
        # 表示する文字列
        text = "Hello"
        # 文字列を中央に表示するための位置を計算
        start_y = height // 2
        start_x = (width - len(text)) // 2

        # 文字列を画面に表示
        stdscr.addstr(start_y, start_x, text)
        # 画面を更新して表示を反映
        stdscr.refresh()

        while True:
            # キー入力を待つ（非ブロッキング）
            key = stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                break
    finally:
        # curses モードを終了し、端末を元の状態に戻す
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.curs_set(1)
        curses.endwin()

if __name__ == '__main__':
    curses.wrapper(main)
