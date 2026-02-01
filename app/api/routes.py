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
                },
                "sgp41": {
                    "sraw_voc": latest_data['sgp41']['sraw_voc'],
                    "sraw_nox": latest_data['sgp41']['sraw_nox'],
                    "voc_index": latest_data['sgp41']['voc_index'],
                    "nox_index": latest_data['sgp41']['nox_index'],
                    "status": health_status['sgp41']
                }
            },
            "units": {
                "co2": "ppm",
                "temperature": "°C",
                "humidity": "%",
                "sraw_voc": "ticks",
                "sraw_nox": "ticks",
                "voc_index": "index",
                "nox_index": "index"
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
    
    # 添加SGP41过滤器统计
    sgp41_filter_stats = {}
    if sensor_manager.sensors.get('sgp41'):
        sgp41_status = sensor_manager.sensors['sgp41'].get_status()
        sgp41_filter_stats = {
            'voc': sgp41_status.get('voc_filter_stats', {}),
            'nox': sgp41_status.get('nox_filter_stats', {})
        }

    healthy_count = sum(1 for status in [
        sensor_health['scd40'], 
        sensor_health['dht22'], 
        sensor_health['sgp41'],
        db_status
    ] if status == 'online')
    total_count = 4
    
    if healthy_count == total_count:
        overall_status = "healthy"
    elif healthy_count >= total_count // 2:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    return jsonify({
        "status": overall_status,
        "service": "sensor_api_triple",
        "version": "5.0",
        "timestamp": int(time.time()),
        "local_time": get_local_now().isoformat(),
        "timezone": f"UTC+{Config.TIMEZONE_OFFSET}",
        "components": {
            "scd40": sensor_health['scd40'],
            "dht22": sensor_health['dht22'],
            "sgp41": sensor_health['sgp41'],
            "database": db_status,
            "api": "online"
        },
        "sensor_status": sensor_manager.get_sensor_status(),
        "filter_stats": filter_stats,
        "sgp41_filter_stats": sgp41_filter_stats
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

@api_bp.route('/sgp41/stats', methods=['GET'])
def get_sgp41_stats():
    """获取SGP41传感器统计信息"""
    from flask import current_app
    
    try:
        sensor_manager = current_app.sensor_manager
        if not sensor_manager.sensors.get('sgp41'):
            return jsonify({
                "success": False,
                "error": "SGP41传感器未初始化"
            }), 404
        
        status = sensor_manager.sensors['sgp41'].get_status()
        
        return jsonify({
            "success": True,
            "sensor": "sgp41",
            "status": status,
            "config": SensorConfig.SGP41_CONFIG,
            "timestamp": int(time.time())
        })
    except Exception as e:
        logger.error(f"获取SGP41统计信息失败: {e}")
        return jsonify({
            "error": "获取统计信息失败",
            "message": str(e)
        }), 500

@api_bp.route('/sgp41/self_test', methods=['POST'])
def sgp41_self_test():
    """执行SGP41自检"""
    from flask import current_app
    
    try:
        sensor_manager = current_app.sensor_manager
        if not sensor_manager.sensors.get('sgp41'):
            return jsonify({
                "success": False,
                "error": "SGP41传感器未初始化"
            }), 404
        
        success, message = sensor_manager.sensors['sgp41'].self_test()
        
        return jsonify({
            "success": success,
            "message": message,
            "timestamp": int(time.time())
        })
    except Exception as e:
        logger.error(f"SGP41自检失败: {e}")
        return jsonify({
            "error": "自检失败",
            "message": str(e)
        }), 500

@api_bp.route('/sgp41/reset_filters', methods=['POST'])
def reset_sgp41_filters():
    """重置SGP41数据过滤器"""
    from flask import current_app
    
    try:
        sensor_manager = current_app.sensor_manager
        if not sensor_manager.sensors.get('sgp41'):
            return jsonify({
                "success": False,
                "error": "SGP41传感器未初始化"
            }), 404
        
        sensor_manager.sensors['sgp41'].reset_filters()
        
        return jsonify({
            "success": True,
            "message": "SGP41数据过滤器已重置",
            "timestamp": int(time.time())
        })
    except Exception as e:
        logger.error(f"重置SGP41过滤器失败: {e}")
        return jsonify({
            "error": "重置过滤器失败",
            "message": str(e)
        }), 500

@api_bp.route('/sgp41/algorithm', methods=['GET'])
def get_sgp41_algorithm_status():
    """获取SGP41算法学习状态"""
    from flask import current_app
    
    try:
        sensor_manager = current_app.sensor_manager
        if not sensor_manager.sensors.get('sgp41'):
            return jsonify({
                "success": False,
                "error": "SGP41传感器未初始化"
            }), 404
        
        sensor = sensor_manager.sensors['sgp41']
        algorithm_status = {}
        
        # 获取算法参数
        if sensor.voc_algorithm:
            try:
                voc_params = sensor.voc_algorithm.get_tuning_parameters()
                algorithm_status['voc'] = {
                    'index_offset': voc_params[0],
                    'learning_time_offset_hours': voc_params[1],
                    'learning_time_gain_hours': voc_params[2],
                    'gating_max_duration_minutes': voc_params[3],
                    'std_initial': voc_params[4],
                    'gain_factor': voc_params[5]
                }
            except:
                algorithm_status['voc'] = "无法获取参数"
        
        if sensor.nox_algorithm:
            try:
                nox_params = sensor.nox_algorithm.get_tuning_parameters()
                algorithm_status['nox'] = {
                    'index_offset': nox_params[0],
                    'learning_time_offset_hours': nox_params[1],
                    'learning_time_gain_hours': nox_params[2],
                    'gating_max_duration_minutes': nox_params[3],
                    'std_initial': nox_params[4],
                    'gain_factor': nox_params[5]
                }
            except:
                algorithm_status['nox'] = "无法获取参数"
        
        return jsonify({
            "success": True,
            "sensor": "sgp41",
            "algorithm_status": algorithm_status,
            "timestamp": int(time.time()),
            "local_time": get_local_now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取SGP41算法状态失败: {e}")
        return jsonify({
            "error": "获取算法状态失败",
            "message": str(e)
        }), 500
    
@api_bp.route('/sgp41/convert', methods=['POST'])
def convert_voc_index():
    """将VOC指数转换为建筑标准浓度"""
    from flask import current_app
    import math
    
    try:
        data = request.get_json()
        voc_index = data.get('voc_index')
        
        if voc_index is None:
            return jsonify({
                "success": False,
                "error": "需要提供voc_index参数"
            }), 400
        
        try:
            voc_index = float(voc_index)
        except ValueError:
            return jsonify({
                "success": False,
                "error": "voc_index必须是数字"
            }), 400
        
        # 检查范围
        if voc_index >= 501 or voc_index < 0:
            return jsonify({
                "success": False,
                "error": "VOC指数必须在0-500范围内"
            }), 400
        
        # 根据应用笔记公式转换
        try:
            # TVOC_Ethanol[ppb] = (ln(501 - VOC_Index) - 6.24) × (-381.97)
            tvoc_ethanol_ppb = (math.log(501 - voc_index) - 6.24) * (-381.97)
            
            # WELL建筑标准：TVOC_Molhave[μg/m³] = 0.58 × TVOC_Ethanol[ppb] × 4.5
            tvoc_well = 0.58 * tvoc_ethanol_ppb * 4.5
            
            # RESET Air标准：TVOC_Isobutylene[μg/m³] = 2.3 × TVOC_Ethanol[ppb]
            tvoc_reset = 2.3 * tvoc_ethanol_ppb
            
            return jsonify({
                "success": True,
                "conversions": {
                    "voc_index": voc_index,
                    "tvoc_ethanol_ppb": round(tvoc_ethanol_ppb, 2),
                    "tvoc_well_ug_m3": round(tvoc_well, 2),  # WELL建筑标准
                    "tvoc_reset_ug_m3": round(tvoc_reset, 2),  # RESET Air标准
                    "standards": {
                        "well_building_standard": {
                            "description": "WELL建筑标准 - Molhave混合气体等效",
                            "unit": "μg/m³",
                            "formula": "TVOC_Molhave = 0.58 × TVOC_Ethanol × 4.5"
                        },
                        "reset_air": {
                            "description": "RESET Air标准 - 异丁烯等效",
                            "unit": "μg/m³",
                            "formula": "TVOC_Isobutylene = 2.3 × TVOC_Ethanol"
                        }
                    }
                },
                "timestamp": int(time.time())
            })
        except Exception as calc_error:
            logger.error(f"VOC指数转换计算失败: {calc_error}")
            return jsonify({
                "success": False,
                "error": "转换计算失败",
                "message": str(calc_error)
            }), 500
            
    except Exception as e:
        logger.error(f"VOC指数转换失败: {e}")
        return jsonify({
            "error": "转换失败",
            "message": str(e)
        }), 500

@api_bp.route('/sgp41/conditioning', methods=['GET'])
def get_sgp41_conditioning_status():
    """获取SGP41调节状态"""
    from flask import current_app
    
    try:
        sensor_manager = current_app.sensor_manager
        if not sensor_manager.sensors.get('sgp41'):
            return jsonify({
                "success": False,
                "error": "SGP41传感器未初始化"
            }), 404
        
        sensor = sensor_manager.sensors['sgp41']
        
        # 计算调节剩余时间
        remaining_time = 0
        conditioning_in_progress = False
        
        if sensor.conditioning_start_time > 0:
            elapsed = time.time() - sensor.conditioning_start_time
            conditioning_time = sensor.config.get('conditioning_time', 10)
            
            if elapsed < conditioning_time:
                conditioning_in_progress = True
                remaining_time = max(0, conditioning_time - elapsed)
        
        return jsonify({
            "success": True,
            "conditioning_status": {
                "is_conditioned": sensor.is_conditioned,
                "conditioning_in_progress": conditioning_in_progress,
                "conditioning_start_time": sensor.conditioning_start_time,
                "last_conditioning_time": sensor.conditioning_start_time,
                "remaining_time_seconds": round(remaining_time, 1),
                "config": {
                    "conditioning_time": sensor.config.get('conditioning_time', 10),
                    "requires_conditioning": not sensor.is_conditioned
                }
            },
            "timestamp": int(time.time())
        })
    except Exception as e:
        logger.error(f"获取SGP41调节状态失败: {e}")
        return jsonify({
            "error": "获取调节状态失败",
            "message": str(e)
        }), 500

@api_bp.route('/data_quality', methods=['GET'])
def get_data_quality():
    """评估数据质量"""
    from flask import current_app
    from datetime import datetime, timedelta
    
    try:
        sensor_manager = current_app.sensor_manager
        
        # 获取最近1小时的数据
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        records = SensorData.query.filter(
            SensorData.timestamp >= one_hour_ago
        ).order_by(SensorData.timestamp.desc()).limit(360).all()  # 最多360条（每小时最多3600秒，但可能采样没那么快）
        
        quality_metrics = {
            "sgp41": {
                "data_points": 0,
                "valid_voc_index": 0,
                "valid_nox_index": 0,
                "avg_voc_index": 0,
                "avg_nox_index": 0,
                "stability_score": 0
            },
            "dht22": {
                "data_points": 0,
                "valid_temperature": 0,
                "valid_humidity": 0
            }
        }
        
        # 分析SGP41数据质量
        sgp41_voc_values = []
        sgp41_nox_values = []
        
        for record in records:
            if hasattr(record, 'sgp41_voc_index') and record.sgp41_voc_index is not None:
                quality_metrics['sgp41']['data_points'] += 1
                quality_metrics['sgp41']['valid_voc_index'] += 1
                sgp41_voc_values.append(record.sgp41_voc_index)
            
            if hasattr(record, 'sgp41_nox_index') and record.sgp41_nox_index is not None:
                quality_metrics['sgp41']['valid_nox_index'] += 1
                sgp41_nox_values.append(record.sgp41_nox_index)
            
            if hasattr(record, 'dht22_temperature') and record.dht22_temperature is not None:
                quality_metrics['dht22']['data_points'] += 1
                quality_metrics['dht22']['valid_temperature'] += 1
            
            if hasattr(record, 'dht22_humidity') and record.dht22_humidity is not None:
                quality_metrics['dht22']['valid_humidity'] += 1
        
        # 计算统计数据
        if sgp41_voc_values:
            quality_metrics['sgp41']['avg_voc_index'] = sum(sgp41_voc_values) / len(sgp41_voc_values)
            
        if sgp41_nox_values:
            quality_metrics['sgp41']['avg_nox_index'] = sum(sgp41_nox_values) / len(sgp41_nox_values)
        
        # 计算数据完整性百分比
        total_possible = 3600  # 1小时最多3600秒
        quality_metrics['sgp41']['completeness_percentage'] = (
            quality_metrics['sgp41']['data_points'] / total_possible * 100
            if total_possible > 0 else 0
        )
        
        quality_metrics['dht22']['completeness_percentage'] = (
            quality_metrics['dht22']['data_points'] / total_possible * 100
            if total_possible > 0 else 0
        )
        
        # 总体质量评分
        overall_quality = (
            quality_metrics['sgp41']['completeness_percentage'] * 0.5 +
            quality_metrics['dht22']['completeness_percentage'] * 0.5
        ) / 100 * 100
        
        return jsonify({
            "success": True,
            "time_range": {
                "start": one_hour_ago.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "quality_metrics": quality_metrics,
            "overall_quality_score": round(overall_quality, 1),
            "quality_assessment": {
                "excellent": overall_quality >= 90,
                "good": 70 <= overall_quality < 90,
                "fair": 50 <= overall_quality < 70,
                "poor": overall_quality < 50
            },
            "recommendations": [] if overall_quality >= 70 else [
                "数据完整性较低，检查传感器连接",
                "确保传感器调节已完成"
            ]
        })
        
    except Exception as e:
        logger.error(f"评估数据质量失败: {e}")
        return jsonify({"error": "评估数据质量失败", "message": str(e)}), 500

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
        return jsonify({"error": "获取过滤器统计信息失败","message": str(e)}), 500

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

