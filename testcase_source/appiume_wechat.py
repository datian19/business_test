# coding:utf-8
import time
import traceback

from appium.webdriver.extensions.android.nativekey import AndroidKey
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy


# 手机端微信 APP执行处理
class Appiume_WeChat:
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

    def start_wechat(self, friend_name, wechart_duration):
        # 连接Appium Server，初始化自动化环境
        self.statedata_callback("连接Appium Server")
        try:
            driver = webdriver.Remote(self.server, self.desired_caps)
        except:
            self.statedata_callback("Appium Server 连接失败！请检查手机的APP是否安装，并且是否已经启动Appium Server！")
            return 2
        # 设置缺省等待时间
        driver.implicitly_wait(10)
        self.statedata_callback("Appium Server连接成功")
        self.statedata_callback("开始尝试连接视频通话")
        result = 0
        try:
            element = driver.find_element(AppiumBy.ID, 'j63')
            if element:
                element.click()
            time.sleep(10)
            self.statedata_callback("查找联系人")
            driver.find_element(AppiumBy.ID, 'cd6').send_keys(friend_name)
            # 输入回车键，确定搜索
            driver.press_keycode(AndroidKey.ENTER)
            # 视频聊天
            time.sleep(10)
            code1 = 'new UiSelector().resourceId("com.tencent.mm:id/a27").className(' \
                    '"android.widget.ImageView")'
            # driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, code1)[0].click()
            elements = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, code1)
            if elements:
                elements[0].click()
            time.sleep(10)

            # driver.find_element(AppiumBy.ID, "com.tencent.mm:id/b3q").click()
            element1 = driver.find_element(AppiumBy.ID, "com.tencent.mm:id/b3q")
            if element1:
                element1.click()
            code2 = 'new UiSelector().resourceId("com.tencent.mm:id/vf").className(' \
                    '"android.widget.ImageView")'
            # driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, code2)[2].click()
            elements1 = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, code2)
            if elements1:
                elements1[2].click()
            time.sleep(10)
            # 打开视频
            self.statedata_callback("打开视频开始视频通话")
            code3 = 'new UiSelector().resourceId("com.tencent.mm:id/ko8").className(' \
                    '"android.widget.TextView")'
            # driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, code3)[0].click()
            elements2 = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, code3)
            if elements2:
                elements2[0].click()
            time.sleep(wechart_duration)

            # 打开语音
            # code3 = 'new UiSelector().resourceId("com.tencent.mm:id/ko8").className(' \
            #         '"android.widget.TextView")'
            # driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, code3)[1].click()
            # time.sleep(10)
        except:
            self.statedata_callback("视频通话出现异常")
            #print(traceback.format_exc())
            result = 1
        # 退出
        self.statedata_callback("5秒钟后退出视频通话")
        time.sleep(5)
        driver.quit()
        return result

    def set_state_data(self, statedataFunc):
        self.statedata_callback = statedataFunc
        return

    # time.sleep(10)
    # b4a = driver.find_element(AppiumBy.ID, "com.tencent.mm:id/b4a")  # 输入框
    # # 需要点击一下唤起键盘，不然全面屏可能找不到发送的元素
    # b4a.click()
    # b4a.send_keys('自动测试用:)')
    # time.sleep(2)
    # driver.press_keycode(AndroidKey.ENTER)
    # time.sleep(2)
    # code1 = 'new UiSelector().resourceId("com.tencent.mm:id/b8k").className(' \
    #         '"android.widget.Button")'
    # driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, code1)[0].click()
    # driver.find_element(AppiumBy.ID, "com.tencent.mm:id/b8k").click()  # 点击发送
