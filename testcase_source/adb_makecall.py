# coding:utf-8
import subprocess


class Adb_Make_Call:
    def __init__(self, serial_number):
        self.statedata_callback = None
        self.serial_number = serial_number

    # 拨打电话
    def make_call(self, destination_number):
        self.statedata_callback("开始拨打电话")
        call_cmd = f'adb -s {self.serial_number}  shell am start -a android.intent.action.CALL tel:{destination_number} '
        sp = subprocess.run(call_cmd, stdout=subprocess.DEVNULL)
        if sp.returncode == 0:
            self.statedata_callback(f'电话拨打成功 {destination_number}...')
            return 0
        else:
            self.statedata_callback(f'电话拨打失败 {destination_number}...')
            return 1

    # 挂断电话
    def end_call(self):
        self.statedata_callback("挂断电话")
        end_call_cmd = f'adb -s {self.serial_number} shell input keyevent KEYCODE_ENDCALL'
        sp = subprocess.run(end_call_cmd, stdout=subprocess.DEVNULL)
        if sp.returncode == 0:
            self.statedata_callback("通话结束")
            return 0
        else:
            self.statedata_callback("电话挂断失败")
            return 1

    def set_state_data(self, statedataFunc):
        self.statedata_callback = statedataFunc
        return