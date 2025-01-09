import os
import subprocess
import json
import opencc
from typing import Dict, List
from pathlib import Path
import pysrt
import tempfile
from src import logger


class WhisperSubtitleGenerator:
    def __init__(self, languages=None):
        """
        初始化字幕生成器
        :param translator: 翻译器实例
        :param config: Whisper 配置字典
        """
        logger.debug("初始化字幕生成器")

        self.cc = opencc.OpenCC("s2t")  # 创建 OpenCC 实例用于简体到繁体转换
        self.languages = languages or []

    def get_media_info(self, input_path: str) -> dict:
        """获取媒体文件信息"""
        try:
            # 检查文件是否存在
            if not Path(input_path).exists():
                raise FileNotFoundError(f"文件不存在: {input_path}")
            
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(input_path)  # 确保路径是字符串
            ]
            
            # 检查 ffprobe 是否可用
            try:
                subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.error("ffprobe 未安装或不可用")
                return {}
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            try:
                probe_data = json.loads(result.stdout)
            except json.JSONDecodeError:
                logger.error("解析媒体信息失败")
                return {}
            
            # 基本信息
            format_info = probe_data.get('format', {})
            if not format_info:
                logger.error("无法获取媒体格式信息")
                return {}
            
            # 安全地获取数值，提供默认值
            try:
                duration = float(format_info.get('duration', '0'))
            except (TypeError, ValueError):
                duration = 0.0
            
            try:
                size = int(format_info.get('size', '0'))
            except (TypeError, ValueError):
                size = 0
            
            try:
                bit_rate = int(format_info.get('bit_rate', '0'))
            except (TypeError, ValueError):
                bit_rate = 0
            
            info = {
                'filename': Path(input_path).name,
                'format': format_info.get('format_name', 'unknown'),
                'duration': duration,
                'size': size,
                'bit_rate': bit_rate,
                'streams': []
            }
            
            # 流信息
            for stream in probe_data.get('streams', []):
                stream_info = {
                    'codec_type': stream.get('codec_type', 'unknown'),
                    'codec_name': stream.get('codec_name', 'unknown'),
                }
                
                # 视频流特有信息
                if stream.get('codec_type') == 'video':
                    fps = stream.get('r_frame_rate', '0/1').split('/')
                    try:
                        fps = float(fps[0]) / float(fps[1]) if len(fps) == 2 else 0
                    except (ValueError, ZeroDivisionError, TypeError):
                        fps = 0
                    
                    try:
                        width = int(stream.get('width', '0'))
                    except (TypeError, ValueError):
                        width = 0
                    
                    try:
                        height = int(stream.get('height', '0'))
                    except (TypeError, ValueError):
                        height = 0
                    
                    stream_info.update({
                        'width': width,
                        'height': height,
                        'fps': round(fps, 2)
                    })
                
                # 音频流特有信息
                elif stream.get('codec_type') == 'audio':
                    try:
                        channels = int(stream.get('channels', '0'))
                    except (TypeError, ValueError):
                        channels = 0
                    
                    stream_info.update({
                        'sample_rate': stream.get('sample_rate', '0'),
                        'channels': channels
                    })
                
                info['streams'].append(stream_info)
            
            return info
            
        except Exception as e:
            logger.error(f"获取媒体信息失败: {str(e)}")
            return {
                'filename': Path(input_path).name,
                'format': 'unknown',
                'duration': 0.0,
                'size': 0,
                'bit_rate': 0,
                'streams': []
            }

    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"

    def format_time(self, seconds: float) -> str:
        """格式化时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def log_media_info(self, media_info: dict):
        """输出媒体信息日志"""
        if not media_info:
            return

        # 分隔线
        separator = "-" * 50
        logger.info(separator)
        logger.info("媒体文件信息:")
        logger.info(f"文件名: {media_info['filename']}")
        logger.info(f"格式: {media_info['format']}")
        logger.info(f"时长: {self.format_time(media_info['duration'])}")
        logger.info(f"大小: {self.format_size(media_info['size'])}")
        logger.info(f"比特率: {media_info['bit_rate'] // 1000} kbps")
        
        # 输出流信息
        for stream in media_info['streams']:
            if stream['codec_type'] == 'video':
                logger.info(f"视频流: {stream['codec_name']} "
                          f"{stream['width']}x{stream['height']} "
                          f"@ {stream['fps']:.2f}fps")
            elif stream['codec_type'] == 'audio':
                logger.info(f"音频流: {stream['codec_name']} "
                          f"{stream['sample_rate']}Hz "
                          f"{stream['channels']}ch")
        logger.info(separator)

    def generate_subtitles(self, input_path: str, device_id: str, model_name: str):
        """生成字幕文件"""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"文件不存在: {input_path}")

        media_info = self.get_media_info(input_path)
        self.log_media_info(media_info)

        output_dir = os.path.dirname(input_path)
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        
        json_path = os.path.join(output_dir, f"{base_name}.json")

        command = [
            'insanely-fast-whisper', 
            '--file-name', input_path,
            "--device-id", device_id,
            "--model-name", model_name,
            '--transcript-path', json_path
        ]

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"生成字幕失败: {result.stderr}")

        srt_path = os.path.join(output_dir, f"{base_name}.srt")
        
        self._json_to_srt(json_path, srt_path)
        
        if os.path.exists(json_path):
            os.remove(json_path)

        return {"subtitle": srt_path}

    def process_subtitle_file(self, subtitle_path: str, output_dir: str, device_id: str = "mps", model_name: str = "large-v3-turbo"):
        """处理字幕文件并生成多语言翻译"""
        from .translator import Translator
        
        if not os.path.exists(subtitle_path):
            raise FileNotFoundError(f"字幕文件不存在: {subtitle_path}")

        if self.translator is None:
            self.translator = Translator(languages=self.languages)

        base_name = os.path.splitext(os.path.basename(subtitle_path))[0]

        # 加载字幕内容
        if subtitle_path.endswith('.json'):
            chunks = self._load_json_chunks(subtitle_path)
        else:
            chunks = self._load_srt_chunks(subtitle_path)

        # 生成基础字幕
        translated_chunks = {
            "simplified": self._convert_to_simplified(chunks),
            "traditional": self._convert_to_traditional(chunks)
        }

        # 为每个配置的语言生成翻译
        for lang in self.languages:
            translated_chunks[lang["name"]] = self._translate_chunks(
                chunks, 
                lang["code"]
            )

        # 生成输出文件路径
        subtitle_paths = {
            "simplified": os.path.join(output_dir, f"{base_name}_zh.srt"),
            "traditional": os.path.join(output_dir, f"{base_name}_zh_hant.srt")
        }

        # 添加其他语言的输出路径
        for lang in self.languages:
            subtitle_paths[lang["name"]] = os.path.join(
                output_dir, 
                f"{base_name}_{lang['code']}.srt"
            )

        # 保存所有翻译
        for name, chunks in translated_chunks.items():
            self._save_chunks_to_srt(chunks, subtitle_paths[name])

        return subtitle_paths

    def _json_to_srt(self, json_path: str, srt_path: str):
        """将JSON格式转换为SRT格式"""
        with open(json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        chunks = json_data.get("chunks", [])
        if not chunks:
            logger.warning("JSON数据中未找到字幕块")
            return

        self._save_chunks_to_srt(chunks, srt_path)

    def _format_time(self, seconds):
        """格式化时间为SRT格式"""
        millis = int((seconds - int(seconds)) * 1000)
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

    def _load_json_chunks(self, json_file_path):
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        return json_data.get("chunks", [])

    def _load_srt_chunks(self, srt_file_path):
        chunks = []
        with open(srt_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            if lines[i].strip().isdigit():
                i += 1
                time_line = lines[i].strip()
                start_end = time_line.split(' --> ')
                start_time = self._parse_time(start_end[0])
                end_time = self._parse_time(start_end[1])
                i += 1
                text = lines[i].strip()
                chunks.append({
                    "timestamp": [start_time, end_time],
                    "text": text
                })
                i += 2
            else:
                i += 1
        return chunks

    def _parse_time(self, time_str):
        """将 SRT 时间字符串转换为秒数"""
        h, m, s = time_str.replace(',', '.').split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)

    def _convert_to_traditional(self, chunks):
        return [{
            "timestamp": chunk["timestamp"],
            "text": self.cc.convert(chunk["text"])
        } for chunk in chunks]

    def _convert_to_simplified(self, chunks):
        return chunks

    def _translate_chunks(self, chunks: List[Dict], target_lang: str) -> List[Dict]:
        """翻译字幕块"""
        logger.debug(f"开始翻译字幕块，目标语言: {target_lang}")
        translated_chunks = []
        
        for i, chunk in enumerate(chunks, 1):
            try:
                text = chunk["text"].strip()
                logger.debug(f"正在翻译第 {i}/{len(chunks)} 个字幕块")
                logger.debug(f"原文: {text}")
                
                translated_text = self.translator.translate(text, target_lang)
                logger.debug(f"译文: {translated_text}")
                
                translated_chunks.append({
                    "timestamp": chunk["timestamp"],
                    "text": translated_text if translated_text else ""
                })
                
            except Exception as e:
                logger.error(f"翻译第 {i} 个字幕块时出错: {e}")
                translated_chunks.append({
                    "timestamp": chunk["timestamp"],
                    "text": ""
                })
        
        return translated_chunks

    def _save_chunks_to_srt(self, chunks, output_srt_path):
        """保存字幕块为SRT文件"""
        with open(output_srt_path, 'w', encoding='utf-8') as f:
            for i, chunk in enumerate(chunks, 1):
                start_time = self._format_time(chunk["timestamp"][0])
                end_time = self._format_time(chunk["timestamp"][1])
                text = chunk["text"].strip()

                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")