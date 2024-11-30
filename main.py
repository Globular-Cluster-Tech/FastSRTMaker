import argparse
from src.audio_extractor import AudioExtractor
from src.whisper_subtitle_generator import WhisperSubtitleGenerator
import os

# 配置支持的语言列表
DEFAULT_LANGUAGES = [
    {
        "code": "en",
        "name": "english",
        "from_code": "zh",
        "to_code": "en"
    },
    {
        "code": "fr", 
        "name": "french",
        "from_code": "en",
        "to_code": "fr"
    },
    {
        "code": "es",
        "name": "spanish", 
        "from_code": "en",
        "to_code": "es"
    },
    {
        "code": "ja",
        "name": "japanese",
        "from_code": "en", 
        "to_code": "ja"
    },
    {
        "code": "ko",
        "name": "korean",
        "from_code": "en",
        "to_code": "ko"
    }
]

def process_media_file(input_path: str, device_id: str, model_name: str, generator: WhisperSubtitleGenerator):
    """处理视频或音频文件"""
    extractor = AudioExtractor()
    
    if os.path.splitext(input_path)[1].lower() in extractor.supported_formats:
        audio_path = extractor.extract_audio(input_path)
        print(f"提取的音频文件路径: {audio_path}")
    else:
        audio_path = input_path
        print(f"使用输入文件作为音频: {audio_path}")

    subtitle_paths = generator.generate_subtitles(
        input_path=audio_path,
        language='zh',
        translate=False,
        device_id=device_id,
        model_name=model_name
    )
    
    print("\n生成的字幕文件路径:")
    for lang, path in subtitle_paths.items():
        print(f"{lang}: {path}")

def process_subtitle_file(input_path: str, generator: WhisperSubtitleGenerator):
    """处理字幕文件，生成多语言翻译"""
    output_dir = os.path.dirname(input_path)
    os.makedirs(output_dir, exist_ok=True)
    
    subtitle_paths = generator.process_subtitle_file(
        subtitle_path=input_path,
        output_dir=output_dir
    )
    
    print("\n生成的多语言字幕文件:")
    for lang, path in subtitle_paths.items():
        print(f"{lang}: {path}")

def main():
    parser = argparse.ArgumentParser(description='视频字幕生成工具')
    parser.add_argument('input_path', help='输入文件路径（视频、音频或字幕文件）')
    parser.add_argument('--device-id', type=str, default='mps', 
                        help='设备ID (mps: Apple Silicon, cuda: NVIDIA GPU)')
    parser.add_argument('--model-name', type=str, 
                        default='openai/whisper-large-v3', 
                        help='Whisper模型名称')
    parser.add_argument('--languages', type=str,
                        help='要生成的目标语言代码列表，用逗号分隔 (例如: en,fr,es)')
    args = parser.parse_args()
    
    if not os.path.exists(args.input_path):
        print(f"错误: 文件不存在 - {args.input_path}")
        return

    # 处理语言参数
    if args.languages:
        selected_langs = args.languages.split(',')
        languages = [lang for lang in DEFAULT_LANGUAGES if lang["code"] in selected_langs]
    else:
        languages = DEFAULT_LANGUAGES

    # 初始化字幕生成器
    generator = WhisperSubtitleGenerator(languages=languages)
    
    # 根据文件类型选择处理方式
    file_ext = os.path.splitext(args.input_path)[1].lower()
    try:
        if file_ext in ['.srt', '.json']:
            process_subtitle_file(args.input_path, generator)
        else:
            process_media_file(args.input_path, args.device_id, args.model_name, generator)
    except Exception as e:
        print(f"处理过程中出错: {e}")
        return

if __name__ == "__main__":
    main()