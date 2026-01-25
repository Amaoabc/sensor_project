# app/models.py
"""
数据模型模块
"""

from datetime import datetime
from app import db

class SensorData(db.Model):
    """双传感器数据模型"""
    __tablename__ = 'sensor_data'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # SCD40数据
    scd40_co2 = db.Column(db.Integer, nullable=True)
    scd40_temperature = db.Column(db.Float, nullable=True)
    scd40_humidity = db.Column(db.Float, nullable=True)
    
    # DHT22数据
    dht22_temperature = db.Column(db.Float, nullable=True)
    dht22_humidity = db.Column(db.Float, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """将数据对象转换为字典"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'scd40': {
                'co2': self.scd40_co2,
                'temperature': self.scd40_temperature,
                'humidity': self.scd40_humidity
            },
            'dht22': {
                'temperature': self.dht22_temperature,
                'humidity': self.dht22_humidity
            },
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<SensorData {self.id}: SCD40(CO2={self.scd40_co2}ppm), DHT22(T={self.dht22_temperature}°C, H={self.dht22_humidity}%)>"