# coding:utf-8
# GUI应用程序主程序入口

import sys
import time

from PyQt5.QtWidgets import QApplication

from main_form.myMainWindow import QmyMainWindow

app = QApplication(sys.argv)  # 创建GUI应用程序

mainForm = QmyMainWindow()  # 创建主窗体

mainForm.show()  # 显示主窗体

time.sleep(1)

sys.exit(app.exec_())
