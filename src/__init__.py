import logging
import os
import coloredlogs

# 配置日志记录
def setup_logger(debug_mode=False):
    """设置日志记录器"""
    log_level = logging.DEBUG if debug_mode else logging.INFO

    # 创建日志记录器
    logger = logging.getLogger('fastsrtmaker')
    logger.setLevel(log_level)

    # 设置 coloredlogs（自动添加 StreamHandler）
    if debug_mode:
        fmt = '%(asctime)s - %(name)s - [%(filename)s:%(lineno)s - %(funcName)20s() ] - %(levelname)s - %(message)s'
    else:
        fmt = '%(asctime)s - %(name)s - [%(filename)s] - %(levelname)s - %(message)s'

    coloredlogs.install(level=log_level, logger=logger, fmt=fmt, datefmt='%Y-%m-%d %H:%M:%S')

    return logger

# 创建日志记录器实例
logger = setup_logger(debug_mode=False)