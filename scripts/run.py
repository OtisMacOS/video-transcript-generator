#!/usr/bin/env python3
"""
视频转录生成器 MVP 启动脚本
"""

import subprocess
import sys
import os
from pathlib import Path

def get_venv_python():
    """获取虚拟环境中的Python路径"""
    if os.name == 'nt':  # Windows
        return Path("venv/Scripts/python.exe")
    else:  # macOS/Linux
        return Path("venv/bin/python")

def check_virtual_environment():
    """检查虚拟环境是否存在"""
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("❌ 虚拟环境不存在")
        print("请先运行: python setup.py")
        return False
    print("✅ 虚拟环境已就绪")
    return True

def check_ffmpeg():
    """检查FFmpeg是否已安装"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg 已安装")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg 未安装")
        print("请安装 FFmpeg:")
        print("  macOS: brew install ffmpeg")
        print("  Ubuntu: sudo apt install ffmpeg")
        print("  Windows: 下载 https://ffmpeg.org/download.html")
        return False

def install_requirements():
    """安装Python依赖"""
    print("📦 安装Python依赖...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def main():
    print("🚀 启动视频转录生成器 MVP")
    print("=" * 50)
    
    # 检查虚拟环境
    if not check_virtual_environment():
        return
    
    # 检查FFmpeg
    if not check_ffmpeg():
        return
    
    # 安装依赖
    if not install_requirements():
        return
    
    print("\n🎯 启动服务器...")
    print("📱 访问地址: http://localhost:8000")
    print("⏹️  按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    # 使用虚拟环境中的Python启动服务器
    venv_python = get_venv_python()
    try:
        subprocess.run([str(venv_python), 'app.py'])
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")

if __name__ == "__main__":
    main() 