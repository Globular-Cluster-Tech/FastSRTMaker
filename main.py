import argparse
from src.audio_extractor import AudioExtractor
from src.whisper_subtitle_generator import WhisperSubtitleGenerator
import os

def main():
    parser = argparse.ArgumentParser(description='视频字幕生成工具')
    parser.add_argument('input_path', help='输入视频或音频文件路径')
    parser.add_argument('--traditional', action='store_true', help='生成繁体中文字幕')
    parser.add_argument('--translate', action='store_true', help='生成英文翻译字幕')
    parser.add_argument('--device-id', type=str, default='mps', help='设备ID')
    parser.add_argument('--model-name', type=str, default='openai/whisper-large-v3-turbo', help='模型名称')
    args = parser.parse_args()
    
    # 初始化组件
    extractor = AudioExtractor()
    whisper_generator = WhisperSubtitleGenerator()

    # 处理输入文件
    if os.path.splitext(args.input_path)[1].lower() in extractor.supported_formats:
        audio_path = extractor.extract_audio(args.input_path)
        print(f"提取的音频文件路径: {audio_path}")
    else:
        audio_path = args.input_path
        print(f"使用输入文件作为音频: {audio_path}")

    # 调试信息，确保音频路径正确
    print(f"传递给生成字幕的音频路径: {audio_path}")

    # 生成字幕
    language = 'zh-hant' if args.traditional else 'zh'
    subtitle_paths = whisper_generator.generate_subtitles(audio_path, language, args.translate, args.device_id, args.model_name)

    print("生成的字幕文件路径:")
    print(f"简体字幕: {subtitle_paths['simplified']}")
    print(f"繁体字幕: {subtitle_paths['traditional']}")
    print(f"英文字幕: {subtitle_paths['english']}")

if __name__ == "__main__":
    main() 