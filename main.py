import argparse,logging,platform,psutil,os
from src.audio_extractor import AudioExtractor
from src.whisper_subtitle_generator import WhisperSubtitleGenerator
from src import logger
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

class WhisperConfig:
    def __init__(self):
        self.model = "small"
        self.batch_size = 8
        self.device = "mps"
        self.compute_type = "int8"
        
    def get_memory_gb(self):
        """获取系统内存大小（GB）"""
        try:
            if platform.system() == "Darwin":  # macOS
                memory = psutil.virtual_memory().total
            else:  # Linux/Windows
                memory = psutil.virtual_memory().total
            return round(memory / (1024 ** 3))  # 转换为 GB
        except Exception as e:
            logger.error(f"获取系统内存失败: {e}")
            return 8  # 默认值
            
    def select_model_by_memory(self):
        """根据系统内存选择合适的模型"""
        memory_gb = self.get_memory_gb()
        logger.info(f"检测到系统内存: {memory_gb}GB")
        
        # 根据内存大小选择模型和批处理大小
        if memory_gb >= 16:
            self.model = "large-v3-turbo"
            self.batch_size = 16
            logger.info("选择 large-v3-turbo 模型 (适中内存)")
        else:
            self.model = "small"
            self.batch_size = 8
            logger.info("选择 small 模型 (内存较小)")
            
        # 检查 GPU 可用性
        try:
            import torch
            if torch.cuda.is_available():
                self.device = "cuda"
                logger.info("使用 CUDA 设备")
            elif torch.backends.mps.is_available():
                self.device = "mps"
                logger.info("使用 MPS 设备")
            else:
                logger.info("使用 CPU 设备")
        except ImportError:
            logger.warning("未检测到 PyTorch，使用 CPU 设备")
            
        return {
            "model": f"openai/whisper-{self.model}",
            "batch_size": self.batch_size,
            "device": self.device,
            "compute_type": self.compute_type
        }

model_config = WhisperConfig().select_model_by_memory()

def process_media_file(input_path: str, device_id: str, model_name: str, generator: WhisperSubtitleGenerator):
    """处理视频或音频文件"""
    extractor = AudioExtractor()
    
    if os.path.splitext(input_path)[1].lower() in extractor.supported_formats:
        audio_path = extractor.extract_audio(input_path)
        logger.info(f"提取的音频文件路径: {audio_path}")
    else:
        audio_path = input_path
        logger.info(f"使用输入文件作为音频: {audio_path}")

    subtitle_paths = generator.generate_subtitles(
        input_path=audio_path,
        language='zh',
        translate=False,
        device_id=device_id,
        model_name=model_name
    )
    
    # logger.info("生成的字幕文件路径:")
    for lang, path in subtitle_paths.items():
        logger.info(f"生成的字幕文件路径: {lang}: {path}")

def process_subtitle_file(input_path: str, generator: WhisperSubtitleGenerator):
    """处理字幕文件，生成多语言翻译"""
    output_dir = os.path.dirname(input_path)
    os.makedirs(output_dir, exist_ok=True)
    
    subtitle_paths = generator.process_subtitle_file(
        subtitle_path=input_path,
        output_dir=output_dir
    )
    
    logger.info("\n生成的多语言字幕文件:")
    for lang, path in subtitle_paths.items():
        logger.info(f"{lang}: {path}")

def main():
    parser = argparse.ArgumentParser(description='视频字幕生成工具')
    parser.add_argument('input_path', help='输入文件路径（视频、音频或字幕文件）')
    parser.add_argument('--device-id', type=str, default='mps', 
                        help='设备ID (mps: Apple Silicon, cuda: NVIDIA GPU)')
    parser.add_argument('--model-name', type=str, 
                        default='{}'.format(model_config['model']), 
                        help='Whisper模型名称')
    parser.add_argument('--languages', type=str,
                        help='要生成的目标语言代码列表，用逗号分隔 (例如: en,fr,es)')
    args = parser.parse_args()
    
    if not os.path.exists(args.input_path):
        logger.error(f"错误: 文件不存在 - {args.input_path}")
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
        logger.error(f"处理过程中出错: {e}")
        return

if __name__ == "__main__":
    main()