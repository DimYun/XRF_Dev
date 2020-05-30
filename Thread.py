# -*- coding: utf-8 -*-

from PyQt5 import QtCore
import Constants
import serial
import struct
import time
import os

from array import array

import usb.core
import usb.util


def spectra_decode(raw_bytes):
    # Make spec from raw_spec
    num = struct.unpack('3B', bytes(raw_bytes))
    return num[2]*256*256 + num[1]*256 + num[0]


def spectra_part_request(part_num):
    # Make bytes-string to take raw spec
    return struct.pack('3B', 253, part_num, 255)


class USBDetector:
    def __init__(self):
        self.dev = usb.core.find(idVendor=0x10C4, idProduct=0x842A)
        if self.dev is None:
            raise RuntimeError('Unable to find detector')
        cfg = self.dev.get_active_configuration()
        intf = cfg[(0, 0)]
        self.in_endpoint = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)
        self.out_endpoint = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)

    def clear_spectre(self):
        self.out_endpoint.write(array('B', [0xf5, 0xfa, 0xf0, 1, 0, 0, 0xfd, 0x20]))
        resp = self.in_endpoint.read(8)

    def start(self):
        self.out_endpoint.write(array('B', [0xf5, 0xfa, 0xf0, 2, 0, 0, 0xfd, 0x1f]))
        resp = self.in_endpoint.read(8)

    def stop(self):
        self.out_endpoint.write(array('B', [0xf5, 0xfa, 0xf0, 3, 0, 0, 0xfd, 0x1e]))
        resp = self.in_endpoint.read(8)

    def get_spectre(self):
        self.out_endpoint.write(array('B', [0xf5, 0xfa, 2, 1, 0, 0, 0xfe, 0x0e]))
        return self.in_endpoint.read(12296)

    def get_spec_and_stat(self):
        self.out_endpoint.write(array('B', [0xf5, 0xfa, 2, 3, 0, 0, 0xfe, 0x0c]))
        return self.in_endpoint.read(12360)

    def release(self):
        # self.dev.reset()
        # This is needed to release interface, otherwise attach_kernel_driver fails
        # due to "Resource busy"
        usb.util.dispose_resources(self.dev)


class COMStartThread (QtCore.QThread):
    # Class for write spec file and doing measure
    ser = None  # serial device
    live_time = 0
    dead_time = 0
    conf_bytes = None  # byte configuration for start measure
    error_signal = QtCore.pyqtSignal('QString')  # signal for error string
    device_signal = QtCore.pyqtSignal('QByteArray')  # signal for devise status string
    progress_signal = QtCore.pyqtSignal('QString')  # signal for progress bar
    measure_signal = QtCore.pyqtSignal('QString')  # signal for end measure
    num_signal = QtCore.pyqtSignal('QString')  # signal for calculate number of spectra which remain

    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)

    def run(self):
        if Constants.device_com == '':
            self.sent_my_signal(type_signal=0, message='Устройство не выбрано')
            return
        elif Constants.exposition_s == 0 or Constants.current_mk_a == 0 or Constants.voltage_kv == 0:
            self.sent_my_signal(type_signal=0, message='Некорректно установлены параметры трубки')
            return
        self.ser = serial.Serial(Constants.device_com, 115200)
        if Constants.running_const:
            # Ignore sample detection
            self.ser.flushInput()
            self.ser.write(struct.pack('B', 12))
            self.ser.read(9)
            # Read current state of device
            self.ser.flushInput()
            self.ser.write(struct.pack('B', 1))
            self.ser.read(9)  # device status
            # self.sent_my_signal(type_signal=1, message=out_str)
            # Start measure
            self.ser.flushInput()
            try:
                self.ser.write(self.start_measure(r'Device/conf.txt',
                                                  Constants.exposition_s * 10,
                                                  Constants.current_mk_a,
                                                  Constants.voltage_kv,
                                                  False))
                out_str = self.ser.read(9)
                self.sent_my_signal(type_signal=1, message=out_str)
            except IOError:
                print('IOError, now try to fix it')
                self.ser.write(self.startM(os.path.abspath(r'Device/conf.txt'),
                                           Constants.exposition_s * 10,
                                           Constants.current_mk_a,
                                           Constants.voltage_kv,
                                           False))
                out_str = self.ser.read(9)
                self.sent_my_signal(type_signal=1, message=out_str)
            # Turn on power of tube and detector
            self.ser.write(struct.pack('B', 10))
            out_str = self.ser.read(9)
            # self.sent_my_signal(type_signal=1, message=out_str)
            time.sleep(1)  # wait tube for 1 second
            # Clear spec in device memory
            self.ser.flushInput()

            if Constants.is_dp5:
                detector = USBDetector()
                detector.clear_spectre()
                detector.start()
                raw_spectra_all = []
                for i in range(0, Constants.exposition_s):
                    # monitor tube status (U, I)
                    self.ser.write(struct.pack('B', 1))
                    out_str = self.ser.read(9)  # device status
                    self.sent_my_signal(type_signal=1, message=out_str)
                    self.sent_my_signal(type_signal=3, message=str(int(100 / Constants.exposition_s * i)))
                    raw_spectra_all.append(detector.get_spectre()[6:12294])
                    time.sleep(1)
                detector.clear_spectre()
                detector.stop()
                detector.release()

            else:
                # For detector with COM-protocol
                self.ser.write(struct.pack('B', 14))
                out_str = self.ser.read(9)
                self.sent_my_signal(type_signal=1, message=out_str)
                for i in range(0, Constants.exposition_s):
                    self.sent_my_signal(type_signal=3, message=str(int(100 / Constants.exposition_s * i)))
                    self.ser.flushInput()
                    self.ser.write(struct.pack('3B', 253, 96, 255))
                    out_str = self.ser.read(65)  # this is detector data
                    self.sent_my_signal(type_signal=6, message=out_str)  # wrong
                    out_str = self.ser.read(9)
                    self.sent_my_signal(type_signal=1, message=out_str)
                    time.sleep(1)
                # Read spectra for COM detector
                raw_spectra = []
                for i in range(0, 48):
                    self.ser.flushInput()
                    self.ser.write(spectra_part_request(i))
                    if self.ser.read(1) == struct.pack('B', 175):
                        raw_spectra += self.ser.read(256)
            self.live_time /= Constants.exposition_s
            self.dead_time /= Constants.exposition_s
            # Stop measure and turn off height voltage
            self.ser.flushInput()
            # Get the status
            # self.ser.write(struct.pack('B', 1))
            # out_str = self.ser.read(9)
            # Stop the measure and high voltage
            self.ser.write(struct.pack('B', 3))
            out_str = self.ser.read(9)
            self.sent_my_signal(type_signal=1, message=out_str)
            time.sleep(1)

            # Write spectra in file
            y_list = []
            y_list_all = [0 for _ in range(0, 4098)]
            Constants.y_list_all = []
            if Constants.spec_all != 0:
                filename_spec = Constants.filename + '[' + str(Constants.index_file) + ']' + '.spe'
                Constants.index_file += 1
                Constants.spec_all -= 1
            else:
                Constants.index_file = 0
                filename_spec = Constants.filename + '[' + str(Constants.index_file) + '_last]' + '.spe'
            t = time.localtime()
            # Write headers in file
            with open(filename_spec, 'w') as out_file:
                out_file.write('!\n')
                out_file.write(str(t[2])+'.'+str(t[1])+'.'+str(t[0])+'\n')
                out_file.write(str(t[3])+':'+str(t[4])+':'+str(t[5])+'\n')
                out_file.write(str(Constants.exposition_s) + '\n')
                out_file.write(str(Constants.live_time) + '\n')
                out_file.write('wtf?\n')
                out_file.write(str(Constants.voltage_kv) + '\n')
                out_file.write(str(Constants.current_mk_a) + '\n')
                out_file.write('2\n')  # filter
                out_file.write('4096\n')  # channels
                out_file.write('1\n')  # No. of tray
                out_file.write('1\n')  # number of probe in quvette
                out_file.write('1\n')  # No. cuvette
                out_file.write('1\n')  # No. probe in cuvette
                out_file.write('1\n')  # Rotation
                out_file.write('Name of spec: ' + Constants.filename + '\n')  # Name of spec
                out_file.write('XRF, wtf?\n')  # Type of spec
                out_file.write('0\n')  # Atmosphere: air
                out_file.write('TRACE_X-SPEC\n')  # Type of devise
                out_file.write('-0.100263\n')  # futher the calibrations coefficient, are direct
                out_file.write('0.00893849\n')
                out_file.write('0\n')
                out_file.write(str(Constants.dead_time) + '\n')  # dead time in percent
                out_file.write('1\n')  # normalization coefficient
                out_file.write('11.219\n')  # calibrations coefficient, are inverse
                out_file.write('111.876\n')
                out_file.write('0\n')
                out_file.write('0\n')  # NKG, wtf?
                out_file.write('0\n')  # wtf?
                out_file.write(str(Constants.exposition_s) + '\n')  # real time of accumulation, wtf?
                out_file.write('!!!-------------Begin of spectrum--------------!!!\n')
                # Write spec in file
                j = 1
                if Constants.is_dp5:
                    j = len(raw_spectra_all)
                    while j > 0:
                        raw_spectra = raw_spectra_all[j - 1]
                        for i in range(0, int(len(raw_spectra) / 3)):
                            y = spectra_decode(raw_spectra[i * 3:i * 3 + 3])
                            y_list.append(y)
                        # Merge all data in one list
                        y_list_all = [(x + y) for (x, y) in zip(y_list_all, y_list)]
                        j -= 1
                else:
                    for i in range(0, int(len(raw_spectra)/3)):
                        y = spectra_decode(raw_spectra[i * 3:i * 3 + 3])
                        y_list.append(y)
                    # Merge all data in one list
                    y_list_all = [(x + y) for (x, y) in zip(y_list_all, y_list)]
                    j -= 1
                for y in y_list_all:
                    out_file.write(str(y) + '\n')
            out_file.close()
            Constants.y_list_all = y_list_all[:]
            self.sent_my_signal(type_signal=3, message=str(100))
            self.sent_my_signal(type_signal=4, message='')
            # Do if we have numbers of measurement
            if Constants.num_meas_sample > 1:
                Constants.num_meas_sample -= 1
                for i in range(Constants.int_meas_sample):
                    time.sleep(1)
                    self.sent_my_signal(type_signal=5, message=str(i+1))
            elif Constants.num_all_sample > 1:
                Constants.num_all_sample -= 1
                Constants.num_meas_sample = Constants.num_meas_sample_const
                for i in range(Constants.int_meas_all):
                    time.sleep(1)
                    self.sent_my_signal(type_signal=5, message=str(i + 1))
        # Bad idea - rewrite normal
        try:
            self.ser.close()
        except serial.SerialException:
            print('Except!!!')
            pass

    def start_measure(self, config_file, exposition, current, voltage, use_trigger):
        # Compile bytes-string for start measure
        with open(config_file) as config:
            lines = filter(lambda x: x[0] != '=', config.readlines())
            lines = [x for x in lines]
            self.conf_bytes = [_ for _ in map(lambda x: int(x, 16), lines)]
        ret = struct.pack('B', 253)
        for i in range(0, 11):
            ret += struct.pack('B', self.conf_bytes[i])
        int_exp = int(exposition)
        ret += struct.pack('3B', int_exp % 256, int((int_exp % (256**2)) / 256), int(int_exp/(256**2)))
        for i in range(14, 64):
            ret += struct.pack('B', self.conf_bytes[i])
        ret += struct.pack('B', 254)
        x_i = int(current / 200.0 * 4.0 / (2.0 * 4.096) * 16384.0)
        ret += struct.pack('2B', int(x_i / 256), int(x_i % 256))
        x_u = int(voltage / 50.0 * 4.0 / (2.0 * 4.096) * 16384.0)
        ret += struct.pack('2B', int(x_u / 256), int(x_u % 256))
        ret += struct.pack('B', int(use_trigger))
        return ret

    def sent_my_signal(self, type_signal, message):
        '''
        Sent signal out of thread
        :param type_signal: int, 0 - error_message, 1 - dev_status, 2 - det_status
        :param message: str, signal value
        :return: None
        '''
        my_signal = self.error_signal
        sig = message
        if type_signal == 0:
            # sig = str(message, 'latin1')
            my_signal.emit(sig)
        elif type_signal == 1:
            my_signal = self.device_signal
            sig = message
            # sig = str(message, 'latin1')
            my_signal.emit(sig)
        elif type_signal == 3:
            my_signal = self.progress_signal
            # sig = str(message, 'latin1')
            my_signal.emit(sig)
        elif type_signal == 4:
            my_signal = self.measure_signal
            # sig = str(message, 'latin1')
            my_signal.emit('0')
        elif type_signal == 5:
            my_signal = self.num_signal
            # sig = str(message, 'latin1')
            my_signal.emit(sig)



