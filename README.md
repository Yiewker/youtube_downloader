# youtube批量下载器

#### 部署save_path

```
git clone https://github.com/Yiewker/youtube_downloader
```

如果需要用aira2的话需要将aria2添加到path

#### 运行

双击ytdl.bat即可。

如果不想用aria2托管下载，可以直接运行 python yt_dlp_gui.py

#### 功能

将需要下载的youtube链接集合的txt文件拖入程序窗口，即可开始下载到指定的路径

更改config.yaml中的max_workers参数可以控制下载的最大线程数

save_path控制视频存储路径

txt文件需要每行一个youtube链接

#### 测试

目前只在win10测试过，其他平台没试过
