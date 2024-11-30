import os
import subprocess
import json
import opencc
from typing import Dict, List
import logging

logger = logging.getLogger('fastsrtmaker.generator')

class WhisperSubtitleGenerator:
    def __init__(self, languages=None):
        logger.debug("初始化字幕生成器")
        self.cc = opencc.OpenCC("s2t")  # 创建 OpenCC 实例用于简体到繁体转换
        self.translator = None  # 将在需要时初始化
        self.languages = languages or []

    def generate_subtitles(self, input_path: str, language: str, translate: bool, device_id: str, model_name: str):
        """生成字幕文件"""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"文件不存在: {input_path}")

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

        if translate:
            command.append('--translate')

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"生成字幕失败: {result.stderr}")

        srt_path = os.path.join(output_dir, f"{base_name}_{language}.srt")
        
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