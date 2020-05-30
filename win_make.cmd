@echo off
@del /Q build
@del /Q dist
C:\Python26\python.exe setup.py py2exe
pause