import tkinter as tk
from tkinter import filedialog, messagebox
import os

class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Python テキストエディタ")
        self.root.geometry("800x600")

        # 現在開いているファイルのパスを記憶する変数
        self.current_file = None

        # 画面の部品（UI）を作成
        self.create_widgets()

    def create_widgets(self):
        # --- 1. メニューバーの作成 ---
        menubar = tk.Menu(self.root)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="新規作成 (N)", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="開く (O)...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="上書き保存 (S)", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="名前を付けて保存 (A)...", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="終了 (X)", command=self.quit_app)
        menubar.add_cascade(label="ファイル (F)", menu=file_menu)

        self.root.config(menu=menubar)

        # --- 2. スクロールバーとテキストエリアの作成 ---
        # スクロールバー用のフレーム
        editor_frame = tk.Frame(self.root)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(editor_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # テキスト入力エリア (文字フォントやサイズを調整可能)
        self.text_area = tk.Text(
            editor_frame, 
            undo=True,  # 元に戻す(Ctrl+Z)機能を有効化
            font=("Consolas", 12), 
            yscrollcommand=scrollbar.set
        )
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_area.yview)

        # --- 3. ステータスバーの作成 (下部の情報表示欄) ---
        self.status_bar = tk.Label(self.root, text="新規ファイル", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # --- 4. ショートカットキーのバインド ---
        self.root.bind("<Control-n>", lambda event: self.new_file())
        self.root.bind("<Control-o>", lambda event: self.open_file())
        self.root.bind("<Control-s>", lambda event: self.save_file())

        # ウィンドウの「×」ボタンを押したときの処理
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

    # --- 機能の実装 ---

    def update_status(self):
        """下部のステータスバーの表示を更新する"""
        if self.current_file:
            self.status_bar.config(text=f"開いているファイル: {self.current_file}")
            self.root.title(f"{os.path.basename(self.current_file)} - Python テキストエディタ")
        else:
            self.status_bar.config(text="新規ファイル")
            self.root.title("Python テキストエディタ")

    def check_saved(self):
        """編集中の内容が破棄されても大丈夫か確認する（簡易版）"""
        # 厳密な変更検知を入れると複雑化するため、今回はテキストエリアが空でない場合に確認を挟む
        if self.text_area.get("1.0", tk.END) != "\n":
            return messagebox.askyesnocancel("確認", "現在の内容を保存、または破棄してよろしいですか？\n(「はい」で保存、「いいえ」で保存せず続行)")
        return "no_need"

    def new_file(self):
        """ファイルを新規作成する"""
        confirm = self.check_saved()
        if confirm is True:
            self.save_file()
        elif confirm is None:  # キャンセル
            return

        self.text_area.delete("1.0", tk.END)
        self.current_file = None
        self.update_status()

    def open_file(self):
        """既存のファイルを開く"""
        confirm = self.check_saved()
        if confirm is True:
            self.save_file()
        elif confirm is None:
            return

        file_path = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", content)
                self.current_file = file_path
                self.update_status()
            except Exception as e:
                messagebox.showerror("エラー", f"ファイルを開けませんでした:\n{e}")

    def save_file(self):
        """ファイルを上書き保存する"""
        if self.current_file:
            try:
                content = self.text_area.get("1.0", tk.END + "-1c") # 末尾の余分な改行を除く
                with open(self.current_file, "w", encoding="utf-8") as f:
                    f.write(content)
                self.update_status()
                return True
            except Exception as e:
                messagebox.showerror("エラー", f"ファイルを保存できませんでした:\n{e}")
                return False
        else:
            return self.save_as_file()

    def save_as_file(self):
        """名前を付けてファイルを保存する"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")]
        )

        if file_path:
            try:
                content = self.text_area.get("1.0", tk.END + "-1c")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.current_file = file_path
                self.update_status()
                return True
            except Exception as e:
                messagebox.showerror("エラー", f"ファイルを保存できませんでした:\n{e}")
                return False
        return False

    def quit_app(self):
        """アプリを安全に終了する"""
        confirm = self.check_saved()
        if confirm is True:
            if self.save_file():
                self.root.destroy()
        elif confirm is False or confirm == "no_need":
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TextEditor(root)
    root.mainloop()