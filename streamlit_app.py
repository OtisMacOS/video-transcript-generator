import streamlit as st
from openai import OpenAI
from core.whisper_transcribe import whisper_transcribe
from core.languages import LANGUAGES, get_text
import tempfile
import time

# 选择界面语言
lang = st.selectbox("Language / 语言", options=["zh", "en"], format_func=lambda x: "中文" if x == "zh" else "English")

st.title(get_text(lang, "title"))

# 选择视频转录语言
transcribe_lang = st.selectbox(
    get_text(lang, "transcribe_lang"),
    options=list(LANGUAGES.keys()),
    format_func=lambda x: LANGUAGES[x]["language_name"] if "language_name" in LANGUAGES[x] else x
)

# 上传视频
video_file = st.file_uploader(get_text(lang, "upload"), type=["mp4", "mov", "avi", "mkv"])
if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video_file.read())
        video_path = tmp.name

    # 转录
    st.info(get_text(lang, "transcribing"))
    progress_bar = st.progress(0)
    text = None
    try:
        for percent in range(0, 100, 10):
            time.sleep(0.1)
            progress_bar.progress(percent)
        text = whisper_transcribe(video_path, language=transcribe_lang)
        progress_bar.progress(100)
        st.success(get_text(lang, "transcribe_success"))
        st.text_area(get_text(lang, "transcribed_text"), value=text, height=200)
    except Exception as e:
        st.error(f"{get_text(lang, 'transcribe_fail')}{e}")
        text = None

    # LLM优化
    if text:
        api_key = st.text_input(get_text(lang, "api_key"), type="password")
        base_url = st.text_input(get_text(lang, "base_url"), value="https://api.openai.com/v1")
        api_key = api_key.strip()
        base_url = base_url.strip()
        if st.button(get_text(lang, "llm_btn")):
            client = OpenAI(api_key=api_key, base_url=base_url)
            try:
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "你是一个有用的助手。" if lang == "zh" else "You are a helpful assistant."},
                        {"role": "user", "content": text}
                    ]
                )
                st.success(get_text(lang, "llm_success"))
                st.write(completion.choices[0].message.content)
            except Exception as e:
                st.error(f"{get_text(lang, 'llm_fail')}{e}")
