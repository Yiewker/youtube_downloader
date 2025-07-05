# YouTube 批量下载器 v2.2

简化版YouTube批量下载器，集成了反检测、智能重试和代理支持功能。支持Windows和macOS跨平台使用。

## 项目结构

```
youtube_downloader/
├── YouTube_Downloader_v2.1.exe     # 独立可执行文件（推荐使用）
├── youtube_downloader.bat          # 启动脚本（自动检测代理和Python环境）
├── youtube_downloader.py           # 主程序（基于yt_dlp_gui5.py改进）
├── youtube_downloader_config.yaml  # 配置文件
├── youtube_downloader.spec         # PyInstaller打包配置
├── requirements.txt                # Python依赖
├── yt-dlp.exe                      # YouTube下载器
├── test_urls.txt                   # 测试链接文件
├── dist/                           # 打包输出目录
├── his/v1/                         # 历史版本文件夹
└── README.md                       # 说明文档
```

## 🚀 快速开始

### Windows用户
1. 从 [Releases页面](https://github.com/Yiewker/youtube_downloader/releases) 下载 `YouTube_Downloader_vX.X.X.exe`
2. 双击运行即可，无需安装Python环境

### macOS用户

#### 方法1：使用.app版本（推荐）
1. 下载 `YouTube_Downloader_vX.X.X_macos.app`
2. 在终端中运行：`chmod +x YouTube_Downloader_vX.X.X_macos.app`
3. 双击运行

#### 方法2：如果双击不工作
```bash
# 下载后在终端中执行
chmod +x YouTube_Downloader_vX.X.X_macos.app
./YouTube_Downloader_vX.X.X_macos.app
```

#### 方法3：右键菜单
1. 右键点击下载的文件
2. 选择"打开方式" → "终端"
3. 或选择"打开方式" → "其他" → 选择"终端"

#### 方法4：设置默认程序
1. 右键点击文件 → "显示简介"
2. 在"打开方式"部分选择"终端"
3. 点击"全部更改"

### 传统方式：使用启动脚本
直接双击 `youtube_downloader.bat` 即可启动程序（仅Windows）。

### 2. 下载方式（两种选择）

#### 方式1：使用链接文件
创建一个txt文件，每行一个YouTube链接，例如：
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://www.youtube.com/watch?v=oHg5SJYRHA0
```
然后：
- 点击"选择链接文件"按钮选择txt文件
- 或直接将txt文件拖放到程序窗口

#### 方式2：直接输入链接（新功能）
- 在程序界面的文本框中直接输入YouTube链接
- 支持多个链接，每行一个或用空格分隔
- 点击"开始下载"按钮

### 3. 画质选择
- 默认下载最佳画质
- 勾选"优先下载最低画质"可节省流量和时间

## 功能特点

### 📦 独立可执行文件
- 🎯 **完全便携**：单个exe文件，约30MB，无需安装Python环境
- ⚡ **即开即用**：双击运行，自动生成配置文件
- 🔧 **自包含**：内置所有依赖库和yt-dlp下载器
- 💾 **配置持久化**：exe同目录下保存用户设置

### 🚀 智能启动检测
- 自动检测Python环境（配置在yaml中）
- 可选代理连接测试（默认关闭以提高启动速度）
- 代理测试失败时给出提示但继续运行

### 🛡️ 反检测机制
- 模拟真实浏览器请求头
- 随机下载间隔（避免被限制）
- 智能重试机制（最多3次）
- 限制并发数（最多2个）

### 📊 智能格式选择
- 自动选择最佳可用格式
- **高画质优先**：1080p60 > 720p60 > 1080p30 > 720p30 > 480p > 360p
- **低画质优先**：360p > 480p > 720p > worst（节省流量）
- 自动回退到可用格式

### 📝 多种输入方式
- 传统文件方式：支持txt文件拖放和选择
- 直接输入方式：界面中直接输入链接，支持多链接
- 智能链接识别：自动识别YouTube链接格式

### 🔧 配置化设计
- 所有设置都在yaml配置文件中
- 支持自定义Python路径
- 支持自定义保存路径
- 支持代理开关

### 💾 错误处理
- 失败的链接自动保存到 `*_failed.txt`
- 详细的错误日志
- 支持断点续传

## 配置说明

### 主要配置项
```yaml
# Python解释器路径
python_path: "J:\\app\\Python\\Python310\\python.exe"

# 下载设置
download:
  save_path: "J:\\Users\\ccd\\Downloads\\"  # 保存路径
  max_workers: 2                            # 并发数
  proxy:
    enabled: true                           # 是否使用代理
    url: "http://127.0.0.1:7890"           # 代理地址

# 视频质量设置
video:
  format_priority:                          # 格式优先级
    - "bestvideo[height=1080][fps=60]+bestaudio/best"
    - "bestvideo[height=720][fps=60]+bestaudio/best"
    # ...更多格式
```

## 代理设置

### Clash配置
1. 启动Clash
2. 确保监听端口为7890
3. 允许局域网连接
4. 确保能正常访问YouTube

### 无代理使用
如果不需要代理，可以在配置文件中设置：
```yaml
download:
  proxy:
    enabled: false
    test_on_startup: false  # 启动时是否测试代理（默认关闭以提高启动速度）
```

## 🐛 故障排除

### macOS "无法打开" 错误
如果遇到 "无法打开，因为它来自身份不明的开发者" 错误：

1. **方法1**：按住 Control 键点击文件，选择"打开"
2. **方法2**：在"系统偏好设置" → "安全性与隐私" → "通用" 中点击"仍要打开"
3. **方法3**：在终端中运行：
   ```bash
   xattr -d com.apple.quarantine YouTube_Downloader_vX.X.X_macos.app
   ```

### macOS "未设定用来打开的程序" 错误
1. **右键点击文件** → "打开方式" → "终端"
2. **或者在终端中运行**：
   ```bash
   chmod +x YouTube_Downloader_vX.X.X_macos.app
   ./YouTube_Downloader_vX.X.X_macos.app
   ```

### Windows "Windows已保护你的电脑" 错误
1. 点击"更多信息"
2. 点击"仍要运行"

### 代理连接失败
- 检查Clash是否启动
- 确认端口是否为7890
- 检查防火墙设置
- 尝试重启代理软件

### Python路径错误
- 检查配置文件中的python_path
- 确保Python已正确安装
- 确保路径使用双反斜杠 `\\`

### 下载失败
- 检查网络连接
- 确认YouTube链接有效
- 查看失败链接文件获取详细错误

## 更新日志

### v2.1 (当前版本)
- 🆕 **新增直接输入链接功能**：无需创建txt文件，直接在界面输入链接
- 🆕 **新增低画质优先选项**：可选择优先下载最低画质节省流量
- 📦 **独立exe文件**：使用PyInstaller打包，完全便携，无需Python环境
- ⚡ **启动速度优化**：代理测试默认关闭，启动速度提升至秒开
- 🎨 **界面优化**：调整窗口大小，添加占位符提示，改进布局
- 🔧 **智能链接识别**：支持多种YouTube链接格式自动识别
- 📝 **多输入方式**：支持换行和空格分隔的多链接输入
- ⚙️ **可配置代理测试**：可在配置文件中控制是否启动时测试代理
- 💾 **配置自动生成**：首次运行自动创建默认配置文件

### v2.0
- 重构项目结构，化繁为简
- 集成智能启动脚本
- 添加配置文件支持
- 增强反检测机制
- 改进错误处理
- 移除历史版本到his/v1文件夹

### v1.x (历史版本)
- 多个实验性版本
- 基础下载功能
- 简单GUI界面

## 依赖要求

- Python 3.10+
- tkinterdnd2 >= 0.3.0
- pyyaml >= 6.0
- requests >= 2.28.0

## 许可证

本项目仅供学习和个人使用，请遵守YouTube的服务条款。
