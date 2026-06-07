import tkinter as tk
import ctypes
import os

# --- Windowsのゲームパッド入力用設定 ---
# 外部ライブラリ(pygame等)を使わず、Windows標準のDLLからコントローラーの状態を取得します
try:
    winmm = ctypes.windll.winmm
    # ジョイスティック（ゲームパッド）の状態を取得する構造体と関数の定義
    class JOYINFOEX(ctypes.Structure):
        _fields_ = [
            ("dwSize", ctypes.c_uint32),
            ("dwFlags", ctypes.c_uint32),
            ("dwXpos", ctypes.c_uint32),
            ("dwYpos", ctypes.c_uint32),
            ("dwZpos", ctypes.c_uint32),
            ("dwButtons", ctypes.c_uint32),
            ("dwButtonNumber", ctypes.c_uint32),
            ("dwPOV", ctypes.c_uint32),
            ("dwReserved1", ctypes.c_uint32),
            ("dwReserved2", ctypes.c_uint32),
        ]
    HAS_PAD = True
except:
    HAS_PAD = False

class BreakoutGame:
    def __init__(self, root):
        self.root = root
        self.root.title("ゲームパッド＆キーボード連動型 ブロック崩し")
        self.root.resizable(False, False)
        
        # 画面サイズ
        self.width = 600
        self.height = 400
        self.canvas = tk.Canvas(root, width=self.width, height=self.height, bg="black")
        self.canvas.pack()
        
        # 内部的な操作入力フラグ（ここをキーボードとパッドで奪い合うように共通化）
        self.move_left = False
        self.move_right = False
        self.trigger_restart = False
        
        # ゲームの状態管理
        self.game_over = False
        self.game_clear = False
        
        # 初期化とイベント登録
        self.init_game()
        self.bind_events()
        
        # ゲームループ開始 (60FPS制御)
        self.update()

    def init_game(self):
        """ゲーム変数の初期化"""
        self.canvas.delete("all")
        self.game_over = False
        self.game_clear = False
        
        # パドル情報
        self.paddle_w = 100
        self.paddle_h = 15
        self.paddle_x = (self.width - self.paddle_w) // 2
        self.paddle_y = self.height - 30
        self.paddle_speed = 8
        self.paddle = self.canvas.create_rectangle(
            self.paddle_x, self.paddle_y, 
            self.paddle_x + self.paddle_w, self.paddle_y + self.paddle_h, 
            fill="cyan"
        )
        
        # ボール情報
        self.ball_r = 8
        self.ball_x = self.width // 2
        self.ball_y = self.height // 2
        self.ball_dx = 4
        self.ball_dy = -4
        self.ball = self.canvas.create_oval(
            self.ball_x - self.ball_r, self.ball_y - self.ball_r,
            self.ball_x + self.ball_r, self.ball_y + self.ball_r,
            fill="white"
        )
        
        # ブロック生成
        self.blocks = []
        rows = 4
        cols = 8
        b_w = 65
        b_h = 20
        offset_x = (self.width - (cols * b_w + (cols-1)*5)) // 2
        offset_y = 50
        
        colors = ["#ff4d4d", "#ffa64d", "#ffff4d", "#4dff4d"]
        for r in range(rows):
            for c in range(cols):
                bx1 = offset_x + c * (b_w + 5)
                by1 = offset_y + r * (b_h + 5)
                bx2 = bx1 + b_w
                by2 = by1 + b_h
                b = self.canvas.create_rectangle(bx1, by1, bx2, by2, fill=colors[r])
                self.blocks.append(b)

    def bind_events(self):
        """キーボードのイベントバインド"""
        # キーを押したとき
        self.root.bind("<KeyPress-Left>", lambda e: self.set_input("left", True))
        self.root.bind("<KeyPress-a>", lambda e: self.set_input("left", True))
        self.root.bind("<KeyPress-Right>", lambda e: self.set_input("right", True))
        self.root.bind("<KeyPress-d>", lambda e: self.set_input("right", True))
        self.root.bind("<KeyPress-r>", lambda e: self.set_input("restart", True))
        
        # キーを離したとき
        self.root.bind("<KeyRelease-Left>", lambda e: self.set_input("left", False))
        self.root.bind("<KeyRelease-a>", lambda e: self.set_input("left", False))
        self.root.bind("<KeyRelease-Right>", lambda e: self.set_input("right", False))
        self.root.bind("<KeyRelease-d>", lambda e: self.set_input("right", False))
        self.root.bind("<KeyRelease-r>", lambda e: self.set_input("restart", False))

    def set_input(self, action, state):
        """入力状態を一括管理するマネージャー"""
        if action == "left":
            self.move_left = state
        elif action == "right":
            self.move_right = state
        elif action == "restart":
            self.trigger_restart = state

    def check_gamepad(self):
        """Windows API経由でゲームパッドの状態を毎フレーム監視し、キーボード入力と同期"""
        if not HAS_PAD:
            return
            
        joy_info = JOYINFOEX()
        joy_info.dwSize = ctypes.sizeof(JOYINFOEX)
        joy_info.dwFlags = 0x000000FF  # すべての情報を取得
        
        # ジョイスティックID 0番（1台目のコントローラー）を取得
        result = winmm.joyGetPosEx(0, ctypes.byref(joy_info))
        if result == 0:  # 正常に接続されている場合
            
            # --- 1. 十字キー / 左アナログスティックの左右入力を同期 ---
            # dwXposの標準中央値は約32768。左に傾くと小さく、右に傾くと大きくなる
            # POV（ハットスイッチ/十字キー）は、左が27000、右が9000
            is_pad_left = (joy_info.dwXpos < 15000) or (joy_info.dwPOV == 27000)
            is_pad_right = (joy_info.dwXpos > 50000) or (joy_info.dwPOV == 9000)
            
            # パッドが押されているか、もしくはキーボードが押されているならTrue
            # これにより「キーボードとパッドの同時マッピング」が成立します
            self.move_left = is_pad_left or self.move_left
            self.move_right = is_pad_right or self.move_right
            
            # --- 2. ボタン入力を同期 (Rキー = Aボタン等) ---
            # dwButtonsはビット演算で押されたボタンを判定 (1: Aボタン, 2: Bボタンなど環境依存)
            # ここでは「いずれかのメインボタン(ボタン1〜4)」または「START/SELECT相当」でリスタート
            is_pad_restart = (joy_info.dwButtons & 0xF) > 0 
            self.trigger_restart = is_pad_restart or self.trigger_restart

    def update(self):
        """メインのゲームループ (約60FPS)"""
        # 最初にパッドの状態を確認し、キーボードのフラグと合流させる
        self.check_gamepad()
        
        if self.trigger_restart:
            self.init_game()
            
        if not self.game_over and not self.game_clear:
            # パドルの移動処理
            if self.move_left and self.paddle_x > 0:
                self.paddle_x -= self.paddle_speed
            if self.move_right and self.paddle_x < self.width - self.paddle_w:
                self.paddle_x += self.paddle_speed
            self.canvas.coords(self.paddle, self.paddle_x, self.paddle_y, self.paddle_x + self.paddle_w, self.paddle_y + self.paddle_h)
            
            # ボールの移動処理
            self.ball_x += self.ball_dx
            self.ball_y += self.ball_dy
            
            # 壁との衝突
            if self.ball_x - self.ball_r <= 0 or self.ball_x + self.ball_r >= self.width:
                self.ball_dx *= -1
            if self.ball_y - self.ball_r <= 0:
                self.ball_dy *= -1
                
            # パドルとの衝突（物理演算つき反射）
            if (self.paddle_y <= self.ball_y + self.ball_r <= self.paddle_y + self.paddle_h and
                self.paddle_x <= self.ball_x <= self.paddle_x + self.paddle_w):
                # 当たった位置に応じて角度を変える
                relative_hit = (self.ball_x - (self.paddle_x + self.paddle_w / 2)) / (self.paddle_w / 2)
                self.ball_dx = relative_hit * 6
                self.ball_dy = -abs(self.ball_dy)
                
            # ブロックとの衝突判定
            ball_box = (self.ball_x - self.ball_r, self.ball_y - self.ball_r, self.ball_x + self.ball_r, self.ball_y + self.ball_r)
            hit_block = None
            for b in self.blocks:
                bx1, by1, bx2, by2 = self.canvas.coords(b)
                if (bx1 <= self.ball_x <= bx2) and (by1 <= self.ball_y <= by2):
                    hit_block = b
                    self.ball_dy *= -1
                    break
            
            if hit_block:
                self.canvas.delete(hit_block)
                self.blocks.remove(hit_block)
                
            # クリア判定
            if not self.blocks:
                self.game_clear = True
                self.canvas.create_text(self.width//2, self.height//2, text="GAME CLEAR!\nPress R or Pad Button to Restart", fill="gold", font=("Arial", 20, "bold"), justify=tk.CENTER)
                
            # ゲームオーバー判定
            if self.ball_y + self.ball_r >= self.height:
                self.game_over = True
                self.canvas.create_text(self.width//2, self.height//2, text="GAME OVER\nPress R or Pad Button to Restart", fill="red", font=("Arial", 20, "bold"), justify=tk.CENTER)
                
            self.canvas.coords(self.ball, self.ball_x - self.ball_r, self.ball_y - self.ball_r, self.ball_x + self.ball_r, self.ball_y + self.ball_r)

        # 16ミリ秒（約60FPS）後に自身を再帰呼び出し
        self.root.after(16, self.update)

if __name__ == "__main__":
    root = tk.Tk()
    app = BreakoutGame(root)
    root.mainloop()