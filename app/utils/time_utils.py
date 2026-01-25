# app/utils/time_utils.py
"""
时间工具模块
"""

from datetime import datetime, timedelta
from config.settings import Config
from config.logging_config import get_logger

logger = get_logger(__name__)

def utc_to_local(utc_dt, offset_hours=None):
    """将UTC时间转换为本地时间"""
    if offset_hours is None:
        offset_hours = Config.TIMEZONE_OFFSET
    return utc_dt + timedelta(hours=offset_hours)

def get_local_now():
    """获取当前本地时间"""
    return datetime.utcnow() + timedelta(hours=Config.TIMEZONE_OFFSET)

def format_local_time(dt, hours=24):
    """根据时间范围格式化本地时间"""
    if hours <= 24:
        # 24小时内显示小时和分钟
        return dt.strftime('%H:%M')
    else:
        # 超过24小时显示月-日 小时:分钟
        return dt.strftime('%m-%d %H:%M')