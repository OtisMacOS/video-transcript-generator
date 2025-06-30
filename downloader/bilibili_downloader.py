import os
from pathlib import Path
import yt_dlp

class BilibiliDownloader:
    def __init__(self, download_path="downloads"):
        self.download_path = Path(download_path)
        self.download_path.mkdir(exist_ok=True)

    def download_video(self, url):
        ydl_opts = {
            'outtmpl': str(self.download_path / '%(title)s.%(ext)s'),
            'progress_hooks': [self._progress_hook],
            'merge_output_format': 'mp4'
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"开始下载: {url}")
                ydl.download([url])
            print("下载完成！")
            return True
        except Exception as e:
            print(f"下载失败: {str(e)}")
            return False

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            if 'total_bytes' in d:
                percent = d['downloaded_bytes'] / d['total_bytes'] * 100
                print(f"\r下载进度: {percent:.1f}%", end='', flush=True)
            elif 'downloaded_bytes' in d:
                print(f"\r已下载: {d['downloaded_bytes']} bytes", end='', flush=True)
        elif d['status'] == 'finished':
            print(f"\n文件下载完成: {d['filename']}")

def main():
    downloader = BilibiliDownloader()
    print("=== Bilibili视频下载器 ===")
    while True:
        url = input("请输入Bilibili视频URL（或输入q退出）: ").strip()
        if url.lower() == 'q':
            print("再见！")
            break
        if url:
            downloader.download_video(url)
        else:
            print("URL不能为空！")

if __name__ == "__main__":
    main()