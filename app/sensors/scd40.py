# app/sensors/scd40.py
"""
SCD40传感器模块
"""

import time
import board
import adafruit_scd4x
from config.sensors import SensorConfig
from config.logging_config import get_logger

logger = get_logger(__name__)

class SCD40Sensor:
    """SCD40 CO₂传感器封装"""
    
    def __init__(self):
        self.config = SensorConfig.SCD40_CONFIG
        self.sensor = None
        self.last_read_time = 0
        self.last_data = {'co2': None, 'timestamp': 0}
        
        self._initialize()
    
    def _initialize(self):
        """初始化传感器"""
        try:
            i2c = board.I2C()
            self.sensor = adafruit_scd4x.SCD4X(i2c)
            
            # 停止任何现有测量
            try:
                self.sensor.stop_periodic_measurement()
            except:
                pass
            
            time.sleep(1)
            
            # 开始周期性测量
            self.sensor.start_low_periodic_measurement()
            
            # 预热
            logger.info(f"SCD40预热中... ({self.config['warmup_time']}秒)")
            time.sleep(self.config['warmup_time'])
            
        except Exception as e:
            logger.error(f"SCD40初始化失败: {e}")
            raise
    
    def read(self):
        """读取传感器数据（带缓存）"""
        current_time = time.time()
        
        # 检查是否需要读取新数据（至少间隔10秒）
        if current_time - self.last_read_time < 10:
            # 返回缓存数据
            logger.debug(f"使用SCD40缓存数据: {self.last_data['co2']} ppm")
            return self.last_data['co2'], None, None
        
        try:
            if self.sensor.data_ready:
                co2 = self.sensor.CO2
                
                # 过滤错误值32768
                if co2 == 32768:
                    logger.warning("SCD40返回错误值32768ppm，忽略此读数")
                    return self.last_data['co2'], None, None
                
                if (400 <= co2 <= 5000):  # 合理范围
                    # 更新缓存
                    self.last_read_time = current_time
                    self.last_data['co2'] = int(round(co2, 0))
                    self.last_data['timestamp'] = current_time
                    
                    logger.info(f"SCD40读取成功: {co2} ppm")
                    return int(round(co2, 0)), None, None
                else:
                    logger.warning(f"SCD40读数超出合理范围: CO2={co2}ppm")
                    return self.last_data['co2'], None, None
            else:
                # 数据未就绪，返回缓存数据
                logger.debug("SCD40数据未就绪，使用缓存")
                return self.last_data['co2'], None, None
                
        except RuntimeError as e:
            logger.error(f"SCD40运行时错误: {e}")
            return self.last_data['co2'], None, None
        except Exception as e:
            logger.error(f"SCD40意外错误: {type(e).__name__}: {e}")
            return self.last_data['co2'], None, None
   
    def get_status(self):
        """获取传感器状态"""
        return {
            'initialized': self.sensor is not None,
            'last_read_time': self.last_read_time,
            'last_data': self.last_data
        }