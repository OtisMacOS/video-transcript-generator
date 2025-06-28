# Video Transcript Generator + LLM Optimization (Multi-language Streamlit Version)

This project supports:
- Video file upload and automatic transcription (Whisper)
- LLM (e.g. OpenAI GPT) text optimization
- Multi-language interface (Chinese/English switch)
- Custom API Key and Base URL support
- Modern project structure for easy maintenance and extension

## Directory Structure

```
.
├── app.py                  # FastAPI main entry (optional)
├── streamlit_app.py        # Streamlit cloud deployment entry
├── requirements.txt        # Dependency list
├── README.md               # Project documentation
├── core/
│   ├── whisper_transcribe.py   # Video-to-audio + Whisper transcription core
│   ├── languages.py           # Multi-language texts and get_text utility
│   └── video_downloader.py    # (Optional) Video download tool
├── config/
│   └── sandbox_config.py      # Sandbox and security config
├── tests/
│   └── test_openai_key.py     # OpenAI Key test script
├── templates/
│   └── index.html             # Jinja2 template (if any)
└── ...  # Other files
```

## Dependency Installation

It is recommended to use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Quick Start (Streamlit)

```bash
streamlit run streamlit_app.py
```

- Visit http://localhost:8501 in your browser
- Supports Chinese/English UI switch
- Supports video file upload and transcription language selection
- Supports custom API Key and Base URL (OpenAI official or proxy)
- Supports LLM text optimization

## Main Features

- **Multi-language UI**: All UI texts are maintained in `core/languages.py` for easy extension and maintenance.
- **Video transcription**: Supports various video formats, automatically extracts audio and transcribes with Whisper model.
- **LLM optimization**: Supports mainstream LLMs such as OpenAI GPT, with customizable API Key and Base URL.
- **Security & Sandbox**: Optional security validation and sandbox config, see `config/sandbox_config.py`.

## FAQ

- **401 error**: Please ensure API Key and Base URL are correct and match the platform type (official/proxy). It is recommended to strip spaces after input.
- **Whisper model slow on first run**: The model will be downloaded automatically on first run, please wait patiently.
- **ffmpeg dependency**: You need to install the ffmpeg command-line tool locally (`brew install ffmpeg` on Mac, `sudo apt install ffmpeg` on Ubuntu).

## Contribution & Extension

- Contributions for more languages, UI improvements, and more LLMs are welcome.
- For Streamlit Cloud deployment, make sure `streamlit_app.py` is in the root directory and all dependencies are included.

---

If you have any questions, feel free to open an issue or PR!


# 视频转录生成器 + LLM 优化（多语言 Streamlit 版）

本项目支持：
- 视频文件上传与自动转录（Whisper）
- LLM（如OpenAI GPT）文本优化
- 多语言界面（中英文切换）
- 支持自定义API Key和Base URL
- 现代化项目结构，便于维护和扩展

## 目录结构

```
.
├── app.py                  # FastAPI 主入口（可选）
├── streamlit_app.py        # Streamlit 云部署入口
├── requirements.txt        # 依赖列表
├── README.md               # 项目说明
├── core/
│   ├── whisper_transcribe.py   # 视频转音频+Whisper转写核心
│   ├── languages.py           # 多语言文本与get_text工具
│   └── video_downloader.py    # （可选）视频下载工具
├── config/
│   └── sandbox_config.py      # 沙箱与安全配置
├── tests/
│   └── test_openai_key.py     # OpenAI Key测试脚本
├── templates/
│   └── index.html             # Jinja2模板（如有）
└── ...  # 其他文件
```

## 依赖安装

建议使用虚拟环境：

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 快速使用（Streamlit）

```bash
streamlit run streamlit_app.py
```

- 浏览器访问 http://localhost:8501
- 支持中英文界面切换
- 支持上传视频文件，选择转录语言
- 支持自定义API Key和Base URL（支持OpenAI官方或代理）
- 支持LLM文本优化

## 主要功能说明

- **多语言界面**：所有UI文本统一维护于`core/languages.py`，便于扩展和维护。
- **视频转录**：支持多种视频格式，自动提取音频并用Whisper模型转写。
- **LLM优化**：支持OpenAI GPT等主流大模型，API Key和Base URL可自定义。
- **安全与沙箱**：可选的安全校验与沙箱配置，详见`config/sandbox_config.py`。

## 常见问题

- **401错误**：请确认API Key和Base URL输入无误，且与平台类型匹配（官方/代理）。建议输入后自动去除空格。
- **Whisper模型首次加载慢**：首次运行会自动下载模型，耐心等待。
- **ffmpeg依赖**：需本地安装ffmpeg命令行工具（Mac可用`brew install ffmpeg`，Ubuntu可用`sudo apt install ffmpeg`）。

## 贡献与扩展

- 欢迎补充更多语言、优化UI、集成更多LLM。
- 如需部署到Streamlit Cloud，确保`streamlit_app.py`在根目录，依赖齐全。

---

如有问题欢迎提issue或PR！ 