# app/sensors/manager.py
# 完整的修复版本

"""
传感器管理器模块 - 修复版本
"""

import threading
import time
from datetime import datetime
from app.sensors.scd40 import SCD40Sensor
from app.sensors.dht22 import DHT22Sensor
from config.sensors import SensorConfig
from config.logging_config import get_logger

logger = get_logger(__name__)

class SensorManager:
    """传感器管理器 - 统一管理所有传感器"""
    
    def __init__(self, app=None):
        self.app = app  # 保存 Flask 应用实例
        self.sensors = {}
        self.sensor_status = {}
        self.latest_data = {
            'timestamp': None,
            'scd40': {'co2': None, 'temperature': None, 'humidity': None},
            'dht22': {'temperature': None, 'humidity': None}
        }
        self.data_lock = threading.Lock()
        self.collection_thread = None
        self.running = False
        
        # 初始化传感器
        self.initialize_sensors()
    
    def initialize_sensors(self):
        """初始化所有传感器"""
        logger.info("初始化传感器...")
        
        # 初始化SCD40
        if SensorConfig.SCD40_CONFIG['enabled']:
            try:
                self.sensors['scd40'] = SCD40Sensor()
                self.sensor_status['scd40'] = 'online'
                logger.info("✅ SCD40传感器初始化成功")
            except Exception as e:
                logger.error(f"❌ SCD40传感器初始化失败: {e}")
                self.sensors['scd40'] = None
                self.sensor_status['scd40'] = 'offline'
        
        # 初始化DHT22
        if SensorConfig.DHT22_CONFIG['enabled']:
            try:
                self.sensors['dht22'] = DHT22Sensor()
                self.sensor_status['dht22'] = 'online'
                logger.info("✅ DHT22传感器初始化成功")
            except Exception as e:
                logger.error(f"❌ DHT22传感器初始化失败: {e}")
                self.sensors['dht22'] = None
                self.sensor_status['dht22'] = 'offline'
        
        logger.info(f"传感器初始化完成: {self.sensor_status}")
    
    def read_all_sensors(self):
        """读取所有传感器数据"""
        sensor_data = {
            'timestamp': time.time(),
            'scd40': {'co2': None, 'temperature': None, 'humidity': None},
            'dht22': {'temperature': None, 'humidity': None}
        }
        
        # 读取SCD40
        if self.sensors.get('scd40'):
            logger.debug("读取SCD40传感器...")
            co2, temp, humi = self.sensors['scd40'].read()
            sensor_data['scd40'] = {
                'co2': co2,
                'temperature': temp,
                'humidity': humi
            }
            logger.debug(f"SCD40读取结果: CO2={co2}, Temp={temp}, Humi={humi}")
        
        # 读取DHT22
        if self.sensors.get('dht22'):
            logger.debug("读取DHT22传感器...")
            temp, humi = self.sensors['dht22'].read()
            sensor_data['dht22'] = {
                'temperature': temp,
                'humidity': humi
            }
            logger.debug(f"DHT22读取结果: Temp={temp}, Humi={humi}")
        
        # 更新缓存数据
        with self.data_lock:
            self.latest_data = sensor_data
        
        logger.debug(f"传感器数据更新完成: {sensor_data}")
        return sensor_data

    def store_sensor_data(self, sensor_data):
        """存储传感器数据到数据库"""
        try:
            from app.models import SensorData
            
            record = SensorData(
                scd40_co2=sensor_data['scd40']['co2'],
                scd40_temperature=None,
                scd40_humidity=None,
                dht22_temperature=sensor_data['dht22']['temperature'],
                dht22_humidity=sensor_data['dht22']['humidity'],
                timestamp=datetime.utcnow()
            )
            
            # 使用应用上下文
            if self.app:
                with self.app.app_context():
                    # 确保 db 被正确导入
                    from app import db
                    db.session.add(record)
                    db.session.commit()
                    return True
            else:
                # 如果没有应用上下文，记录日志但不存储
                logger.warning("无法存储数据：缺少应用上下文")
                return False
                
        except Exception as e:
            logger.error(f"数据存储失败: {e}")
            # 尝试回滚
            try:
                from app import db
                db.session.rollback()
            except:
                pass
            return False
    def collection_worker(self):
        """数据采集工作线程"""
        logger.info("数据采集线程启动")
        data_count = 0
        
        while self.running:
            try:
                # 读取传感器数据
                sensor_data = self.read_all_sensors()
                
                # 存储到数据库（如果有有效数据）
                if any([sensor_data['scd40']['co2'], 
                       sensor_data['dht22']['temperature'], 
                       sensor_data['dht22']['humidity']]):
                    
                    if self.store_sensor_data(sensor_data):
                        data_count += 1
                        if data_count % 50 == 0:
                            logger.info(f"已持续记录 {data_count} 条传感器数据")
                
                # 使用最短的轮询间隔
                poll_interval = min(
                    SensorConfig.DHT22_CONFIG['poll_interval'],
                    SensorConfig.SCD40_CONFIG['poll_interval']
                )
                time.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"数据采集线程错误: {e}")
                time.sleep(5)
    
    def start_collection(self, app=None):
        """启动数据采集"""
        if self.running:
            return
        
        # 如果提供了新的应用实例，更新它
        if app:
            self.app = app
        
        if not self.app:
            logger.error("无法启动数据采集：缺少 Flask 应用实例")
            return
        
        self.running = True
        self.collection_thread = threading.Thread(
            target=self.collection_worker,
            daemon=True
        )
        self.collection_thread.start()
        logger.info("数据采集线程已启动")
    
    def stop_collection(self):
        """停止数据采集"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logger.info("数据采集线程已停止")
    
    def get_latest_data(self):
        """获取最新数据"""
        with self.data_lock:
            return self.latest_data.copy()
    
    def get_sensor_status(self):
        """获取传感器状态"""
        return self.sensor_status.copy()
    
    def get_health_status(self):
        """获取健康状态"""
        from config.settings import Config
        
        # 检查数据新鲜度
        latest_data = self.get_latest_data()
        now_ts = time.time()
        
        # SCD40健康状态
        scd40_health = 'offline'
        if self.sensor_status.get('scd40') == 'online':
            freshness_threshold = max(SensorConfig.SCD40_CONFIG['poll_interval'] * 2, 30)
            if (latest_data.get('timestamp') and 
                (now_ts - latest_data['timestamp']) < freshness_threshold and
                latest_data.get('scd40', {}).get('co2') is not None):
                scd40_health = 'online'
            else:
                scd40_health = 'degraded'
        
        # DHT22健康状态
        dht22_health = 'offline'
        if self.sensor_status.get('dht22') == 'online':
            freshness_threshold = max(SensorConfig.DHT22_CONFIG['poll_interval'] * 2, 30)
            if (latest_data.get('timestamp') and 
                (now_ts - latest_data['timestamp']) < freshness_threshold and
                latest_data.get('dht22', {}).get('temperature') is not None):
                dht22_health = 'online'
            else:
                dht22_health = 'degraded'
        
        return {
            'scd40': scd40_health,
            'dht22': dht22_health,
            'overall': 'healthy' if (scd40_health == 'online' and dht22_health == 'online') 
                       else 'degraded' if (scd40_health != 'offline' or dht22_health != 'offline')
                       else 'unhealthy'
        }
    
    def test_sensors(self):
        """测试所有传感器"""
        logger.info("测试传感器...")
        results = {}
        
        # 测试SCD40
        if self.sensors.get('scd40'):
            try:
                co2, temp, humi = self.sensors['scd40'].read()
                if co2 is not None and co2 != 32768:
                    results['scd40'] = {'status': 'passed', 'co2': co2}
                else:
                    results['scd40'] = {'status': 'failed', 'error': '无效读数'}
            except Exception as e:
                results['scd40'] = {'status': 'error', 'error': str(e)}
        else:
            results['scd40'] = {'status': 'offline'}
        
        # 测试DHT22
        if self.sensors.get('dht22'):
            try:
                temp, humi = self.sensors['dht22'].read()
                if temp is not None and humi is not None:
                    results['dht22'] = {'status': 'passed', 'temperature': temp, 'humidity': humi}
                else:
                    results['dht22'] = {'status': 'failed', 'error': '无效读数'}
            except Exception as e:
                results['dht22'] = {'status': 'error', 'error': str(e)}
        else:
            results['dht22'] = {'status': 'offline'}
        
        return results