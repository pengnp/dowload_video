@echo off
call activate D:\Anaconda\envs\test_rqsdk
pyinstaller -F -w -i icon\2333.ico dow_video_th.py
cmd /k