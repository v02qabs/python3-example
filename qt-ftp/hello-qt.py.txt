import sys
from PyQt5.QtWidgets import QApplication, QLabel

if __name__ == '__main__':
    app = QApplication(sys.argv)
    label = QLabel("Hello!")
    label.show()
    sys.exit(app.exec_())
