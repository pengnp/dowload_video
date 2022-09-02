import string
import sys
import time
from itertools import zip_longest
from pprint import pprint
from tkinter import *
import requests
import json
import re
from tkinter import messagebox
import threading
import os
import subprocess
import yaml
import random
import tempfile
import traceback


class DEMO:

    def __init__(self):
        self._window = Tk()
        self._video_data = {}  # 数据列表
        self._dow_list = []  # 需要下载的数据
        self._already_list = {}  # 已存在的数据
        self._check_buts = {}  # 所有的多选按钮
        self._wait_dow_list = []  # 等待下载的列表
        self._address_input = ''
        self._semaphore = threading.Semaphore(3)  # 线程的运行数量
        self._dirs = ''
        self._folder_user = 'USER_FOLDER'
        self._folder_temp = 'Temp'
        self._header = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/87.0.4280.88 Safari/537.36',
                'referer': 'https://www.bilibili.com/',
                'cookie': ''
            }
        self._folder_name = ''
        self._dow_but_text = StringVar(value='点我下载(0个正在下载)')
        self._tips_flag = True  # 提示弹窗标识，判断提示窗是否存在
        self._excpe_dow = True  # 异常时的下载标识
        self._video_type = ''  # 区分类型  FAN番剧  BV普通视频  UP阿婆主的视频列表
        self._schedule = 0  # 累积滚动值
        self._accumulate = 0  # 每次鼠标滚动时需要移动的数值
        self._vsb_location = 0  # 滚动条位置
        self._pn = 0

    def _ui(self):
        """界面UI"""
        self._window.resizable(False, False)
        self._window.title('小工具')
        width = 400
        height = 400
        scree_width = (self._window.winfo_screenwidth() - width) // 2
        scree_height = (self._window.winfo_screenheight() - height) // 2
        self._window.geometry(f'{width}x{height}+{scree_width}+{scree_height}')
        try:
            for ico in os.listdir('./icon'):
                if ico.split('.')[-1] == 'ico':
                    self._window.iconbitmap(f'./icon/{ico}')
                break
        except:
            pass

        operation_box = Frame(self._window)
        operation_box.pack(side=TOP)
        Label(operation_box, text='地址：').pack(side=LEFT)
        var = StringVar()
        entry = Entry(operation_box, textvariable=var, width=42)
        entry.pack(side=LEFT)
        self._menu(entry)
        Button(operation_box, text='点我搜索', font=('微软雅黑', 8), command=lambda: self._set_video_type(var)).pack(
            side=LEFT)

        show_box = LabelFrame(self._window, padx=5, pady=4)
        show_box.pack(fill=X, side=TOP)
        self._canvas = Canvas(show_box, borderwidth=0)

        self._frame = Frame(self._canvas)
        self._frame.pack(side=TOP)
        vsb = Scrollbar(show_box, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set, height=250, width=270)
        vsb.pack(side=RIGHT, fill=Y)
        self._canvas.pack(side=LEFT, fill="both", expand=True)
        self._canvas.create_window((4, 4), window=self._frame, anchor="nw", tags="frame")
        self._frame.bind("<Configure>", lambda event, canvas1=self._canvas: self._canvas.configure(scrollregion=self._canvas.bbox("all")))

        Button(self._window, textvariable=self._dow_but_text, font=('微软雅黑', 8), width=300,
               command=lambda: self._disabled_or_select(True)).pack(side=TOP)

        def get_loc(event):
            """
            获取鼠标释放时，滚动条所在位置坐标
            :param event: 事件
            """
            self._schedule = vsb.get()[0]
            print(f'当前位置：{self._schedule}')

        vsb.bind("<ButtonRelease>", get_loc)

        def define(event):
            """
            canvas滚动
            :param event: 事件
            """
            if event.delta > 0:  # 向上滚动
                if self._schedule > 0:
                    self._schedule -= self._accumulate
                    self._canvas.yview_moveto(self._schedule)
            else:  # 向下滚动
                if self._schedule < 1:
                    self._schedule += self._accumulate
                    self._canvas.yview_moveto(self._schedule)
                if self._schedule >= 1 and self._video_type == 'UP':
                    self._pn += 1
                    self._get_video_info()
                    self._schedule = self._pn * 25 / len(self._video_data) - self._accumulate * 10

            print(self._schedule)
        self._window.bind('<MouseWheel>', define)

        self._window.mainloop()

    def _menu(self, entry):
        """
        右键剪切、复制、粘贴
        :param entry: 传入需要实现的右键的 entry组件
        """
        menu = Menu(self._window, tearoff=False)

        def popup(event):
            menu.post(event.x_root, event.y_root)

        def ctrl_x():
            entry.event_generate('<<Cut>>')

        def ctrl_c():
            entry.event_generate('<<Copy>>')

        def ctrl_v():
            entry.event_generate('<<Paste>>')

        menu.add_command(label="剪切", command=ctrl_x)
        menu.add_command(label="复制", command=ctrl_c)
        menu.add_command(label="粘贴", command=ctrl_v)
        entry.bind('<Button-3>', popup)

    def _get_entry_value(self, window, user_cookie, data):
        """
        获取提示框中输入信息，并做信息存储
        :param window: 所在的主界面名称，如 windows
        :param user_cookie: 组件定义的StringVar()
        :param data: 被弹窗阻塞的需要下载的视频数据
        """
        content = user_cookie.get()
        if content:
            window.destroy()
            self._tips_flag = True
            self._excpe_dow = True
            self._window.attributes('-disabled', 0)
            self._header['cookie'] = content
            self._save_cookie(content)
            if data:
                self._thread(data)
        else:
            pass

    def _tips(self, data=None, message=None):
        """
        提示窗口，且阻塞需要大会员才能下载的视频
        :param data: 视频数据
        """
        if self._tips_flag:
            self._tips_flag = False
            messagebox.showerror(message=message)
            self._window.attributes('-disabled', 1)
            window = Toplevel(self._window)
            window.wm_attributes('-topmost', 1)
            window.title('最好输入大会员cookie，且输入cookie不正确应用将无法使用')
            width = 500
            height = 50
            user_cookie = StringVar()
            scree_width = (window.winfo_screenwidth() - width) // 2
            scree_height = (window.winfo_screenheight() - height) // 2
            window.geometry(f'{width}x{height}+{scree_width}+{scree_height}')
            window.resizable(False, False)
            Label(window, text='cookie:').pack(side=LEFT)
            entry = Entry(window, textvariable=user_cookie, width=40)
            entry.pack(side=LEFT)
            self._menu(entry)
            Button(window, text='点我保存', width=10, command=lambda: self._get_entry_value(window, user_cookie, data)).pack(side=LEFT)
            Button(window, text='关闭程序', width=10, command=lambda: sys.exit(0)).pack(side=LEFT)
            window.protocol('WM_DELETE_WINDOW', lambda: onclose())

            def onclose():
                """判断是否为手动关闭，是  则继续弹窗"""
                self._tips_flag = True
                window.destroy()
                self._tips(message='你还没输入cookie')
        else:
            while True:
                if self._excpe_dow:  # 如果用户输入了cookie，且有效，则excpe_dow变为True
                    break
                time.sleep(3)
            self._thread(data)

    def _clear(self):
        """清除视频信息及按钮信息"""
        if self._check_buts:
            for but in self._check_buts.values():
                but[0].destroy()
        self._check_buts.clear()
        self._video_data.clear()
        self._dow_list.clear()
        self._schedule = 0  # canvas 滚动进度
        self._canvas.yview_moveto(0)  # 滚动条复位
        self._pn = 0

    def _set_video_type(self, var):
        """
        将获取到的视频信息展示到画布
        :param var: 搜索框的StringVar()
        """
        self._clear()
        self._address_input = var.get()
        if self._address_input:
            if 'https' not in self._address_input:
                if 'BV' in self._address_input:
                    self._address_input = f'https://www.bilibili.com/video/{self._address_input}'
                    self._video_type = 'BV'
                else:
                    self._video_type = 'UP'
            else:
                if 'BV' in self._address_input:
                    self._video_type = 'BV'
                else:
                    self._video_type = 'FAN'
            self._get_video_info()
        var.set('')

    def _show_data(self):
        """
        展示视频信息
        """
        for title in list(self._video_data.keys())[self._pn * 25:]:
            but = Checkbutton(self._frame, text=title, justify=LEFT, font=('微软雅黑', 8), command=lambda tit=title: self._get_dow_list(tit))
            but.pack(anchor='w')
            self._check_buts[title] = [but, False]
        self._disabled_or_select(False)

    def _get_dow_list(self, title):
        """勾选的视频存入列表，取消勾选的视频移除列表"""
        if title in self._dow_list:
            print(f'remove {title}')
            self._dow_list.remove(title)
        else:
            print(f'add {title}')
            self._dow_list.append(title)

    def _disabled_or_select(self, dis_flag=True):
        """
        多选按钮的状态控制
        :param dis_flag: 是  提前检验搜索的番剧在本地是否存在，存在则禁用对用的视频按钮。否 则不进行检验
        """
        if dis_flag:
            if self._check_buts:
                if self._dow_list:
                    self._thread()
                    for title in self._dow_list:
                        self._check_buts[title][1] = True
                        self._check_buts[title][0].config(state=DISABLED)
                    self._dow_list.clear()
                else:  # 全选操作
                    self._dow_list = list(self._video_data.keys() ^ set(self._already_list[self._folder_name]))
                    for dow in self._dow_list:
                        self._check_buts[dow][0].select()
        else:
            if self._already_list[self._folder_name]:
                for title in set(self._already_list[self._folder_name]) & self._check_buts.keys():
                    self._check_buts[title][0].config(state=DISABLED)

    def _create_folder(self, c_user_temp=True, c_vname_already=False):
        """
        创建文件夹或进行本地数据获取
        :param c_user_temp: 是 创建user、temp文件夹。否  进行数据获取或创建视频文件夹
        :param c_vname_already: 是 创建存储视频的文件夹。否  进行本地视频数据获取
        """
        self._dirs = os.listdir('./')
        if c_user_temp:
            if self._folder_user not in self._dirs:
                os.makedirs(self._folder_user)
            if self._folder_temp not in self._dirs:
                os.makedirs(self._folder_temp)
        else:
            if c_vname_already:
                if self._folder_name not in self._dirs:
                    os.makedirs(self._folder_name)
            else:
                if self._folder_name not in self._already_list:  # 如果历史数据中存在该视频记录， 则不进行本地数据检索
                    self._already_list[self._folder_name] = []
                    if self._folder_name in self._dirs:
                        for file in os.listdir(f'./{self._folder_name}'):
                            titles = file.split('.')
                            if len(titles) >= 2:
                                title = ''.join(titles[:-1])
                            else:
                                title = titles[0]
                            self._already_list[self._folder_name].append(title)

    def _delete_file(self, cid):
        """
        视频合成完成后，删除temp中对应的视频数据
        :param cid: 视频的名称
        """
        os.remove(f'./{self._folder_temp}/{cid}.mp3')
        os.remove(f'./{self._folder_temp}/{cid}.mp4')

    def _get_video_info(self):
        """获取视频信息"""
        try:
            if self._video_type in ['FAN', 'BV']:
                response = requests.get(self._address_input, headers=self._header).text
                video_info = json.loads(re.findall(r"<script>window\.__INITIAL_STATE__=(.*?)</script>", response)[0][0:-122])
                if self._video_type == 'FAN':
                    self._folder_name = video_info['mediaInfo']['title'].replace(' ', '').replace('/', '-')
                    for info in video_info['epList']:
                        if info['longTitle'] != '':
                            video_title = f"{info['titleFormat']}-{info['longTitle']}"
                        else:
                            video_title = f"{info['titleFormat']}"
                        video_title = video_title.replace('.', '_').replace('/', '-').replace(' ', '_')
                        self._video_data[video_title] = [info['cid'], info['bvid'], video_title, info['aid'], info['id'],
                                                         self._folder_name, self._video_type]
                elif self._video_type == 'BV':
                    info = video_info['videoData']
                    self._folder_name = info['title'].replace(' ', '').replace('/', '-').replace('.', '_')
                    self._video_data[self._folder_name] = [info['cid'], info['bvid'], self._folder_name, self._video_type]
            else:
                response = requests.get(url='https://api.bilibili.com/x/space/arc/search', headers=self._header,
                                        params={
                                            'mid': self._address_input,
                                            'pn': self._pn + 1,
                                            'ps': 25,
                                            'index': 1,
                                            'jsonp': 'jsonp',
                                        }).json()['data']['list']['vlist']
                if response:
                    self._folder_name = response[0]['author'].replace(' ', '').replace('/', '-').replace('.', '_')
                    for vlist in response:
                        video_title = vlist['title'].replace(' ', '').replace('/', '-').replace('.', '_')
                        cid = requests.get(url=f"https://api.bilibili.com/x/player/pagelist?aid={vlist['aid']}&jsonp=json",
                                           headers=self._header).json()['data'][0]['cid']
                        self._video_data[video_title] = [cid, vlist['bvid'], video_title, self._folder_name, self._video_type]
            self._create_folder(False)
            self._accumulate = 1 / len(self._video_data)  # 计算每次鼠标滚动时需要移动的距离
            self._show_data()
        except:
            messagebox.showerror(message=traceback.format_exc().replace('\n', '\n') + '\n未查到视频信息，请检查输入的url是否正确')

    def _thread(self, data=None):
        """
        创建线程，且提示需要下载的视频数量
        :param data: 视频信息
        """
        threading_list = []
        if data:
            threading_list.append(threading.Thread(target=self._download_video, args=(data,)))
        else:
            self._create_folder(False, True)
            for title in self._dow_list:
                self._already_list[self._folder_name].append(title)
                self._wait_dow_list.append(title)
                threading_list.append(threading.Thread(target=self._download_video, args=(self._video_data[title],)))
        for th in threading_list:
            th.daemon = True
            th.start()
        self._dow_but_text.set(f'点我下载({len(self._wait_dow_list)}个正在下载)')

    def _save_cookie(self, content):
        """
        存储cookie信息
        :param content: cookie值
        """
        cookie = {
            'key': [content]
        }
        with open(f'./{self._folder_user}/data.yaml', 'w', encoding='utf-8') as f:
            yaml.safe_dump(cookie, f, allow_unicode=True)

    def _get_cookie(self):
        """获取本地cookie信息，如果本地不存在则弹窗提示用户需要输入"""
        try:
            with open(f'./{self._folder_user}/data.yaml', encoding='utf-8') as f:
                yaml_result = yaml.safe_load(f)
            self._header['cookie'] = yaml_result['key'][0]
        except:
            self._tips(message='检测到本地不存在cookie，请输入cookie以便使用')

    def _download_video(self, data):
        """
        获取需要下载的视频video url、audio url。如果获取时报错，则弹窗提示cookie过期
        :param data: 视频数据
        """
        self._semaphore.acquire()
        time.sleep(random.uniform(0.1, 1.0))
        session = ''.join(random.sample(string.ascii_letters + string.digits, 32))
        video_title = data[2]
        try:
            if data[-1] == 'FAN':
                folder_name = data[-2]
                param = {
                    'avid': data[3],
                    'bvid': data[1],
                    'cid': data[0],
                    'qn': 0,
                    'fnver': 0,
                    'fnval': 4048,
                    'fourk': 1,
                    'ep_id': data[4],
                    'session': session
                }
                url = 'https://api.bilibili.com/pgc/player/web/playurl'  # 番剧
                response = requests.get(url, headers=self._header, params=param).json()
                try:
                    video_url = response['result']['dash']['video'][0]['backupUrl'][0]
                    audio_url = response['result']['dash']['audio'][0]['backupUrl'][0]
                except:
                    try:
                        video_url = response['result']['dash']['video'][0]['base_url']
                        audio_url = response['result']['dash']['audio'][0]['base_url']
                    except:
                        video_url = response['result']['durl'][0]['backup_url'][0]
                        audio_url = None
            else:
                url = 'https://api.bilibili.com/x/player/playurl'  # 普通
                param = {
                    'cid': data[0],
                    'qn': 116,
                    'otype': 'json',
                    'fourk': 1,
                    'bvid': data[1],
                    'fnver': 0,
                    'fnval': 976,
                    'session': session
                }
                if data[-1] == 'BV':
                    folder_name = video_title
                else:
                    folder_name = data[-2]
                response = requests.get(url, headers=self._header, params=param).json()
                try:
                    video_url = response['data']['dash']['video'][0]['backupUrl'][0]
                    audio_url = response['data']['dash']['audio'][0]['backupUrl'][0]
                except:
                    video_url = response['data']['dash']['video'][0]['baseUrl']
                    audio_url = response['data']['dash']['audio'][0]['baseUrl']
            text = StringVar()
            label = Label(self._window, textvariable=text, font=('微软雅黑', 8))
            label.pack(side=TOP, anchor=NW, pady=3)
            self._progress(video_url, audio_url, video_title, data[0], text, folder_name)
            label.destroy()
            self._wait_dow_list.remove(video_title)
            self._dow_but_text.set(f'点我下载({len(self._wait_dow_list)}个正在下载)')
        except:
            message = traceback.format_exc().replace('\n', '\n') + '\n请尝试输入新的大会员cookie，如不能解决请联系作者'
            self._excpe_dow = False
            self._tips(data, message)
        self._semaphore.release()

    def _progress(self, video_url, audio_url, video_title, cid, text, folder_name):
        """
        下载视频，并展示下载进度条
        :param video_url: 视频地址
        :param audio_url: 音频地址
        :param video_title: 视频的标题
        :param cid: 视频的cid
        :param text: Label组件的StringVar()
        :param folder_name: 保存视频的文件夹名称
        """
        size = 0  # 初始化已下载大小
        chunk_size = 30720  # 每次下载的数据大小
        video_response = requests.get(video_url, headers=self._header, stream=True)
        if audio_url:
            audio_response = requests.get(audio_url, headers=self._header, stream=True)
            with open(f"./{self._folder_temp}/{cid}.mp4", 'wb') as vf, open(f"./{self._folder_temp}/{cid}.mp3", 'wb') as af:
                content_size = int(video_response.headers['content-length']) + int(audio_response.headers['content-length'])
                for v, a in zip_longest(video_response.iter_content(chunk_size=chunk_size),
                                        audio_response.iter_content(chunk_size=chunk_size)):
                    if v:
                        vf.write(v)
                        size += len(v)
                    else:
                        pass
                    if a:
                        af.write(a)
                        size += len(a)
                    else:
                        pass
                    text.set(
                        '[文件<{}...>下载进度]:{size:.2f}%'.format(video_title[:24], size=float(size / content_size * 100)))
            out_temp = tempfile.SpooledTemporaryFile(max_size=10 * 1000)  # 临时文件包
            fileno = out_temp.fileno()
            cmd = f'ffmpeg -y -i ./{self._folder_temp}/{cid}.mp4 -i ./{self._folder_temp}/{cid}.mp3' \
                  f' -c:v copy -c:a aac -strict experimental ./{folder_name}/{video_title}.mp4 -nostdin'
            proc = subprocess.Popen(cmd, stdout=fileno, stderr=fileno, stdin=fileno, shell=True)
            text.set('文件合并中，请勿关闭')
            proc.wait()
            out_temp.seek(0)
            for i in out_temp.readlines():
                print(i.decode('utf-8').replace('\n', ''))
            if proc.poll() == 0:
                self._delete_file(cid)
        else:
            with open(f"./{folder_name}/{video_title}.mp4", 'wb') as vf:
                content_size = int(video_response.headers['content-length'])
                for v in video_response.iter_content(chunk_size=chunk_size):
                    vf.write(v)
                    size += len(v)
                    text.set(
                        '[文件<{}...>下载进度]:{size:.2f}%'.format(video_title[:24], size=float(size / content_size * 100)))

    def start(self):
        """梦开始的地方"""
        self._create_folder()
        self._get_cookie()
        self._ui()


if __name__ == '__main__':
    DEMO().start()


