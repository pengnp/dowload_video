@echo off
d:
cd D:\pythonData\push\dowload\dabao
call activate D:\Anaconda\envs\test_rqsdk
pyinstaller -F -w -i icon\2333.ico dow_video_th.py
cmd /k