# coding:utf-8
import time
import traceback

from appium import webdriver

# 手机端  哔哩哔哩 APP执行处理
from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.extensions.android.nativekey import AndroidKey
from selenium.webdriver.common.by import By


class Appiume_Bilibili:
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

    def start_bilibili(self, duration):
        result = 0
        self.statedata_callback("连接Appium Server")
        # 连接Appium Server，初始化自动化环境
        try:
            driver = webdriver.Remote(self.server, self.desired_caps)
        except:
            self.statedata_callback("Appium Server 连接失败！请检查手机的APP是否安装，并且是否已经启动Appium Server！")
            return 2
        driver.implicitly_wait(10)
        self.statedata_callback("Appium Server连接成功")
        try:
            self.statedata_callback("开始视频播放处理")
            # 如果有`青少年保护`界面，点击`我知道了`
            titles = driver.find_elements(By.ID, 'tv.danmaku.bili:id/button')
            for item in titles:
                if item.text == "我知道了":
                    item.click()
                    break

            self.statedata_callback("搜索并选择要播放的视频")
            time.sleep(10)
            # 根据id定位搜索位置框，点击
            # driver.find_element(By.ID, 'expand_search').click()
            element = driver.find_element(By.ID, 'expand_search')
            if element:
                element.click()

            # 根据id定位搜索输入框，点击
            sbox = driver.find_element(By.ID, 'search_src_text')
            sbox.send_keys('电影')
            # 输入回车键，确定搜索
            driver.press_keycode(AndroidKey.ENTER)
            time.sleep(10)
            self.statedata_callback("开始播放")
            code = 'new UiSelector().resourceId("tv.danmaku.bili:id/ogv_item_relation_video_image").className(' \
                   '"android.widget.ImageView")'
            # driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, code)[0].click()
            elements = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, code)
            if elements:
                elements[0].click()
            time.sleep(duration)

        except:
            self.statedata_callback("视频播放出现异常")
            # print(traceback.format_exc())
            result = 1
        self.statedata_callback("测试结束，5秒后关闭bilibili")
        time.sleep(5)
        # 退出
        driver.quit()
        return result

    def set_state_data(self, statedataFunc):
        self.statedata_callback = statedataFunc
        return
