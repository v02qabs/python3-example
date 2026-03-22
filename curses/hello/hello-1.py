# hello-1.py
import curses

def main(stdscr):
    # 初期設定
    key = 0  # 最初にkeyを定義しておく
    cursor_x = 1
    cursor_y = 1
    
    stdscr.clear()

    # 'q'が押されるまでループ
    while key != ord('q'):
        # 画面を一度クリアして描画を更新
        stdscr.clear()
        
        # 座標の計算（例：左右に1マスずつ動く）
        cursor_x = 0 if cursor_x == 1 else 1
        
        # 文字を表示（x, y座標を指定）
        stdscr.addstr(cursor_y, cursor_x, "Hello!")
        
        # 実際のカーソルを移動
        stdscr.move(cursor_y, cursor_x)
        
        stdscr.refresh()
        
        # キー入力を待機
        key = stdscr.getch()

# cursesを安全に開始・終了させるためのラッパー
curses.wrapper(main)