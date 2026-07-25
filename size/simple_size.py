import os
import sys


def format_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f"{size:.2f} {units[i]}"


# コマンドライン引数のチェック
if len(sys.argv) < 2:
    print("使い方: python3 simple_size.py <ファイルパス>")
    sys.exit(1)

filepath = sys.argv[1]

if os.path.isfile(filepath):
    size_bytes = os.path.getsize(filepath)
    print(f"サイズ: {format_size(size_bytes)}")
else:
    print(f"エラー: '{filepath}' が見つからないか、ファイルではありません。")
