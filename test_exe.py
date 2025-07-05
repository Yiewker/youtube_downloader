#!/usr/bin/env python3
"""
测试打包后的exe文件
"""

import subprocess
import time
import os

def test_exe():
    """测试exe文件"""
    exe_path = r".\dist\YouTube_Downloader_v2.1.exe"
    
    if not os.path.exists(exe_path):
        print("❌ exe文件不存在")
        return False
    
    print(f"✅ 找到exe文件: {exe_path}")
    print(f"📁 文件大小: {os.path.getsize(exe_path) / (1024*1024):.1f} MB")
    
    try:
        # 启动exe
        print("🚀 启动exe文件...")
        process = subprocess.Popen([exe_path], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        # 等待几秒看是否有错误
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ exe正在运行中...")
            print("💡 请检查是否有GUI窗口打开")
            
            # 终止进程
            process.terminate()
            time.sleep(1)
            if process.poll() is None:
                process.kill()
            
            return True
        else:
            # 进程已退出，检查错误
            stdout, stderr = process.communicate()
            print(f"❌ exe退出，返回码: {process.returncode}")
            if stdout:
                print(f"标准输出: {stdout}")
            if stderr:
                print(f"错误输出: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 启动exe时出错: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 YouTube Downloader exe测试")
    print("=" * 50)
    
    success = test_exe()
    
    print("=" * 50)
    if success:
        print("🎉 测试通过！exe文件可以正常启动")
        print("📝 建议手动测试GUI功能和下载功能")
    else:
        print("💥 测试失败！请检查错误信息")
    print("=" * 50)
