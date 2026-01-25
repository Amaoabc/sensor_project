# config/settings.py
"""
应用主配置文件
"""

import os
from pathlib import Path

# 项目基础目录
BASE_DIR = Path(__file__).parent.parent

class Config:
    """应用配置类"""
    
    # ========== Flask配置 ==========
    SECRET_KEY = os.getenv('SECRET_KEY', 'sensor_api_dual_secret_key')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # ========== 服务器配置 ==========
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # ========== 数据库配置 ==========
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'sensor_data_dual.db')
    DATABASE_PATH = BASE_DIR / DATABASE_NAME
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    
    # ========== API配置 ==========
    DEFAULT_HISTORY_LIMIT = 100
    MAX_HISTORY_LIMIT = 1000
    DATA_CACHE_DURATION = 2  # 秒
    
    # ========== 时区配置 ==========
    TIMEZONE_OFFSET = int(os.getenv('TIMEZONE_OFFSET', 8))  # 东八区
    
    # ========== 数据验证范围 ==========
    VALID_RANGES = {
        'co2': (0, 5000),
        'temperature': (-40, 80),
        'humidity': (0, 100)
    }
    
    # ========== 服务元数据 ==========
    SERVICE_NAME = '树莓派双传感器环境监测系统'
    SERVICE_VERSION = '2.5'
    SERVICE_DESCRIPTION = '同时监控SCD40 CO₂传感器和DHT22温湿度传感器'
    

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = False  # 设置为True可查看SQL日志


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'production_secret_key_change_me')


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    DATABASE_NAME = 'test_sensor_data.db'
    DATABASE_PATH = BASE_DIR / DATABASE_NAME
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'


# 配置映射
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}

# 当前使用的配置
current_config = config_by_name.get(
    os.getenv('FLASK_ENV', 'production').lower(),
    ProductionConfig
)