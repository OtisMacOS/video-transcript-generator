#!/usr/bin/env python3
"""
YouTube视频下载器
使用yt-dlp包从YouTube下载最高画质视频或音频
"""

import os
from pathlib import Path
import yt_dlp

class YouTubeDownloader:
    def __init__(self, download_path="downloads"):
        self.download_path = Path(download_path)
        self.download_path.mkdir(exist_ok=True)

    def download_video(self, url, audio_only=False):
        try:
            ydl_opts = {
                'outtmpl': str(self.download_path / '%(title)s.%(ext)s'),
                'progress_hooks': [self._progress_hook],
            }
            if audio_only:
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
            else:
                # 总是优先下载最高画质（合并音视频）
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
                ydl_opts['merge_output_format'] = 'mp4'
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

    def get_video_info(self, url):
        try:
            with yt_dlp.YoutubeDL() as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'view_count': info.get('view_count'),
                    'formats': [f['format_id'] for f in info.get('formats', [])]
                }
        except Exception as e:
            print(f"获取视频信息失败: {str(e)}")
            return None

def main():
    downloader = YouTubeDownloader()
    print("=== YouTube视频下载器 ===")
    print("1. 下载视频（总是最高画质）")
    print("2. 只下载音频")
    print("3. 获取视频信息")
    print("4. 退出")
    while True:
        choice = input("\n请选择操作 (1-4): ").strip()
        if choice == '4':
            print("再见！")
            break
        if choice in ['1', '2', '3']:
            url = input("请输入YouTube视频URL: ").strip()
            if not url:
                print("URL不能为空！")
                continue
            if choice == '1':
                downloader.download_video(url)
            elif choice == '2':
                downloader.download_video(url, audio_only=True)
            elif choice == '3':
                info = downloader.get_video_info(url)
                if info:
                    print(f"\n视频标题: {info['title']}")
                    print(f"上传者: {info['uploader']}")
                    print(f"时长: {info['duration']}秒")
                    print(f"观看次数: {info['view_count']}")
        else:
            print("无效选择，请重新输入！")

if __name__ == "__main__":
    main()