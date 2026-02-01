# config/sensors.py
"""
传感器配置文件
包含SCD40和DHT22的配置
"""

import board

class SensorConfig:
    """传感器配置基类"""
    
    # SCD40传感器配置
    SCD40_CONFIG = {
        'type': 'SCD40',
        'enabled': True,
        'i2c_address': 0x62,    # SCD40默认I2C地址
        'retry_attempts': 3,    # 重试次数3次
        'retry_delay': 5,       # 重试间隔5秒
        'warmup_time': 10,      # 预热时间10秒
        'poll_interval': 30,    # 读取间隔30秒
        'description': '二氧化碳浓度传感器 (I2C接口)',
        'data_fields': ['co2', 'temperature', 'humidity'],
        'valid_ranges': {
            'co2': (400, 5000),      # ppm
            'temperature': (-10, 60), # °C
            'humidity': (0, 100)      # %
        }
    }
    
    # DHT22传感器配置
    DHT22_CONFIG = {
        'type': 'DHT22',
        'enabled': True,
        'pin': board.D4,
        'use_pulseio': False,
        'retry_attempts': 5,    # 重试次数3次
        'retry_delay': 1,       # 重试间隔1秒
        'poll_interval': 30,    # 读取间隔30秒
        'description': '温湿度传感器 (GPIO4)',
        'data_fields': ['temperature', 'humidity'],
        'valid_ranges': {
            'temperature': (-40, 80),  # °C
            'humidity': (0, 100)       # %
        },
        # 数据过滤器配置
        'data_filter': {
            'enabled': True,
            'window_size': 5,
            'temperature': {
                'min': 5,           # 最低合理温度 °C
                'max': 40,           # 最高合理温度 °C
                'max_change': 5.0,   # 最大允许变化 °C（每次读取）
                'std_threshold': 2.5 # 标准差阈值
            },
            'humidity': {
                'min': 10,           # 最低合理湿度 %
                'max': 90,           # 最高合理湿度 %
                'max_change': 15.0,  # 最大允许变化 %
                'std_threshold': 5.0 # 标准差阈值
            }
        }
    }

    # SGP41传感器配置
    SGP41_CONFIG = {
        'type': 'SGP41',
        'enabled': True,
        'i2c_address': 0x59,    # SGP41默认I2C地址
        'retry_attempts': 3,    # 重试次数3次
        'retry_delay': 2,       # 重试间隔2秒
        'poll_interval': 1,     # 读取间隔1秒（算法推荐）
        'conditioning_time': 10, # 调节时间10秒（不得超过10秒）
        'description': 'VOC和NOx空气质量传感器 (I2C接口)',
        'data_fields': ['sraw_voc', 'sraw_nox', 'voc_index', 'nox_index'],
        'valid_ranges': {
            'sraw_voc': (0, 65535),      # 原始VOC信号范围
            'sraw_nox': (0, 65535),      # 原始NOx信号范围
            'voc_index': (1, 500),       # VOC指数范围
            'nox_index': (1, 500)        # NOx指数范围
        },
        # 算法配置
        'algorithm': {
            'sampling_interval': 1.0,    # 采样间隔1秒
            'voc_algorithm_params': {
                'index_offset': 100,     # VOC指数基准值
                'learning_time_offset_hours': 720,  # 重要：从12改为720小时！
                'learning_time_gain_hours': 12,
                'gating_max_duration_minutes': 180,
                'std_initial': 50,
                'gain_factor': 230
            },
            'nox_algorithm_params': {
                'index_offset': 1,       # NOx指数基准值
                'learning_time_offset_hours': 12,
                'learning_time_gain_hours': 12,      # 添加此参数
                'gating_max_duration_minutes': 720,
                'std_initial': 50,                   # 添加此参数
                'gain_factor': 230
            }
        },
        
        # 数据过滤器配置
        'data_filter': {
            'enabled': True,
            'window_size': 10,
            'voc_index': {
                'min': 0,           # 最低合理VOC指数
                'max': 500,         # 最高合理VOC指数
                'max_change': 100,  # 最大允许变化（每次读取）
                'std_threshold': 50 # 标准差阈值
            },
            'nox_index': {
                'min': 0,           # 最低合理NOx指数
                'max': 500,         # 最高合理NOx指数
                'max_change': 100,  # 最大允许变化（每次读取）
                'std_threshold': 50 # 标准差阈值
            }
        },
        # 温湿度补偿配置
        'compensation': {
            'enabled': True,
            'humidity_source': 'dht22',  # 使用DHT22的湿度数据
            'temperature_source': 'dht22' # 使用DHT22的温度数据
        }
    }
    
    # 所有传感器配置字典
    SENSORS = {
        'scd40': SCD40_CONFIG,
        'dht22': DHT22_CONFIG,
        'sgp41': SGP41_CONFIG
    }
    
    # 传感器状态定义
    SENSOR_STATUS = {
        'online': {
            'description': '传感器在线且正常工作',
            'color': 'green'
        },
        'degraded': {
            'description': '传感器在线但数据可能不准确',
            'color': 'yellow'
        },
        'offline': {
            'description': '传感器离线或无法访问',
            'color': 'red'
        }
    }
    
    @classmethod
    def get_sensor_config(cls, sensor_name):
        """获取指定传感器的配置"""
        return cls.SENSORS.get(sensor_name, {})
    
    @classmethod
    def get_enabled_sensors(cls):
        """获取启用的传感器列表"""
        return [name for name, config in cls.SENSORS.items() 
                if config.get('enabled', True)]
    
    @classmethod
    def get_sensor_pins(cls):
        """获取传感器引脚配置"""
        pins = {}
        for name, config in cls.SENSORS.items():
            if 'pin' in config:
                pins[name] = config['pin']
        return pins
    
    @classmethod
    def validate_sensor_data(cls, sensor_name, data):
        """验证传感器数据是否在有效范围内"""
        config = cls.get_sensor_config(sensor_name)
        if not config:
            return False
        
        valid_ranges = config.get('valid_ranges', {})
        
        for field, value in data.items():
            if value is not None and field in valid_ranges:
                min_val, max_val = valid_ranges[field]
                if not (min_val <= value <= max_val):
                    return False
                    
        return True