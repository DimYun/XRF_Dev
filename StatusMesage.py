# -*- coding: utf-8 -*-

import Constants
import struct


def dev_status_message(parent, status_list):
    # Read device status and write it to log-file and devStatus field
    # try:
    #     status_list = status_list.toLatin1()
    # except AttributeError:
    #     print('AttributeError in devStatusMessage')
    #     pass
    if len(status_list) != 9:
        raise Exception('Wrong device status list length')
        return
    byte = struct.unpack('9B', status_list)
    if byte[0] != 21:
        raise Exception('Wrong status header: ' + status_list[0])
        return
    # read second byte
    bit_in_byte2 = '{0:b}'.format(byte[1])
    robot_control = (bit_in_byte2[0] == '1')
    target_present = (bit_in_byte2[1] == '1')
    high_voltage_on = (bit_in_byte2[2] == '1')
    wait_status = int(bit_in_byte2[3:], 2)
    ws = ''
    if wait_status == 0:
        ws = 'ожидает'
    elif wait_status == 1:
        ws = 'нажмите курок для статра'
    elif wait_status == 4:
        ws = 'включите напряжение на трубке'
    elif wait_status == '6':
        ws = 'измерение'
    else:
        ws = 'не определенный статус: '+str(wait_status)
    # read third byte
    bit_in_byte3 = '{0:b}'.format(byte[2])
    tube_power_present = (bit_in_byte3[2] == '1')
    detector_power_present = (bit_in_byte3[3] == '1')
    bluetooth_used = int(bit_in_byte3[4:6], 2)
    sr = ''
    last_stop_reason = int(bit_in_byte3[-2:], 2)
    if last_stop_reason == 0:
        sr = 'нормальное завершение'
    elif last_stop_reason == 2:
        sr = 'выпадание образца'
    elif last_stop_reason == 3:
        sr = 'U или I превысили максимум!'
    else:
        sr = 'не определенный статус: ' + str(last_stop_reason)
    curr_real_tube = byte[3] * 256 + byte[4]
    current_tube = float(curr_real_tube) / 1024.0 * 5.0 * (200.0 / 4.0) / (10.0 / 11.0)
    volt_real_tube = byte[5] * 256.0 + byte[6]
    voltage_tube = float(volt_real_tube) / 1024.0 * 5.0 * (50.0 / 4.0) / (10.0 / 11.0)
    byte_real = byte[7] * 256.0 + byte[8]
    byte_voltage = float(byte_real) / 1024.0 * 5.0 * 88.0 / 20.0
    status_string = '<b> Статус прибора: \n </b>' +\
        '\t' + 'Высокое напрядение: ' + str(high_voltage_on) + "\n" +\
        '\t' + 'Наличие образца: ' + str(target_present) + "\n" +\
        '\t' + 'Робот: ' + str(robot_control) + "\n" +\
        '\t' + 'Статус ожидания: ' + ws + "\n" +\
        '\t' + 'Напряжение на трубке: ' + str(tube_power_present) + "\n" +\
        '\t' + 'Напряжение на детекторе: ' + str(detector_power_present) + "\n" +\
        '\t' + 'Использование bluetooth: ' + str(bluetooth_used) + "\n" +\
        '\t' + 'Причина остановки: ' + sr + "\n" +\
        '\t' + '\tток: ' + str(round(current_tube, 3)) + "\n" +\
        '\t' + '\tнапряжение: ' + str(round(voltage_tube, 3)) + "\n" +\
        '\t' + 'напряжение батареи: ' + str(round(byte_voltage, 3))
    # Try this
    status_string_user = 'ток: ' + str(round(current_tube, 3)) + '\n'+\
        'напряжение: ' + str(round(voltage_tube, 3)) + "\n"
    parent.dev_status_te.append(status_string_user)
    # helpFunc.logWrite(Constants.filenameLOG, 'Статус детектора: ', True)
    # helpFunc.logWrite(Constants.filenameLOG, status_string, False)


def det_status_message(parent, inp_bytes):
    # Read detector status and put it to log-file and devStatus field
    try:
        inp_bytes = inp_bytes.toLatin1()
    except AttributeError:
        pass
    
    byte = struct.unpack('65B', inp_bytes)
    Constants.live_time = 0
    Constants.dead_time = 0
    
    in_impulses_fast = byte[4] * float(0x01000000) + byte[3] * float(0x010000) +\
        byte[2] * float(0x0100) + byte[1] * float(0x01)
    out_impulses_slow = byte[8] * float(0x01000000) + byte[7] * float(0x010000) +\
        byte[6] * float(0x0100) + byte[5] * float(0x01)
    time_calc = (100.0 * (float(0x010000) * byte[13] + float(0x0100) * byte[12] +
                          float(0x01)*(byte[11]) + byte[10])) / 1000.0
    Constants.live_time = (100.0 * (float(0x010000) * byte[48] + float(0x0100) * byte[47] +
                                    float(0x01) * (byte[46]) + byte[45])) / 1000.0
    Constants.tempr = (float(0x100) * (byte[21] & 0x0f) + byte[21]) * 0.1
    status_string = '<b>Статус детектора: \n </b>' +\
        '\t' + 'вход (быстрые имп.): ' + str(in_impulses_fast) + "\n" +\
        '\t' + 'выход (медл. имп.): ' + str(out_impulses_slow) + "\n" +\
        '\t' + 'время, с: ' + str(time_calc) + "\n" +\
        '\t' + 'температура, K: ' + str(Constants.tempr) + '\n' +\
        '\t' + 'живое время, с: ' + str(round(Constants.live_time, 3)) + '\n'
    status_string_user = u'время, с: ' + str(time_calc) + '\n'+\
        u'температура, K: ' + str(Constants.tempr) + '\n' +\
        u'живое время, с: ' + str(round(Constants.live_time, 3))
    parent.dev_status_te.append(status_string_user)
    # helpFunc.logWrite(Constants.filenameLOG, 'Статус детектора: ', True)
    # helpFunc.logWrite(Constants.filenameLOG, status_string, False)
    
    if in_impulses_fast != 0:
        Constants.dead_time = 100.0 * (1 - out_impulses_slow / in_impulses_fast)
        parent.dev_status_te.append(u'мертвое время, с:' +
                                    str(round(Constants.dead_time, 3)) + '\n')
        # helpFunc.logWrite(Constants.filenameLOG, '\tмертвое время, с:' +
        #                   str(round(Constants.deadTime, 3)), False)
    else: 
        parent.dev_status_te.append(u'мертвое время, с: 0' + '\n')
        # helpFunc.logWrite(Constants.filenameLOG, '\tмертвое время, с: 0', False)
