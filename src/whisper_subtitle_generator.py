import os
import subprocess
import json
import opencc

from .translator import Translator

# 格式化时间为 SRT 格式
def format_time(seconds):
    millis = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

# 从 JSON 文件生成 SRT 文件
def json_to_srt(json_file_path, output_srt_path):
    with open(json_file_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    chunks = json_data.get("chunks", [])
    if not chunks:
        print("No chunks found in the JSON data.")
        return

    with open(output_srt_path, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            start_time = format_time(chunk["timestamp"][0])
            end_time = format_time(chunk["timestamp"][1])
            text = chunk["text"].strip()

            f.write(f"{i + 1}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")

class WhisperSubtitleGenerator:
    def __init__(self):
        self.translator = Translator()
        self.cc = opencc.OpenCC("s2t")  # 创建 OpenCC 实例用于简体到繁体转换

    def generate_subtitles(self, audio_path: str, language: str, translate: bool, device_id: str, model_name: str):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        command = [
            'insanely-fast-whisper', 
            '--file-name', audio_path,
            "--device-id", device_id,
            "--model-name", model_name,
            '--transcript-path', os.path.splitext(audio_path)[0] + '.json'
        ]

        if translate:
            command.append('--translate')

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"生成字幕失败: {result.stderr}")

        subtitle_file_path = os.path.splitext(audio_path)[0] + '.json'
        
        # 生成简体中文字幕
        json_to_srt(subtitle_file_path, os.path.splitext(audio_path)[0] + '_zh.srt')

        # 生成繁体中文字幕
        simplified_chunks = self._load_json_chunks(subtitle_file_path)
        traditional_chunks = self._convert_to_traditional(simplified_chunks)
        self._save_chunks_to_srt(traditional_chunks, os.path.splitext(audio_path)[0] + '_zh_hant.srt')

        # 生成英文字幕
        english_chunks = self._translate_chunks(simplified_chunks)
        self._save_chunks_to_srt(english_chunks, os.path.splitext(audio_path)[0] + '_en.srt')

        # 删除临时音频文件
        if os.path.exists(audio_path):
            os.remove(audio_path)

        if os.path.exists(subtitle_file_path):
            os.remove(subtitle_file_path)

        # 返回生成的字幕文件路径
        return {
            "simplified": os.path.splitext(audio_path)[0] + '_zh.srt',
            "traditional": os.path.splitext(audio_path)[0] + '_zh_hant.srt',
            "english": os.path.splitext(audio_path)[0] + '_en.srt'
        }

    def _load_json_chunks(self, json_file_path):
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        return json_data.get("chunks", [])

    def _convert_to_traditional(self, chunks):
        for chunk in chunks:
            chunk["text"] = self.cc.convert(chunk["text"])  # 使用 OpenCC 进行转换
        return chunks

    def _translate_chunks(self, chunks):
        for chunk in chunks:
            try:
                translation = self.translator.translate_en(chunk["text"])  # 确保使用正确的参数
                if translation:  # 检查翻译是否为非空字符串
                    chunk["text"] = translation  # 直接使用翻译结果
                else:
                    print("翻译返回了空字符串，使用默认值。")
                    chunk["text"] = ""  # 或者设置为默认值
            except Exception as e:
                print(f"翻译错误: {e}")  # 捕获并打印错误
                chunk["text"] = ""  # 或者设置为默认值
        return chunks

    def _save_chunks_to_srt(self, chunks, output_srt_path):
        with open(output_srt_path, 'w', encoding='utf-8') as f:
            for i, chunk in enumerate(chunks):
                start_time = format_time(chunk["timestamp"][0])
                end_time = format_time(chunk["timestamp"][1])
                text = chunk["text"].strip()

                f.write(f"{i + 1}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")