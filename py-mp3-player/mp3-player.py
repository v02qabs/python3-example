import os
import random
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import miniaudio

class MP3PlayerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python 3.14 MP3 Player (ファイル選択拡張版)")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # プレイリストデータ管理
        # (内部的には、表示用のファイル名だけでなく「フルパス」のリストを保持します)
        self.playlist_paths = []
        self.original_playlist_paths = []
        
        self.current_idx = 0
        self.is_playing = False
        self.is_paused = False
        self.loop_mode = "NONE"  # "NONE", "TRACK", "ALL"
        self.shuffle_mode = False

        # miniaudioのデバイスとストリーム
        self.device = None
        self.stream = None

        # GUIコンポーネントの構築
        self._create_widgets()
        
        # 定期的に曲の終了を監視するループを開始
        self.root.after(100, self.update_auto_advance)

    def _create_widgets(self):
        # 1. 現在の再生曲情報
        self.lbl_status = ttk.Label(self.root, text="ステータス: 停止中", font=("Arial", 10, "bold"))
        self.lbl_status.pack(pady=5)

        self.lbl_track = ttk.Label(self.root, text="曲名: なし", font=("Arial", 11), wraplength=550, justify="center")
        self.lbl_track.pack(pady=5)

        # 2. ファイル/フォルダー選択コントロール
        frame_file_ops = ttk.LabelFrame(self.root, text=" プレイリスト編集 ")
        frame_file_ops.pack(pady=5, padx=20, fill=tk.X)

        btn_add_files = ttk.Button(frame_file_ops, text="ファイルを選択追加", command=self.add_files)
        btn_add_files.pack(side=tk.LEFT, padx=10, pady=5)

        btn_add_folder = ttk.Button(frame_file_ops, text="フォルダーごと追加", command=self.add_folder)
        btn_add_folder.pack(side=tk.LEFT, padx=10, pady=5)

        btn_remove_selected = ttk.Button(frame_file_ops, text="選択した曲を削除", command=self.remove_selected_track)
        btn_remove_selected.pack(side=tk.RIGHT, padx=10, pady=5)

        btn_clear_all = ttk.Button(frame_file_ops, text="リスト全クリア", command=self.clear_playlist)
        btn_clear_all.pack(side=tk.RIGHT, padx=10, pady=5)

        # 3. プレイリスト（リストボックス）
        frame_list = ttk.Frame(self.root)
        frame_list.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)

        self.scrollbar = ttk.Scrollbar(frame_list, orient=tk.VERTICAL)
        self.listbox = tk.Listbox(frame_list, yscrollcommand=self.scrollbar.set, font=("Arial", 10), selectmode=tk.SINGLE)
        self.scrollbar.config(command=self.listbox.yview)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # リストボックスのダブルクリックで曲指定再生
        self.listbox.bind("<Double-1>", self.on_listbox_double_click)

        # 4. 音楽コントロールボタン群
        frame_controls = ttk.Frame(self.root)
        frame_controls.pack(pady=10)

        self.btn_play = ttk.Button(frame_controls, text="再生 / 一時停止", command=self.toggle_pause_or_play, width=15)
        self.btn_play.grid(row=0, column=0, padx=5)

        self.btn_stop = ttk.Button(frame_controls, text="停止", command=self.stop, width=10)
        self.btn_stop.grid(row=0, column=1, padx=5)

        self.btn_next = ttk.Button(frame_controls, text="スキップ", command=self.next_track, width=10)
        self.btn_next.grid(row=0, column=2, padx=5)

        # 5. モード切替ボタン群
        frame_modes = ttk.Frame(self.root)
        frame_modes.pack(pady=5)

        self.btn_loop = ttk.Button(frame_modes, text="ループ: NONE", command=self.toggle_loop, width=15)
        self.btn_loop.grid(row=0, column=0, padx=5)

        self.btn_shuffle = ttk.Button(frame_modes, text="シャッフル: OFF", command=self.toggle_shuffle, width=15)
        self.btn_shuffle.grid(row=0, column=1, padx=5)

    # --- ファイル操作ロジック ---
    def add_files(self):
        """ファイルを個別・複数選択してプレイリストに追加"""
        files = filedialog.askopenfilenames(
            title="MP3ファイルを選択（複数可）",
            filetypes=[("Audio Files", "*.mp3"), ("All Files", "*.*")]
        )
        if files:
            for file_path in files:
                normalized_path = os.path.normpath(file_path)
                if normalized_path not in self.playlist_paths:
                    self.playlist_paths.append(normalized_path)
            
            # 元の並び順バックアップ（シャッフル解除用）を更新
            if not self.shuffle_mode:
                self.original_playlist_paths = self.playlist_paths.copy()
            self._refresh_listbox_ui()

    def add_folder(self):
        """フォルダーを一括選択して中のMP3をすべて追加"""
        folder = filedialog.askdirectory(title="MP3が入っているフォルダーを選択")
        if folder:
            found_files = []
            for root_dir, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith('.mp3'):
                        found_files.append(os.path.normpath(os.path.join(root_dir, file)))
            
            if not found_files:
                messagebox.showinfo("情報", "選択したフォルダー内にMP3ファイルが見つかりませんでした。")
                return
                
            # 重複を避けつつ追加
            for path in found_files:
                if path not in self.playlist_paths:
                    self.playlist_paths.append(path)
                    
            if not self.shuffle_mode:
                self.original_playlist_paths = self.playlist_paths.copy()
            self._refresh_listbox_ui()

    def remove_selected_track(self):
        """現在選択されている曲をプレイリストから除去"""
        selection = self.listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        
        # 再生中の曲を消す場合は停止
        if self.is_playing and idx == self.current_idx:
            self.stop()
            
        del self.playlist_paths[idx]
        if not self.shuffle_mode:
            self.original_playlist_paths = self.playlist_paths.copy()
            
        # インデックスの調整
        if self.current_idx >= len(self.playlist_paths) and self.playlist_paths:
            self.current_idx = len(self.playlist_paths) - 1
            
        self._refresh_listbox_ui()

    def clear_playlist(self):
        """プレイリストを全クリア"""
        self.stop()
        self.playlist_paths.clear()
        self.original_playlist_paths.clear()
        self.current_idx = 0
        self._refresh_listbox_ui()
        self.lbl_track.config(text="曲名: なし")

    # --- 再生ロジック ---
    def _refresh_listbox_ui(self):
        self.listbox.delete(0, tk.END)
        for i, path in enumerate(self.playlist_paths):
            # 画面上はフルパスではなくファイル名だけ見せる
            filename = os.path.basename(path)
            self.listbox.insert(tk.END, f"{i+1}. {filename}")
        self._update_selection_highlight()

    def _update_selection_highlight(self):
        if self.playlist_paths:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.current_idx)
            self.listbox.see(self.current_idx)

    def on_listbox_double_click(self, event):
        selection = self.listbox.curselection()
        if selection:
            self.current_idx = selection[0]
            self.play()

    def toggle_shuffle(self):
        if not self.playlist_paths:
            return
        current_track = self.playlist_paths[self.current_idx] if self.is_playing or self.is_paused else None
        
        self.shuffle_mode = not self.shuffle_mode
        if self.shuffle_mode:
            random.shuffle(self.playlist_paths)
            self.btn_shuffle.config(text="シャッフル: ON")
        else:
            self.playlist_paths = self.original_playlist_paths.copy()
            self.btn_shuffle.config(text="シャッフル: OFF")
            
        if current_track in self.playlist_paths:
            self.current_idx = self.playlist_paths.index(current_track)
        else:
            self.current_idx = 0
            
        self._refresh_listbox_ui()

    def play(self):
        if not self.playlist_paths:
            return
        
        self.stop()

        track_path = self.playlist_paths[self.current_idx]
        try:
            self.stream = miniaudio.stream_file(track_path)
            self.device = miniaudio.PlaybackDevice()
            self.device.start(self.stream)
            self.is_playing = True
            self.is_paused = False
            self.lbl_status.config(text="ステータス: 再生中")
            self.lbl_track.config(text=f"曲名: {os.path.basename(track_path)}")
            self._update_selection_highlight()
        except Exception:
            messagebox.showerror("エラー", f"再生に失敗しました:\n{os.path.basename(track_path)}")
            self.next_track()

    def toggle_pause_or_play(self):
        if not self.playlist_paths:
            return
        if not self.is_playing:
            self.play()
            return
            
        if self.is_paused:
            self.device.start(self.stream)
            self.is_paused = False
            self.lbl_status.config(text="ステータス: 再生中")
        else:
            self.device.stop()
            self.is_paused = True
            self.lbl_status.config(text="ステータス: 一時停止中")

    def stop(self):
        if self.device:
            self.device.close()
            self.device = None
        if self.stream:
            self.stream.close()
            self.stream = None
        self.is_playing = False
        self.is_paused = False
        self.lbl_status.config(text="ステータス: 停止中")

    def next_track(self):
        if not self.playlist_paths:
            return
        if self.loop_mode == "TRACK" and self.is_playing:
            self.play()
        else:
            self.current_idx = (self.current_idx + 1) % len(self.playlist_paths)
            self.play()

    def toggle_loop(self):
        modes = ["NONE", "TRACK", "ALL"]
        next_mode_idx = (modes.index(self.loop_mode) + 1) % len(modes)
        self.loop_mode = modes[next_mode_idx]
        self.btn_loop.config(text=f"ループ: {self.loop_mode}")

    def update_auto_advance(self):
        if self.is_playing and not self.is_paused:
            if self.stream and not self.stream.running:
                if self.loop_mode == "TRACK":
                    self.play()
                elif self.loop_mode == "ALL":
                    self.next_track()
                else:  # NONE
                    if self.current_idx < len(self.playlist_paths) - 1:
                        self.current_idx += 1
                        self.play()
                    else:
                        self.stop()
                        
        self.root.after(100, self.update_auto_advance)

if __name__ == "__main__":
    root = tk.Tk()
    app = MP3PlayerGUI(root)
    
    def on_closing():
        app.stop()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()