# coding:utf-8
import time
import traceback

from appium import webdriver


# 手机端抖音 APP执行处理
from selenium.webdriver.common.by import By


class Appiume_TikTok:
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

    def start_tiktok(self, duration):
        result = 0
        # 连接Appium Server，初始化自动化环境
        self.statedata_callback("连接Appium Server")
        try:
            driver = webdriver.Remote(self.server, self.desired_caps)
        except:
            self.statedata_callback("Appium Server 连接失败！请检查手机的APP是否安装，并且是否已经启动Appium Server！")
            return 2
        driver.implicitly_wait(10)
        self.statedata_callback("Appium Server连接成功")
        self.statedata_callback("短视频开始播放")

        # 如果有`发现通讯录朋友`界面，点击`拒绝`
        titles = driver.find_elements(By.ID, 'com.ss.android.ugc.aweme:id/tv_cancel')
        for item in titles:
            if item.text == "拒绝":
                item.click()
                time.sleep(2)
                break
        # 如果有`发现通讯录朋友`界面，点击`拒绝`
        titles1 = driver.find_elements(By.ID, 'android.widget.Button')
        for item1 in titles1:
            if item1.text == "我知道了":
                item1.click()
                time.sleep(2)
                break
        time.sleep(2)
        try:
            time_start = time.time()
            while True:
                '''从下向上滑动'''
                driver.swipe(300, 1500, 300, 500)
                time.sleep(5)
                if (time.time() - time_start) > duration:
                    break
        except:
            self.statedata_callback("视频播放出现异常")
            # print(traceback.format_exc())
            result = 1
        self.statedata_callback("5秒钟后关闭抖音")
        time.sleep(5)
        # 退出
        driver.quit()
        return result

    def set_state_data(self, statedataFunc):
        self.statedata_callback = statedataFunc
        return