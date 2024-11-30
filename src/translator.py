import argostranslate.package
import argostranslate.translate
import logging
from typing import Dict, Optional
import torch
import warnings
from functools import lru_cache

# 设置日志
logger = logging.getLogger('fastsrtmaker.translator')
logging.basicConfig(level=logging.INFO)

# 忽略 FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning)

class Translator:
    def __init__(self, languages=None, log_level=logging.INFO):
        """初始化翻译器"""
        logger.setLevel(log_level)
        logger.debug("初始化翻译器")
        self.languages = languages or []
        self._install_language_packages()

    def _install_language_packages(self):
        """安装所需的语言包"""
        try:
            logger.info("更新语言包索引")
            argostranslate.package.update_package_index()
            
            available_packages = argostranslate.package.get_available_packages()
            logger.debug(f"可用语言包数量: {len(available_packages)}")
            
            installed_packages = argostranslate.package.get_installed_packages()
            installed_pairs = {(pkg.from_code, pkg.to_code) for pkg in installed_packages}
            
            # 使用配置的语言对
            language_pairs = []
            for lang in self.languages:
                language_pairs.append((lang["from_code"], lang["to_code"]))
            
            for from_code, to_code in language_pairs:
                if (from_code, to_code) in installed_pairs:
                    logger.debug(f"语言包已安装: {from_code} -> {to_code}")
                    continue
                
                try:
                    package = next(
                        filter(
                            lambda x: x.from_code == from_code and x.to_code == to_code,
                            available_packages
                        ),
                        None
                    )
                    
                    if package:
                        logger.debug(f"安装语言包: {from_code} -> {to_code}")
                        argostranslate.package.install_from_path(package.download())
                        logger.debug(f"语言包安装成功: {from_code} -> {to_code}")
                    else:
                        logger.warning(f"未找到语言包: {from_code} -> {to_code}")
                        
                except Exception as e:
                    logger.error(f"安装语言包失败 ({from_code} -> {to_code}): {e}")
                    
        except Exception as e:
            logger.error(f"更新语言包索引失败: {e}")
            raise

    @lru_cache(maxsize=128)
    def _translate_to_english(self, text: str) -> str:
        """将文本翻译成英语"""
        if not text.strip():
            return ""
        
        try:
            translator = argostranslate.translate.get_translation_from_codes("zh", "en")
            return translator.translate(text)
        except Exception as e:
            logger.error(f"翻译到英语失败: {e}")
            raise RuntimeError("翻译到英语失败") from e

    @lru_cache(maxsize=128)
    def _translate_from_english(self, text: str, target_lang: str) -> str:
        """从英语翻译到目标语言"""
        if not text.strip():
            return ""
            
        try:
            translator = argostranslate.translate.get_translation_from_codes("en", target_lang)
            return translator.translate(text)
        except Exception as e:
            logger.error(f"从英语翻译失败 ({target_lang}): {e}")
            raise RuntimeError(f"翻译到{target_lang}失败") from e

    def translate(self, text: str, target_lang: str) -> str:
        """翻译文本到目标语言（通过英语中转）"""
        if not text.strip():
            logger.debug("输入文本为空，跳过翻译")
            return ""

        if not self.is_language_supported(target_lang):
            logger.error(f"不支持的目标语言: {target_lang}")
            raise ValueError(f"不支持的目标语言代码: {target_lang}")
        
        try:
            if target_lang == 'en':
                return self._translate_to_english(text)
            english_text = self._translate_to_english(text)
            return self._translate_from_english(english_text, target_lang)
        except Exception as e:
            logger.error(f"翻译出错 ({target_lang}): {e}")
            raise RuntimeError("翻译失败") from e

    def _get_supported_languages(self) -> list:
        """动态获取支持的语言列表"""
        installed_packages = argostranslate.package.get_installed_packages()
        languages = set(pkg.to_code for pkg in installed_packages)
        return list(languages)

    def is_language_supported(self, lang_code: str) -> bool:
        """检查语言是否支持"""
        supported = lang_code in self._get_supported_languages()
        logger.debug(f"检查语言支持: {lang_code} - {'支持' if supported else '不支持'}")
        return supported

    def load_model(self, filename):
        """加载模型"""
        try:
            checkpoint = torch.load(filename, weights_only=True)
            logger.debug("模型加载成功")
            return checkpoint
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            raise RuntimeError("模型加载失败") from e