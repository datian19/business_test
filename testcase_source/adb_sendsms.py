# coding:utf-8
import subprocess
import time


class Adb_Send_Sms:
    def __init__(self, serial_number):
        self.serial_number = serial_number
        self.statedata_callback = None

    # 发送短信息
    def send_sms(self, destination_number, sms_string):
        self.statedata_callback("编辑并发送")
        cmd = f'adb -s {self.serial_number} shell service call isms 7 i32 0 s16 ' \
              f'"com.android.mms.service" s16  ' \
              f'"{destination_number}" s16 "null" s16 "{sms_string}" s16 "null" s16 "null" '
        sp = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL)
        time.sleep(1)
        if sp.returncode == 0:
            self.statedata_callback("发送成功")
            self.statedata_callback(f'sent test SMS to {destination_number}  Message sent: {sms_string}')
            return 0
        else:
            self.statedata_callback("发送失败")
            return 1

    def set_state_data(self, statedataFunc):
        self.statedata_callback = statedataFunc
        return
