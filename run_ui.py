import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import setTheme, Theme

if __name__ == '__main__':
    app = QApplication(sys.argv)
    setTheme(Theme.DARK)  # 设置主题
    window = uic.loadUi('untitled.ui')  # 加载 UI 文件
    window.show()  # 显示窗口
    sys.exit(app.exec_())  # 运行应用程序 