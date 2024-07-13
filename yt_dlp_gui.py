import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import yaml
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置文件名称
CONFIG_FILE = 'config.yaml'
current_directory = os.path.dirname(os.path.abspath(__file__))
yt_dlp_path = os.path.join(current_directory, 'yt-dlp.exe')

# 读取配置文件
def read_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            config = yaml.safe_load(file)
            return config.get('save_path', ''), config.get('max_workers', 3)
    return '', 3

# 保存配置文件
def save_config(save_path, max_workers):
    with open(CONFIG_FILE, 'w') as file:
        yaml.dump({'save_path': save_path, 'max_workers': max_workers}, file)

# 检查路径是否合法并尝试创建路径
def validate_save_path(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except Exception as e:
            update_status(f"无法创建路径: {e}")
            return False
    return True

# 更新状态标签
def update_status(message):
    status_label.config(text=message)

# 选择文件
def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("INI files", "*.ini")])
    if file_path:
        file_label.config(text=file_path)
        update_status("下载中...")
        threading.Thread(target=download_videos, args=(file_path,)).start()

# 拖放文件处理
def drop(event):
    file_path = event.data.strip('{}')  # 去掉路径中的花括号
    if file_path:
        file_label.config(text=file_path)
        update_status("下载中...")
        threading.Thread(target=download_videos, args=(file_path,)).start()

# 下载单个视频
def download_video(link, save_path):
    command = [
        yt_dlp_path,
        '-f', 'bv*+ba/b',
        '-o', os.path.join(save_path, '%(title)s.%(ext)s'),
        '--proxy', 'socks5://127.0.0.1:10808',
        link
    ]
    subprocess.run(command)

# 下载视频
def download_videos(file_path):
    save_path = save_path_entry.get()
    max_workers = int(max_workers_entry.get())
    
    if not file_path:
        update_status("请先选择一个文件")
        return
    
    if not validate_save_path(save_path):
        return
    
    # 保存配置
    save_config(save_path, max_workers)
    
    # 读取文件中的链接
    with open(file_path, 'r') as file:
        links = [line.strip() for line in file]
    
    # 使用线程池批量下载
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_video, link, save_path) for link in links]
        for future in as_completed(futures):
            future.result()  # 等待所有线程完成
    
    update_status("下载完成")

# 创建主窗口
root = TkinterDnD.Tk()
root.title("YouTube 视频下载器")

# 存储路径设置
save_path_label = tk.Label(root, text="文件存储路径:")
save_path_label.pack()

save_path, max_workers = read_config()
save_path_entry = tk.Entry(root, width=50)
save_path_entry.pack()
save_path_entry.insert(0, save_path)

# 最大工作线程数设置
max_workers_label = tk.Label(root, text="最大工作线程数:")
max_workers_label.pack()

max_workers_entry = tk.Entry(root, width=5)
max_workers_entry.pack()
max_workers_entry.insert(0, str(max_workers))

# 选择文件按钮
select_file_button = tk.Button(root, text="选择文件", command=select_file)
select_file_button.pack()

file_label = tk.Label(root, text="未选择文件")
file_label.pack()

# 状态标签
status_label = tk.Label(root, text="请选择文件")
status_label.pack()

# 绑定拖放到整个窗口
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', drop)

root.mainloop()
