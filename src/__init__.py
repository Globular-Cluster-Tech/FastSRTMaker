import logging
import os

# 配置日志记录
def setup_logger(debug_mode=False):
    """设置日志记录器"""
    log_level = logging.DEBUG if debug_mode else logging.INFO
    
    # 创建日志记录器
    logger = logging.getLogger('fastsrtmaker')
    logger.setLevel(log_level)
    
    # 创建控制台处理程序
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理程序到记录器
    logger.addHandler(console_handler)
    
    return logger

# 创建日志记录器实例
logger = setup_logger(debug_mode=False)
