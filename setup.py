from distutils.core import setup
import py2exe

setup(windows=['MainProgram.py'], options={"py2exe": {"includes": ["sip", "PyQt4.QtSvg", "serial"]}})
