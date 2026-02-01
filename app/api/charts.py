# app/api/charts.py
"""
图表API模块
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from app import db
from app.models import SensorData
from app.utils.time_utils import utc_to_local
from app.utils.data_utils import generate_co2_sample_data, generate_temp_humi_sample_data
from config.settings import Config
from config.logging_config import get_logger

logger = get_logger(__name__)

charts_bp = Blueprint('charts', __name__)

@charts_bp.route('/co2', methods=['GET'])
def get_co2_chart_data():
    """获取CO2历史数据图表"""
    try:
        hours = request.args.get('hours', default=24, type=int)
        
        # 先检查是否有真实数据
        record_count = SensorData.query.filter(
            SensorData.scd40_co2.isnot(None)
        ).count()
        
        if record_count == 0:
            # 没有数据，返回示例数据
            return jsonify(generate_co2_sample_data(hours))
        
        # 计算时间范围（UTC时间）
        time_limit = datetime.utcnow() - timedelta(hours=hours)
        query = SensorData.query.filter(
            SensorData.timestamp >= time_limit,
            SensorData.scd40_co2.isnot(None)
        )
        
        # 获取数据并按时间排序
        records = query.order_by(SensorData.timestamp.asc()).all()
        
        if not records:
            # 指定时间范围内没有数据，返回示例数据
            return jsonify(generate_co2_sample_data(hours))
        
        timestamps = []
        co2_data = []
        
        for record in records:
            if record.timestamp:
                # 转换为本地时间
                local_time = utc_to_local(record.timestamp)
                
                # 根据时间范围格式化时间标签
                if hours <= 24:
                    # 24小时内显示小时:分钟
                    timestamps.append(local_time.strftime('%H:%M'))
                else:
                    # 超过24小时显示月-日 小时:分钟
                    timestamps.append(local_time.strftime('%m-%d %H:%M'))
            
            # 只使用SCD40的CO2数据
            co2_data.append(record.scd40_co2)
        
        return jsonify({
            'success': True,
            'count': len(records),
            'labels': timestamps,
            'datasets': [{
                'label': 'CO₂浓度',
                'data': co2_data,
                'borderColor': 'rgb(76, 201, 240)',
                'backgroundColor': 'rgba(76, 201, 240, 0.1)',
                'borderWidth': 2,
                'tension': 0.4
            }],
            'units': 'ppm',
            'source': 'SCD40',
            'timezone': f"UTC+{Config.TIMEZONE_OFFSET}",
            'range': {
                'min': min(co2_data) if co2_data else None,
                'max': max(co2_data) if co2_data else None,
                'avg': sum(co2_data)/len(co2_data) if co2_data else None
            }
        })
    
    except Exception as e:
        logger.error(f"获取CO2图表数据失败: {e}")
        # 返回示例数据作为后备
        return jsonify(generate_co2_sample_data(24))

@charts_bp.route('/temperature_humidity', methods=['GET'])
def get_temperature_humidity_chart_data():
    """获取温湿度历史数据图表"""
    try:
        hours = request.args.get('hours', default=24, type=int)
        
        # 先检查是否有真实数据
        record_count = SensorData.query.filter(
            db.or_(
                SensorData.dht22_temperature.isnot(None),
                SensorData.dht22_humidity.isnot(None)
            )
        ).count()
        
        if record_count == 0:
            # 没有数据，返回示例数据
            return jsonify(generate_temp_humi_sample_data(hours))
        
        # 计算时间范围（UTC时间）
        time_limit = datetime.utcnow() - timedelta(hours=hours)
        query = SensorData.query.filter(
            SensorData.timestamp >= time_limit,
            db.or_(
                SensorData.dht22_temperature.isnot(None),
                SensorData.dht22_humidity.isnot(None)
            )
        )
        
        # 获取数据并按时间排序
        records = query.order_by(SensorData.timestamp.asc()).all()
        
        if not records:
            # 指定时间范围内没有数据，返回示例数据
            return jsonify(generate_temp_humi_sample_data(hours))
        
        timestamps = []
        temperature_data = []
        humidity_data = []
        
        for record in records:
            if record.timestamp:
                # 转换为本地时间
                local_time = utc_to_local(record.timestamp)
                
                # 根据时间范围格式化时间标签
                if hours <= 24:
                    # 24小时内显示小时:分钟
                    timestamps.append(local_time.strftime('%H:%M'))
                else:
                    # 超过24小时显示月-日 小时:分钟
                    timestamps.append(local_time.strftime('%m-%d %H:%M'))
            
            # 只使用DHT22的温湿度数据
            temperature_data.append(record.dht22_temperature)
            humidity_data.append(record.dht22_humidity)
        
        return jsonify({
            'success': True,
            'count': len(records),
            'labels': timestamps,
            'datasets': [
                {
                    'label': '温度',
                    'data': temperature_data,
                    'borderColor': 'rgb(247, 37, 133)',
                    'backgroundColor': 'rgba(247, 37, 133, 0.1)',
                    'borderWidth': 2,
                    'tension': 0.4,
                    'yAxisID': 'y'
                },
                {
                    'label': '湿度',
                    'data': humidity_data,
                    'borderColor': 'rgb(74, 214, 109)',
                    'backgroundColor': 'rgba(74, 214, 109, 0.1)',
                    'borderWidth': 2,
                    'tension': 0.4,
                    'yAxisID': 'y1'
                }
            ],
            'units': {
                'temperature': '°C',
                'humidity': '%'
            },
            'sources': {
                'temperature': 'DHT22',
                'humidity': 'DHT22'
            },
            'timezone': f"UTC+{Config.TIMEZONE_OFFSET}"
        })
    
    except Exception as e:
        logger.error(f"获取温湿度图表数据失败: {e}")
        # 返回示例数据作为后备
        return jsonify(generate_temp_humi_sample_data(24))

@charts_bp.route('/voc_nox', methods=['GET'])
def get_voc_nox_chart_data():
    """获取VOC/NOx图表数据"""
    try:
        hours = request.args.get('hours', default=24, type=int)
        
        # 生成示例数据（未来应查询真实数据）
        from datetime import datetime, timedelta
        from app.utils.time_utils import get_local_now
        
        labels = []
        voc_data = []
        nox_data = []
        
        if hours <= 1:
            points = 30
        elif hours <= 6:
            points = 36
        elif hours <= 24:
            points = 48
        else:
            points = 56
        
        now_local = get_local_now()
        start_time = now_local - timedelta(hours=hours)
        
        voc_base = 100
        nox_base = 1
        
        for i in range(points):
            point_time = start_time + timedelta(hours=hours * i / points)
            
            if hours <= 24:
                labels.append(point_time.strftime('%H:%M'))
            else:
                labels.append(point_time.strftime('%m-%d %H:%M'))
            
            # 模拟VOC和NOx数据
            import random
            import math
            
            time_of_day = (i % points) / points
            voc_variation = 150 * math.sin(time_of_day * 2 * math.pi) + random.uniform(-30, 30)
            nox_variation = 100 * math.sin(time_of_day * math.pi) + random.uniform(-20, 20)
            
            voc_data.append(max(1, min(500, int(voc_base + voc_variation))))
            nox_data.append(max(1, min(500, int(nox_base + nox_variation))))
        
        return jsonify({
            'success': True,
            'count': points,
            'labels': labels,
            'datasets': [
                {
                    'label': 'VOC指数 (示例数据)',
                    'data': voc_data,
                    'borderColor': 'rgb(255, 159, 64)',
                    'backgroundColor': 'rgba(255, 159, 64, 0.1)',
                    'borderWidth': 2,
                    'tension': 0.4
                },
                {
                    'label': 'NOx指数 (示例数据)',
                    'data': nox_data,
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.1)',
                    'borderWidth': 2,
                    'tension': 0.4
                }
            ],
            'units': 'index',
            'source': 'SGP41 (示例数据)'
        })
    
    except Exception as e:
        logger.error(f"获取VOC/NOx图表数据失败: {e}")
        return jsonify({'error': '获取图表数据失败', 'message': str(e)}), 500