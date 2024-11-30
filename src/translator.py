from transformers import pipeline
import torch
import platform

class Translator:
    def __init__(self):
        self.device = self._check_device()
        if not self.device:
            raise RuntimeError("需要 NVIDIA GPU 或 Apple Silicon 芯片才能运行")
            
        self.translator = pipeline(
            "translation",
            model="Helsinki-NLP/opus-mt-zh-en",
            device=self.device
        )
    
    def _check_device(self) -> str:
        """检查可用的计算设备"""
        if platform.processor() == 'arm' and torch.backends.mps.is_available():
            return 'mps'
        if torch.cuda.is_available():
            return 'cuda'
        return None
    
    def translate_en(self, text: str) -> str:
        """翻译文本到目标语言"""
        result = self.translator(text)
        return result[0]['translation_text'] 