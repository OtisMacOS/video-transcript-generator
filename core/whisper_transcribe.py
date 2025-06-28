import tempfile
from pathlib import Path
import ffmpeg
from faster_whisper import WhisperModel
import logging

def whisper_transcribe(video_path: str, language: str = "auto") -> str:
    """
    输入视频文件路径，返回转录文本。language为'auto'时自动检测，否则指定语言。
    """
    logger = logging.getLogger(__name__)
    # 1. 提取音频
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        audio_path = temp_path / "audio.wav"
        try:
            stream = ffmpeg.input(str(video_path))
            stream = ffmpeg.output(stream, str(audio_path), acodec='pcm_s16le', ac=1, ar='16000')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
        except Exception as e:
            logger.error(f"音频提取失败: {str(e)}")
            raise RuntimeError(f"音频提取失败: {str(e)}")

        # 2. 加载Whisper模型
        try:
            model = WhisperModel("tiny", device="cpu", compute_type="int8")
            transcribe_params = {}
            if language != "auto":
                transcribe_params["language"] = language
            segments, info = model.transcribe(str(audio_path), **transcribe_params)
            text = " ".join([seg.text.strip() for seg in segments if seg.text.strip()])
            return text
        except Exception as e:
            logger.error(f"Whisper转录失败: {str(e)}")
            raise RuntimeError(f"Whisper转录失败: {str(e)}") 