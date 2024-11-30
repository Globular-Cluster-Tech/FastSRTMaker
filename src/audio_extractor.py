import os
from moviepy.video.io.VideoFileClip import VideoFileClip
import subprocess

class AudioExtractor:
    def __init__(self):
        self.supported_formats = ['.mp4', '.mov', '.avi', '.mkv']
    
    def extract_audio(self, video_path: str) -> str:
        """从视频文件中提取音频"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 生成输出音频路径
        audio_path = os.path.splitext(video_path)[0] + '.wav'
        
        # 检查视频文件的音频流
        if not self._check_audio_stream(video_path):
            raise RuntimeError(f"视频文件 {video_path} 中没有有效的音频流")

        # 提取音频
        try:
            command = [
                'ffmpeg', '-i', video_path,
                '-vn',  # 不处理视频
                '-acodec', 'pcm_s16le',  # 音频编码为16位PCM
                '-ar', '16000',  # 采样率16kHz
                '-ac', '1',  # 单声道
                '-y',  # 覆盖已存在的文件
                audio_path
            ]
            subprocess.run(command, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"提取音频时出错: {e.stderr.decode()}")
        except Exception as e:
            raise RuntimeError(f"提取音频时出错: {e}")
        return audio_path

    def _check_audio_stream(self, video_path: str) -> bool:
        """检查视频文件是否包含有效的音频流"""
        if os.path.exists('/tmp/test.wav'):
            os.remove('/tmp/test.wav')
        command = ['ffmpeg', '-i', video_path, '-ar', '16000', '/tmp/test.wav']

        result = subprocess.run(command, capture_output=True, text=True, check=True)

        # 检查输出中是否包含音频流的信息
        if "Audio:" in result.stderr:
            return True
        else:
            # 输出错误信息以帮助调试
            print(f"音频流检查失败: {result.stderr}")
        return False