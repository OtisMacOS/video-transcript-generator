#!/usr/bin/env python3
"""
视频转录生成器 - 环境设置脚本
"""

import subprocess
import sys
import os
import venv
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python版本过低: {version.major}.{version.minor}")
        print("需要Python 3.8或更高版本")
        return False
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True

def create_virtual_environment():
    """创建虚拟环境"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ 虚拟环境已存在")
        return True
    
    print("📦 创建虚拟环境...")
    try:
        venv.create(venv_path, with_pip=True)
        print("✅ 虚拟环境创建成功")
        return True
    except Exception as e:
        print(f"❌ 虚拟环境创建失败: {e}")
        return False

def get_venv_python():
    """获取虚拟环境中的Python路径"""
    if os.name == 'nt':  # Windows
        return Path("venv/Scripts/python.exe")
    else:  # macOS/Linux
        return Path("venv/bin/python")

def get_venv_pip():
    """获取虚拟环境中的pip路径"""
    if os.name == 'nt':  # Windows
        return Path("venv/Scripts/pip.exe")
    else:  # macOS/Linux
        return Path("venv/bin/pip")

def install_requirements():
    """安装Python依赖"""
    print("📦 安装Python依赖...")
    
    venv_pip = get_venv_pip()
    
    try:
        # 升级pip
        subprocess.run([str(venv_pip), "install", "--upgrade", "pip"], check=True)
        print("✅ pip升级完成")
        
        # 安装依赖
        subprocess.run([str(venv_pip), "install", "-r", "requirements.txt"], check=True)
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def check_ffmpeg():
    """检查FFmpeg是否已安装"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg 已安装")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg 未安装")
        print("\n请安装 FFmpeg:")
        print("  macOS: brew install ffmpeg")
        print("  Ubuntu: sudo apt install ffmpeg")
        print("  Windows: 下载 https://ffmpeg.org/download.html")
        return False

def main():
    print("🚀 视频转录生成器 - 环境设置")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        return
    
    # 创建虚拟环境
    if not create_virtual_environment():
        return
    
    # 安装依赖
    if not install_requirements():
        return
    
    # 检查FFmpeg
    if not check_ffmpeg():
        print("\n⚠️  请先安装FFmpeg，然后重新运行此脚本")
        return
    
    print("\n🎉 环境设置完成！")
    print("=" * 50)
    print("下一步操作:")
    print("1. 激活虚拟环境:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # macOS/Linux
        print("   source venv/bin/activate")
    print("2. 启动应用:")
    print("   python app.py")
    print("3. 或者直接运行:")
    print("   python run.py")

if __name__ == "__main__":
    main() 