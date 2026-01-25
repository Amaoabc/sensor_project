# app/sensors/dht22.py
"""
DHT22传感器模块
"""

import time
import threading
import board
import adafruit_dht
from .data_filter import SensorDataFilter
from config.sensors import SensorConfig
from config.logging_config import get_logger

logger = get_logger(__name__)

class DHT22Sensor:
    """DHT22温湿度传感器封装"""
    
    def __init__(self):
        self.config = SensorConfig.DHT22_CONFIG
        self.sensor = None
        self.dht_lock = threading.Lock()
        self.filter = SensorDataFilter(self.config, 'dht22')
        
        # 日志抑制配置
        self.dht_log = {
            'last_msg': None,
            'last_time': 0,
            'min_interval': 60,
            'error_interval': 300
        }
        
        self._initialize()
    
    def _initialize(self):
        """初始化传感器"""
        try:
            self.sensor = adafruit_dht.DHT22(
                self.config['pin'], 
                use_pulseio=self.config['use_pulseio']
            )
            logger.info(f"DHT22初始化成功 (GPIO{self.config['pin']})")
        except Exception as e:
            logger.error(f"DHT22初始化失败: {e}")
            raise
    
    def read(self):
        """读取传感器数据（带重试和过滤）"""
        retry_attempts = self.config['retry_attempts']
        retry_delay = self.config['retry_delay']
        
        for attempt in range(retry_attempts):
            try:
                # 序列化对 DHT 的访问
                with self.dht_lock:
                    temperature = self.sensor.temperature
                    humidity = self.sensor.humidity

                if temperature is not None and humidity is not None:
                    # 数据过滤
                    filtered_temp, filtered_humi = self.filter.filter_data(temperature, humidity)
                    
                    # 如果过滤后数据无效，继续重试
                    if filtered_temp is None or filtered_humi is None:
                        now = time.time()
                        if now - self.dht_log['last_time'] > self.dht_log['min_interval']:
                            logger.debug(f"DHT22数据过滤后无效，继续重试 (尝试{attempt+1}/{retry_attempts})")
                            self.dht_log['last_time'] = now
                        time.sleep(retry_delay)
                        continue
                    
                    # 室内环境合理范围检查
                    if 10 <= filtered_temp <= 40 and 20 <= filtered_humi <= 90:
                        if filtered_temp == 0.0 and filtered_humi == 0.0:
                            now = time.time()
                            if now - self.dht_log['last_time'] > self.dht_log['min_interval']:
                                logger.debug("DHT22返回零值，可能为瞬时读数错误，已忽略")
                                self.dht_log['last_time'] = now
                            time.sleep(retry_delay)
                            continue
                        logger.info(f"DHT22读取成功: {filtered_temp} °C, {filtered_humi} %")
                        return round(filtered_temp, 1), round(filtered_humi, 1)
                    
                    else:
                        now = time.time()
                        if now - self.dht_log['last_time'] > self.dht_log['min_interval']:
                            logger.debug(f"DHT22过滤后读数仍超出范围，温度={filtered_temp}，湿度={filtered_humi}")
                            self.dht_log['last_time'] = now

                time.sleep(retry_delay)

            except RuntimeError as e:
                self._handle_runtime_error(e, attempt, retry_attempts)
                time.sleep(retry_delay)

            except Exception as e:
                self._handle_general_error(e, attempt, retry_attempts)
                time.sleep(retry_delay)
        
        logger.debug(f"DHT22读取失败，已尝试{retry_attempts}次")
        return None, None




    def _handle_runtime_error(self, error, attempt, max_attempts):
        """处理运行时错误"""
        msg = str(error).lower()
        now = time.time()

        transient = any(k in msg for k in ("checksum", "full buffer", "buffer was not returned"))
        not_found = any(k in msg for k in ("sensor not found", "dht sensor not found", "no response"))

        if transient:
            if self.dht_log['last_msg'] != msg or (now - self.dht_log['last_time']) > self.dht_log['min_interval']:
                logger.debug(f"DHT22瞬时读取错误（尝试{attempt+1}/{max_attempts}）: {error}")
                self.dht_log['last_msg'] = msg
                self.dht_log['last_time'] = now

        elif not_found:
            if self.dht_log['last_msg'] != msg or (now - self.dht_log['last_time']) > self.dht_log['error_interval']:
                logger.error(f"DHT22未响应或未找到（尝试{attempt+1}/{max_attempts}）: {error}")
                self.dht_log['last_msg'] = msg
                self.dht_log['last_time'] = now

            # 尝试重新初始化
            self._try_reinitialize()

        else:
            if now - self.dht_log['last_time'] > self.dht_log['min_interval']:
                logger.debug(f"DHT22运行时错误（尝试{attempt+1}/{max_attempts}）: {error}")
                self.dht_log['last_time'] = now
    
    def _handle_general_error(self, error, attempt, max_attempts):
        """处理一般错误"""
        now = time.time()
        if attempt == max_attempts - 1:
            logger.exception(f"DHT22意外错误（最终尝试）: {type(error).__name__}: {error}")
        else:
            if now - self.dht_log['last_time'] > self.dht_log['min_interval']:
                logger.debug(f"DHT22意外异常（尝试{attempt+1}）: {type(error).__name__}: {error}")
                self.dht_log['last_time'] = now
    
    def _try_reinitialize(self):
        """尝试重新初始化传感器"""
        try:
            pin = self.config['pin']
            use_pulseio = self.config['use_pulseio']
            self.sensor = adafruit_dht.DHT22(pin, use_pulseio=use_pulseio)
            logger.info("已尝试重新初始化 DHT22 传感器")
        except Exception as e:
            logger.debug(f"重新初始化 DHT22失败: {type(e).__name__}: {e}")
    
    def get_status(self):
        """获取传感器状态"""
        return {
            'initialized': self.sensor is not None,
            'filter_stats': self.filter.get_stats()
        }