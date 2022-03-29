# coding:utf-8
from collections import defaultdict
import serial
import serial.tools.list_ports
import subprocess

from utils.ue import Ue_Adb_Util


class spawnUe:

    def __init__(self):
        self.dut = None

    def spawn_ue(self):
        comport_dict = defaultdict(list)
        ue_dict = {}
        # 例如：'9e504da5'
        try:
            sn_list = [device.split('\t')[0] for device in subprocess.check_output(
                'adb devices').decode().splitlines() if device.endswith('\tdevice')]
        except:
            sn_list = []
        # Collect COM ports of connect UEs based on sn_list
        for pinFo in serial.tools.list_ports.comports():
            if pinFo.serial_number.upper() in [sn.upper() for sn in sn_list]:
                comport_dict[pinFo.serial_number.upper()].append(pinFo.description)

        # Create UE instances based on sn_list and store in ue_dict
        for i, ue_sn in enumerate(sn_list):
            ue_dict[ue_sn] = Ue_Adb_Util(i, ue_sn, comport_dict[ue_sn.upper()])
        # print(f'UE spawned: {len(ue_dict)}\n')
        self.dut = ue_dict
