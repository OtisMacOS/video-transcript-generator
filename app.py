import os
import tempfile
import shutil
import logging
import time
from pathlib import Path
from typing import Optional
import ffmpeg
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from faster_whisper import WhisperModel
from core.languages import get_text, LANGUAGES
from config.sandbox_config import sandbox_manager, SandboxConfig
from starlette.concurrency import run_in_threadpool

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="视频转录生成器 MVP", version="1.0.0")

# 配置模板引擎
templates = Jinja2Templates(directory="templates")

# 配置Whisper模型
# 可选模型: tiny, base, small, medium, large
WHISPER_MODEL = "tiny"  # 使用tiny模型，速度更快
logger.info(f"正在加载Whisper模型: {WHISPER_MODEL}")
model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
logger.info("Whisper模型加载完成")

class TranscriptResponse(BaseModel):
    text: str
    segments: list
    language: str

class LLMRequest(BaseModel):
    """LLM润色请求模型"""
    text: str
    api_key: str
    provider: str = "openai"  # openai, anthropic, google
    style: str = "polish"  # polish, summarize, translate
    target_language: str = "zh"
    base_url: Optional[str] = None

class LLMResponse(BaseModel):
    """LLM润色响应模型"""
    original_text: str
    polished_text: str
    provider: str
    style: str
    processing_time: float
    sandbox_validation: dict

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, ui_lang: str = Query("zh", description="界面语言")):
    """多语言HTML上传页面"""
    if ui_lang not in LANGUAGES:
        ui_lang = "zh"
    
    # 准备模板变量
    template_vars = {
        "request": request,
        "ui_lang": ui_lang,
        "title": get_text(ui_lang, "title"),
        "subtitle": get_text(ui_lang, "subtitle"),
        "select_language": get_text(ui_lang, "select_language"),
        "auto_detect": get_text(ui_lang, "auto_detect"),
        "chinese": get_text(ui_lang, "chinese"),
        "english": get_text(ui_lang, "english"),
        "russian": get_text(ui_lang, "russian"),
        "german": get_text(ui_lang, "german"),
        "french": get_text(ui_lang, "french"),
        "japanese": get_text(ui_lang, "japanese"),
        "upload_text": get_text(ui_lang, "upload_text"),
        "select_file": get_text(ui_lang, "select_file"),
        "processing": get_text(ui_lang, "processing"),
        "log_title": get_text(ui_lang, "log_title"),
        "start_processing": get_text(ui_lang, "start_processing"),
        "selected_language": get_text(ui_lang, "selected_language"),
        "transcription_complete": get_text(ui_lang, "transcription_complete"),
        "language": get_text(ui_lang, "language"),
        "transcription_content": get_text(ui_lang, "transcription_content"),
        "error": get_text(ui_lang, "error"),
        "upload_failed": get_text(ui_lang, "upload_failed"),
        "llm_section_title": get_text(ui_lang, "llm_section_title"),
        "llm_provider_label": get_text(ui_lang, "llm_provider_label"),
        "llm_style_label": get_text(ui_lang, "llm_style_label"),
        "llm_api_key_label": get_text(ui_lang, "llm_api_key_label"),
        "llm_api_key_placeholder": get_text(ui_lang, "llm_api_key_placeholder"),
        "llm_target_language_label": get_text(ui_lang, "llm_target_language_label"),
        "llm_polish": get_text(ui_lang, "llm_polish"),
        "llm_summarize": get_text(ui_lang, "llm_summarize"),
        "llm_translate": get_text(ui_lang, "llm_translate"),
        "llm_openai": get_text(ui_lang, "llm_openai"),
        "llm_anthropic": get_text(ui_lang, "llm_anthropic"),
        "llm_google": get_text(ui_lang, "llm_google"),
        "llm_optimize_button": get_text(ui_lang, "llm_optimize_button"),
        "llm_optimizing": get_text(ui_lang, "llm_optimizing"),
        "llm_optimize_complete": get_text(ui_lang, "llm_optimize_complete"),
        "llm_original_text": get_text(ui_lang, "llm_original_text"),
        "llm_optimized_text": get_text(ui_lang, "llm_optimized_text"),
        "llm_processing_time": get_text(ui_lang, "llm_processing_time"),
        "llm_provider": get_text(ui_lang, "llm_provider"),
        "llm_style": get_text(ui_lang, "llm_style"),
        "llm_sandbox_validation": get_text(ui_lang, "llm_sandbox_validation"),
        "llm_validation_passed": get_text(ui_lang, "llm_validation_passed"),
        "llm_validation_failed": get_text(ui_lang, "llm_validation_failed"),
        "llm_api_key_required": get_text(ui_lang, "llm_api_key_required"),
        "llm_text_required": get_text(ui_lang, "llm_text_required"),
        "llm_optimize_failed": get_text(ui_lang, "llm_optimize_failed"),
        "llm_copy_button": get_text(ui_lang, "llm_copy_button"),
        "llm_download_button": get_text(ui_lang, "llm_download_button")
    }
    
    return templates.TemplateResponse("index.html", template_vars)

@app.post("/transcribe", response_model=TranscriptResponse)
async def transcribe_video(file: UploadFile = File(...), language: str = Form("auto")):
    """视频转录接口"""
    
    # 定义日志函数（这里只是占位符，实际日志会通过WebSocket或SSE发送）
    def addLog(message, level='info'):
        logger.info(f"[WEB] {message}")
    
    start_time = time.time()
    logger.info(f"收到文件上传请求: {file.filename}, 大小: {file.size} bytes, 语言: {language}")
    
    # 检查文件类型
    if not file.content_type.startswith('video/'):
        logger.error(f"不支持的文件类型: {file.content_type}")
        raise HTTPException(status_code=400, detail="只支持视频文件")
    
    # 检查文件大小 (限制为100MB)
    if file.size > 100 * 1024 * 1024:
        logger.error(f"文件过大: {file.size} bytes")
        raise HTTPException(status_code=400, detail="文件大小不能超过100MB")
    
    # 验证语言参数
    valid_languages = ["auto", "zh", "en", "ru", "de", "fr", "ja"]
    if language not in valid_languages:
        logger.error(f"不支持的语言: {language}")
        raise HTTPException(status_code=400, detail="不支持的语言")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        logger.info(f"创建临时目录: {temp_path}")
        
        # 保存上传的视频文件
        video_path = temp_path / f"input{Path(file.filename).suffix}"
        logger.info(f"保存视频文件到: {video_path}")
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 提取音频
        audio_path = temp_path / "audio.wav"
        logger.info("开始提取音频...")
        addLog("开始提取音频...", 'info')
        audio_start = time.time()
        try:
            stream = ffmpeg.input(str(video_path))
            stream = ffmpeg.output(stream, str(audio_path), acodec='pcm_s16le', ac=1, ar='16000')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            audio_time = time.time() - audio_start
            logger.info(f"音频提取完成: {audio_path}, 耗时: {audio_time:.2f}秒")
            addLog(f"音频提取完成，耗时: {audio_time:.2f}秒", 'info')
        except Exception as e:
            logger.error(f"音频提取失败: {str(e)}")
            addLog(f"音频提取失败: {str(e)}", 'error')
            raise HTTPException(status_code=500, detail=f"音频提取失败: {str(e)}")
        
        # 使用Whisper转录
        logger.info("开始语音识别...")
        addLog("开始语音识别...", 'info')
        whisper_start = time.time()
        try:
            # 准备转录参数
            transcribe_params = {
                'beam_size': 5,
                'vad_filter': True,
                'vad_parameters': dict(min_silence_duration_ms=500),
                'word_timestamps': True,
                'condition_on_previous_text': False,
                'initial_prompt': None
            }
            
            # 如果指定了语言，添加到参数中
            if language != "auto":
                transcribe_params['language'] = language
                logger.info(f"使用指定语言: {language}")
                addLog(f"使用指定语言: {language}", 'info')
            else:
                logger.info("使用自动语言检测")
                addLog("使用自动语言检测", 'info')
            
            addLog("正在加载Whisper模型...", 'info')
            segments, info = model.transcribe(str(audio_path), **transcribe_params)
            whisper_time = time.time() - whisper_start
            logger.info(f"识别完成，语言: {info.language}, 耗时: {whisper_time:.2f}秒")
            addLog(f"语音识别完成，检测到语言: {info.language}, 耗时: {whisper_time:.2f}秒", 'info')
            
            # 收集转录结果，添加去重逻辑
            text_segments = []
            full_text = ""
            seen_texts = set()  # 用于去重
            processed_segments = 0
            skipped_segments = 0
            
            addLog("开始处理转录结果...", 'info')
            for segment in segments:
                processed_segments += 1
                segment_text = segment.text.strip()
                
                # 跳过空文本或重复文本
                if not segment_text or segment_text in seen_texts:
                    skipped_segments += 1
                    continue
                
                # 跳过过长的重复模式（如 "livin' livin' livin'..."）
                if len(segment_text.split()) > 50:  # 如果单段超过50个词
                    words = segment_text.split()
                    # 检查是否有重复模式
                    if len(set(words)) < len(words) * 0.3:  # 如果重复词超过70%
                        logger.warning(f"跳过重复模式文本: {segment_text[:100]}...")
                        addLog(f"跳过重复模式文本: {segment_text[:100]}...", 'warning')
                        skipped_segments += 1
                        continue
                
                seen_texts.add(segment_text)
                text_segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment_text
                })
                full_text += segment_text + " "
            
            addLog(f"处理完成: 总段数 {processed_segments}, 有效段数 {len(text_segments)}, 跳过段数 {skipped_segments}", 'info')
            
            # 清理最终文本
            full_text = full_text.strip()
            addLog("开始清理文本...", 'info')
            
            # 移除重复的短语
            words = full_text.split()
            cleaned_words = []
            removed_duplicates = 0
            for i, word in enumerate(words):
                # 检查是否与前一个词相同
                if i > 0 and word == words[i-1]:
                    removed_duplicates += 1
                    continue
                cleaned_words.append(word)
            
            full_text = " ".join(cleaned_words)
            addLog(f"文本清理完成，移除了 {removed_duplicates} 个重复单词", 'info')
            
            total_time = time.time() - start_time
            logger.info(f"转录完成，总长度: {len(full_text)} 字符, 总耗时: {total_time:.2f}秒")
            logger.info(f"处理了 {len(text_segments)} 个音频段")
            addLog(f"转录完成！总字符数: {len(full_text)}, 总耗时: {total_time:.2f}秒", 'info')
            addLog(f"最终处理了 {len(text_segments)} 个有效音频段", 'info')
            
            return TranscriptResponse(
                text=full_text,
                segments=text_segments,
                language=info.language
            )
            
        except Exception as e:
            logger.error(f"转录失败: {str(e)}")
            addLog(f"转录失败: {str(e)}", 'error')
            raise HTTPException(status_code=500, detail=f"转录失败: {str(e)}")

@app.post("/polish", response_model=LLMResponse)
def polish_text(request: LLMRequest):
    start_time = time.time()
    logger.info(f"收到LLM润色请求: provider={request.provider}, style={request.style}, base_url={request.base_url}")

    validation_result = sandbox_manager.validate_request(
        api_key=request.api_key,
        input_text=request.text
    )
    if not validation_result["valid"]:
        logger.warning(f"沙箱校验警告: {validation_result['errors']}")

    try:
        if request.provider == "openai":
            polished_text = _call_openai_api(request)
        elif request.provider == "anthropic":
            polished_text = _call_anthropic_api(request)
        elif request.provider == "google":
            polished_text = _call_google_api(request)
        else:
            raise HTTPException(status_code=400, detail="不支持的LLM提供商")

        processing_time = time.time() - start_time

        sandbox_manager.log_request({
            "provider": request.provider,
            "input": request.text,
            "api_key": request.api_key,
            "style": request.style,
            "base_url": request.base_url
        })

        logger.info(f"LLM润色完成，耗时: {processing_time:.2f}秒")

        return LLMResponse(
            original_text=request.text,
            polished_text=polished_text,
            provider=request.provider,
            style=request.style,
            processing_time=processing_time,
            sandbox_validation=validation_result
        )

    except Exception as e:
        logger.error(f"LLM润色失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM润色失败: {str(e)}")

def _call_openai_api(request: LLMRequest) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=request.api_key,
        base_url=request.base_url if request.base_url else None
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个有用的助手。"},
                {"role": "user", "content": request.text}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API调用失败: {str(e)}")
        raise Exception(f"OpenAI API错误: {str(e)}")

async def _call_anthropic_api(request: LLMRequest) -> str:
    """调用Anthropic API"""
    import anthropic
    
    client = anthropic.Anthropic(api_key=request.api_key)
    
    # 构建提示词
    if request.style == "polish":
        prompt = f"请润色以下文本，使其更加流畅自然：\n\n{request.text}"
    elif request.style == "summarize":
        prompt = f"请总结以下文本的主要内容：\n\n{request.text}"
    elif request.style == "translate":
        prompt = f"请将以下文本翻译成{request.target_language}：\n\n{request.text}"
    else:
        prompt = f"请处理以下文本：\n\n{request.text}"
    
    try:
        response = await client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text.strip()
        
    except Exception as e:
        logger.error(f"Anthropic API调用失败: {str(e)}")
        raise Exception(f"Anthropic API错误: {str(e)}")

async def _call_google_api(request: LLMRequest) -> str:
    """调用Google AI API"""
    import google.generativeai as genai
    
    genai.configure(api_key=request.api_key)
    model = genai.GenerativeModel('gemini-pro')
    
    # 构建提示词
    if request.style == "polish":
        prompt = f"请润色以下文本，使其更加流畅自然：\n\n{request.text}"
    elif request.style == "summarize":
        prompt = f"请总结以下文本的主要内容：\n\n{request.text}"
    elif request.style == "translate":
        prompt = f"请将以下文本翻译成{request.target_language}：\n\n{request.text}"
    else:
        prompt = f"请处理以下文本：\n\n{request.text}"
    
    try:
        response = await model.generate_content_async(prompt)
        return response.text.strip()
        
    except Exception as e:
        logger.error(f"Google AI API调用失败: {str(e)}")
        raise Exception(f"Google AI API错误: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 