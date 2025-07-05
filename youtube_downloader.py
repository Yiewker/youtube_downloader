#!/usr/bin/env python3
"""
YouTube 批量下载器 - 简化版
基于 yt_dlp_gui5.py 并集成反检测和智能重试功能
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import yaml
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import ctypes
import atexit
import signal
import time
import random
import uuid
import requests

def get_resource_path(relative_path):
    """获取资源文件路径（支持打包后的exe）"""
    try:
        # PyInstaller打包后的临时目录
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境下的当前目录
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_config_path():
    """获取配置文件路径（exe同目录下）"""
    if getattr(sys, 'frozen', False):
        # 打包后的exe文件目录
        return os.path.join(os.path.dirname(sys.executable), 'youtube_downloader_config.yaml')
    else:
        # 开发环境
        return 'youtube_downloader_config.yaml'

# 配置文件名称和路径
CONFIG_FILE = get_config_path()
current_directory = os.path.dirname(os.path.abspath(__file__))
yt_dlp_path = get_resource_path('yt-dlp.exe')

class YouTubeDownloader:
    def __init__(self):
        self.config = self.load_config()
        self.root = None
        self.status_label = None
        self.progress_var = None
        self.progress_bar = None
        self.save_path_entry = None
        self.max_workers_entry = None
        self.proxy_var = None
        self.debug_var = None
        self.low_quality_var = None
        self.proxy_test_var = None
        self.url_text = None
        
    def load_config(self):
        """加载配置文件"""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            # 配置文件不存在，创建默认配置
            default_config = self.create_default_config()
            self.save_default_config(default_config)
            return default_config
        except Exception as e:
            messagebox.showerror("配置错误", f"无法加载配置文件: {e}")
            sys.exit(1)

    def create_default_config(self):
        """创建默认配置"""
        return {
            'behavior': {
                'download_interval': 2,
                'ignore_errors': True,
                'max_retries': 3,
                'random_delay_range': [1, 3],
                'retry_delay': 5,
                'unique_filename': True
            },
            'debug': {
                'enabled': False,
                'save_logs': False,
                'show_formats': False
            },
            'download': {
                'max_workers': 2,
                'proxy': {
                    'enabled': True,
                    'test_on_startup': False,
                    'test_url': 'https://www.google.com',
                    'timeout': 3,
                    'url': 'http://127.0.0.1:7890'
                },
                'save_path': os.path.join(os.path.expanduser('~'), 'Downloads')
            },
            'python_path': sys.executable,
            'video': {
                'format_priority': [
                    'bestvideo[height=1080][fps=60]+bestaudio/best',
                    'bestvideo[height=720][fps=60]+bestaudio/best',
                    'bestvideo[height=1080][fps=30]+bestaudio/best',
                    'bestvideo[height=720][fps=30]+bestaudio/best',
                    'bestvideo[height=480]+bestaudio/best',
                    'bestvideo[height=360]+bestaudio/best'
                ],
                'max_height': 1080,
                'output_format': 'mp4'
            }
        }

    def save_default_config(self, config):
        """保存默认配置到文件"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as file:
                yaml.dump(config, file, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"无法保存默认配置: {e}")
    
    def save_config(self):
        """保存配置文件"""
        try:
            # 更新配置
            self.config['download']['save_path'] = self.save_path_entry.get()
            self.config['download']['max_workers'] = int(self.max_workers_entry.get())
            self.config['download']['proxy']['enabled'] = self.proxy_var.get()
            if hasattr(self, 'proxy_test_var'):
                self.config['download']['proxy']['test_on_startup'] = self.proxy_test_var.get()
            self.config['debug']['enabled'] = self.debug_var.get()
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as file:
                yaml.dump(self.config, file, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def validate_save_path(self, path):
        """检查并创建保存路径"""
        if not os.path.exists(path):
            try:
                os.makedirs(path)
                return True
            except Exception as e:
                self.update_status(f"无法创建路径: {e}")
                return False
        return True
    
    def update_status(self, message):
        """线程安全的状态更新"""
        if self.root and self.status_label:
            self.root.after(0, lambda: self.status_label.config(text=message))
    
    def update_progress(self, current, total):
        """更新进度条"""
        if self.root and self.progress_var:
            progress = (current / total) * 100 if total > 0 else 0
            self.root.after(0, lambda: self.progress_var.set(progress))
    
    def test_proxy_connection(self):
        """测试代理连接"""
        if not self.config['download']['proxy']['enabled']:
            return True
            
        try:
            proxy_url = self.config['download']['proxy']['url']
            test_url = self.config['download']['proxy']['test_url']
            timeout = self.config['download']['proxy']['timeout']
            
            proxies = {'http': proxy_url, 'https': proxy_url}
            response = requests.get(test_url, proxies=proxies, timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_best_format(self, link, prefer_low_quality=False):
        """获取最佳可用格式"""
        try:
            command = [yt_dlp_path, '-F', link]
            if self.config['download']['proxy']['enabled']:
                command.extend(['--proxy', self.config['download']['proxy']['url']])

            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            formats_output = result.stdout

            if self.config['debug']['enabled']:
                print(f"可用格式: {formats_output}")

            # 如果优先下载最低画质
            if prefer_low_quality:
                low_quality_formats = [
                    "worst[height<=360]+bestaudio/worst",
                    "worst[height<=480]+bestaudio/worst",
                    "worst[height<=720]+bestaudio/worst",
                    "worst"
                ]
                for format_str in low_quality_formats:
                    if any(keyword in formats_output for keyword in format_str.split('+')):
                        return format_str
                return "worst"

            # 按优先级选择格式（高画质优先）
            for format_str in self.config['video']['format_priority']:
                if any(keyword in formats_output for keyword in format_str.split('+')):
                    return format_str

            # 如果没有找到理想格式，使用备用格式
            return "best[height<=1080]"

        except Exception as e:
            print(f"获取格式失败: {e}")
            return "worst" if prefer_low_quality else "best[height<=720]"
    
    def download_video(self, link, save_path, prefer_low_quality=False):
        """下载单个视频"""
        max_retries = self.config['behavior']['max_retries']
        retry_delay = self.config['behavior']['retry_delay']

        # 生成唯一文件名
        if self.config['behavior']['unique_filename']:
            short_uuid = uuid.uuid4().hex[:8]
            filename_template = f"%(title)s_{short_uuid}.%(ext)s"
        else:
            filename_template = "%(title)s.%(ext)s"

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = retry_delay * attempt + random.uniform(1, 3)
                    time.sleep(delay)
                    print(f"重试下载 {link} (第 {attempt + 1} 次)")

                # 获取最佳格式
                format_str = self.get_best_format(link, prefer_low_quality)
                
                # 构建下载命令
                command = [
                    yt_dlp_path,
                    '-f', format_str,
                    '-o', os.path.join(save_path, filename_template),
                    '--merge-output-format', self.config['video']['output_format'],
                    # 反检测措施
                    '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    '--referer', 'https://www.youtube.com/',
                    '--add-header', 'Accept-Language:en-US,en;q=0.9',
                    '--add-header', 'Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    '--sleep-interval', str(self.config['behavior']['download_interval']),
                    '--max-sleep-interval', str(self.config['behavior']['download_interval'] + 2),
                    '--retries', str(max_retries),
                    '--fragment-retries', str(max_retries),
                ]
                
                # 添加代理设置
                if self.config['download']['proxy']['enabled']:
                    command.extend(['--proxy', self.config['download']['proxy']['url']])
                
                # 添加错误忽略
                if self.config['behavior']['ignore_errors']:
                    command.append('--ignore-errors')
                
                command.append(link)
                
                # 执行下载
                result = subprocess.run(command, capture_output=True, text=True)
                
                if result.returncode == 0:
                    return 0  # 成功
                else:
                    print(f"下载失败 (尝试 {attempt + 1}): {result.stderr}")
                    
            except Exception as e:
                print(f"下载异常 (尝试 {attempt + 1}): {e}")
        
        return -1  # 所有重试都失败
    
    def download_videos(self, file_path, links_list=None):
        """批量下载视频"""
        save_path = self.save_path_entry.get()
        max_workers = int(self.max_workers_entry.get())
        prefer_low_quality = self.low_quality_var.get() if self.low_quality_var else False

        if not file_path and not links_list:
            self.update_status("请先选择一个文件或输入链接")
            return

        if not self.validate_save_path(save_path):
            return

        # 保存配置
        self.save_config()

        # 测试代理连接
        if self.config['download']['proxy']['enabled']:
            self.update_status("正在测试代理连接...")
            if not self.test_proxy_connection():
                self.update_status("代理连接失败，请检查代理设置")
                messagebox.showerror("代理错误", "无法连接到代理服务器，请检查Clash是否启动并开放7890端口")
                return

        # 读取链接
        if links_list:
            links = links_list
        else:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    links = [line.strip() for line in file if line.strip()]
            except Exception as e:
                self.update_status(f"读取文件失败: {e}")
                return

        if not links:
            self.update_status("没有找到有效链接")
            return

        total_count = len(links)
        completed_count = 0
        failed_links = []

        quality_text = "最低画质" if prefer_low_quality else "最佳画质"
        self.update_status(f"开始下载 {total_count} 个视频 ({quality_text})...")
        self.update_progress(0, total_count)

        # 限制并发数以避免被检测
        actual_workers = min(max_workers, 2)

        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            futures = {}

            for i, link in enumerate(links):
                # 添加随机延迟
                if i > 0:
                    delay_range = self.config['behavior']['random_delay_range']
                    delay = random.uniform(delay_range[0], delay_range[1])
                    time.sleep(delay)

                future = executor.submit(self.download_video, link, save_path, prefer_low_quality)
                futures[future] = link
            
            for future in as_completed(futures):
                link = futures[future]
                try:
                    result = future.result()
                    if result == 0:
                        completed_count += 1
                    else:
                        failed_links.append(link)
                        
                    self.update_progress(completed_count + len(failed_links), total_count)
                    self.update_status(f"进度: {completed_count + len(failed_links)}/{total_count} (成功: {completed_count})")
                    
                except Exception as e:
                    failed_links.append(link)
                    print(f"下载异常: {link}, 错误: {e}")
        
        # 保存失败的链接
        if failed_links:
            failed_file = file_path + '_failed.txt'
            try:
                with open(failed_file, 'w', encoding='utf-8') as f:
                    for link in failed_links:
                        f.write(link + '\n')
                self.update_status(f"下载完成: {completed_count}/{total_count} 成功，失败链接已保存到 {failed_file}")
            except Exception as e:
                self.update_status(f"下载完成: {completed_count}/{total_count} 成功，但无法保存失败链接: {e}")
        else:
            self.update_status(f"全部下载完成: {completed_count}/{total_count}")
    
    def select_file(self):
        """选择文件"""
        file_path = filedialog.askopenfilename(
            title="选择包含YouTube链接的文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            self.update_status("开始下载...")
            threading.Thread(target=self.download_videos, args=(file_path,), daemon=True).start()
    
    def drop_file(self, event):
        """拖放文件处理"""
        file_path = event.data.strip('{}')
        if file_path:
            self.update_status("开始下载...")
            threading.Thread(target=self.download_videos, args=(file_path,), daemon=True).start()

    def download_from_text(self):
        """从文本框下载链接"""
        url_text = self.url_text.get("1.0", tk.END).strip()

        # 检查是否为占位符文本
        placeholder_text = "在此输入YouTube链接，例如:\nhttps://www.youtube.com/watch?v=example1\nhttps://youtu.be/example2"
        if not url_text or url_text == placeholder_text:
            self.update_status("请输入YouTube链接")
            messagebox.showwarning("输入错误", "请在文本框中输入YouTube链接")
            return

        # 解析链接（支持换行和空格分隔）
        import re
        # 匹配YouTube链接的正则表达式
        youtube_pattern = r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]+'
        links = re.findall(youtube_pattern, url_text)

        if not links:
            # 如果没有找到标准YouTube链接，尝试按行分割
            lines = [line.strip() for line in url_text.split('\n') if line.strip()]
            # 过滤出可能的链接
            links = [line for line in lines if 'youtube.com' in line or 'youtu.be' in line]

        if not links:
            self.update_status("未找到有效的YouTube链接")
            messagebox.showerror("链接错误", "未找到有效的YouTube链接，请检查输入格式")
            return

        self.update_status(f"找到 {len(links)} 个链接，开始下载...")
        threading.Thread(target=self.download_videos, args=(None, links), daemon=True).start()
    
    def update_ytdlp(self):
        """更新yt-dlp"""
        def update_worker():
            try:
                self.update_status("正在更新 yt-dlp...")
                result = subprocess.run([yt_dlp_path, '-U'], capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    self.update_status("yt-dlp 更新完成")
                else:
                    self.update_status("yt-dlp 更新失败")
            except Exception as e:
                self.update_status(f"更新失败: {e}")
        
        threading.Thread(target=update_worker, daemon=True).start()
    
    def prevent_sleep(self):
        """防止系统休眠"""
        try:
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
        except:
            pass
    
    def restore_sleep(self):
        """恢复系统休眠设置"""
        try:
            ES_CONTINUOUS = 0x80000000
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        except:
            pass
    
    def signal_handler(self, sig, frame):
        """信号处理"""
        self.restore_sleep()
        if self.root:
            self.root.quit()
        sys.exit(0)

    def create_gui(self):
        """创建GUI界面"""
        self.root = TkinterDnD.Tk()
        self.root.title("YouTube 批量下载器 v2.0")
        self.root.geometry("650x700")

        # 设置图标（如果存在）
        try:
            self.root.iconbitmap(default="youtube.ico")
        except:
            pass

        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        row = 0

        # 标题
        title_label = ttk.Label(main_frame, text="YouTube 批量下载器", font=("Arial", 16, "bold"))
        title_label.grid(row=row, column=0, columnspan=3, pady=(0, 20))
        row += 1

        # 保存路径设置
        ttk.Label(main_frame, text="保存路径:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.save_path_entry = ttk.Entry(main_frame, width=50)
        self.save_path_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        self.save_path_entry.insert(0, self.config['download']['save_path'])

        browse_button = ttk.Button(main_frame, text="浏览",
                                 command=lambda: self.browse_folder())
        browse_button.grid(row=row, column=2, padx=(5, 0), pady=5)
        row += 1

        # 最大工作线程数
        ttk.Label(main_frame, text="并发数:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.max_workers_entry = ttk.Entry(main_frame, width=10)
        self.max_workers_entry.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        self.max_workers_entry.insert(0, str(self.config['download']['max_workers']))
        row += 1

        # 代理设置
        self.proxy_var = tk.BooleanVar(value=self.config['download']['proxy']['enabled'])
        proxy_check = ttk.Checkbutton(main_frame, text="使用代理 (7890端口)", variable=self.proxy_var)
        proxy_check.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1

        # 调试模式
        self.debug_var = tk.BooleanVar(value=self.config['debug']['enabled'])
        debug_check = ttk.Checkbutton(main_frame, text="调试模式", variable=self.debug_var)
        debug_check.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1

        # 优先下载最低画质
        self.low_quality_var = tk.BooleanVar(value=False)
        low_quality_check = ttk.Checkbutton(main_frame, text="优先下载最低画质", variable=self.low_quality_var)
        low_quality_check.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1

        # 启动时测试代理
        self.proxy_test_var = tk.BooleanVar(value=self.config['download']['proxy'].get('test_on_startup', False))
        proxy_test_check = ttk.Checkbutton(main_frame, text="启动时测试代理连接", variable=self.proxy_test_var)
        proxy_test_check.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1

        # 分隔线
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20)
        row += 1

        # 操作按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=10)

        # 选择文件按钮
        select_button = ttk.Button(button_frame, text="选择链接文件", command=self.select_file)
        select_button.pack(side=tk.LEFT, padx=(0, 10))

        # 更新yt-dlp按钮
        update_button = ttk.Button(button_frame, text="更新 yt-dlp", command=self.update_ytdlp)
        update_button.pack(side=tk.LEFT, padx=(0, 10))

        # 测试代理按钮
        test_proxy_button = ttk.Button(button_frame, text="测试代理", command=self.test_proxy_gui)
        test_proxy_button.pack(side=tk.LEFT)

        row += 1

        # 拖放提示
        drop_label = ttk.Label(main_frame, text="或将包含YouTube链接的txt文件拖放到此窗口",
                              font=("Arial", 10), foreground="gray")
        drop_label.grid(row=row, column=0, columnspan=3, pady=10)
        row += 1

        # 第二个分隔线
        separator2 = ttk.Separator(main_frame, orient='horizontal')
        separator2.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1

        # 直接输入链接区域
        ttk.Label(main_frame, text="或直接输入YouTube链接:", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        row += 1

        # 链接输入文本框
        url_frame = ttk.Frame(main_frame)
        url_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        url_frame.columnconfigure(0, weight=1)

        self.url_text = tk.Text(url_frame, height=4, wrap=tk.WORD, font=("Arial", 9))
        self.url_text.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        # 添加占位符文本
        placeholder_text = "在此输入YouTube链接，例如:\nhttps://www.youtube.com/watch?v=example1\nhttps://youtu.be/example2"
        self.url_text.insert("1.0", placeholder_text)
        self.url_text.config(foreground="gray")

        # 绑定焦点事件来处理占位符
        def on_focus_in(event):
            if self.url_text.get("1.0", tk.END).strip() == placeholder_text:
                self.url_text.delete("1.0", tk.END)
                self.url_text.config(foreground="black")

        def on_focus_out(event):
            if not self.url_text.get("1.0", tk.END).strip():
                self.url_text.insert("1.0", placeholder_text)
                self.url_text.config(foreground="gray")

        self.url_text.bind("<FocusIn>", on_focus_in)
        self.url_text.bind("<FocusOut>", on_focus_out)

        # 滚动条
        url_scrollbar = ttk.Scrollbar(url_frame, orient=tk.VERTICAL, command=self.url_text.yview)
        url_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.url_text.config(yscrollcommand=url_scrollbar.set)

        row += 1

        # 提示文本
        hint_label = ttk.Label(main_frame, text="支持多个链接，每行一个或用空格分隔",
                              font=("Arial", 8), foreground="gray")
        hint_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        row += 1

        # 下载按钮
        download_button = ttk.Button(main_frame, text="开始下载", command=self.download_from_text)
        download_button.grid(row=row, column=0, sticky=tk.W, pady=5)
        row += 1

        # 进度条
        ttk.Label(main_frame, text="下载进度:").grid(row=row, column=0, sticky=tk.W, pady=(20, 5))
        row += 1

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        row += 1

        # 状态标签
        self.status_label = ttk.Label(main_frame, text="就绪 - 请选择包含YouTube链接的文件",
                                     font=("Arial", 10))
        self.status_label.grid(row=row, column=0, columnspan=3, pady=10)
        row += 1

        # 使用说明
        help_text = """使用说明：
方式1: 准备一个txt文件，每行一个YouTube链接，点击"选择链接文件"或拖放文件到窗口
方式2: 直接在上方文本框中输入YouTube链接，支持多个链接（每行一个或空格分隔）
• 勾选"优先下载最低画质"可节省流量和时间
• 如需使用代理，请确保Clash等代理软件已启动并开放7890端口"""

        help_label = ttk.Label(main_frame, text=help_text, font=("Arial", 9),
                              foreground="gray", justify=tk.LEFT)
        help_label.grid(row=row, column=0, columnspan=3, pady=(20, 0), sticky=tk.W)

        # 绑定拖放
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.drop_file)

        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        return self.root

    def browse_folder(self):
        """浏览文件夹"""
        folder = filedialog.askdirectory(title="选择保存路径")
        if folder:
            self.save_path_entry.delete(0, tk.END)
            self.save_path_entry.insert(0, folder)

    def test_proxy_gui(self):
        """GUI中的代理测试"""
        def test_worker():
            self.update_status("正在测试代理连接...")
            if self.test_proxy_connection():
                self.update_status("代理连接测试成功")
                messagebox.showinfo("代理测试", "代理连接正常")
            else:
                self.update_status("代理连接测试失败")
                messagebox.showerror("代理测试", "代理连接失败，请检查Clash是否启动并开放7890端口")

        threading.Thread(target=test_worker, daemon=True).start()

    def on_closing(self):
        """窗口关闭事件"""
        self.restore_sleep()
        self.root.destroy()

    def run(self):
        """运行程序"""
        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # 防止系统休眠
        self.prevent_sleep()
        atexit.register(self.restore_sleep)

        # 创建并运行GUI
        root = self.create_gui()

        # 启动时检查yt-dlp
        self.update_status("检查 yt-dlp 状态...")
        threading.Thread(target=self.check_ytdlp_on_startup, daemon=True).start()

        root.mainloop()

    def check_ytdlp_on_startup(self):
        """启动时检查yt-dlp"""
        try:
            result = subprocess.run([yt_dlp_path, '--version'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.update_status(f"就绪 - yt-dlp {version}")
            else:
                self.update_status("yt-dlp 检查失败，建议更新")
        except Exception:
            self.update_status("yt-dlp 检查失败，建议更新")


def main():
    """主函数"""
    try:
        app = YouTubeDownloader()
        app.run()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
        input("按回车键退出...")


if __name__ == "__main__":
    main()
