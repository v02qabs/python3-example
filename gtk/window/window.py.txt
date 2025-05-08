import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

# ウィンドウクラスの定義
class MyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Hello GTK")
        self.set_default_size(400, 300)

        # ラベルを追加
        label = Gtk.Label(label="Hello, Ubuntu 24.04!")
        self.add(label)

# メイン関数
def main():
    # インスタンスを生成して表示
    window = MyWindow()
    window.connect("destroy", Gtk.main_quit)  # ウィンドウを閉じる時にGTKメインループを終了
    window.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
