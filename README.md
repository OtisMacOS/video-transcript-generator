# 视频转录生成器 MVP

一个简单的视频转录工具，使用Whisper AI进行语音识别。

## 🎯 MVP功能

- 📹 视频文件上传
- 🎵 自动音频提取
- 🤖 Whisper语音识别
- 📝 文字转录显示

## 🆓 免费运行方案

### Whisper运行位置
1. **本地运行** (推荐) - 完全免费，无需API费用
2. **Hugging Face** - 免费GPU资源
3. **Google Colab** - 免费GPU，有时间限制

## 🚀 快速开始

### 1. 安装FFmpeg
```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt install ffmpeg

# Windows
# 下载 https://ffmpeg.org/download.html
```

### 2. 运行项目
```bash
# 方法1: 使用启动脚本
python run.py

# 方法2: 手动启动
pip install -r requirements.txt
python app.py
```

### 3. 访问网站
打开浏览器访问: http://localhost:8000

## 📁 项目结构
```
├── app.py              # 主应用文件
├── run.py              # 启动脚本
├── requirements.txt    # Python依赖
└── README.md          # 说明文档
```

## 🛠️ 技术栈
- **FastAPI** - Web框架
- **Faster-Whisper** - 语音识别
- **FFmpeg** - 音频提取
- **HTML/JS** - 前端界面

## 📝 使用说明
1. 打开网站
2. 拖拽或选择视频文件
3. 等待处理完成
4. 查看转录结果

## 🔧 配置选项
在 `app.py` 中可以调整：
- Whisper模型大小 (tiny/base/small/medium/large)
- 文件大小限制
- 音频质量设置

## 🚀 后续扩展
- 用户认证
- 文件存储
- LLM内容优化
- 多语言支持
- 导出功能 