# config/logging_config.py
"""
日志配置文件
"""

import logging
import sys
from pathlib import Path

# 首先定义日志级别映射
LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}


def get_log_level(level_name):
    """根据名称获取日志级别"""
    if isinstance(level_name, str):
        level_name = level_name.lower()
        return LOG_LEVELS.get(level_name, logging.INFO)
    # 如果已经是数字级别，直接返回
    return level_name


def setup_logging(app_name='sensor_api', log_level='info', log_to_file=True):
    """
    设置日志配置
    
    Args:
        app_name: 应用名称，用于日志文件名
        log_level: 日志级别（可以是字符串或logging常量）
        log_to_file: 是否记录到文件
    """
    # 将日志级别转换为数值
    numeric_log_level = get_log_level(log_level)
    
    # 日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 创建格式化器
    formatter = logging.Formatter(log_format, date_format)
    
    # 创建根日志记录器
    logger = logging.getLogger()
    logger.setLevel(numeric_log_level)
    
    # 清除现有处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_log_level)
    logger.addHandler(console_handler)
    
    # 文件处理器（可选）
    if log_to_file:
        try:
            log_file = Path(__file__).parent.parent / f'{app_name}.log'
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(numeric_log_level)
            logger.addHandler(file_handler)
            
            # 同时记录错误到单独的错误日志文件
            error_log_file = Path(__file__).parent.parent / f'{app_name}_error.log'
            error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
            error_handler.setFormatter(formatter)
            error_handler.setLevel(logging.ERROR)  # 错误日志只记录ERROR及以上
            logger.addHandler(error_handler)
            
            logger.info(f"日志文件: {log_file}")
            logger.info(f"错误日志文件: {error_log_file}")
            
        except Exception as e:
            logger.error(f"创建日志文件失败: {e}")
    
    # 设置第三方库的日志级别
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    return logger


def get_logger(name):
    """获取指定名称的日志记录器"""
    return logging.getLogger(name)


# 默认配置
DEFAULT_LOGGING_CONFIG = {
    'app_name': 'sensor_api_dual',
    'log_level': 'info',
    'log_to_file': True,
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S'
}