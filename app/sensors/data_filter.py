# app/sensors/data_filter.py
"""
数据过滤器模块
"""

import math
from config.logging_config import get_logger

logger = get_logger(__name__)

class SensorDataFilter:
    """传感器数据过滤器 - 用于去除异常波动"""
    
    def __init__(self, config, sensor_type='dht22'):
        self.config = config
        self.sensor_type = sensor_type
        self.window_size = config['data_filter']['window_size']
        
        # 历史数据队列
        self.temperature_history = []
        self.humidity_history = []
        
        # 最后一次有效读数
        self.last_valid_temperature = None
        self.last_valid_humidity = None
        
        # 统计信息
        self.filtered_count = 0
        self.total_count = 0
        
        # 过滤器状态
        self.temperature_filter_enabled = config['data_filter']['temperature'].get('enabled', True)
        self.humidity_filter_enabled = config['data_filter']['humidity'].get('enabled', True)
        
        logger.info(f"初始化{self.sensor_type.upper()}数据过滤器，窗口大小: {self.window_size}")
    
    def reset(self):
        """重置过滤器"""
        self.temperature_history = []
        self.humidity_history = []
        self.last_valid_temperature = None
        self.last_valid_humidity = None
        self.filtered_count = 0
        self.total_count = 0
        logger.info(f"{self.sensor_type.upper()}数据过滤器已重置")
    
    def _calculate_statistics(self, data_list):
        """计算数据列表的统计信息"""
        if not data_list:
            return None, None, None, None
        
        valid_data = [d for d in data_list if d is not None]
        if not valid_data:
            return None, None, None, None
        
        mean = sum(valid_data) / len(valid_data)
        variance = sum((x - mean) ** 2 for x in valid_data) / len(valid_data)
        std_dev = math.sqrt(variance)
        
        # 计算中位数
        sorted_data = sorted(valid_data)
        n = len(sorted_data)
        if n % 2 == 0:
            median = (sorted_data[n//2 - 1] + sorted_data[n//2]) / 2
        else:
            median = sorted_data[n//2]
        
        return mean, std_dev, median, len(valid_data)
    
    def _is_valid_temperature(self, temperature):
        """检查温度是否有效"""
        if temperature is None:
            return False
        
        temp_config = self.config['data_filter']['temperature']
        
        # 1. 范围检查
        if not (temp_config['min'] <= temperature <= temp_config['max']):
            logger.debug(f"温度超出范围: {temperature}°C (允许范围: {temp_config['min']}-{temp_config['max']}°C)")
            return False
        
        # 2. 突变检查（如果有历史数据）
        if self.last_valid_temperature is not None:
            change = abs(temperature - self.last_valid_temperature)
            if change > temp_config['max_change']:
                logger.debug(f"温度变化过大: {change}°C (最大允许: {temp_config['max_change']}°C)")
                return False
        
        # 3. 统计检查（如果有足够的历史数据）
        if len(self.temperature_history) >= 3:
            mean, std_dev, median, _ = self._calculate_statistics(self.temperature_history)
            if mean is not None and std_dev is not None:
                # 检查是否在3个标准差范围内
                threshold = max(std_dev, temp_config['std_threshold'])
                if abs(temperature - mean) > (3 * threshold):
                    logger.debug(f"温度统计异常: {temperature}°C (均值: {mean:.1f}°C, 标准差: {std_dev:.1f})")
                    return False
        
        return True
    
    def _is_valid_humidity(self, humidity):
        """检查湿度是否有效"""
        if humidity is None:
            return False
        
        humi_config = self.config['data_filter']['humidity']
        
        # 1. 范围检查
        if not (humi_config['min'] <= humidity <= humi_config['max']):
            logger.debug(f"湿度超出范围: {humidity}% (允许范围: {humi_config['min']}-{humi_config['max']}%)")
            return False
        
        # 2. 突变检查（如果有历史数据）
        if self.last_valid_humidity is not None:
            change = abs(humidity - self.last_valid_humidity)
            if change > humi_config['max_change']:
                logger.debug(f"湿度变化过大: {change}% (最大允许: {humi_config['max_change']}%)")
                return False
        
        # 3. 统计检查（如果有足够的历史数据）
        if len(self.humidity_history) >= 3:
            mean, std_dev, median, _ = self._calculate_statistics(self.humidity_history)
            if mean is not None and std_dev is not None:
                # 检查是否在3个标准差范围内
                threshold = max(std_dev, humi_config['std_threshold'])
                if abs(humidity - mean) > (3 * threshold):
                    logger.debug(f"湿度统计异常: {humidity}% (均值: {mean:.1f}%, 标准差: {std_dev:.1f})")
                    return False
        
        return True
    
    def filter_data(self, temperature, humidity):
        """过滤温度湿度数据"""
        self.total_count += 1
        
        original_temp = temperature
        original_humi = humidity
        
        # 温度过滤
        if self.temperature_filter_enabled and temperature is not None:
            if not self._is_valid_temperature(temperature):
                # 使用最后一次有效值或历史中位数
                if self.last_valid_temperature is not None:
                    temperature = self.last_valid_temperature
                    self.filtered_count += 1
                    logger.debug(f"温度被过滤: {original_temp}°C -> {temperature}°C (使用上次有效值)")
                else:
                    # 如果没有历史数据，尝试使用历史中位数
                    if self.temperature_history:
                        _, _, median, _ = self._calculate_statistics(self.temperature_history)
                        if median is not None:
                            temperature = median
                            self.filtered_count += 1
                            logger.debug(f"温度被过滤: {original_temp}°C -> {temperature}°C (使用历史中位数)")
                        else:
                            temperature = None
                            logger.debug(f"温度被过滤: {original_temp}°C -> None (无有效历史数据)")
                    else:
                        temperature = None
                        logger.debug(f"温度被过滤: {original_temp}°C -> None (无历史数据)")
            else:
                # 更新历史数据
                self.temperature_history.append(temperature)
                if len(self.temperature_history) > self.window_size:
                    self.temperature_history.pop(0)
                
                # 更新最后一次有效值
                self.last_valid_temperature = temperature
        
        # 湿度过滤
        if self.humidity_filter_enabled and humidity is not None:
            if not self._is_valid_humidity(humidity):
                # 使用最后一次有效值或历史中位数
                if self.last_valid_humidity is not None:
                    humidity = self.last_valid_humidity
                    self.filtered_count += 1
                    logger.debug(f"湿度被过滤: {original_humi}% -> {humidity}% (使用上次有效值)")
                else:
                    # 如果没有历史数据，尝试使用历史中位数
                    if self.humidity_history:
                        _, _, median, _ = self._calculate_statistics(self.humidity_history)
                        if median is not None:
                            humidity = median
                            self.filtered_count += 1
                            logger.debug(f"湿度被过滤: {original_humi}% -> {humidity}% (使用历史中位数)")
                        else:
                            humidity = None
                            logger.debug(f"湿度被过滤: {original_humi}% -> None (无有效历史数据)")
                    else:
                        humidity = None
                        logger.debug(f"湿度被过滤: {original_humi}% -> None (无历史数据)")
            else:
                # 更新历史数据
                self.humidity_history.append(humidity)
                if len(self.humidity_history) > self.window_size:
                    self.humidity_history.pop(0)
                
                # 更新最后一次有效值
                self.last_valid_humidity = humidity
        
        return temperature, humidity
    
    def get_stats(self):
        """获取过滤器统计信息"""
        return {
            'total': self.total_count,
            'filtered': self.filtered_count,
            'filter_rate': self.filtered_count / self.total_count if self.total_count > 0 else 0,
            'window_size': len(self.temperature_history),
            'temperature_history_size': len(self.temperature_history),
            'humidity_history_size': len(self.humidity_history),
            'last_valid': {
                'temperature': self.last_valid_temperature,
                'humidity': self.last_valid_humidity
            }
        }
    def filter_voc_index(self, voc_index):
        """过滤VOC指数"""
        """待补充"""
        return voc_index
    
    def filter_nox_index(self, nox_index):
        """过滤NOx指数"""
        """待补充"""
        return nox_index