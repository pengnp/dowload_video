@echo off
call activate D:\Anaconda\envs\dabao
pyinstaller -F -w -i icon\2333.ico dow_video_th.py
rd __pycache__ /s /q
rd build /s /q
del dow_video_th.spec
move dist\dow_video_th.exe D:\pythonData\push\dowload_video
rd dist /s /q
exit
