# coding:utf-8
import os
import traceback
import urllib
import speedtest  # 导入speedtest_cli


# 电脑端speedtest 执行处理
class Speedtest_PC:
    def __init__(self):
        self.statedata_callback = None

    def start_test(self):
        servers = []
        try:
            self.statedata_callback("SpeedTest测试开始......")
            # 创建实例对象
            speed_test = speedtest.Speedtest()
            self.statedata_callback("获取可用于测试的服务器列表......")
            # 获取可用于测试的服务器列表
            speed_test.get_servers(servers)
            self.statedata_callback("筛选出最佳服务器......")
            # 筛选出最佳服务器
            speed_test.get_best_server()
            self.statedata_callback("下载速度分析......")
            # 下载速度
            download_speed = int(speed_test.download() / 1024 / 1024)
            # 上传速度
            self.statedata_callback("上传速度分析......")
            upload_speed = int(speed_test.upload() / 1024 / 1024)
            # 获取结果字典
            result_dict = speed_test.results.dict()

            ret_dict = {"download": str(download_speed) + " Mbps",
                        "upload": str(upload_speed) + " Mbps",
                        "ping": str(result_dict["ping"]) + " ms",
                        "timestamp": result_dict["timestamp"],
                        "server-url": result_dict["server"]["url"],
                        "server-name": result_dict["server"]["name"],
                        "server-country": result_dict["server"]["country"],
                        "server-sponsor": result_dict["server"]["sponsor"],
                        "client-isp": result_dict["client"]["isp"]}
        except speedtest.ConfigRetrievalError:
            # print(traceback.format_exc())
            self.statedata_callback("请确认网络是否有效")
            return {"retcode": 1, "data": "speedtest失败"}
        except:
            # print(traceback.format_exc())
            self.statedata_callback("速率（speedtest）测试失败")
            return {"retcode": 1, "data": "speedtest失败"}

        try:
            self.statedata_callback("测试结果图片加载......")
            pngUrl = speed_test.results.share()
            path = os.path.realpath(os.curdir)
            pngPath = os.path.join(path, "image", "speedtest_img.png")
            if os.path.exists(pngPath):
                os.remove(pngPath)
            response = urllib.request.urlopen(pngUrl)
            if response.getcode() == 200:
                with open(pngPath, "wb") as f:
                    f.write(response.read())  # 将内容写入图片
            self.statedata_callback("速率（speedtest）测试完成")
        except:
            # print(traceback.format_exc())
            self.statedata_callback("测试结果图片加载失败")
            return {"retcode": 2, "data": ret_dict}
        return {"retcode": 0, "data": result_dict}

    def set_state_data(self, statedataFunc):
        self.statedata_callback = statedataFunc
        return
