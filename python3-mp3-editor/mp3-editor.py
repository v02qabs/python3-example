import os
import tkinter as tk
from tkinter import filedialog, messagebox


class MP3BulkTagEditor:

    def __init__(self, root):
        self.root = root
        self.root.title("MP3 Bulk Tag Editor (ID3v1)")
        self.root.geometry("700x450")

        self.folder_path = ""
        self.mp3_files = []  # フォルダー内のMP3ファイル名リスト

        # --- UIの構築 ---
        # 1. 上部：フォルダー選択
        frame_top = tk.Frame(root)
        frame_top.pack(pady=10, fill=tk.X, padx=10)

        self.btn_open = tk.Button(
            frame_top, text="フォルダーを開く", command=self.open_folder
        )
        self.btn_open.pack(side=tk.LEFT)

        self.lbl_folder = tk.Label(
            frame_top, text="フォルダーが選択されていません", fg="gray"
        )
        self.lbl_folder.pack(side=tk.LEFT, padx=10)

        # 2. 中央：メインエリア（左：リスト、右：編集フィールド）
        frame_main = tk.Frame(root)
        frame_main.pack(pady=5, fill=tk.BOTH, expand=True, padx=10)

        # 左側：ファイルリストボックス（複数選択可能モード: EXTENDED）
        frame_left = tk.Frame(frame_main)
        frame_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(
            frame_left, text="MP3一覧 (Ctrl+Aで全選択 / CtrlやShiftで複数選択):"
        ).pack(anchor="w")
        self.scrollbar = tk.Scrollbar(frame_left)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            frame_left,
            yscrollcommand=self.scrollbar.set,
            selectmode=tk.EXTENDED,  # 複数選択を有効化
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self.on_file_select)

        # 右側：一括編集フィールド
        frame_right = tk.LabelFrame(frame_main, text=" 一括編集（チェック有効のみ更新） ", padx=10, pady=10)
        frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=15)

        # タイトル
        self.chk_title_var = tk.BooleanVar()
        self.chk_title = tk.Checkbutton(
            frame_right, text="変更する", variable=self.chk_title_var, command=self.toggle_inputs
        )
        self.chk_title.grid(row=0, column=0, sticky="w", pady=5)
        tk.Label(frame_right, text="タイトル:").grid(row=0, column=1, sticky="e")
        self.ent_title = tk.Entry(frame_right, width=30, state=tk.DISABLED)
        self.ent_title.grid(row=0, column=2, pady=5, padx=5)

        # アーティスト
        self.chk_artist_var = tk.BooleanVar()
        self.chk_artist = tk.Checkbutton(
            frame_right, text="変更する", variable=self.chk_artist_var, command=self.toggle_inputs
        )
        self.chk_artist.grid(row=1, column=0, sticky="w", pady=5)
        tk.Label(frame_right, text="アーティスト:").grid(row=1, column=1, sticky="e")
        self.ent_artist = tk.Entry(frame_right, width=30, state=tk.DISABLED)
        self.ent_artist.grid(row=1, column=2, pady=5, padx=5)

        # アルバム
        self.chk_album_var = tk.BooleanVar()
        self.chk_album = tk.Checkbutton(
            frame_right, text="変更する", variable=self.chk_album_var, command=self.toggle_inputs
        )
        self.chk_album.grid(row=2, column=0, sticky="w", pady=5)
        tk.Label(frame_right, text="アルバム:").grid(row=2, column=1, sticky="e")
        self.ent_album = tk.Entry(frame_right, width=30, state=tk.DISABLED)
        self.ent_album.grid(row=2, column=2, pady=5, padx=5)

        # 3. 下部：一括保存ボタン
        self.btn_save = tk.Button(
            root,
            text="選択されたすべてのファイルに一括保存",
            command=self.bulk_save_tags,
            state=tk.DISABLED,
            bg="#d1e7dd",
        )
        self.btn_save.pack(pady=15)

    def open_folder(self):
        """フォルダーを開いてMP3をリスト化"""
        self.folder_path = filedialog.askdirectory()
        if not self.folder_path:
            return

        self.lbl_folder.config(text=self.folder_path, fg="black")
        self.listbox.delete(0, tk.END)
        self.mp3_files = []

        try:
            files = os.listdir(self.folder_path)
            self.mp3_files = sorted(
                [f for f in files if f.lower().endswith(".mp3")]
            )
        except Exception as e:
            messagebox.showerror("エラー", f"フォルダーの読み込み失敗:\n{e}")
            return

        if not self.mp3_files:
            messagebox.showinfo("通知", "MP3ファイルが見つかりません。")
            return

        for file_name in self.mp3_files:
            self.listbox.insert(tk.END, file_name)

    def toggle_inputs(self):
        """チェックボックスの状態に応じてエントリーの有効/無効を切り替える"""
        self.ent_title.config(
            state=tk.NORMAL if self.chk_title_var.get() else tk.DISABLED
        )
        self.ent_artist.config(
            state=tk.NORMAL if self.chk_artist_var.get() else tk.DISABLED
        )
        self.ent_album.config(
            state=tk.NORMAL if self.chk_album_var.get() else tk.DISABLED
        )

    def on_file_select(self, event):
        """リストの選択状態が変わった時の処理"""
        selection = self.listbox.curselection()
        if selection:
            self.btn_save.config(state=tk.NORMAL)
            
            # 単一選択の場合のみ、既存のタグを自動で読み込んで入力欄のヒントにする
            if len(selection) == 1:
                file_name = self.mp3_files[selection[0]]
                full_path = os.path.join(self.folder_path, file_name)
                self.load_single_tag(full_path)
        else:
            self.btn_save.config(state=tk.DISABLED)

    def load_single_tag(self, path):
        """1ファイルだけ選ばれている時、現在のタグを表示（編集の参考用）"""
        with open(path, "rb") as f:
            try:
                f.seek(-128, os.SEEK_END)
                tag_data = f.read(128)
            except OSError:
                tag_data = b""

        if len(tag_data) == 128 and tag_data[:3] == b"TAG":
            title = tag_data[3:33].strip(b"\x00 \x01").decode("cp932", "ignore")
            artist = (
                tag_data[33:63].strip(b"\x00 \x01").decode("cp932", "ignore")
            )
            album = (
                tag_data[63:93].strip(b"\x00 \x01").decode("cp932", "ignore")
            )

            # チェックが入っていない場合のみ、読み込んだ値を一時表示
            if not self.chk_title_var.get():
                self.ent_title.config(state=tk.NORMAL)
                self.ent_title.delete(0, tk.END)
                self.ent_title.insert(0, title)
                self.ent_title.config(state=tk.DISABLED)
            if not self.chk_artist_var.get():
                self.ent_artist.config(state=tk.NORMAL)
                self.ent_artist.delete(0, tk.END)
                self.ent_artist.insert(0, artist)
                self.ent_artist.config(state=tk.DISABLED)
            if not self.chk_album_var.get():
                self.ent_album.config(state=tk.NORMAL)
                self.ent_album.delete(0, tk.END)
                self.ent_album.insert(0, album)
                self.ent_album.config(state=tk.DISABLED)

    def bulk_save_tags(self):
        """選択されたすべてのファイルに対して、チェックされた項目を一括更新"""
        selection = self.listbox.curselection()
        if not selection:
            return

        # どの項目もチェックされていなければ警告して終了
        if (
            not self.chk_title_var.get()
            and not self.chk_artist_var.get()
            and not self.chk_album_var.get()
        ):
            messagebox.showwarning(
                "警告", "変更する項目のチェックボックスを少なくとも1つ有効にしてください。"
            )
            return

        # バイト列データの準備
        title_text = self.ent_title.get()
        artist_text = self.ent_artist.get()
        album_text = self.ent_album.get()

        success_count = 0

        # 選択されたすべてのファイルをループ処理
        for index in selection:
            file_name = self.mp3_files[index]
            full_path = os.path.join(self.folder_path, file_name)

            # 1. 現状のタグ情報を一度読み込む
            current_title = b"\x00" * 30
            current_artist = b"\x00" * 30
            current_album = b"\x00" * 30
            has_tag = False

            if os.path.exists(full_path):
                with open(full_path, "rb") as f:
                    try:
                        f.seek(-128, os.SEEK_END)
                        tag_data = f.read(128)
                        if len(tag_data) == 128 and tag_data[:3] == b"TAG":
                            has_tag = True
                            current_title = tag_data[3:33]
                            current_artist = tag_data[33:63]
                            current_album = tag_data[63:93]
                    except OSError:
                        pass

            # 2. チェックがついている項目だけ新しい値で上書き、そうでないものは現状維持
            if self.chk_title_var.get():
                title_bytes = title_text.encode("cp932", "ignore")[:30].ljust(
                    30, b"\x00"
                )
            else:
                title_bytes = current_title

            if self.chk_artist_var.get():
                artist_bytes = artist_text.encode("cp932", "ignore")[:30].ljust(
                    30, b"\x00"
                )
            else:
                artist_bytes = current_artist

            if self.chk_album_var.get():
                album_bytes = album_text.encode("cp932", "ignore")[:30].ljust(
                    30, b"\x00"
                )
            else:
                album_bytes = current_album

            # 新しい128バイトのタグブロックを作成
            new_tag = (
                b"TAG" + title_bytes + artist_bytes + album_bytes + (b"\x00" * 35)
            )

            # 3. ファイルへの書き込み
            try:
                with open(full_path, "r+b" if has_tag else "a+b") as f:
                    if has_tag:
                        f.seek(-128, os.SEEK_END)
                    else:
                        f.seek(0, os.SEEK_END)
                    f.write(new_tag)
                success_count += 1
            except Exception as e:
                print(f"ファイル書き込みエラー ({file_name}): {e}")

        messagebox.showinfo(
            "完了", f"{success_count} 個のファイルのタグを一括更新しました！"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = MP3BulkTagEditor(root)
    root.mainloop()