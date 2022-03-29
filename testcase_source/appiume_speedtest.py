# coding:utf-8
import time
import traceback

from selenium.webdriver.common.by import By
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy


# 手机端speedtest APP执行处理
class Appiume_Speedtest:
    def __init__(self, version, server, appPackage, appActivity):
        self.statedata_callback = None
        self.server = server
        self.desired_caps = {
            'platformName': 'Android',  # 被测手机是安卓
            'platformVersion': version,  # 手机安卓版本(例：‘10’)
            'deviceName': 'xxx',  # 设备名，安卓手机可以随意填写
            'appPackage': appPackage,  # 启动APP Package名称
            'appActivity': appActivity,  # 启动Activity名称
            'unicodeKeyboard': True,  # 使用自带输入法，输入中文时填True
            'resetKeyboard': True,  # 执行完程序恢复原来输入法
            'noReset': True,  # 不要重置App
            'newCommandTimeout': 6000,
            'automationName': 'UiAutomator2'
            # 'app': r'd:\apk\bili.apk',
        }

    def start_speedtest(self):
        # 连接Appium Server，初始化自动化环境
        self.statedata_callback("连接Appium Server")
        try:
            driver = webdriver.Remote(self.server, self.desired_caps)
        except:
            self.statedata_callback("Appium Server 连接失败！请检查手机的APP是否安装，并且是否已经启动Appium Server！")
            return 2
        driver.implicitly_wait(10)
        self.statedata_callback("Appium Server连接成功")
        result = 0
        try:
            self.statedata_callback("手机端SpeedTest测试开始")
            time.sleep(2)
            element = driver.find_element(By.ID, 'go_button')
            if element:
                element.click()
            time.sleep(35)
            self.statedata_callback("SpeedTest测试结果编辑......")
            # Download
            download_driver = driver.find_element(By.ID, 'download_result_view')
            download_data = download_driver.find_element(By.ID, 'txt_test_result_value').text
            self.statedata_callback("上传(Mbps):  " + download_data)
            # Upload
            upload_driver = driver.find_element(By.ID, 'upload_result_view')
            upload_data = upload_driver.find_element(By.ID, 'txt_test_result_value').text
            self.statedata_callback("下载(Mbps):  " + upload_data)
            # Ping
            ping_driver = driver.find_element(By.ID, 'test_result_item_ping')
            ping_data = ping_driver.find_element(By.ID, 'txt_test_result_value').text
            self.statedata_callback("Ping(毫秒):  " + ping_data)
            # 抖动
            jitter_driver = driver.find_element(By.ID, 'test_result_item_jitter')
            jitter_data = jitter_driver.find_element(By.ID, 'txt_test_result_value').text
            self.statedata_callback("抖动(毫秒):  " + jitter_data)
            # 丢包
            loss_driver = driver.find_element(By.ID, 'test_result_item_packet_loss')
            loss_data = loss_driver.find_element(By.ID, 'txt_test_result_value').text
            self.statedata_callback("丢包:  " + loss_data)
            time.sleep(5)
        except:
            # print(traceback.format_exc())
            result = 1
        self.statedata_callback("手机端SpeedTest测试完成")
        self.statedata_callback("5秒钟后退出speedtest")
        time.sleep(5)
        # 退出
        driver.quit()
        return result

    def set_state_data(self, statedataFunc):
        self.statedata_callback = statedataFunc
        return
