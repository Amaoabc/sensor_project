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
        'retry_delay': 2,       # 重试间隔5秒
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
        'retry_delay': 1,       # 重试间隔5秒
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
    
    # 所有传感器配置字典
    SENSORS = {
        'scd40': SCD40_CONFIG,
        'dht22': DHT22_CONFIG
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