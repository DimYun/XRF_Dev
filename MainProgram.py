# -*- coding: utf-8 -*-
# require packages: PyQt5, pyqtgraph, pyserial, pyusb


from PyQt5 import QtCore, QtWidgets, QtGui
import pyqtgraph as pg
# from pyqtgraph import QtCore, QtGui

import sys
import os
import time
import serial
from serial.tools import list_ports
import struct
import Constants
import Constants_help
import Thread
import StatusMesage
import importlib

Constants_help.ind_color = 0


class CustomPlot(pg.GraphicsObject):
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)
        self.data = data
        print(self.data)
        self.generatePicture()

    def generatePicture(self):
        self.picture = pg.QtGui.QPicture()
        pg.plot(self.data)
        # p = pg.QtGui.QPainter(self.picture)
        # p.setPen(pg.mkPen('w', width=1 / 2.))
        # p. plot(self.data)
        # # for (t, v) in self.data:
        # #     p.drawLine(pg.QtCore.QPointF(t, v - 2), pg.QtCore.QPointF(t, v + 2))
        # p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.picture.boundingRect())


# class ManipulationEventFilterBuilder(QtWidgets.QObject):
#     # Print element tips for mouse cursor on plot canvas
#     def __init__(self, parent):
#         QtWidgets.QObject.__init__(self, parent)
#         self.parent = parent
#
#     def eventFilter(self, source, event):
#         # New event filter for objects
#         if (event.type() == QtCore.QEvent.MouseMove and
#                     source is self.parent.plotCanvas):
#             pos = event.pos()
#             x = round(float(self.parent.qwtPlot.invTransform(self.parent.qwtPlot.xBottom, pos.x())), 3)
#             y = round(float(self.parent.qwtPlot.invTransform(self.parent.qwtPlot.yLeft, pos.y())), 3)
#             z = ''
#             for atom in Constants_help.elementsInfo:
#                 for line in atom['char']:
#                     try:
#                         lineEnergy = 12.398/line['l']
#                     except KeyError as var:
#                         print(str(var) + '\n')
#                         print(str(atom['name']) + '\n')
#                         break
#
#                     if abs(lineEnergy-x) < 0.01 and \
#                         (line['type'] == 'Ka1/2' or line['type'] == "Ka1" or line['type'] == "La1/2") :
#                         z = atom['name'] + ': ' + line['type']
#             self.parent.qwtPlot.setToolTip('x = %.6g, y = %.6g' %(x, y) + '\n' + z)
#         return QtGui.QWidget.eventFilter(self, source, event)


class GuiXRF(QtWidgets.QWidget):
    # Draw main window with controls

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        # put on center of desktop
        desktop = QtWidgets.QApplication.desktop()
        x = desktop.width() / 2
        y = desktop.height() / 2
        self.move(0, 0)
        self.setWindowTitle('XRF measure')
        # draw main window
        self.main_layout = QtWidgets.QHBoxLayout(self)
        # draw control elements
        self.left_layout = QtWidgets.QVBoxLayout()
        # draw COM port select
        self.com_gb = QtWidgets.QGroupBox()
        self.com_gb.setTitle(u"Выбор прибора (порт)")
        size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.com_gb.sizePolicy().hasHeightForWidth())
        self.com_gb.setSizePolicy(size_policy)
        self.com_gb.setMaximumSize(QtCore.QSize(209, 16777215))
        self.com_layout = QtWidgets.QGridLayout(self.com_gb)
        self.com_cb = QtWidgets.QComboBox(self.com_gb)
        self.com_layout.addWidget(self.com_cb, 0, 0, 1, 2)
        self.refresh_com_pb = QtWidgets.QPushButton(self.com_gb)
        self.refresh_com_pb.setText(u"Обновить")
        self.com_layout.addWidget(self.refresh_com_pb, 1, 0, 1, 1)
        self.use_com_pb = QtWidgets.QPushButton(self.com_gb)
        self.use_com_pb.setText(u"Выбрать")
        self.com_layout.addWidget(self.use_com_pb, 1, 1, 1, 1)
        self.left_layout.addWidget(self.com_gb)
        # draw XRF parameters
        self.parameters_gb = QtWidgets.QGroupBox()
        self.parameters_gb.setTitle(u"Параметры")
        # size_policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        # size_policy.setHorizontalStretch(0)
        # size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.parameters_gb.sizePolicy().hasHeightForWidth())
        self.parameters_gb.setSizePolicy(size_policy)
        self.parameters_gb.setMinimumSize(QtCore.QSize(0, 0))
        self.parameters_gb.setMaximumSize(QtCore.QSize(209, 16777215))
        self.parameters_layout = QtWidgets.QGridLayout(self.parameters_gb)
        self.energy_l = QtWidgets.QLabel(self.parameters_gb)
        self.energy_l.setText(u"U, кВ")
        self.parameters_layout.addWidget(self.energy_l, 0, 0, 1, 1)
        self.energy_le = QtWidgets.QLineEdit(self.parameters_gb)
        self.energy_le.setValidator(QtGui.QIntValidator(0, 50, self))
        self.parameters_layout.addWidget(self.energy_le, 0, 1, 1, 1)
        self.energy_unit_l = QtWidgets.QLabel(self.parameters_gb)
        self.energy_unit_l.setText(u"< 50")
        self.parameters_layout.addWidget(self.energy_unit_l, 0, 2, 1, 1)
        self.current_l = QtWidgets.QLabel(self.parameters_gb)
        self.current_l.setText(u"i, мкА")
        self.parameters_layout.addWidget(self.current_l, 1, 0, 1, 1)
        self.current_le = QtWidgets.QLineEdit(self.parameters_gb)
        self.current_le.setValidator(QtGui.QIntValidator(0, 200, self))
        self.parameters_layout.addWidget(self.current_le, 1, 1, 1, 1)
        self.current_unit_l = QtWidgets.QLabel(self.parameters_gb)
        self.current_unit_l.setText(u"< 200")
        self.parameters_layout.addWidget(self.current_unit_l, 1, 2, 1, 1)
        self.exposition_l = QtWidgets.QLabel(self.parameters_gb)
        self.exposition_l.setText(u"t, с")
        self.parameters_layout.addWidget(self.exposition_l, 2, 0, 1, 1)
        self.exposition_le = QtWidgets.QLineEdit(self.parameters_gb)
        self.exposition_le.setValidator(QtGui.QIntValidator(0, 2000, self))
        self.parameters_layout.addWidget(self.exposition_le, 2, 1, 1, 1)
        self.left_layout.addWidget(self.parameters_gb)
        # draw measure number window
        self.measure_num_gb = QtWidgets.QGroupBox()
        self.measure_num_gb.setTitle(u"Количество измерений")
        self.measure_num_gb.setMaximumSize(QtCore.QSize(209, 16777215))
        self.measure_num_layout = QtWidgets.QGridLayout(self.measure_num_gb)
        self.measure_one_l = QtWidgets.QLabel(self.measure_num_gb)
        self.measure_one_l.setText(u"одного образца")
        self.measure_one_l.setWordWrap(True)
        self.measure_num_layout.addWidget(self.measure_one_l, 0, 0, 1, 1)
        self.measure_all = QtWidgets.QLabel(self.measure_num_gb)
        self.measure_all.setText(u"всего образцов")
        self.measure_all.setWordWrap(True)
        self.measure_num_layout.addWidget(self.measure_all, 0, 1, 1, 1)
        self.measure_one_cb = QtWidgets.QComboBox(self.measure_num_gb)
        self.measure_num_layout.addWidget(self.measure_one_cb, 1, 0, 1, 1)
        self.measure_all_cb = QtWidgets.QComboBox(self.measure_num_gb)
        self.measure_num_layout.addWidget(self.measure_all_cb, 1, 1, 1, 1)
        self.left_layout.addWidget(self.measure_num_gb)
        # draw time window
        self.time_gb = QtWidgets.QGroupBox()
        self.time_gb.setTitle(u"Время между измерениями")
        self.time_gb.setMaximumSize(QtCore.QSize(209, 16777215))
        self.time_layout = QtWidgets.QGridLayout(self.time_gb)
        self.time_one_l = QtWidgets.QLabel(self.time_gb)
        self.time_one_l.setText(u"одного образца, с")
        self.time_one_l.setWordWrap(True)
        self.time_layout.addWidget(self.time_one_l, 0, 0, 1, 1)
        self.time_between_l = QtWidgets.QLabel(self.time_gb)
        self.time_between_l.setText(u"между образцами, с")
        self.time_between_l.setWordWrap(True)
        self.time_layout.addWidget(self.time_between_l, 0, 1, 1, 1)
        self.time_one_le = QtWidgets.QLineEdit(self.time_gb)
        self.time_one_le.setText('0')
        self.time_layout.addWidget(self.time_one_le, 1, 0, 1, 1)
        self.time_all_le = QtWidgets.QLineEdit(self.time_gb)
        self.time_all_le.setText('0')
        self.time_layout.addWidget(self.time_all_le, 1, 1, 1, 1)
        self.left_layout.addWidget(self.time_gb)
        # draw save file option
        self.save_file_pb = QtWidgets.QPushButton()
        self.save_file_pb.setText(u"Сохранить спектр(ы) как")
        self.save_file_pb.setMaximumSize(QtCore.QSize(209, 16777215))
        self.left_layout.addWidget(self.save_file_pb)
        # draw device status
        self.dev_status_gb = QtWidgets.QGroupBox()
        # size_policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        # size_policy.setHorizontalStretch(0)
        # size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.dev_status_gb.sizePolicy().hasHeightForWidth())
        self.dev_status_gb.setSizePolicy(size_policy)
        self.dev_status_gb.setTitle(u"Окно статуса")
        self.dev_status_gb.setMaximumSize(QtCore.QSize(209, 16777215))
        self.dev_status_layout = QtWidgets.QVBoxLayout(self.dev_status_gb)
        self.dev_status_te = QtWidgets.QTextEdit(self.dev_status_gb)
        self.dev_status_te.setEnabled(True)
        self.dev_status_te.setReadOnly(True)
        self.dev_status_layout.addWidget(self.dev_status_te)
        self.left_layout.addWidget(self.dev_status_gb)
        self.main_layout.addLayout(self.left_layout)

        # right layout for plot canvas
        self.right_layout = QtWidgets.QVBoxLayout()
        self.guiplot = pg.PlotWidget()
        self.right_layout.addWidget(self.guiplot)
        # pgcustom = CustomPlot(data)
        # self.guiplot.addItem(pgcustom)

        # self.right_layout.setMinimumSize(QtCore.QSize(700, 0))
        # self.plotCanvas = self.qwtPlot.canvas()
        # self.plotCanvas.setMouseTracking(True)
        # self.plotCanvas.installEventFilter(ManipulationEventFilterBuilder(self))
        # self.right_layout.addWidget(self.qwtPlot)

        # draw progress bar and main buttons
        self.control_elem_layout = QtWidgets.QHBoxLayout()
        self.time_prb = QtWidgets.QProgressBar()
        self.time_prb.setProperty("value", 0)
        self.control_elem_layout.addWidget(self.time_prb)
        self.stop_pb = QtWidgets.QPushButton()
        self.stop_pb.setText(u"Остановка съемки")
        self.control_elem_layout.addWidget(self.stop_pb)
        self.go_pb = QtWidgets.QPushButton()
        self.go_pb.setText(u"Старт")
        self.control_elem_layout.addWidget(self.go_pb)
        self.right_layout.addLayout(self.control_elem_layout)
        self.main_layout.addLayout(self.right_layout)
        # initialize thread for XRF device
        self.thread = Thread.COMStartThread()

        # Need use new style self.lineedit.returnPressed.connect(self.updateUi)
        self.refresh_com_pb.clicked.connect(self.refresh)
        self.use_com_pb.clicked.connect(self.use_com)
        self.save_file_pb.clicked.connect(self.save_file)
        self.stop_pb.clicked.connect(self.stop_now)
        self.go_pb.clicked.connect(self.start_go)

        # catch signal from outside
        self.thread.error_signal.connect(self.thread_error)
        self.thread.device_signal.connect(lambda x, y = self: StatusMesage.dev_status_message(y, x))
        self.thread.progress_signal.connect(self.progress_change)
        self.thread.measure_signal.connect(self.print_measure)
        self.thread.num_signal.connect(self.num_change)

        # QtCore.QObject.connect(self.thread, QtCore.SIGNAL('DetStatusMessage(QString)'),
        #                        lambda x, y = self: StatusMesage.det_status_message(y, x), QtCore.Qt.QueuedConnection)
        self.thread.started.connect(self.on_started)
        self.thread.finished.connect(self.on_finished)
        self.index_make()

    def index_make(self):
        # Make index for measure number comboBox
        cb_list = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        self.measure_one_cb.addItems(cb_list)
        self.measure_all_cb.addItems(cb_list)

    # def eventFilter(self, source, event):
    #     # New event filter for objects
    #     if (event.type() == QtCore.QEvent.MouseMove and
    #                 source is self.qwtPlot):
    #         pos = event.pos()
    #         x = round(float(self.qwtPlot.invTransform(Qwt5.QwtPlot.xBottom, pos.x())), 3)
    #         y = round(float(self.qwtPlot.invTransform(Qwt5.QwtPlot.yLeft, pos.y())), 3)
    #         z = ''
    #         for atom in Constants_help.elementsInfo:
    #             for line in atom['char']:
    #                 try:
    #                     lineEnergy = 12.398/line['l']
    #                 except KeyError as var:
    #                     print(str(var) + '\n')
    #                     print(str(atom['name']) + '\n')
    #                     break
    #
    #                 if abs(lineEnergy-x) < 0.01 and \
    #                     (line['type'] == 'Ka1/2' or line['type'] == "Ka1" or line['type'] == "La1/2") :
    #                     z = atom['name'] + ': ' + line['type']
    #         self.qwtPlot.setToolTip('x = %.6g, y = %.6g' %(x, y) + '\n'+z)
    #     return QtGui.QWidget.eventFilter(self, source, event)

    def available_com (self):
        # Scan system for available COM (virtual COM) ports
        if os.name == 'nt':
            # Windows
            Constants.availableCOM = []
            for i in range(256):
                try:
                    com_name = 'COM' + str(i)
                    ser = serial.Serial(com_name)
                    Constants.availableCOM.append(com_name)
                    self.com_cb.addItem(com_name)
                    ser.close()
                except serial.SerialException:
                    pass
            return Constants.availableCOM
        else:
            # Mac / Linux
            Constants.availableCOM = []
            for i in [port[0] for port in list_ports.comports()]:
                Constants.availableCOM.append(i)
                self.com_cb.addItem(i)
            return Constants.availableCOM

    def refresh(self):
        # Put found ports in GUI
        self.com_cb.clear()
        self.available_com()
        self.com_cb.setCurrentIndex(self.com_cb.count() - 1)

    def use_com(self):
        # Emit signal to COM-port and print answer
        try:
            Constants.device_com = ''
            ind = self.com_cb.currentIndex()
            if ind != -1:  # when choose blank
                Constants.device_com = Constants.availableCOM[ind]
                ser = serial.Serial(Constants.device_com, 115200)
                ser.flushInput()
                ser.write(bytes([1]))
                string_bytes = ser.read(9)
                ser.close()
            else:
                raise serial.SerialException
        except serial.SerialException:
            self.dev_status_te.setTextColor(QtGui.QColor('red'))
            self.dev_status_te.setText(u'Не могу подключиться к КОМ-порту\n')
            self.dev_status_te.setTextColor(QtGui.QColor('black'))
            Constants.device_com = ''
            ser = ''
            return
        if string_bytes[0] != 21:
            # Not for user
            self.dev_status_te.setTextColor(QtGui.QColor('red'))
            self.dev_status_te.append(u'Неверно задан КОМ-порт: первый байт != 21 \n')
            self.dev_status_te.setTextColor(QtGui.QColor('black'))
            ser = ''
        else:
            self.dev_status_te.setTextColor(QtGui.QColor('green'))
            self.dev_status_te.append(u'<b>Подключение прошло успешно!</b>\n')
            self.dev_status_te.setTextColor(QtGui.QColor('black'))
            ser = serial.Serial(Constants.device_com, 115200)
            ser.flushInput()
            ser.write(bytes([40]))
            string_bytes = ser.read(4)
            ser.close()

            bytes_array = struct.unpack('4B', string_bytes)
            self.dev_status_te.append(u'Версия прошивки и тип прибора: ' + str(bytes_array))
            if bytes_array[2] == 'S': Constants.panda = True

    def save_file(self):
        # Take file name for save spec
        Constants.filename = ''
        Constants.filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', '.')

    def progress_change(self, i):
        # Take signal from thread ang change progressBar value
        self.time_prb.setProperty('value', int(i))

    def num_change(self, i):
        # Change num value for line edit to indicate time for new start
        if self.measure_one_cb.currentIndex() > 0:
            self.time_one_le.setStyleSheet('solid green')
            self.time_one_le.setText(str(Constants.int_meas_sample - int(i)))
        else:
            self.time_all_le.setStyleSheet('solid green')
            self.time_all_le.setText(str(Constants.int_meas_all - int(i)))

    def thread_error(self, s):
        # Write error from thread in log file and teDevStatus
        self.dev_status_te.setTextColor(QtGui.QColor('red'))
        self.dev_status_te.append(u'Ошибка в потоке съемки спектра\n')
        self.dev_status_te.append(s + '\n')
        self.dev_status_te.setTextColor(QtGui.QColor('black'))

    def on_started(self):
        # Do when thread start
        self.go_pb.setDisabled(True)

    def print_measure(self):
        self.dev_status_te.append(u'<b>Прошло: </b>' + str(Constants.count_measure) + u'<b> измерение(й)</b>\n')
        Constants.count_measure += 1

    def on_finished(self):
        # Do when thread stop
        #self.teDevStatus.append(u'<b>Прошло: ' + str(constCOM.count_measure) + u' измерение(й)</b>\n')
        #constCOM.count_measure += 1
        self.go_pb.setDisabled(False)
        self.time_prb.setProperty('value', 0)
        self.time_one_le.setStyleSheet('solid white')
        self.time_all_le.setStyleSheet('solid white')
        self.time_one_le.setText(str(Constants.int_meas_sample))
        self.time_all_le.setText(str(Constants.int_meas_all))
        try:
            if self.measure_one_cb.currentIndex() > 0:
                self.measure_one_cb.setCurrentIndex(self.measure_one_cb.currentIndex() - 1)
                self.thread.start()
            elif self.measure_all_cb.currentIndex() > 0:
                self.measure_all_cb.setCurrentIndex(self.measure_all_cb.currentIndex() - 1)
                self.measure_one_cb.setCurrentIndex(Constants.num_meas_sample_const - 1)
                self.thread.start()
            else:
                raise ValueError
        except ValueError:
            self.dev_status_te.append(u'<b>Измерения закончены</b>\n')
            pass

        x_list = []
        y_list = Constants.y_list_all[:]
        # self.qwtPlot.clear()


        a0 = -0.10026
        a1 = 0.00893849
        a2 = 0

        for ind in range(len(y_list)):
            E = a0 + a1*float(ind) + a2*float(ind*ind)
            x_list.append(E)
        self.guiplot.plot(x_list, y_list, pen='w')
        # self.qwtPlot.plot(Qwt5.qplt.Curve(x_list, y_list, Qwt5.qplt.Pen(Qwt5.qplt.Red)))

    def stop_now (self):
        # Stop doing thread and turn off Hight voltage
        Constants.running_const = False
        Constants.num_all_sample = 0
        Constants.num_meas_sample = 0
        Constants.num_meas_sample_const = 0
        Constants.num_all_sample = 0
        Constants.int_meas_sample = 0
        Constants.int_meas_all = 0
        Constants.spec_all = 0
        Constants.count_measure = 1
        Constants.live_time = 0
        Constants.dead_time = 0
        Constants.y_list_all = []

        try:
            self.thread.running = False
        except NameError:
            pass
        try:
            self.stop_pb.setDisabled(True)
            ser = serial.Serial(Constants.device_com, 115200)
            # ser.flushInput()
            ser.write(struct.pack('B', 3))
            ser.close()
            self.stop_pb.setDisabled(False)
        except serial.SerialException:
            self.dev_status_te.append(u"Не могу подключиться к КОМ-порту")
            self.stop_pb.setDisabled(False)
        # constCOM.running_const = True

    def start_go(self):
        # Start measure in thread
        Constants.count_measure = 1
        Constants.running_const = True
        Constants.exposition_s = 0
        Constants.current_mk_a = 0
        Constants.voltage_kv = 0
        # print 'Staart go'
        try:
            Constants.exposition_s = int(self.exposition_le.text())
            Constants.current_mk_a = int(self.current_le.text())
            Constants.voltage_kv = int(self.energy_le.text())
        except ValueError:
            self.dev_status_te.setTextColor(QtGui.QColor('red'))
            self.dev_status_te.append(u'<b>Введите U, I, t!</b>')
            self.dev_status_te.setTextColor(QtGui.QColor('black'))
            Constants.exposition_s = 0
            Constants.current_mk_a = 0
            Constants.voltage_kv = 0
            return

        Constants.num_meas_sample = int(self.measure_one_cb.currentText())
        if Constants.num_meas_sample != 0 and self.measure_all_cb.currentText() == '':
            Constants.num_all_sample = 1
        else:
            Constants.num_all_sample = int(self.measure_all_cb.currentText())
        try:
            Constants.num_meas_sample_const = int(self.measure_one_cb.currentText())
            Constants.int_meas_sample = int(self.time_one_le.text())
            Constants.int_meas_all = int(self.time_all_le.text())
            Constants.spec_all = Constants.num_all_sample * Constants.num_meas_sample

            Constants.index_file = 0
            if Constants.int_meas_sample == 0 or Constants.int_meas_all == 0:
                self.dev_status_te.append(u'<b>Запуск одного измерения</b>')
            else:
                self.dev_status_te.append(u'<b>Запуск нескольких измерений</b>')
        except ValueError as var:
            print('Error in value S: 510')
            return

        if Constants.filename == '':
            Constants.filename = 'Noname_' + time.asctime().replace(':', '_')
            self.dev_status_te.append(u'<b>Файл сохранен как Noname</b>')

        if Constants.device_com == '':
            self.dev_status_te.append(u'<b>Пожалуйста используйте КОМ-порт</b>')
            return

        self.thread.start()

importlib.reload(sys)
# sys.setdefaultencoding('utf-8')
app = QtWidgets.QApplication(sys.argv)
sw = GuiXRF()
sw.resize(959, 857)
#sw.move(0,0)
sw.show()
sys.exit(app.exec_())
