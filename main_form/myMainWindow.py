# coding:utf-8
import configparser
import datetime
import json
import os
import queue
import sys
import threading
import time
import subprocess
import csv
import urllib

from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (QAbstractItemView, QMainWindow, QMessageBox, QSlider, QTableWidgetItem, QTextBrowser)
from PyQt5.QtCore import QObject, QTimer, Qt, pyqtSignal
from PyQt5 import QtWidgets

import pandas as pd
import psutil as psutil

from main_form.Form.dtn_business_test import Ui_BusinessTets_Form
from testcase_source.adb_makecall import Adb_Make_Call
from testcase_source.adb_sendsms import Adb_Send_Sms
from testcase_source.appiume_bilibili import Appiume_Bilibili
from testcase_source.appiume_kuaishou import Appiume_Kuaishou
from testcase_source.appiume_speedtest import Appiume_Speedtest
from testcase_source.appiume_tiktok import Appiume_TikTok
from testcase_source.appiume_wechat import Appiume_WeChat
from testcase_source.data_filtration import Data_Filtration
from testcase_source.speedtest_pc import Speedtest_PC
from testcase_source.testcase_list import Testcase_Item
from utils.spawnue import spawnUe
from utils.vlc_player import Player


class MySignals(QObject):
    # 定义一种信号，两个参数 类型分别是: QTextBrowser 和 字符串
    # 调用 emit方法 发信号时，传入参数 必须是这里指定的 参数类型
    text_print = pyqtSignal(QTextBrowser, str)
    # 还可以定义其他种类的信号
    update_table = pyqtSignal(list)

    update_batch_table = pyqtSignal(list)

    state_text_print = pyqtSignal(str)

    batch_state_text_print = pyqtSignal(str)

    videotime = pyqtSignal(QSlider, int)

    bytes_label_print = pyqtSignal(str, str)

    sp_pc_state_text_print = pyqtSignal(str)

    adb_state_text_print = pyqtSignal(str)

    road_state_text_print = pyqtSignal(str)


class QmyMainWindow(QMainWindow):

    def __init__(self, parent=None):
        # 调用父类构造函数，创建窗体
        super().__init__(parent)

        # 读取配置文件
        self.wechat_dict_cfg = None
        self.speedtest_dict_cfg = None
        self.kuaishou_dict_cfg = None
        self.bilibili_dict_cfg = None
        self.tiktok_dict_cfg = None
        self.appserver_dict_cfg = None
        self.read_config()
        self.batch_flg = False

        # 创建UI对象
        self.mainform_init()

        path = os.path.realpath(os.curdir)
        nametime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        self.logFilePath = path + '/log/log_' + nametime + '.log'

        # 实例化终端对象
        self.ueutil = spawnUe()
        self.test_result_list = []
        self.resultStateDataQueue = queue.Queue()
        self.sp_pc_StateDataQueue = queue.Queue()
        self.roadStateDataQueue = queue.Queue()

        self.testcase_item = Testcase_Item()

        self.test_stop_flag = True
        self.exitFlg = False
        # 自定义信号的处理函数
        self.mysignals = MySignals()
        self.mysignals.state_text_print.connect(self.print_state_text)
        self.mysignals.batch_state_text_print.connect(self.print_batch_state_text)
        self.mysignals.update_table.connect(self.print_table)
        self.mysignals.update_batch_table.connect(self.print_batch_table)
        self.mysignals.bytes_label_print.connect(self.print_bytes_label)
        self.mysignals.sp_pc_state_text_print.connect(self.print_sp_pc_result_text)
        self.mysignals.adb_state_text_print.connect(self.print_adb_state_text)
        self.mysignals.road_state_text_print.connect(self.print_road_result_text)

        # 界面显示测试状态线程
        self.show_state_thread = threading.Thread(target=self.show_result_state, daemon=True)
        self.show_state_thread.daemon = 1

        # 界面显示测试状态线程
        self.show_batch_state_thread = threading.Thread(target=self.show_batch_result_state, daemon=True)
        self.show_batch_state_thread.daemon = 1

        # UE列表显示
        self.show_ue_thread = threading.Thread(target=self.on_btn_refresh, daemon=True)
        self.show_ue_thread.daemon = 1
        self.show_ue_thread.start()

        # 接收发送流量监控
        self.bytes_sent_rcvd_thread = threading.Thread(target=self.show_bytes_sent_rcvd, daemon=True)
        self.bytes_sent_rcvd_thread.daemon = 1
        self.bytes_sent_rcvd_thread.start()

        # 视频播放
        self.edit_video_tab_init()

    # 主界面初始化
    def mainform_init(self):
        # 构造UI界面
        self.ui = Ui_BusinessTets_Form()
        self.ui.setupUi(self)

        self.setWindowFlags(Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.ui.lbl_quit.hide()
        # 信号和槽函数连接
        self.ui.btn_exit.clicked.connect(lambda: self.close())
        # 手机终端设备刷新
        self.ui.btn_ue_refresh.clicked.connect(self.on_btn_refresh)
        self.ui.btn_ue_screen.clicked.connect(self.on_btn_screen)
        self.ui.btn_ue_sscom.clicked.connect(self.on_btn_sscom)

        # 批量业务处理
        self.ui.btn_testcase_clear.clicked.connect(self.on_btnList_Clear)
        self.ui.btn_testcase_Delete.clicked.connect(self.on_btnList_Delete)
        self.ui.btn_testcase_import.clicked.connect(self.on_btnList_Import)
        self.ui.btn_testcase_SelAll.clicked.connect(self.on_btnSel_ALL)
        self.ui.btn_testcase_SelNone.clicked.connect(self.on_btnSel_None)
        self.ui.btn_testcase_SeInvs.clicked.connect(self.on_btnSel_Invs)

        # 测试开始
        self.ui.btn_test_start.clicked.connect(self.on_btn_start)
        self.ui.btn_test_stop.clicked.connect(self.on_btn_stop)

        # speedtest测试启动
        self.ui.btn_speed_pc_start.clicked.connect(self.on_start_speedtest_pc)

        # 数据编辑处理
        self.ui.btn_open_road_file.clicked.connect(self.open_road_file)
        self.ui.btn_road_data_edit.clicked.connect(self.edit_road_test_data)

        # adb命令执行处理
        self.ui.btn_adb_run.clicked.connect(self.run_adb_command)
        self.ui.btn_adb_clear.clicked.connect(self.run_adb_clear)

        #
        self.ui.cBox_test_business.currentIndexChanged.connect(self.run_business_change)

        # 批量测试开始
        self.ui.btn_batchtest_excute.clicked.connect(self.run_batch_test)

        # 设备信息
        self.ui.tbl_ue_info.setEditTriggers(QAbstractItemView.NoEditTriggers)
        font = self.ui.tbl_ue_info.horizontalHeader().font()
        font.setBold(False)
        self.ui.tbl_ue_info.horizontalHeader().setFont(font)
        self.ui.tbl_ue_info.horizontalHeader().resizeSection(0, 50)
        self.ui.tbl_ue_info.horizontalHeader().resizeSection(1, 150)
        self.ui.tbl_ue_info.horizontalHeader().resizeSection(2, 120)
        self.ui.tbl_ue_info.horizontalHeader().resizeSection(3, 120)
        self.ui.tbl_ue_info.horizontalHeader().resizeSection(4, 120)
        self.ui.tbl_ue_info.resizeRowsToContents()
        self.ui.tbl_ue_info.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.tbl_ue_info.cellChanged.connect(self.ue_info_change)
        self.ui.tbl_ue_info.hideColumn(2)

        # 批量测试业务用例
        font = self.ui.tbl_testcase.horizontalHeader().font()
        font.setBold(False)
        self.ui.tbl_testcase.horizontalHeader().setFont(font)
        self.ui.tbl_testcase.horizontalHeader().resizeSection(0, 50)
        self.ui.tbl_testcase.horizontalHeader().resizeSection(1, 150)
        self.ui.tbl_testcase.horizontalHeader().resizeSection(2, 60)
        self.ui.tbl_testcase.horizontalHeader().resizeSection(3, 60)
        self.ui.tbl_testcase.horizontalHeader().resizeSection(4, 120)
        self.ui.tbl_testcase.horizontalHeader().resizeSection(5, 180)
        self.ui.tbl_testcase.horizontalHeader().resizeSection(6, 120)
        self.ui.tbl_testcase.horizontalHeader().resizeSection(7, 120)
        self.ui.tbl_testcase.horizontalHeader().resizeSection(8, 120)
        self.ui.tbl_testcase.resizeRowsToContents()
        self.ui.tbl_testcase.setSelectionBehavior(QAbstractItemView.SelectRows)

        # 批量测试结果
        self.ui.tbl_run_batchtest_result.setEditTriggers(QAbstractItemView.NoEditTriggers)
        font = self.ui.tbl_run_batchtest_result.horizontalHeader().font()
        font.setBold(False)
        self.ui.tbl_run_batchtest_result.horizontalHeader().setFont(font)
        self.ui.tbl_run_batchtest_result.horizontalHeader().resizeSection(0, 240)
        self.ui.tbl_run_batchtest_result.horizontalHeader().resizeSection(1, 90)
        self.ui.tbl_run_batchtest_result.horizontalHeader().resizeSection(2, 90)
        self.ui.tbl_run_batchtest_result.horizontalHeader().resizeSection(3, 90)
        self.ui.tbl_run_batchtest_result.resizeRowsToContents()
        self.ui.tbl_run_batchtest_result.setSelectionBehavior(QAbstractItemView.SelectRows)

        # 单个业务测试结果
        self.ui.tbl_test_result.setEditTriggers(QAbstractItemView.NoEditTriggers)
        font = self.ui.tbl_test_result.horizontalHeader().font()
        font.setBold(False)
        self.ui.tbl_test_result.horizontalHeader().setFont(font)
        self.ui.tbl_test_result.horizontalHeader().resizeSection(0, 240)
        self.ui.tbl_test_result.horizontalHeader().resizeSection(1, 90)
        self.ui.tbl_test_result.horizontalHeader().resizeSection(2, 90)
        self.ui.tbl_test_result.horizontalHeader().resizeSection(3, 90)
        self.ui.tbl_test_result.resizeRowsToContents()
        self.ui.tbl_test_result.setSelectionBehavior(QAbstractItemView.SelectRows)

        # 数据编辑处理结果
        self.ui.tbl_data_result_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        font = self.ui.tbl_data_result_list.horizontalHeader().font()
        font.setBold(False)
        self.ui.tbl_data_result_list.horizontalHeader().setFont(font)
        self.ui.tbl_data_result_list.horizontalHeader().resizeSection(0, 120)
        self.ui.tbl_data_result_list.horizontalHeader().resizeSection(1, 120)
        self.ui.tbl_data_result_list.horizontalHeader().resizeSection(2, 120)
        self.ui.tbl_data_result_list.horizontalHeader().resizeSection(3, 120)
        self.ui.tbl_data_result_list.horizontalHeader().resizeSection(4, 120)
        self.ui.tbl_data_result_list.horizontalHeader().resizeSection(5, 120)
        self.ui.tbl_data_result_list.horizontalHeader().resizeSection(6, 120)
        self.ui.tbl_data_result_list.resizeRowsToContents()
        self.ui.tbl_data_result_list.setSelectionBehavior(QAbstractItemView.SelectRows)

        # 重复数据一览
        self.ui.tbl_repetitions_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        font = self.ui.tbl_repetitions_list.horizontalHeader().font()
        font.setBold(False)
        self.ui.tbl_repetitions_list.horizontalHeader().setFont(font)
        self.ui.tbl_repetitions_list.horizontalHeader().resizeSection(0, 180)
        self.ui.tbl_repetitions_list.horizontalHeader().resizeSection(1, 180)
        self.ui.tbl_repetitions_list.horizontalHeader().resizeSection(2, 180)
        self.ui.tbl_repetitions_list.horizontalHeader().resizeSection(3, 120)
        self.ui.tbl_repetitions_list.resizeRowsToContents()
        self.ui.tbl_repetitions_list.setSelectionBehavior(QAbstractItemView.SelectRows)

    # 读取配置文件(config.ini)文件
    def read_config(self):
        path = os.path.realpath(os.curdir)
        cfgPath = os.path.join(path, "config.ini")
        if not os.path.exists(cfgPath):
            QMessageBox.warning(self, "警告", "配置文件(config.ini)没找到,部分手机的业务功能无法正常使用！")
            return
        config = configparser.ConfigParser()
        config.read(cfgPath, encoding="utf-8")
        # 获取section节点
        self.appserver_dict_cfg = dict(config.items("AppiumServer"))
        self.tiktok_dict_cfg = dict(config.items("TikTok_APP"))
        self.bilibili_dict_cfg = dict(config.items("Bilibili_APP"))
        self.kuaishou_dict_cfg = dict(config.items("KuaiShou_APP"))
        self.speedtest_dict_cfg = dict(config.items("SpeedTest_APP"))
        self.wechat_dict_cfg = dict(config.items("WeChat_APP"))

    # <editor-fold desc="窗体关闭">
    def closeEvent(self, event):
        self.ui.lbl_quit.show()
        preguntar = QMessageBox.question(self, "提示", "确定要退出吗？", QMessageBox.Yes | QMessageBox.No)
        if preguntar == QMessageBox.Yes:
            self.exitFlg = True
            self.timer.stop()
            # time.sleep(2)
            # sys.exit(self.exec_())
            sys.exit()
        else:
            self.ui.lbl_quit.hide()
            event.ignore()

    # </editor-fold>

    # <editor-fold desc="终端设备管理">
    # 手机终端信息刷新
    def on_btn_refresh(self):
        self.ui.tbl_ue_info.setRowCount(0)
        self.ui.tbl_ue_info.clearContents()
        if self.ueutil is not None:
            self.ueutil.spawn_ue()
            for i, key in enumerate(self.ueutil.dut.keys()):
                curRow = self.ui.tbl_ue_info.rowCount()
                self.ui.tbl_ue_info.insertRow(curRow)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                item.setFont(QFont('Times', 8, QFont.Normal))
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.ui.tbl_ue_info.setItem(curRow, 0, item)

                item1 = QTableWidgetItem(self.ueutil.dut[key].serial_number)
                item1.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                item1.setFont(QFont('Times', 8, QFont.Normal))
                self.ui.tbl_ue_info.setItem(curRow, 1, item1)

                item2 = QTableWidgetItem(self.ueutil.dut[key].version)
                item2.setFont(QFont('Times', 8, QFont.Normal))
                item2.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.ui.tbl_ue_info.setItem(curRow, 2, item2)

                item3 = QTableWidgetItem(self.ueutil.dut[key].manufacturer)
                item3.setFont(QFont('Times', 8, QFont.Normal))
                item3.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.ui.tbl_ue_info.setItem(curRow, 3, item3)

                item4 = QTableWidgetItem(self.ueutil.dut[key].model)
                item4.setFont(QFont('Times', 8, QFont.Normal))
                item4.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.ui.tbl_ue_info.setItem(curRow, 4, item4)

    # 手机投屏显示
    def on_btn_screen(self):
        sel_count = 0
        path = os.path.realpath(os.curdir)
        scrcpy_comm = os.path.join(path, "scrcpy", "scrcpy.exe")
        # print(scrcpy_comm)
        for index in range(self.ui.tbl_ue_info.rowCount()):
            if self.ui.tbl_ue_info.item(index, 0).checkState() == Qt.Checked:
                sel_count = sel_count + 1
                cellItem = self.ui.tbl_ue_info.item(index, 1)
                # cmd = 'scrcpy -s ' + cellItem.text() + ' --always-on-top --stay-awake'
                cmd = scrcpy_comm + ' -s ' + cellItem.text() + ' --always-on-top --stay-awake'
                t = threading.Thread(target=lambda s: subprocess.call(f'{s}'), args=([cmd]))
                t.start()
        if sel_count == 0:
            QMessageBox.warning(self, "警告", "未选择终端")
            return

    # 运行指定路径下sscom
    def on_btn_sscom(self):
        try:
            path = os.path.realpath(os.curdir)
            sscom_path = os.path.join(path, "sscom", "sscom5.13.1.exe")
            os.startfile(sscom_path)
        except:
            QMessageBox.warning(self, "警告", "sscom启动失败!")

    # </editor-fold>

    # <editor-fold desc="ADB执行处理">
    def run_adb_command(self):
        adb_command = self.ui.le_adb_command.text()
        shell_command = self.ui.txt_adb_command.toPlainText()
        if adb_command == "":
            QMessageBox.warning(self, "警告", "请选择执行命令的手机终端")
            return
        if shell_command == "":
            QMessageBox.warning(self, "警告", "请输入想要执行的ADB命令")
            return
        self.ui.txt_adb_result.clear()

        def run_adb():
            run_cmd = adb_command + " " + shell_command
            adb_result = subprocess.Popen(run_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            for line in iter(adb_result.stdout.readline, b''):
                resultstr = str(line, encoding='utf-8')  # .replace('\n', '').replace('\r', '')
                self.mysignals.adb_state_text_print.emit(resultstr)
                if not subprocess.Popen.poll(adb_result) is None:
                    if line == "":
                        break

        runthread = threading.Thread(target=run_adb, daemon=True)
        runthread.start()

    def run_adb_clear(self):
        self.ui.txt_adb_command.clear()
        self.ui.txt_adb_result.clear()

    # 测试状态实时显示
    def print_adb_state_text(self, strState):
        cursor = self.ui.txt_adb_result.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(strState)
        self.ui.txt_adb_result.ensureCursorVisible()

    def ue_info_change(self):
        sel_cnt = 0
        sn_no = ""
        self.ui.le_adb_command.clear()
        for index in range(self.ui.tbl_ue_info.rowCount()):
            if self.ui.tbl_ue_info.item(index, 0).checkState() == Qt.Checked:
                sel_cnt = sel_cnt + 1
                sn_no = self.ui.tbl_ue_info.item(index, 1).text()
        if sel_cnt > 1:
            QMessageBox.warning(self, "警告", "当前系统支持一个终端的处理")
            return
        if sn_no != "":
            self.ui.le_adb_command.setText(f'adb -s {sn_no}')

    # </editor-fold>

    # <editor-fold desc="测试用例执行状态实时显示">
    # 显示测试结果状态信息
    def show_result_state(self):
        while not self.exitFlg:
            if self.resultStateDataQueue.empty():
                continue
            else:
                if not self.batch_flg:
                    resultStateData = self.resultStateDataQueue.get()
                    self.mysignals.state_text_print.emit(resultStateData)

    # 测试状态实时显示
    def print_state_text(self, strState):
        cursor = self.ui.txt_text_result.textCursor()
        cursor.movePosition(cursor.End)
        strTime = str(datetime.datetime.now())[:23]
        cursor.insertText("[" + strTime + "]   " + strState + '\n')
        self.ui.txt_text_result.ensureCursorVisible()

    # 显示批量测试结果状态信息
    def show_batch_result_state(self):
        while not self.exitFlg:
            if self.resultStateDataQueue.empty():
                continue
            else:
                if self.batch_flg:
                    resultStateData = self.resultStateDataQueue.get()
                    self.mysignals.batch_state_text_print.emit(resultStateData)

    # 批量测试状态实时显示
    def print_batch_state_text(self, strState):
        cursor = self.ui.txt_run_batchtest_state.textCursor()
        cursor.movePosition(cursor.End)
        strTime = str(datetime.datetime.now())[:23]
        cursor.insertText("[" + strTime + "]   " + strState + '\n')
        self.ui.txt_run_batchtest_state.ensureCursorVisible()

    # </editor-fold>

    # <editor-fold desc="批量处理测试业务管理界面按钮功能">
    # 清空
    def on_btnList_Clear(self):
        self.ui.tbl_testcase.setRowCount(0)
        self.ui.tbl_testcase.clearContents()

    # 测试用例文件导入
    def on_btnList_Import(self):
        filePath, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "选取测试用例文件", "./", "*.csv")
        if filePath == "":
            return
        self.ui.tbl_testcase.setRowCount(0)
        self.ui.tbl_testcase.clearContents()
        with open(filePath, encoding='utf-8') as csvFile:
            row_reader = csv.reader(csvFile)
            header_row = next(row_reader)
            for row in row_reader:
                curRow = self.ui.tbl_testcase.rowCount()
                self.ui.tbl_testcase.insertRow(self.ui.tbl_testcase.rowCount())
                item = QTableWidgetItem()
                item.setCheckState(Qt.Checked)
                item.setFont(QFont('Times', 8, QFont.Normal))
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.ui.tbl_testcase.setItem(curRow, 0, item)
                for i in range(8):
                    item1 = QTableWidgetItem(row[i + 1])
                    item1.setFont(QFont('Times', 8, QFont.Normal))
                    item1.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    # 业务名称和测试对象APP不可编辑
                    if i == 0 or i == 6:
                        item1.setFlags(Qt.NoItemFlags)
                    self.ui.tbl_testcase.setItem(curRow, i + 1, item1)

    # 删除当前项
    def on_btnList_Delete(self):
        curRow = self.ui.tbl_testcase.currentRow()  # 当前行号
        self.ui.tbl_testcase.removeRow(curRow)

    # 全选
    def on_btnSel_ALL(self):
        for i in range(self.ui.tbl_testcase.rowCount()):
            aItem = self.ui.tbl_testcase.item(i, 0)
            aItem.setCheckState(Qt.Checked)

    # 全不选
    def on_btnSel_None(self):
        for i in range(self.ui.tbl_testcase.rowCount()):
            aItem = self.ui.tbl_testcase.item(i, 0)
            aItem.setCheckState(Qt.Unchecked)

    # 反选
    def on_btnSel_Invs(self):
        for i in range(self.ui.tbl_testcase.rowCount()):
            aItem = self.ui.tbl_testcase.item(i, 0)
            if aItem.checkState() != Qt.Checked:
                aItem.setCheckState(Qt.Checked)
            else:
                aItem.setCheckState(Qt.Unchecked)

    # </editor-fold>

    # <editor-fold desc="批量处理业务测试执行">
    def run_batch_test(self):
        # 测试用终端选择状态
        sn_list = []
        versions = []
        for index in range(self.ui.tbl_ue_info.rowCount()):
            if self.ui.tbl_ue_info.item(index, 0).checkState() == Qt.Checked:
                sn_list.append(self.ui.tbl_ue_info.item(index, 1).text())
                versions.append(self.ui.tbl_ue_info.item(index, 2).text())
        if len(sn_list) == 0:
            QMessageBox.warning(self, "警告", "未选择测试用终端")
            return

        if len(sn_list) > 1:
            QMessageBox.warning(self, "警告", "当前系统仅支持一个终端")
            return

        selRowCunt = 0
        for index in range(self.ui.tbl_testcase.rowCount()):
            if self.ui.tbl_testcase.item(index, 0).checkState() == Qt.Checked:
                if not self.check_batch_test_item_value(index):
                    return
                selRowCunt += 1

        if selRowCunt == 0:
            QMessageBox.warning(self, "警告", "未选择业务")
            return

        self.ui.txt_run_batchtest_state.clear()
        self.test_result_list = []
        self.test_stop_flag = False
        self.batch_flg = True
        time.sleep(1)
        # 批量业务执行状态线程没有启动的场合：
        if not self.show_batch_state_thread.is_alive():
            self.show_batch_state_thread.start()

        # 判断屏幕是否关闭(OFF:关闭; ON:点亮)
        if self.ueutil.dut[sn_list[0]].check_screenstate() == "OFF":
            self.ueutil.dut[sn_list[0]].set_screen_on()
            time.sleep(2)
            self.ueutil.dut[sn_list[0]].set_screen_swipe()
            time.sleep(1)

        def run_batch_test():
            self.resultStateDataQueue.put("业务批量执行开始......")
            for index in range(self.ui.tbl_testcase.rowCount()):
                if self.ui.tbl_testcase.item(index, 0).checkState() == Qt.Checked:
                    itemName = self.ui.tbl_testcase.item(index, 1).text()
                    itemCode = self.testcase_item.get_item_byItem(itemName)
                    times = self.ui.tbl_testcase.item(index, 2).text()
                    interval = self.ui.tbl_testcase.item(index, 3).text()
                    telNo = self.ui.tbl_testcase.item(index, 4).text()
                    smsMessage = self.ui.tbl_testcase.item(index, 5).text()
                    person = self.ui.tbl_testcase.item(index, 6).text()
                    testApp = self.ui.tbl_testcase.item(index, 7).text()
                    duration = self.ui.tbl_testcase.item(index, 8).text()
                    # 短信息
                    if itemCode == "CASE0001":
                        self.run_test_case0001(sn_list[0], times, interval, telNo, smsMessage, itemName)
                    # 语音通话
                    if itemCode == "CASE0002":
                        self.run_test_case0002(sn_list[0], times, interval, telNo, duration, itemName)
                    # 微信视频通话
                    if itemCode == "CASE0003":
                        self.run_test_case0003(versions[0], times, interval, person, duration, itemName)
                    # 短视频播放
                    if itemCode == "CASE0004":
                        self.run_test_case0004(versions[0], testApp, times, interval, duration, itemName)
                    # 视频播放
                    if itemCode == "CASE0005":
                        self.run_test_case0005(versions[0], testApp, times, interval, duration, itemName)
                    # 速率监控
                    if itemCode == "CASE0006":
                        self.run_test_case0006(versions[0], times, interval, itemName)

            self.mysignals.update_batch_table.emit(self.test_result_list)
            self.resultStateDataQueue.put("业务批量执行结束")
            self.ui.btn_test_start.setEnabled(True)
            self.ui.btn_test_stop.setEnabled(True)

        runthread = threading.Thread(target=run_batch_test, daemon=True)
        runthread.start()

    def check_batch_test_item_value(self, index):
        itemName = self.ui.tbl_testcase.item(index, 1).text()
        itemCode = self.testcase_item.get_item_byItem(itemName)
        # 为True表示输入的所有字符都是数字
        if itemCode == "CASE0001":
            smstimes = self.ui.tbl_testcase.item(index, 2).text()
            if not smstimes.isdigit():
                QMessageBox.warning(self, "警告", f'次数必须是数字 [{itemName}]')
                return False
            smsinterval = self.ui.tbl_testcase.item(index, 3).text()
            # 为True表示输入的所有字符都是数字
            if not smsinterval.isdigit():
                QMessageBox.warning(self, "警告", f'间隔必须是数字 [{itemName}]')
                return False
            sms_tell_no = self.ui.tbl_testcase.item(index, 4).text()
            if sms_tell_no == "":
                QMessageBox.warning(self, "警告", f'电话号码不能为空 [{itemName}]')
                return False
            if not sms_tell_no.isdigit():
                QMessageBox.warning(self, "警告", f'电话号码必须是数字 [{itemName}]')
                return False
            smsMessage = self.ui.tbl_testcase.item(index, 5).text()
            if smsMessage == "":
                QMessageBox.warning(self, "警告", f'短信息内容不能为空 [{itemName}]')
                return False

        if itemCode == "CASE0002":
            votimes = self.ui.tbl_testcase.item(index, 2).text()
            # 为True表示输入的所有字符都是数字
            if not votimes.isdigit():
                QMessageBox.warning(self, "警告", f'次数必须是数字 [{itemName}]')
                return False
            vointerval = self.ui.tbl_testcase.item(index, 3).text()
            # 为True表示输入的所有字符都是数字
            if not vointerval.isdigit():
                QMessageBox.warning(self, "警告", f'间隔必须是数字 [{itemName}]')
                return False
            vo_tell_no = self.ui.tbl_testcase.item(index, 4).text()
            if vo_tell_no == "":
                QMessageBox.warning(self, "警告", f'电话号码不能为空 [{itemName}]')
                return False
            if not vo_tell_no.isdigit():
                QMessageBox.warning(self, "警告", f'电话号码必须是数字 [{itemName}]')
                return False
            vo_strduration = self.ui.tbl_testcase.item(index, 8).text()
            if not vo_strduration.isdigit():
                QMessageBox.warning(self, "警告", f'连接时长必须是数字 [{itemName}]')
                return False

        if itemCode == "CASE0003":
            wecharttimes = self.ui.tbl_testcase.item(index, 2).text()
            # 为True表示输入的所有字符都是数字
            if not wecharttimes.isdigit():
                QMessageBox.warning(self, "警告", f'次数必须是数字 [{itemName}]')
                return False
            wecharinterval = self.ui.tbl_testcase.item(index, 3).text()
            # 为True表示输入的所有字符都是数字
            if not wecharinterval.isdigit():
                QMessageBox.warning(self, "警告", f'间隔必须是数字 [{itemName}]')
                return False
            person = self.ui.tbl_testcase.item(index, 6).text()
            if person == "":
                QMessageBox.warning(self, "警告", f'微信联系人不能为空 [{itemName}]')
                return False
            wechartstrduration = self.ui.tbl_testcase.item(index, 8).text()
            if not wechartstrduration.isdigit():
                QMessageBox.warning(self, "警告", f'连接时长必须是数字 [{itemName}]')
                return False

        if itemCode == "CASE0004":
            minivideotimes = self.ui.tbl_testcase.item(index, 2).text()
            # 为True表示输入的所有字符都是数字
            if not minivideotimes.isdigit():
                QMessageBox.warning(self, "警告", f'次数必须是数字 [{itemName}]')
                return False
            minivideointerval = self.ui.tbl_testcase.item(index, 3).text()
            # 为True表示输入的所有字符都是数字
            if not minivideointerval.isdigit():
                QMessageBox.warning(self, "警告", f'间隔必须是数字 [{itemName}]')
                return False
            minivideoduration = self.ui.tbl_testcase.item(index, 8).text()
            if not minivideoduration.isdigit():
                QMessageBox.warning(self, "警告", f'连接时长必须是数字 [{itemName}]')
                return False

        if itemCode == "CASE0005":
            videotimes = self.ui.tbl_testcase.item(index, 2).text()
            # 为True表示输入的所有字符都是数字
            if not videotimes.isdigit():
                QMessageBox.warning(self, "警告", f'次数必须是数字 [{itemName}]')
                return False
            videointerval = self.ui.tbl_testcase.item(index, 3).text()
            # 为True表示输入的所有字符都是数字
            if not videointerval.isdigit():
                QMessageBox.warning(self, "警告", f'间隔必须是数字 [{itemName}]')
                return False
            videoduration = self.ui.tbl_testcase.item(index, 8).text()
            if not videoduration.isdigit():
                QMessageBox.warning(self, "警告", f'连接时长必须是数字 [{itemName}]')
                return False

        if itemCode == "CASE0006":
            speedtesttimes = self.ui.tbl_testcase.item(index, 2).text()
            # 为True表示输入的所有字符都是数字
            if not speedtesttimes.isdigit():
                QMessageBox.warning(self, "警告", f'次数必须是数字 [{itemName}]')
                return False
            speedtestinterval = self.ui.tbl_testcase.item(index, 3).text()
            # 为True表示输入的所有字符都是数字
            if not speedtestinterval.isdigit():
                QMessageBox.warning(self, "警告", f'间隔必须是数字 [{itemName}]')
                return False
        return True

    def print_batch_table(self, resultlist):
        self.ui.tbl_run_batchtest_result.clearContents()
        self.ui.tbl_run_batchtest_result.setRowCount(0)
        self.ui.tbl_run_batchtest_result.resizeRowsToContents()
        # 设置行宽和高按照内容自适应
        # result list（'业务名称', '测试次数', '成功次数', '失败次数'）
        # 测试结果没找到
        if (len(resultlist)) == 0:
            return
        # 测试结果一览画面表示处理
        dframe = pd.DataFrame(resultlist)
        df = dframe.groupby(0, as_index=False).sum()
        for i in df.index:
            frameData = df.loc[i].values[0:]
            curRow = self.ui.tbl_run_batchtest_result.rowCount()
            self.ui.tbl_run_batchtest_result.insertRow(curRow)
            item1 = QTableWidgetItem(str(frameData[0]))
            item1.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.ui.tbl_run_batchtest_result.setItem(curRow, 0, item1)
            item2 = QTableWidgetItem(str(frameData[1]))
            item2.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.ui.tbl_run_batchtest_result.setItem(curRow, 1, item2)
            item3 = QTableWidgetItem(str(frameData[2]))
            item3.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.ui.tbl_run_batchtest_result.setItem(curRow, 2, item3)
            item4 = QTableWidgetItem(str(frameData[3]))
            item4.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.ui.tbl_run_batchtest_result.setItem(curRow, 3, item4)

    # </editor-fold>

    # <editor-fold desc="业务测试用例实行">
    def check_test_item_value(self, itemCode, itemName):
        smstimes = self.ui.text_sms_times_case.text()
        # 为True表示输入的所有字符都是数字
        if itemCode == "CASE0001":
            if not smstimes.isdigit():
                QMessageBox.warning(self, "警告", f'次数必须是数字 [{itemName}]')
                return False
            smsinterval = self.ui.text_sms_interval_cace.text()
            # 为True表示输入的所有字符都是数字
            if not smsinterval.isdigit():
                QMessageBox.warning(self, "警告", f'间隔必须是数字 [{itemName}]')
                return False
            sms_tell_no = self.ui.text_sms_tell_no.text()
            if sms_tell_no == "":
                QMessageBox.warning(self, "警告", f'电话号码不能为空 [{itemName}]')
                return False
            if not sms_tell_no.isdigit():
                QMessageBox.warning(self, "警告", f'电话号码必须是数字 [{itemName}]')
                return False
            smsMessage = self.ui.pText_sms_string.toPlainText()
            if smsMessage == "":
                QMessageBox.warning(self, "警告", f'短信息内容不能为空 [{itemName}]')
                return False

        if itemCode == "CASE0002":
            votimes = self.ui.text_vo_times.text()
            # 为True表示输入的所有字符都是数字
            if not votimes.isdigit():
                QMessageBox.warning(self, "警告", f'次数必须是数字 [{itemName}]')
                return False
            vointerval = self.ui.text_vo_interval.text()
            # 为True表示输入的所有字符都是数字
            if not vointerval.isdigit():
                QMessageBox.warning(self, "警告", f'间隔必须是数字 [{itemName}]')
                return False
            vo_tell_no = self.ui.text_vo_tell_no.text()
            if vo_tell_no == "":
                QMessageBox.warning(self, "警告", f'电话号码不能为空 [{itemName}]')
                return False
            if not vo_tell_no.isdigit():
                QMessageBox.warning(self, "警告", f'电话号码必须是数字 [{itemName}]')
                return False
            vo_strduration = int(self.ui.text_vo_duration.text())
            if not vo_strduration.isdigit():
                QMessageBox.warning(self, "警告", f'连接时长必须是数字 [{itemName}]')
                return False

        if itemCode == "CASE0003":
            wecharttimes = self.ui.text_wechart_times.text()
            # 为True表示输入的所有字符都是数字
            if not wecharttimes.isdigit():
                QMessageBox.warning(self, "警告", f'次数必须是数字 [{itemName}]')
                return False
            wecharinterval = self.ui.text_wechart_interval.text()
            # 为True表示输入的所有字符都是数字
            if not wecharinterval.isdigit():
                QMessageBox.warning(self, "警告", f'间隔必须是数字 [{itemName}]')
                return False
            person = self.ui.text_wechart_person.text()
            if person == "":
                QMessageBox.warning(self, "警告", f'微信联系人不能为空 [{itemName}]')
                return False
            wechartstrduration = self.ui.text_wechart_duration.text()
            if not wechartstrduration.isdigit():
                QMessageBox.warning(self, "警告", f'连接时长必须是数字 [{itemName}]')
                return False

        if itemCode == "CASE0004":
            minivideotimes = self.ui.text_mini_video_times.text()
            # 为True表示输入的所有字符都是数字
            if not minivideotimes.isdigit():
                QMessageBox.warning(self, "警告", f'次数必须是数字 [{itemName}]')
                return False
            minivideointerval = self.ui.text_mini_video_interval.text()
            # 为True表示输入的所有字符都是数字
            if not minivideointerval.isdigit():
                QMessageBox.warning(self, "警告", f'间隔必须是数字 [{itemName}]')
                return False
            minivideoduration = self.ui.text_mini_video_duration.text()
            if not minivideoduration.isdigit():
                QMessageBox.warning(self, "警告", f'连接时长必须是数字 [{itemName}]')
                return False

        if itemCode == "CASE0005":
            videotimes = self.ui.text_video_times.text()
            # 为True表示输入的所有字符都是数字
            if not videotimes.isdigit():
                QMessageBox.warning(self, "警告", f'次数必须是数字 [{itemName}]')
                return False
            videointerval = self.ui.text_video_interval.text()
            # 为True表示输入的所有字符都是数字
            if not videointerval.isdigit():
                QMessageBox.warning(self, "警告", f'间隔必须是数字 [{itemName}]')
                return False
            videoduration = self.ui.text_video_duration.text()
            if not videoduration.isdigit():
                QMessageBox.warning(self, "警告", f'连接时长必须是数字 [{itemName}]')
                return False

        if itemCode == "CASE0006":
            speedtesttimes = self.ui.text_speedtest_ue_times.text()
            # 为True表示输入的所有字符都是数字
            if not speedtesttimes.isdigit():
                QMessageBox.warning(self, "警告", f'次数必须是数字 [{itemName}]')
                return False
            speedtestinterval = self.ui.text_speedtest_ue_interval.text()
            # 为True表示输入的所有字符都是数字
            if not speedtestinterval.isdigit():
                QMessageBox.warning(self, "警告", f'间隔必须是数字 [{itemName}]')
                return False
        return True

    # 测试用例执行
    def on_btn_start(self):
        time.sleep(1)
        # 测试用终端选择状态
        sn_list = []
        versions = []
        for index in range(self.ui.tbl_ue_info.rowCount()):
            if self.ui.tbl_ue_info.item(index, 0).checkState() == Qt.Checked:
                sn_list.append(self.ui.tbl_ue_info.item(index, 1).text())
                versions.append(self.ui.tbl_ue_info.item(index, 2).text())
        if len(sn_list) == 0:
            QMessageBox.warning(self, "警告", "未选择测试用终端")
            return

        if len(sn_list) > 1:
            QMessageBox.warning(self, "警告", "当前系统仅支持一个终端")
            return

        itemName = self.ui.cBox_test_business.currentText()
        itemCode = self.testcase_item.get_item_byItem(itemName)
        if not self.check_test_item_value(itemCode, itemName):
            return

        self.ui.txt_text_result.clear()
        self.ui.btn_test_start.setEnabled(False)
        self.ui.btn_test_stop.setEnabled(True)
        self.test_stop_flag = False
        self.test_result_list = []
        self.batch_flg = False
        time.sleep(1)

        # 批量业务执行状态线程没有启动的场合：
        if not self.show_state_thread.is_alive():
            self.show_state_thread.start()

        # 判断屏幕是否关闭(OFF:关闭; ON:点亮)
        if self.ueutil.dut[sn_list[0]].check_screenstate() == "OFF":
            self.ueutil.dut[sn_list[0]].set_screen_on()
            time.sleep(2)
            self.ueutil.dut[sn_list[0]].set_screen_swipe()
            time.sleep(1)

        def run_test():
            self.resultStateDataQueue.put("测试开始......")
            # 短消息测试实施
            if itemCode == "CASE0001":
                times = int(self.ui.text_sms_times_case.text())
                interval = int(self.ui.text_sms_interval_cace.text())
                tell_no = self.ui.text_sms_tell_no.text()
                smsMessage = self.ui.pText_sms_string.toPlainText()
                self.run_test_case0001(sn_list[0], times, interval, tell_no, smsMessage, itemName)
            # 语音通话测试实施
            if itemCode == "CASE0002":
                times = int(self.ui.text_vo_times.text())
                interval = int(self.ui.text_vo_interval.text())
                tell_no = self.ui.text_vo_tell_no.text()
                duration = int(self.ui.text_vo_duration.text())
                self.run_test_case0002(sn_list[0], times, interval, tell_no, duration, itemName)
            # 微信视频通话测试实施
            if itemCode == "CASE0003":
                times = int(self.ui.text_wechart_times.text())
                interval = int(self.ui.text_wechart_interval.text())
                person = self.ui.text_wechart_person.text()
                duration = int(self.ui.text_wechart_duration.text())
                self.run_test_case0003(versions[0], times, interval, person, duration, itemName)
            # 短视频测试实施
            if itemCode == "CASE0004":
                app = self.ui.cbox_mini_video_app.currentText()
                times = int(self.ui.text_mini_video_times.text())
                interval = int(self.ui.text_mini_video_interval.text())
                duration = int(self.ui.text_mini_video_duration.text())
                self.run_test_case0004(versions[0], app, times, interval, duration, itemName)
            # 视频播放测试实施
            if itemCode == "CASE0005":
                app = self.ui.cbox_video_app.currentText()
                times = int(self.ui.text_video_times.text())
                interval = int(self.ui.text_video_interval.text())
                duration = int(self.ui.text_video_duration.text())
                self.run_test_case0005(versions[0], app, times, interval, duration, itemName)
            # 实时网络监控测试实施
            if itemCode == "CASE0006":
                times = int(self.ui.text_speedtest_ue_times.text())
                interval = int(self.ui.text_speedtest_ue_interval.text())
                self.run_test_case0006(versions[0], times, interval, itemName)

            self.mysignals.update_table.emit(self.test_result_list)
            self.resultStateDataQueue.put("自动测试结束")
            self.ui.btn_test_start.setEnabled(True)
            self.ui.btn_test_stop.setEnabled(True)

        runthread = threading.Thread(target=run_test, daemon=True)
        runthread.start()

    # 短信息测试执行
    def run_test_case0001(self, serial_number, sms_times, sms_interval, sms_tell_no, sms_mess, itemName):
        # 实例化测试用例
        testcase_sms = Adb_Send_Sms(serial_number)
        # 注册接收数据回调函数
        testcase_sms.set_state_data(self.get_stateInfo)
        self.resultStateDataQueue.put(f'短消息发送开始......')
        for i in range(sms_times):
            self.resultStateDataQueue.put(f'第 {i + 1} 次短消息发送开始......')
            ret = testcase_sms.send_sms(sms_tell_no, sms_mess)
            if ret == 0:
                self.resultStateDataQueue.put(f'第 {i + 1} 次短消息发送成功')
                self.test_result_list.append([itemName, 1, 1, 0])
            else:
                self.resultStateDataQueue.put(f'第 {i + 1} 次短消息发送失败')
                self.test_result_list.append([itemName, 1, 0, 1])
            if self.test_stop_flag:
                break
            time.sleep(sms_interval)
        self.resultStateDataQueue.put(f'短消息发送结束')

    # 语音通话
    def run_test_case0002(self, serial_number, vo_times, vo_interval, vo_tell_no, vo_duration, itemName):
        # 实例化测试用例
        testcase_vo = Adb_Make_Call(serial_number)
        # 注册接收数据回调函数
        testcase_vo.set_state_data(self.get_stateInfo)
        self.resultStateDataQueue.put(f'语音通话开始......')
        for i in range(vo_times):
            self.resultStateDataQueue.put(f'第 {i + 1} 次开始......')
            ret = testcase_vo.make_call(vo_tell_no)
            if ret == 0:
                time.sleep(vo_duration)
                if self.ueutil.dut[serial_number].check_callstate() != 0:
                    ret1 = testcase_vo.end_call()
                    if ret1 == 0:
                        self.resultStateDataQueue.put(f'第 {i + 1} 次语音通话成功')
                        self.test_result_list.append([itemName, 1, 1, 0])
                    else:
                        self.resultStateDataQueue.put(f'第 {i + 1} 次语音通话失败')
                        self.test_result_list.append([itemName, 1, 0, 1])
                else:
                    self.resultStateDataQueue.put(f'第 {i + 1} 次语音通话成功')
                    self.test_result_list.append([itemName, 1, 1, 0])
            else:
                self.resultStateDataQueue.put(f'第 {i + 1} 次语音通话失败')
                self.test_result_list.append([itemName, 1, 0, 1])
            if self.test_stop_flag:
                break
            time.sleep(vo_interval)
        self.resultStateDataQueue.put(f'语音通话结束')

    # 微信视频通话
    def run_test_case0003(self, version, times, interval, person, duration, itemName):
        if not self.check_config_dict(self.appserver_dict_cfg, self.wechat_dict_cfg):
            self.resultStateDataQueue.put(f'微信的配置文件有误，无法完成当前业务')
            return
        # 实例化测试用例
        testcase_wechat = Appiume_WeChat(version, self.appserver_dict_cfg["server"],
                                         self.wechat_dict_cfg["apppackage"], self.wechat_dict_cfg["appactivity"])
        # 注册接收数据回调函数
        testcase_wechat.set_state_data(self.get_stateInfo)
        self.resultStateDataQueue.put(f'微信视频通话开始......')
        for i in range(times):
            self.resultStateDataQueue.put(f'第 {i + 1} 次微信视频通话开始......')
            ret = testcase_wechat.start_wechat(person, duration)
            if ret == 0:
                self.resultStateDataQueue.put(f'第 {i + 1} 次微信视频通话成功')
                self.test_result_list.append([itemName, 1, 1, 0])
            else:
                self.resultStateDataQueue.put(f'第 {i + 1} 次微信视频通话失败')
                self.test_result_list.append([itemName, 1, 0, 1])
            time.sleep(interval)
            if self.test_stop_flag:
                break
        self.resultStateDataQueue.put(f'微信视频通话结束')

    # 短视频播放
    def run_test_case0004(self, version, app, times, interval, duration, itemName):
        # 实例化测试用例
        if app == self.testcase_item.get_mini_video_item_byKey("MINIVIDEO0001"):
            if not self.check_config_dict(self.appserver_dict_cfg, self.kuaishou_dict_cfg):
                self.resultStateDataQueue.put(f'快手的配置文件有误，无法完成当前业务')
                return
            testcase_kuaishou = Appiume_Kuaishou(version, self.appserver_dict_cfg["server"],
                                                 self.kuaishou_dict_cfg["apppackage"],
                                                 self.kuaishou_dict_cfg["appactivity"])
            # 注册接收数据回调函数
            testcase_kuaishou.set_state_data(self.get_stateInfo)
        if app == self.testcase_item.get_mini_video_item_byKey("MINIVIDEO0002"):
            if not self.check_config_dict(self.appserver_dict_cfg, self.tiktok_dict_cfg):
                self.resultStateDataQueue.put(f'抖音的配置文件有误，无法完成当前业务')
                return
            testcase_tikTok = Appiume_TikTok(version,
                                             self.appserver_dict_cfg["server"],
                                             self.tiktok_dict_cfg["apppackage"],
                                             self.tiktok_dict_cfg["appactivity"])
            # 注册接收数据回调函数
            testcase_tikTok.set_state_data(self.get_stateInfo)
        self.resultStateDataQueue.put(f'短视频播放开始......')
        for i in range(times):
            self.resultStateDataQueue.put(f'第 {i + 1} 次短视频播放开始......')
            if app == self.testcase_item.get_mini_video_item_byKey("MINIVIDEO0001"):
                ret = testcase_kuaishou.start_kuaishou(duration)
            if app == self.testcase_item.get_mini_video_item_byKey("MINIVIDEO0002"):
                ret = testcase_tikTok.start_tiktok(duration)
            if ret == 0:
                self.resultStateDataQueue.put(f'第 {i + 1} 次短视频播放成功')
                self.test_result_list.append([itemName, 1, 1, 0])
            else:
                self.resultStateDataQueue.put(f'第 {i + 1} 次短视频播放失败')
                self.test_result_list.append([itemName, 1, 0, 1])
            time.sleep(interval)
            if self.test_stop_flag:
                return
        self.resultStateDataQueue.put(f'短视频播放结束')

    # 视频播放
    def run_test_case0005(self, version, app, times, interval, duration, itemName):
        # 实例化测试用例
        if app == self.testcase_item.get_video_item_byKey("VIDEO0001"):
            if not self.check_config_dict(self.appserver_dict_cfg, self.bilibili_dict_cfg):
                self.resultStateDataQueue.put(f'哔哩哔哩的配置文件有误，无法完成当前业务')
                return
            testcase_bilibili = Appiume_Bilibili(version, self.appserver_dict_cfg["server"],
                                                 self.bilibili_dict_cfg["apppackage"],
                                                 self.bilibili_dict_cfg["appactivity"])
            # 注册接收数据回调函数
            testcase_bilibili.set_state_data(self.get_stateInfo)
        if app == self.testcase_item.get_video_item_byKey("VIDEO0002"):
            self.resultStateDataQueue.put(f'爱奇艺app未实装')
            return
            # self.resultStateDataQueue.put(f'视频播放测试开始:')
        for i in range(times):
            self.resultStateDataQueue.put(f'第 {i + 1} 次视频播放开始......')
            if app == self.testcase_item.get_video_item_byKey("VIDEO0001"):
                ret = testcase_bilibili.start_bilibili(duration)
            if ret == 0:
                self.resultStateDataQueue.put(f'第 {i + 1} 次视频播放成功......')
                self.test_result_list.append([itemName, 1, 1, 0])
            else:
                self.resultStateDataQueue.put(f'第 {i + 1} 次视频播放失败')
                self.test_result_list.append([itemName, 1, 0, 1])
            time.sleep(interval)
            if self.test_stop_flag:
                break
        self.resultStateDataQueue.put(f'视频播放结束')

    # 速率监控
    def run_test_case0006(self, version, times, interval, itemName):
        # 实例化测试用例
        if not self.check_config_dict(self.appserver_dict_cfg, self.speedtest_dict_cfg):
            self.resultStateDataQueue.put(f'speedtest的配置文件有误，无法完成当前业务')
            return
        testcase_Speedtest = Appiume_Speedtest(version, self.appserver_dict_cfg["server"],
                                               self.speedtest_dict_cfg["apppackage"],
                                               self.speedtest_dict_cfg["appactivity"])
        # 注册接收数据回调函数
        testcase_Speedtest.set_state_data(self.get_stateInfo)
        self.resultStateDataQueue.put(f'速率监控开始......')
        for i in range(times):
            self.resultStateDataQueue.put(f'第 {i + 1} 次速率监控开始......')
            ret = testcase_Speedtest.start_speedtest()
            if ret == 0:
                self.resultStateDataQueue.put(f'第 {i + 1} 次速率监控成功')
                self.test_result_list.append([itemName, 1, 1, 0])
            else:
                self.resultStateDataQueue.put(f'第 {i + 1} 次速率监控失败')
                self.test_result_list.append([itemName, 1, 0, 1])
            time.sleep(interval)
            if self.test_stop_flag:
                break
        self.resultStateDataQueue.put(f'速率监控结束')

    # 判断配置文件的完整性
    def check_config_dict(self, appdict, itemdict):
        if not 'server' in appdict.keys():
            return False
        if not 'apppackage' in itemdict.keys():
            return False
        if not 'appactivity' in itemdict.keys():
            return False
        return True

    def on_btn_stop(self):
        if not self.test_stop_flag:
            self.resultStateDataQueue.put("当前执行中的业务完成后，测试将结束！")
            self.ui.btn_test_stop.setEnabled(False)
        else:
            self.ui.btn_test_stop.setEnabled(True)
        self.test_stop_flag = True

    # 测试用例执行状态用（回调函数）
    def get_stateInfo(self, stateData):
        self.resultStateDataQueue.put(stateData)

    # 主线程的数据输出(测试结果)
    def print_table(self, resultlist):
        self.ui.tbl_test_result.clearContents()
        self.ui.tbl_test_result.setRowCount(0)
        self.ui.tbl_test_result.resizeRowsToContents()
        # 设置行宽和高按照内容自适应
        self.ui.btn_test_stop.setEnabled(True)
        self.ui.btn_test_start.setEnabled(True)
        # result list（'业务名称', '测试次数', '成功次数', '失败次数'）
        # 测试结果没找到
        if (len(resultlist)) == 0:
            return
        # 测试结果一览画面表示处理
        dframe = pd.DataFrame(resultlist)
        df = dframe.groupby(0, as_index=False).sum()
        for i in df.index:
            frameData = df.loc[i].values[0:]
            curRow = self.ui.tbl_test_result.rowCount()
            self.ui.tbl_test_result.insertRow(curRow)
            item1 = QTableWidgetItem(str(frameData[0]))
            item1.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.ui.tbl_test_result.setItem(curRow, 0, item1)
            item2 = QTableWidgetItem(str(frameData[1]))
            item2.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.ui.tbl_test_result.setItem(curRow, 1, item2)
            item3 = QTableWidgetItem(str(frameData[2]))
            item3.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.ui.tbl_test_result.setItem(curRow, 2, item3)
            item4 = QTableWidgetItem(str(frameData[3]))
            item4.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.ui.tbl_test_result.setItem(curRow, 3, item4)

    #
    def run_business_change(self):
        if self.ui.cBox_test_business.currentText() == self.testcase_item.get_item_byKey("CASE0001"):
            self.ui.toolBox.setCurrentIndex(0)
        if self.ui.cBox_test_business.currentText() == self.testcase_item.get_item_byKey("CASE0002"):
            self.ui.toolBox.setCurrentIndex(1)
        if self.ui.cBox_test_business.currentText() == self.testcase_item.get_item_byKey("CASE0003"):
            self.ui.toolBox.setCurrentIndex(2)
        if self.ui.cBox_test_business.currentText() == self.testcase_item.get_item_byKey("CASE0004"):
            self.ui.toolBox.setCurrentIndex(3)
        if self.ui.cBox_test_business.currentText() == self.testcase_item.get_item_byKey("CASE0005"):
            self.ui.toolBox.setCurrentIndex(4)
        if self.ui.cBox_test_business.currentText() == self.testcase_item.get_item_byKey("CASE0006"):
            self.ui.toolBox.setCurrentIndex(5)

    # </editor-fold>

    # <editor-fold desc="PC端speedtest实施处理">

    def on_start_speedtest_pc(self):
        # UE列表显示
        self.ui.lbl_image.setPixmap(QPixmap(""))
        self.ui.btn_speed_pc_start.setEnabled(False)
        self.ui.txt_speedtest_pc_result.clear()

        # 界面显示测试状态线程
        show_sp_state_thread = threading.Thread(target=self.show_sp_pc_result_state, daemon=True)
        show_sp_state_thread.daemon = 1
        show_sp_state_thread.start()

        # speedtest测试实施
        speedtest_pc_thread = threading.Thread(target=self.test_speedtest_pc, daemon=True)
        speedtest_pc_thread.daemon = 1
        speedtest_pc_thread.start()

    def test_speedtest_pc(self):
        speedtest_pc = Speedtest_PC()
        speedtest_pc.set_state_data(self.get_speedtest_pc_stateInfo)
        retDict = speedtest_pc.start_test()
        if retDict.get("retcode") == 0:
            self.sp_pc_StateDataQueue.put("测试结果图片展示")
            path = os.path.realpath(os.curdir)
            pngPath = os.path.join(path, "image", "speedtest_img.png")
            pix = QPixmap(pngPath)
            self.ui.lbl_image.setPixmap(pix)
        elif retDict.get("retcode") == 2:
            self.sp_pc_StateDataQueue.put("测试结果数据展示")
            self.ui.lbl_image.setText((json.dumps(retDict.get("data"), indent=4)))
        self.ui.btn_speed_pc_start.setEnabled(True)

    # speettest 回调函数
    def get_speedtest_pc_stateInfo(self, sp_pc_stateData):
        self.sp_pc_StateDataQueue.put(sp_pc_stateData)

    # 显示测试结果状态信息
    def show_sp_pc_result_state(self):
        while not self.exitFlg:
            if self.sp_pc_StateDataQueue.empty():
                continue
            else:
                resultStateData = self.sp_pc_StateDataQueue.get()
                self.mysignals.sp_pc_state_text_print.emit(resultStateData)

    # 测试状态实时显示
    def print_sp_pc_result_text(self, strState):
        cursor = self.ui.txt_speedtest_pc_result.textCursor()
        cursor.movePosition(cursor.End)
        strTime = str(datetime.datetime.now())[:23]
        cursor.insertText("[" + strTime + "]   " + strState + '\n')
        self.ui.txt_speedtest_pc_result.ensureCursorVisible()

    # </editor-fold>

    # <editor-fold desc="数据处理">
    def open_road_file(self):
        inFilePaths, filetype = QtWidgets.QFileDialog.getOpenFileNames(self, 'open file', "./", "*.*")
        # inFilePath, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "选取路测", "./", "*.*")
        if len(inFilePaths) == 0:
            # print(len(inFilePaths))
            return
        self.ui.txt_road_file_path.clear()
        for filePath in inFilePaths:
            self.ui.txt_road_file_path.append(filePath)

    def edit_road_test_data(self):
        inFilePaths = self.ui.txt_road_file_path.toPlainText()
        if inFilePaths == "":
            QMessageBox.warning(self, "警告", "请选择路测文件")
            return
        fileList = inFilePaths.split('\n')
        for path in fileList:
            if not os.path.exists(path):
                QMessageBox.warning(self, "警告", f'选择的路测文件[{path}]不存在！')
                return

        outFilePath, filetype = QtWidgets.QFileDialog.getSaveFileName(self, "输出结果", "./", "*.xlsx")
        if outFilePath == "":
            return
        self.ui.txt_road_result.clear()
        self.ui.txt_road_result_end.clear()
        self.ui.tbl_data_result_list.setRowCount(0)
        self.ui.tbl_data_result_list.clearContents()
        self.ui.tbl_repetitions_list.setRowCount(0)
        self.ui.tbl_repetitions_list.clearContents()
        # 界面显示测试状态线程
        show_road_state_thread = threading.Thread(target=self.show_road_result_state, daemon=True)
        show_road_state_thread.daemon = 1
        show_road_state_thread.start()

        # speedtest测试实施
        speedtest_pc_thread = threading.Thread(target=self.run_roda_data_edit, args=(fileList, outFilePath,),
                                               daemon=True)
        speedtest_pc_thread.daemon = 1
        speedtest_pc_thread.start()

    # 路测文件编辑
    def run_roda_data_edit(self, inRoadFilePaths, outRoadFilePath):
        data_filtration = Data_Filtration()
        data_filtration.set_road_state(self.get_road_stateInfo)
        ret = data_filtration.run_data_edit(inRoadFilePaths, outRoadFilePath)

        if ret == 0:
            self.ui.txt_road_result_end.append("数据编辑正常结束")
            self.ui.txt_road_result_end.append(outRoadFilePath)

            retData = data_filtration.return_data
            curRow = self.ui.tbl_data_result_list.rowCount()
            self.ui.tbl_data_result_list.insertRow(curRow)
            self.ui.tbl_data_result_list.setRowHeight(curRow, 20)
            # 输入数据件数
            item1 = QTableWidgetItem(str(retData[0]))
            item1.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.ui.tbl_data_result_list.setItem(curRow, 0, item1)

            # 输出数据件数
            item2 = QTableWidgetItem(str(retData[6]))
            item2.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.ui.tbl_data_result_list.setItem(curRow, 1, item2)
            # CGI是空件数
            item3 = QTableWidgetItem(str(retData[1]))
            item3.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.ui.tbl_data_result_list.setItem(curRow, 2, item3)
            # 经度是空件数
            item4 = QTableWidgetItem(str(retData[2]))
            item4.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.ui.tbl_data_result_list.setItem(curRow, 3, item4)
            # 纬度是空件数
            item5 = QTableWidgetItem(str(retData[3]))
            item5.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.ui.tbl_data_result_list.setItem(curRow, 4, item5)
            # RSRP是空件数
            item6 = QTableWidgetItem(str(retData[4]))
            item6.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.ui.tbl_data_result_list.setItem(curRow, 5, item6)
            # 重复件数
            item7 = QTableWidgetItem(str(retData[5]))
            item7.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.ui.tbl_data_result_list.setItem(curRow, 6, item7)

            for item in retData[7]:
                curRow1 = self.ui.tbl_repetitions_list.rowCount()
                # print(curRow1)
                self.ui.tbl_repetitions_list.insertRow(curRow1)
                self.ui.tbl_repetitions_list.setRowHeight(curRow1, 20)
                # CGI
                item8 = QTableWidgetItem(str(item[0]))
                item8.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.ui.tbl_repetitions_list.setItem(curRow1, 0, item8)
                # 经度
                item9 = QTableWidgetItem(str(item[1]))
                item9.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.ui.tbl_repetitions_list.setItem(curRow1, 1, item9)
                # 纬度
                item10 = QTableWidgetItem(str(item[2]))
                item10.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.ui.tbl_repetitions_list.setItem(curRow1, 2, item10)
                # 件数
                item11 = QTableWidgetItem(str(item[3]))
                item11.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.ui.tbl_repetitions_list.setItem(curRow1, 3, item11)

        else:
            self.ui.txt_road_result_end.append("数据编辑失败")

    # 测试用例执行状态用（回调函数）
    def get_road_stateInfo(self, stateData):
        self.roadStateDataQueue.put(stateData)

    # 显示测试结果状态信息
    def show_road_result_state(self):
        while not self.exitFlg:
            if self.roadStateDataQueue.empty():
                continue
            else:
                roadStateData = self.roadStateDataQueue.get()
                self.mysignals.road_state_text_print.emit(roadStateData)

    # 测试状态实时显示
    def print_road_result_text(self, strState):
        cursor = self.ui.txt_road_result.textCursor()
        cursor.movePosition(cursor.End)
        strTime = str(datetime.datetime.now())[:23]
        cursor.insertText("[" + strTime + "]   " + strState + '\n')
        self.ui.txt_road_result.ensureCursorVisible()

    # </editor-fold>

    # <editor-fold desc="Video-source">

    def edit_video_tab_init(self):
        self.player = Player()
        self.player.set_window(self.ui.Video_frame_vlc.winId())
        self.mysignals.videotime.connect(self.on_video_time)
        self.ui.video_btn_open.clicked.connect(self.on_video_open)
        self.ui.video_btn_back.clicked.connect(self.on_video_back)
        self.ui.video_btn_play.clicked.connect(self.on_video_play)
        self.ui.video_btn_forward.clicked.connect(self.on_video_forward)
        self.ui.video_btn_stop.clicked.connect(self.on_video_stop)
        self.ui.video_horslider_sound.valueChanged.connect(self.on_video_sound)
        self.ui.video_horslider_moved.sliderMoved.connect(self.on_video_time)
        self.ui.Video_frame_vlc.setStyleSheet("background-color: rgb(0,0,0);")
        self.ui.video_txt_url.setText("https://vjs.zencdn.net/v/oceans.mp4")
        self.timer = QTimer()
        self.timer.start(200)
        self.timer.timeout.connect(self.on_video_clock)

    def on_video_clock(self):
        try:
            num = self.player.get_time()
            if num < 0:
                num = 0
            if num > 0:
                self.ui.video_horslider_moved.setValue(num)
                self.ui.video_lcdNumber_minute.display(str(num // 60000 + 100)[1:])
                self.ui.video_lcdNumber_second.display(':' + str(num // 1000 % 60 + 100)[1:])
        except KeyboardInterrupt:
            pass

    def on_video_play(self):
        if self.player.is_playing() == 1:
            self.player.pause()
            self.ui.video_btn_play.setText('播放')
        else:
            self.player.resume()
            self.ui.video_btn_play.setText('暂停')
        self.ui.video_horslider_moved.setValue(self.player.get_time())

    def on_video_open(self):
        text_url = self.ui.video_txt_url.toPlainText()
        if self.check_url(text_url):
            self.opencamera(text_url)
        else:
            QMessageBox.warning(self, "警告", "请确定网络和视频URL是否有效")

    def check_url(self, text_url):
        # 播放本地视频
        if len(text_url) > 4 and text_url[0:4] != "http":
            return True
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/49.0.2')]
        try:
            opener.open(text_url)
            return True
        except:
            return False

    def on_video_back(self):
        self.player.set_time(self.player.get_time() - 5000)
        self.ui.video_horslider_moved.setValue(self.player.get_time())

    def on_video_forward(self):
        self.player.set_time(self.player.get_time() + 5000)
        self.ui.video_horslider_moved.setValue(self.player.get_time())

    def on_video_stop(self):
        self.player.stop()
        self.ui.video_horslider_moved.setValue(self.player.get_time())

    def on_video_sound(self):
        self.player.set_volume(self.ui.video_horslider_sound.value())

    def on_video_time(self):
        self.player.set_time(self.ui.video_horslider_moved.value())

    def opencamera(self, videourl):
        self.player.play(videourl)  # 开始显示
        self.ui.video_btn_play.setText('暂停')
        time.sleep(1)
        self.ui.video_horslider_sound.setValue(self.player.get_volume())
        self.ui.video_horslider_moved.setMaximum(self.player.get_length())
        self.ui.video_horslider_moved.setValue(self.player.get_time())

    def timehandle(self, timestr):
        if ':' in timestr:
            stoptime = timestr.split(':')
            second = float(stoptime[0]) * 60 + float(stoptime[1])
        else:
            second = float(timestr)
        return second

    # </editor-fold>

    # <editor-fold desc="接收和发送流量">
    def print_bytes_label(self, sent, rcvd):
        self.ui.lbl_bytes_sent.setText(sent)
        self.ui.lbl_bytes_recv.setText(rcvd)

    def show_bytes_sent_rcvd(self):
        first = True
        while not self.exitFlg:
            if first:
                first = False
                last_download = psutil.net_io_counters().bytes_recv
                last_upload = psutil.net_io_counters().bytes_sent
            else:
                cur_download = psutil.net_io_counters().bytes_recv
                cur_upload = psutil.net_io_counters().bytes_sent
                bytes_recv = round((cur_download - last_download) / 1024, 2)
                bytes_sent = round((cur_upload - last_upload) / 1024, 2)
                self.mysignals.bytes_label_print.emit(str(bytes_sent), str(bytes_recv))
                last_download = cur_download
                last_upload = cur_upload
            time.sleep(0.5)

    # </editor-fold>
