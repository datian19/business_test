# coding:utf-8


# Testcase
class Testcase_Item:
    def __init__(self):
        self.testcase_dict = {}
        self.testcase_dict.update({'CASE0001': "短信息"})
        self.testcase_dict.update({'CASE0002': "语音通话"})
        self.testcase_dict.update({'CASE0003': "微信视频通话"})
        self.testcase_dict.update({'CASE0004': "短视频播放"})
        self.testcase_dict.update({'CASE0005': "视频播放"})
        self.testcase_dict.update({'CASE0006': "速率监控"})

        self.mini_video_app_dict = {}
        self.mini_video_app_dict.update({'MINIVIDEO0001': "快手"})
        self.mini_video_app_dict.update({'MINIVIDEO0002': "抖音"})

        self.video_app_dict = {}
        self.video_app_dict.update({'VIDEO0001': "bilibili"})
        self.video_app_dict.update({'VIDEO0002': "爱奇艺"})

    # <editor-fold desc="业务信息处理">
    # 测试用例list获取
    def get_testcase_itemlist(self):
        return list(self.testcase_dict.values())

    # 根据key获取item
    def get_item_byKey(self, key):
        return self.testcase_dict[key]

    # 根据item获取key
    def get_item_byItem(self, item):
        for key, value in self.testcase_dict.items():
            if value == item:
                return key

    # </editor-fold>

    # <editor-fold desc="短视频业务">
    # 测试用例list获取
    def get_mini_video_itemlist(self):
        return list(self.mini_video_app_dict.values())

    # 根据key获取item
    def get_mini_video_item_byKey(self, key):
        return self.mini_video_app_dict[key]

    # 根据item获取key
    def get_mini_video_item_byItem(self, item):
        for key, value in self.mini_video_app_dict.items():
            if value == item:
                return key
    # </editor-fold>

    # <editor-fold desc="视频业务">
    # 测试用例list获取
    def get_video_itemlist(self):
        return list(self.video_app_dict.values())

    # 根据key获取item
    def get_video_item_byKey(self, key):
        return self.video_app_dict[key]

    # 根据item获取key
    def get_video_item_byItem(self, item):
        for key, value in self.video_app_dict.items():
            if value == item:
                return key
    # </editor-fold>
