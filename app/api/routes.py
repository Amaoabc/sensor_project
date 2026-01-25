# app/api/routes.py
"""
API路由模块
"""

import time
from flask import Blueprint, jsonify, request
from app import db
from app.models import SensorData
from config.settings import Config
from config.sensors import SensorConfig
from app.utils.time_utils import get_local_now
from config.logging_config import get_logger

logger = get_logger(__name__)

api_bp = Blueprint('api', __name__)

@api_bp.route('/environment', methods=['GET'])
def get_environment_data():
    """获取当前所有传感器数据"""
    from flask import current_app
    
    try:
        sensor_manager = current_app.sensor_manager
        latest_data = sensor_manager.get_latest_data()
        sensor_status = sensor_manager.get_sensor_status()
        
        # 获取健康状态
        health_status = sensor_manager.get_health_status()
        
        # 获取当前本地时间
        local_now = get_local_now()
        
        response_data = {
            "timestamp": int(latest_data['timestamp']) if latest_data['timestamp'] else int(time.time()),
            "iso_timestamp": local_now.isoformat(),
            "local_timestamp": local_now.isoformat(),
            "timezone": f"UTC+{Config.TIMEZONE_OFFSET}",
            "sensors": {
                "scd40": {
                    "co2": latest_data['scd40']['co2'],
                    "temperature": None,
                    "humidity": None,
                    "status": health_status['scd40']
                },
                "dht22": {
                    "temperature": latest_data['dht22']['temperature'],
                    "humidity": latest_data['dht22']['humidity'],
                    "status": health_status['dht22']
                }
            },
            "units": {
                "co2": "ppm",
                "temperature": "°C",
                "humidity": "%"
            }
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"获取环境数据失败: {e}")
        return jsonify({
            "error": "传感器读取失败",
            "message": str(e),
            "timestamp": int(time.time())
        }), 500

@api_bp.route('/history', methods=['GET'])
def get_history_data():
    """获取历史数据"""
    try:
        limit = min(request.args.get('limit', default=Config.DEFAULT_HISTORY_LIMIT, type=int), 
                   Config.MAX_HISTORY_LIMIT)
        
        start_time = request.args.get('start_time', type=str)
        end_time = request.args.get('end_time', type=str)
        
        query = SensorData.query
        
        if start_time:
            try:
                from datetime import datetime
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                query = query.filter(SensorData.timestamp >= start_dt)
            except ValueError:
                return jsonify({'error': '无效的起始时间格式，请使用ISO格式'}), 400
        
        if end_time:
            try:
                from datetime import datetime
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                query = query.filter(SensorData.timestamp <= end_dt)
            except ValueError:
                return jsonify({'error': '无效的结束时间格式，请使用ISO格式'}), 400
        
        records = query.order_by(SensorData.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'count': len(records),
            'limit': limit,
            'data': [record.to_dict() for record in records]
        })
    
    except Exception as e:
        logger.error(f"获取历史数据失败: {e}")
        return jsonify({'error': '获取历史数据失败', 'message': str(e)}), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    from flask import current_app
    
    # 检查数据库
    db_status = "online"
    try:
        db.session.execute("SELECT 1")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        db_status = "offline"
    
    # 获取传感器健康状态
    sensor_manager = current_app.sensor_manager
    sensor_health = sensor_manager.get_health_status()
    
    # 获取过滤器统计
    filter_stats = {}
    if sensor_manager.sensors.get('dht22'):
        filter_stats = sensor_manager.sensors['dht22'].filter.get_stats()
    
    healthy_count = sum(1 for status in [sensor_health['scd40'], sensor_health['dht22'], db_status] 
                       if status == 'online')
    total_count = 3
    
    if healthy_count == total_count:
        overall_status = "healthy"
    elif healthy_count >= total_count // 2:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    return jsonify({
        "status": overall_status,
        "service": "sensor_api_dual",
        "version": "4.0",
        "timestamp": int(time.time()),
        "local_time": get_local_now().isoformat(),
        "timezone": f"UTC+{Config.TIMEZONE_OFFSET}",
        "components": {
            "scd40": sensor_health['scd40'],
            "dht22": sensor_health['dht22'],
            "database": db_status,
            "api": "online"
        },
        "sensor_status": sensor_manager.get_sensor_status(),
        "filter_stats": filter_stats
    })

@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    try:
        import os
        from datetime import datetime, timedelta
        from config.settings import Config
        
        total_records = SensorData.query.count()
        
        day_ago = datetime.utcnow() - timedelta(days=1)
        recent_records = SensorData.query.filter(SensorData.timestamp >= day_ago).count()
        
        earliest = SensorData.query.order_by(SensorData.timestamp.asc()).first()
        latest = SensorData.query.order_by(SensorData.timestamp.desc()).first()
        
        return jsonify({
            "success": True,
            "stats": {
                "total_records": total_records,
                "recent_24h_records": recent_records,
                "earliest_record": earliest.timestamp.isoformat() if earliest else None,
                "latest_record": latest.timestamp.isoformat() if latest else None,
                "database_size": os.path.getsize(Config.DATABASE_PATH) if Config.DATABASE_PATH.exists() else 0
            },
            "timezone": f"UTC+{Config.TIMEZONE_OFFSET}"
        })
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({"error": "获取统计信息失败", "message": str(e)}), 500


@api_bp.route('/filter_stats', methods=['GET'])
def get_filter_stats():
    """获取数据过滤器统计信息"""
    from flask import current_app
    
    try:
        sensor_manager = current_app.sensor_manager
        # 检查 DHT22 传感器是否存在
        if hasattr(sensor_manager.sensors.get('dht22'), 'filter'):
            stats = sensor_manager.sensors['dht22'].filter.get_stats()
            
            return jsonify({
                "success": True,
                "sensor": "dht22",
                "filter_enabled": SensorConfig.DHT22_CONFIG['data_filter']['enabled'],
                "stats": stats,
                "config": {
                    "window_size": SensorConfig.DHT22_CONFIG['data_filter']['window_size'],
                    "temperature": SensorConfig.DHT22_CONFIG['data_filter']['temperature'],
                    "humidity": SensorConfig.DHT22_CONFIG['data_filter']['humidity']
                },
                "timestamp": int(time.time()),
                "local_time": get_local_now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": "DHT22传感器未初始化或没有数据过滤器"
            }), 404
    except Exception as e:
        logger.error(f"获取过滤器统计信息失败: {e}")
        return jsonify({
            "error": "获取过滤器统计信息失败",
            "message": str(e)
        }), 500

@api_bp.route('/reset_filter', methods=['POST'])
def reset_filter():
    """重置数据过滤器"""
    from flask import current_app
    
    try:
        sensor_manager = current_app.sensor_manager
        # 检查 DHT22 传感器是否存在
        if hasattr(sensor_manager.sensors.get('dht22'), 'filter'):
            sensor_manager.sensors['dht22'].filter.reset()
            logger.info("DHT22数据过滤器已重置")
            
            return jsonify({
                "success": True,
                "message": "数据过滤器已重置",
                "timestamp": int(time.time())
            })
        else:
            return jsonify({
                "success": False,
                "error": "DHT22传感器未初始化或没有数据过滤器"
            }), 404
    except Exception as e:
        logger.error(f"重置过滤器失败: {e}")
        return jsonify({
            "error": "重置过滤器失败",
            "message": str(e)
        }), 500    
