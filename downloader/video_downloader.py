import os
import tempfile
import yt_dlp
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class VideoDownloader:
    """视频下载器，支持YouTube和Bilibili"""
    
    def __init__(self):
        self.supported_platforms = {
            'youtube': ['youtube.com', 'youtu.be'],
            'bilibili': ['bilibili.com', 'b23.tv']
        }
    
    def detect_platform(self, url):
        """检测视频平台"""
        url_lower = url.lower()
        for platform, domains in self.supported_platforms.items():
            if any(domain in url_lower for domain in domains):
                return platform
        return None
    
    def download_youtube(self, url, output_dir):
        """下载YouTube视频"""
        ydl_opts = {
            'format': 'best[height<=720]',  # 限制质量
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"开始下载YouTube视频: {url}")
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)
                logger.info(f"YouTube视频下载完成: {video_path}")
                return video_path
        except Exception as e:
            logger.error(f"YouTube下载失败: {str(e)}")
            raise
    
    def download_bilibili(self, url, output_dir):
        """下载Bilibili视频（需要额外实现）"""
        # 这里需要实现Bilibili下载逻辑
        # 可以使用 bilibili-api-python 库
        logger.warning("Bilibili下载功能需要额外实现")
        raise NotImplementedError("Bilibili下载功能暂未实现")
    
    def download_video(self, url, output_dir=None):
        """通用视频下载接口"""
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        
        platform = self.detect_platform(url)
        if not platform:
            raise ValueError(f"不支持的视频平台: {url}")
        
        if platform == 'youtube':
            return self.download_youtube(url, output_dir)
        elif platform == 'bilibili':
            return self.download_bilibili(url, output_dir)
        else:
            raise ValueError(f"不支持的平台: {platform}")

# 使用示例
if __name__ == "__main__":
    downloader = VideoDownloader()
    
    # 测试YouTube链接
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    try:
        video_path = downloader.download_video(youtube_url)
        print(f"下载成功: {video_path}")
    except Exception as e:
        print(f"下载失败: {e}") 