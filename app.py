import os
import tempfile
import shutil
import logging
import time
from pathlib import Path
from typing import Optional
import ffmpeg
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from faster_whisper import WhisperModel
from languages import get_text, LANGUAGES
from sandbox_config import sandbox_manager, SandboxConfig

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="视频转录生成器 MVP", version="1.0.0")

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

class LLMResponse(BaseModel):
    """LLM润色响应模型"""
    original_text: str
    polished_text: str
    provider: str
    style: str
    processing_time: float
    sandbox_validation: dict

def generate_html(ui_lang="zh"):
    """生成多语言HTML页面"""
    t = lambda key: get_text(ui_lang, key)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{t('title')}</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .upload-area {{ border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }}
            .upload-area.dragover {{ border-color: #007bff; background-color: #f8f9fa; }}
            button {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
            button:hover {{ background: #0056b3; }}
            #result {{ margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; white-space: pre-wrap; }}
            .loading {{ display: none; color: #007bff; }}
            .language-select {{ margin: 20px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
            .log-container {{ margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 5px; font-family: monospace; font-size: 12px; max-height: 300px; overflow-y: auto; }}
            .log-entry {{ margin: 2px 0; }}
            .log-info {{ color: #007bff; }}
            .log-warning {{ color: #ffc107; }}
            .log-error {{ color: #dc3545; }}
            .ui-language {{ margin-bottom: 20px; padding: 10px; background: #e9ecef; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>🎬 {t('title')}</h1>
        <p>{t('subtitle')}</p>
        
        <div class="ui-language">
            <label for="uiLanguageSelect"><strong>界面语言 / UI Language:</strong></label>
            <select id="uiLanguageSelect" style="margin-left: 10px; padding: 5px;" onchange="changeUILanguage()">
                <option value="zh" {'selected' if ui_lang == 'zh' else ''}>中文</option>
                <option value="en" {'selected' if ui_lang == 'en' else ''}>English</option>
                <option value="ru" {'selected' if ui_lang == 'ru' else ''}>Русский</option>
                <option value="de" {'selected' if ui_lang == 'de' else ''}>Deutsch</option>
                <option value="fr" {'selected' if ui_lang == 'fr' else ''}>Français</option>
                <option value="ja" {'selected' if ui_lang == 'ja' else ''}>日本語</option>
            </select>
        </div>
        
        <div class="language-select">
            <label for="languageSelect"><strong>{t('select_language')}</strong></label>
            <select id="languageSelect" style="margin-left: 10px; padding: 5px;">
                <option value="auto">{t('auto_detect')}</option>
                <option value="zh">{t('chinese')}</option>
                <option value="en">{t('english')}</option>
                <option value="ru">{t('russian')}</option>
                <option value="de">{t('german')}</option>
                <option value="fr">{t('french')}</option>
                <option value="ja">{t('japanese')}</option>
            </select>
        </div>
        
        <div class="upload-area" id="uploadArea">
            <p>{t('upload_text')}</p>
            <input type="file" id="fileInput" accept="video/*" style="display: none;">
            <button onclick="document.getElementById('fileInput').click()">{t('select_file')}</button>
        </div>
        
        <div class="loading" id="loading">
            <p>⏳ {t('processing')}</p>
        </div>
        
        <div class="log-container" id="logContainer" style="display: none;">
            <h4>{t('log_title')}</h4>
            <div id="logContent"></div>
        </div>
        
        <div id="result"></div>
        
        <script>
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            const logContainer = document.getElementById('logContainer');
            const logContent = document.getElementById('logContent');
            const languageSelect = document.getElementById('languageSelect');
            const uiLanguageSelect = document.getElementById('uiLanguageSelect');
            
            function changeUILanguage() {{
                const newLang = uiLanguageSelect.value;
                window.location.href = `/?ui_lang=${{newLang}}`;
            }}
            
            function addLog(message, type = 'info') {{
                const timestamp = new Date().toLocaleTimeString();
                const logEntry = document.createElement('div');
                logEntry.className = `log-entry log-${{type}}`;
                logEntry.textContent = `[${{timestamp}}] ${{message}}`;
                logContent.appendChild(logEntry);
                logContent.scrollTop = logContent.scrollHeight;
            }}
            
            // 拖拽上传
            uploadArea.addEventListener('dragover', (e) => {{
                e.preventDefault();
                uploadArea.classList.add('dragover');
            }});
            
            uploadArea.addEventListener('dragleave', () => {{
                uploadArea.classList.remove('dragover');
            }});
            
            uploadArea.addEventListener('drop', (e) => {{
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {{
                    uploadFile(files[0]);
                }}
            }});
            
            fileInput.addEventListener('change', (e) => {{
                if (e.target.files.length > 0) {{
                    uploadFile(e.target.files[0]);
                }}
            }});
            
            async function uploadFile(file) {{
                const formData = new FormData();
                formData.append('file', file);
                formData.append('language', languageSelect.value);
                
                loading.style.display = 'block';
                result.innerHTML = '';
                logContainer.style.display = 'block';
                logContent.innerHTML = '';
                
                addLog(`${{getText('start_processing')}} ${{file.name}} (${{(file.size / 1024 / 1024).toFixed(2)}} MB)`, 'info');
                addLog(`${{getText('selected_language')}} ${{languageSelect.options[languageSelect.selectedIndex].text}}`, 'info');
                
                try {{
                    const response = await fetch('/transcribe', {{
                        method: 'POST',
                        body: formData
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok) {{
                        addLog(getText('transcription_complete'), 'info');
                        result.innerHTML = `
                            <h3>✅ ${{getText('transcription_complete')}}</h3>
                            <p><strong>${{getText('language')}}</strong> ${{data.language}}</p>
                            <p><strong>${{getText('transcription_content')}}</strong></p>
                            <div style="background: white; padding: 15px; border-radius: 5px; border: 1px solid #ddd;">
                                ${{data.text}}
                            </div>
                        `;
                    }} else {{
                        addLog(`${{getText('error')}} ${{data.detail}}`, 'error');
                        result.innerHTML = `<p style="color: red;">❌ ${{getText('error')}} ${{data.detail}}</p>`;
                    }}
                }} catch (error) {{
                    addLog(`${{getText('upload_failed')}} ${{error.message}}`, 'error');
                    result.innerHTML = `<p style="color: red;">❌ ${{getText('upload_failed')}} ${{error.message}}</p>`;
                }} finally {{
                    loading.style.display = 'none';
                }}
            }}
            
            // 多语言文本函数
            const texts = {{
                'zh': {{
                    'start_processing': '{t('start_processing')}',
                    'selected_language': '{t('selected_language')}',
                    'transcription_complete': '{t('transcription_complete')}',
                    'language': '{t('language')}',
                    'transcription_content': '{t('transcription_content')}',
                    'error': '{t('error')}',
                    'upload_failed': '{t('upload_failed')}'
                }},
                'en': {{
                    'start_processing': 'Start processing file:',
                    'selected_language': 'Selected language:',
                    'transcription_complete': 'Transcription complete!',
                    'language': 'Language:',
                    'transcription_content': 'Transcription content:',
                    'error': 'Error:',
                    'upload_failed': 'Upload failed:'
                }},
                'ru': {{
                    'start_processing': 'Начало обработки файла:',
                    'selected_language': 'Выбранный язык:',
                    'transcription_complete': 'Транскрипция завершена!',
                    'language': 'Язык:',
                    'transcription_content': 'Содержание транскрипции:',
                    'error': 'Ошибка:',
                    'upload_failed': 'Ошибка загрузки:'
                }},
                'de': {{
                    'start_processing': 'Dateiverarbeitung starten:',
                    'selected_language': 'Ausgewählte Sprache:',
                    'transcription_complete': 'Transkription abgeschlossen!',
                    'language': 'Sprache:',
                    'transcription_content': 'Transkriptionsinhalt:',
                    'error': 'Fehler:',
                    'upload_failed': 'Upload fehlgeschlagen:'
                }},
                'fr': {{
                    'start_processing': 'Début du traitement du fichier:',
                    'selected_language': 'Langue sélectionnée:',
                    'transcription_complete': 'Transcription terminée!',
                    'language': 'Langue:',
                    'transcription_content': 'Contenu de la transcription:',
                    'error': 'Erreur:',
                    'upload_failed': 'Échec du téléchargement:'
                }},
                'ja': {{
                    'start_processing': 'ファイル処理開始:',
                    'selected_language': '選択された言語:',
                    'transcription_complete': '文字起こし完了！',
                    'language': '言語:',
                    'transcription_content': '文字起こし内容:',
                    'error': 'エラー:',
                    'upload_failed': 'アップロード失敗:'
                }}
            }};
            
            function getText(key) {{
                const currentLang = uiLanguageSelect.value;
                return texts[currentLang] ? texts[currentLang][key] : texts['en'][key];
            }}
        </script>
    </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
async def read_root(ui_lang: str = Query("zh", description="界面语言")):
    """多语言HTML上传页面"""
    if ui_lang not in LANGUAGES:
        ui_lang = "zh"
    return generate_html(ui_lang)

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
async def polish_text(request: LLMRequest):
    """LLM文本润色接口（沙箱模式）"""
    
    start_time = time.time()
    logger.info(f"收到LLM润色请求: provider={request.provider}, style={request.style}")
    
    # 沙箱验证
    validation_result = sandbox_manager.validate_request(
        api_key=request.api_key,
        input_text=request.text
    )
    
    if not validation_result["valid"]:
        logger.error(f"沙箱验证失败: {validation_result['errors']}")
        raise HTTPException(
            status_code=400, 
            detail=f"安全验证失败: {', '.join(validation_result['errors'])}"
        )
    
    logger.info("沙箱验证通过，开始处理LLM请求")
    
    try:
        # 根据提供商调用不同的LLM API
        if request.provider == "openai":
            polished_text = await _call_openai_api(request)
        elif request.provider == "anthropic":
            polished_text = await _call_anthropic_api(request)
        elif request.provider == "google":
            polished_text = await _call_google_api(request)
        else:
            raise HTTPException(status_code=400, detail="不支持的LLM提供商")
        
        processing_time = time.time() - start_time
        
        # 记录沙箱审计日志
        sandbox_manager.log_request({
            "provider": request.provider,
            "input": request.text,
            "api_key": request.api_key,
            "style": request.style
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

async def _call_openai_api(request: LLMRequest) -> str:
    """调用OpenAI API"""
    import openai
    
    # 设置API密钥
    openai.api_key = request.api_key
    
    # 根据风格构建提示词
    if request.style == "polish":
        prompt = f"请润色以下文本，使其更加流畅自然：\n\n{request.text}"
    elif request.style == "summarize":
        prompt = f"请总结以下文本的主要内容：\n\n{request.text}"
    elif request.style == "translate":
        prompt = f"请将以下文本翻译成{request.target_language}：\n\n{request.text}"
    else:
        prompt = f"请处理以下文本：\n\n{request.text}"
    
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的文本处理助手。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
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