# coding:utf-8
import subprocess
import platform


class Ue_Adb_Util:
    def __init__(self, id, serial_number, devices_com):
        self.version = None
        self.manufacturer = None
        self.port_Free = None
        self.build = None
        self.model = None
        self.cur_system = platform.system()
        self.find = ''
        self.id = id
        self.get_find()
        self.serial_number = serial_number
        self.get_manufacturer()
        self.get_build()
        self.get_version()
        self.get_model()
        self.devices_com = devices_com

    # 判断系统类型，windows使用findstr，linux使用grep
    def get_find(self):
        if self.cur_system == "Windows":
            self.find = "findstr"
        else:
            self.find = "grep"

    # 获取设备id
    def get_sn(self):
        cmd = f'adb -s {self.serial_number} shell getprop ro.serialno'
        sp = subprocess.run(cmd, capture_output=True)
        if sp.returncode == 0:
            sn = sp.stdout.decode().strip()
            self.serial_number = sn
            return sn
        elif sp.returncode == 1:
            print('Failed to retrieve sn')

    # 获取安卓系统版本
    def get_version(self):
        cmd = f'adb -s {self.serial_number} shell getprop ro.build.version.release'
        sp = subprocess.run(cmd, capture_output=True)
        if sp.returncode == 0:
            version = sp.stdout.decode().strip()
            self.version = version
            return version
        elif sp.returncode == 1:
            print('Failed to retrieve version')

    # 获取品牌
    def get_manufacturer(self):
        cmd = f'adb -s {self.serial_number} shell getprop ro.product.manufacturer'
        sp = subprocess.run(cmd, capture_output=True)
        if sp.returncode == 0:
            self.manufacturer = sp.stdout.decode().strip()
        elif sp.returncode == 1:
            raise ValueError('get_manufacturer() error')

    # 获取设备型号
    def get_model(self):
        cmd = f'adb -s {self.serial_number} shell getprop ro.product.model'
        sp = subprocess.run(cmd, capture_output=True)
        if sp.returncode == 0:
            model = sp.stdout.decode().strip()
            self.model = model
            return model
        elif sp.returncode == 1:
            print('Failed to retrieve sn')

    # 获取屏幕id
    def get_build(self):
        cmd = f'adb -s {self.serial_number} shell getprop ro.build.display.id'
        sp = subprocess.run(cmd, capture_output=True)
        if sp.returncode == 0:
            self.build = sp.stdout.decode().strip()
            return self.build
        elif sp.returncode == 1:
            raise ValueError('get_build() error')

    # 判断屏幕是否关闭(OFF:关闭; ON:点亮)
    def check_screenstate(self):
        check_cmd = f'adb -s {self.serial_number} shell dumpsys display | grep mScreenState='
        screen_state = subprocess.run(check_cmd, capture_output=True).stdout.decode().strip()
        eql_idx = screen_state.find('=')
        state = screen_state[eql_idx + 1:]
        return state

    # 点亮屏幕
    def set_screen_on(self):
        screen_on_cmd = f'adb -s {self.serial_number} shell input keyevent 224'
        subprocess.run(screen_on_cmd, stdout=subprocess.DEVNULL)

    # 滑动解锁
    def set_screen_swipe(self):
        screen_on_cmd = f'adb -s {self.serial_number} shell input swipe 300 1000 300 500'
        subprocess.run(screen_on_cmd, stdout=subprocess.DEVNULL)

    # 判断是否实在通话中（注意双卡）
    def check_callstate(self):
        check_cmd = f'adb -s {self.serial_number} shell dumpsys telephony.registry | grep mCallState'
        call_state = subprocess.run(
            check_cmd, capture_output=True).stdout.decode().strip()
        eql_idx = call_state.find('=')
        call_state = int(call_state[eql_idx + 1])
        return call_state

    # 检查sim卡
    def check_hasSim(self):
        check_cmd = f'adb -s {self.serial_number} shell service call phone 65'
        out = subprocess.run(
            check_cmd, capture_output=True).stdout.decode().strip()
        if '1' in out:
            has_Sim = True
        elif '1' not in out:
            has_Sim = False
        return has_Sim

    # 重启手机
    def reboot(self):
        reboot_cmd = f'adb -s {self.serial_number} reboot'
        subprocess.run(reboot_cmd, stdout=subprocess.DEVNULL)

    # 获取手机ip
    def get_ue_ip(self, ue):
        if ue:
            if ue.startswith('RFCN') or ue.startswith('RF3N') or ue.startswith('R3CN') or ue.startswith(
                    'LMV60') or ue.startswith('RFCR'):
                cmd = f'adb -s {ue} shell ifconfig -S rmnet_data0'
            elif ue.startswith('9RJ'):
                cmd = f'adb -s {ue} shell ifconfig -S rmnet0'
            elif ue.startswith('9e50'):
                cmd = f'adb -s {ue} shell ifconfig -S wlan0'
            else:
                # return self.get_destination()
                return ""
            output = subprocess.check_output(cmd)
            print(output.decode())
            start = output.decode().find('1')
            end = output.decode().find('/')
            print(output.decode()[start:end])
            return output.decode()[start:end]
        else:
            return ''
