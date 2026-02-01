# app/sensors/sgp41.py
"""
SGP41传感器模块
"""

import time
import threading
import board
from sensirion_i2c_driver import I2cConnection, LinuxI2cTransceiver
from sensirion_i2c_sgp4x import Sgp41I2cDevice
from sensirion_i2c_sgp4x.sgp41.commands import Sgp41I2cCmdMeasureRawSignals
from sensirion_gas_index_algorithm.voc_algorithm import VocAlgorithm
from sensirion_gas_index_algorithm.nox_algorithm import NoxAlgorithm
from config.logging_config import get_logger
from app.sensors.data_filter import SensorDataFilter
from config.sensors import SensorConfig

logger = get_logger(__name__)

class SGP41Sensor:
    """SGP41 VOC和NOx传感器封装"""
    
    def __init__(self):
        self.config = SensorConfig.SGP41_CONFIG
        self.sensor = None
        self.voc_algorithm = None
        self.nox_algorithm = None
        self.sgp_lock = threading.Lock()
        
        # 数据过滤器
        self.voc_filter = SensorDataFilter(self._get_voc_filter_config(), 'sgp41_voc')
        self.nox_filter = SensorDataFilter(self._get_nox_filter_config(), 'sgp41_nox')
        
        # 状态跟踪
        self.is_conditioned = False
        self.conditioning_start_time = 0
        self.last_read_time = 0
        self.last_data = {
            'sraw_voc': None,
            'sraw_nox': None,
            'voc_index': None,
            'nox_index': None,
            'timestamp': 0
        }
        
        # 补偿数据源
        self.compensation_temp = 25.0  # 默认值
        self.compensation_humi = 50.0  # 默认值
        
        # 日志抑制配置（与现有传感器一致）
        self.sgp_log = {
            'last_msg': None,
            'last_time': 0,
            'min_interval': 60,
            'error_interval': 300
        }
        
        self._initialize()
    
    def _get_voc_filter_config(self):
        """获取VOC指数过滤器配置"""
        return {
            'data_filter': {
                'window_size': self.config['data_filter']['window_size'],
                'temperature': self.config['data_filter']['voc_index'],
                'humidity': self.config['data_filter']['voc_index']
            }
        }
    
    def _get_nox_filter_config(self):
        """获取NOx指数过滤器配置"""
        return {
            'data_filter': {
                'window_size': self.config['data_filter']['window_size'],
                'temperature': self.config['data_filter']['nox_index'],
                'humidity': self.config['data_filter']['nox_index']
            }
        }
    
    def _initialize(self):
        """初始化传感器和算法"""
        try:
            # 修正：使用正确的I2C连接方式
            # 对于树莓派，通常使用 /dev/i2c-1
            # 如果这个不行，可以尝试 /dev/i2c-0
            try:
                i2c_transceiver = LinuxI2cTransceiver('/dev/i2c-1')
            except Exception as e:
                logger.warning(f"无法打开 /dev/i2c-1: {e}，尝试 /dev/i2c-0")
                i2c_transceiver = LinuxI2cTransceiver('/dev/i2c-0')
            
            # 创建I2C连接
            i2c_connection = I2cConnection(i2c_transceiver)
            
            # 创建SGP41设备实例
            self.sensor = Sgp41I2cDevice(i2c_connection, self.config['i2c_address'])
            
            # 初始化算法引擎
            algorithm_config = self.config['algorithm']
            self.voc_algorithm = VocAlgorithm(
                sampling_interval=algorithm_config['sampling_interval']
            )
            self.nox_algorithm = NoxAlgorithm()
            
            # 设置算法参数
            voc_params = algorithm_config['voc_algorithm_params']
            self.voc_algorithm.set_tuning_parameters(
                index_offset=voc_params['index_offset'],
                learning_time_offset_hours=voc_params['learning_time_offset_hours'],
                learning_time_gain_hours=voc_params['learning_time_gain_hours'],
                gating_max_duration_minutes=voc_params['gating_max_duration_minutes'],
                std_initial=voc_params['std_initial'],
                gain_factor=voc_params['gain_factor']
            )
            
            nox_params = algorithm_config['nox_algorithm_params']
            # 使用get方法提供默认值，防止配置不完整
            self.nox_algorithm.set_tuning_parameters(
                index_offset=nox_params['index_offset'],
                learning_time_offset_hours=nox_params['learning_time_offset_hours'],
                learning_time_gain_hours=nox_params.get('learning_time_gain_hours', 12),  # 默认12小时
                gating_max_duration_minutes=nox_params['gating_max_duration_minutes'],
                std_initial=nox_params.get('std_initial', 50),  # 默认50
                gain_factor=nox_params['gain_factor']
            )
            
            logger.info(f"SGP41初始化成功 (I2C地址: 0x{self.config['i2c_address']:02x})")
            
        except Exception as e:
            logger.error(f"SGP41初始化失败: {e}")
            raise
    
    def set_compensation_data(self, temperature, humidity):
        """设置温湿度补偿数据（从DHT22获取）"""
        logger.debug(f"SGP41补偿数据更新: 温度={temperature}°C, 湿度={humidity}%")
        self.compensation_temp = temperature
        self.compensation_humi = humidity
    
    def conditioning(self):
        """执行传感器调节（必须在首次测量前调用）"""
        if self.is_conditioned:
            logger.debug("SGP41已经调节过，跳过调节")
            return True
        
        try:
            current_time = time.time()
            
            # 检查是否需要重新调节（超过10分钟需要重新调节）
            if self.conditioning_start_time > 0 and (current_time - self.conditioning_start_time) < 600:
                logger.debug("SGP41调节仍在有效期内")
                return True
            
            # 检查调节时间是否超过10秒（API文档警告）
            if self.config['conditioning_time'] > 10:
                logger.warning(f"SGP41调节时间({self.config['conditioning_time']}秒)超过建议的10秒，可能会损坏传感器")
            
            logger.info(f"开始SGP41调节 ({self.config['conditioning_time']}秒)...")
            
            # 执行调节 - 传递原始百分比和摄氏度，库会内部转换
            with self.sgp_lock:
                logger.debug(f"调用conditioning参数: 湿度={self.compensation_humi}%, 温度={self.compensation_temp}°C")
                
                # 直接传递原始值，库内部会进行转换
                conditioning_result = self.sensor.conditioning(
                    relative_humidity=self.compensation_humi,
                    temperature=self.compensation_temp
                )
                logger.debug(f"SGP41调节结果: {conditioning_result}")
            
            # 等待调节完成
            time.sleep(self.config['conditioning_time'])
            
            self.is_conditioned = True
            self.conditioning_start_time = current_time
            logger.info("SGP41调节完成")
            return True
            
        except Exception as e:
            logger.error(f"SGP41调节失败: {e}")
            self.is_conditioned = False
            return False
    


    def read(self):
        """读取传感器数据（包含温湿度补偿）"""
        retry_attempts = self.config['retry_attempts']
        retry_delay = self.config['retry_delay']
        
        # 检查是否需要调节
        if not self.is_conditioned:
            if not self.conditioning():
                logger.warning("SGP41调节失败，无法读取数据")
                return None, None, None, None
        
        for attempt in range(retry_attempts):
            try:
                with self.sgp_lock:
                    # 注意：使用measure_raw方法，它接收原始百分比和摄氏度
                    logger.debug(f"调用measure_raw参数: 湿度={self.compensation_humi}%, 温度={self.compensation_temp}°C")
                    
                    # 使用measure_raw方法
                    raw_signals = self.sensor.measure_raw(
                        relative_humidity=self.compensation_humi,
                        temperature=self.compensation_temp
                    )
                
                # 解包原始信号
                sraw_voc, sraw_nox = raw_signals
                
                # 调试：打印原始信号
                logger.debug(f"原始信号: sraw_voc={sraw_voc}, sraw_nox={sraw_nox}")
                logger.debug(f"原始信号ticks: sraw_voc.ticks={sraw_voc.ticks if sraw_voc else None}, sraw_nox.ticks={sraw_nox.ticks if sraw_nox else None}")
                
                # 处理原始信号并计算指数
                if sraw_voc is not None and sraw_nox is not None:
                    sraw_voc_ticks = sraw_voc.ticks
                    sraw_nox_ticks = sraw_nox.ticks

                    logger.debug(f"原始信号ticks值: VOC={sraw_voc_ticks}, NOx={sraw_nox_ticks}")

                    # 检查原始信号是否在合理范围内
                    if sraw_voc_ticks == 0 or sraw_nox_ticks == 0:
                        logger.warning(f"原始信号为0: sraw_voc={sraw_voc_ticks}, sraw_nox={sraw_nox_ticks}")
                        
                        time.sleep(retry_delay)
                        continue
                    # 处理原始信号并计算指数
                    logger.debug("处理原始信号...")
                    voc_index = self.voc_algorithm.process(sraw_voc_ticks)
                    nox_index = self.nox_algorithm.process(sraw_nox_ticks)
                    
                    # 调试：打印算法处理结果
                    logger.debug(f"算法处理结果: voc_index={voc_index}, nox_index={nox_index}")
                    
                    # 处理算法初始化阶段：如果指数为0，可能是初始化阶段
                    # 在初始化阶段，我们可以暂时返回原始信号，或者使用默认值
                    if voc_index == 0 or nox_index == 0:
                        logger.debug("算法初始化阶段，指数为0")


                    # 数据过滤
                    filtered_voc_index, _ = self.voc_filter.filter_data(voc_index, None)
                    filtered_nox_index, _ = self.nox_filter.filter_data(nox_index, None)
                    
                    # 调试：打印过滤后结果
                    logger.debug(f"过滤后结果: filtered_voc_index={filtered_voc_index}, filtered_nox_index={filtered_nox_index}")
                    
                    # 验证数据范围
                    if self._validate_data(sraw_voc.ticks, sraw_nox.ticks, filtered_voc_index, filtered_nox_index):
                        # 更新缓存
                        current_time = time.time()
                        self.last_read_time = current_time
                        self.last_data = {
                            'sraw_voc': int(sraw_voc.ticks),
                            'sraw_nox': int(sraw_nox.ticks),
                            'voc_index': int(round(filtered_voc_index)) if filtered_voc_index else None,
                            'nox_index': int(round(filtered_nox_index)) if filtered_nox_index else None,
                            'timestamp': current_time
                        }
                        
                        logger.info(f"SGP41读取成功: VOC指数={filtered_voc_index}, NOx指数={filtered_nox_index}")
                        return (
                            int(sraw_voc.ticks),
                            int(sraw_nox.ticks),
                            int(round(filtered_voc_index)) if filtered_voc_index else None,
                            int(round(filtered_nox_index)) if filtered_nox_index else None
                        )
                    else:
                        logger.debug(f"数据验证失败: sraw_voc={sraw_voc.ticks}, sraw_nox={sraw_nox.ticks}, "
                                    f"voc_index={filtered_voc_index}, nox_index={filtered_nox_index}")
                
                time.sleep(retry_delay)
                
            except Exception as e:
                self._handle_error(e, attempt, retry_attempts)
                time.sleep(retry_delay)
        
        logger.debug(f"SGP41读取失败，已尝试{retry_attempts}次")
        # 返回最后一次有效数据
        return (
            self.last_data['sraw_voc'],
            self.last_data['sraw_nox'],
            self.last_data['voc_index'],
            self.last_data['nox_index']
        )


    def _validate_data(self, sraw_voc, sraw_nox, voc_index, nox_index):
        """验证数据是否在合理范围内"""
        valid_ranges = self.config['valid_ranges']
        
        # 检查原始信号范围
        if sraw_voc is not None:
            if sraw_voc == 0:
                logger.debug("SRAW_VOC为0，可能是传感器故障")
                return False
            if not (valid_ranges['sraw_voc'][0] <= sraw_voc <= valid_ranges['sraw_voc'][1]):
                logger.debug(f"SRAW_VOC超出范围: {sraw_voc}")
                return False
        
        if sraw_nox is not None:
            if sraw_nox == 0:
                logger.debug("SRAW_NOX为0，可能是传感器故障")
                return False
            if not (valid_ranges['sraw_nox'][0] <= sraw_nox <= valid_ranges['sraw_nox'][1]):
                logger.debug(f"SRAW_NOX超出范围: {sraw_nox}")
                return False
        
        # 检查指数范围 - 特殊处理算法初始化阶段
        # 注意：算法初始化阶段可能返回0，这是正常的
        if voc_index is not None:
            # 算法初始化阶段可能返回0，这是正常的，允许通过
            if voc_index == 0:
                logger.debug(f"VOC指数为0（算法初始化阶段），允许通过")
                # 返回True，允许算法继续初始化
                # 不进行范围检查
                pass
            elif not (valid_ranges['voc_index'][0] <= voc_index <= valid_ranges['voc_index'][1]):
                logger.debug(f"VOC指数超出范围: {voc_index}")
                return False
        
        if nox_index is not None:
            # 算法初始化阶段可能返回0，这是正常的，允许通过
            if nox_index == 0:
                logger.debug(f"NOx指数为0（算法初始化阶段），允许通过")
                # 返回True，允许算法继续初始化
                # 不进行范围检查
                pass
            elif not (valid_ranges['nox_index'][0] <= nox_index <= valid_ranges['nox_index'][1]):
                logger.debug(f"NOx指数超出范围: {nox_index}")
                return False
        
        return True
    
    def _handle_error(self, error, attempt, max_attempts):
        """处理错误（与现有传感器一致的策略）"""
        now = time.time()
        
        if attempt == max_attempts - 1:
            logger.error(f"SGP41最终尝试失败: {type(error).__name__}: {error}")
        else:
            if now - self.sgp_log['last_time'] > self.sgp_log['min_interval']:
                logger.debug(f"SGP41读取错误（尝试{attempt+1}/{max_attempts}）: {type(error).__name__}: {error}")
                self.sgp_log['last_time'] = now
    
    def self_test(self):
        """执行自检"""
        try:
            with self.sgp_lock:
                result = self.sensor.measure_test()
            
            # 根据SGP41 API文档，检查低四位是否为0
            # 结果格式：0xXX 0xYY，忽略高字节0xXX，检查低字节0xYY的低四位
            low_byte = result & 0xFF
            if low_byte & 0x0F == 0:
                logger.info("SGP41自检通过")
                return True, "所有测试通过"
            else:
                logger.warning(f"SGP41自检失败: 0x{result:04X}")
                return False, f"自检失败: 0x{result:04X}"
                
        except Exception as e:
            logger.error(f"SGP41自检异常: {e}")
            return False, f"自检异常: {str(e)}"
    
    def get_status(self):
        """获取传感器状态"""
        return {
            'initialized': self.sensor is not None,
            'is_conditioned': self.is_conditioned,
            'conditioning_start_time': self.conditioning_start_time,
            'last_read_time': self.last_read_time,
            'last_data': self.last_data,
            'voc_filter_stats': self.voc_filter.get_stats(),
            'nox_filter_stats': self.nox_filter.get_stats(),
            'algorithms': {
                'voc': self.voc_algorithm is not None,
                'nox': self.nox_algorithm is not None
            }
        }
    
    def reset_filters(self):
        """重置数据过滤器"""
        self.voc_filter.reset()
        self.nox_filter.reset()
        logger.info("SGP41数据过滤器已重置")
    
    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'sensor') and self.sensor:
            try:
                self.sensor.connection.close()
                logger.info("SGP41连接已关闭")
            except Exception as e:
                logger.error(f"SGP41连接关闭失败: {e}")

    def convert_to_tvoc_well(self, voc_index):
        """根据WELL建筑标准将VOC指数转换为TVOC浓度 (μg/m³)"""
        if voc_index is None or voc_index >= 501:
            return None
        import math
        try:
            # 公式: TVOC_Molhave[μg/m³] = (ln(501 - VOC_Index) - 6.24) × (-996.94)
            tvoc = (math.log(501 - voc_index) - 6.24) * (-996.94)
            return max(0, tvoc)  # 确保非负
        except (ValueError, TypeError) as e:
            logger.error(f"TVOC转换失败: {e}")
            return None

    def convert_to_tvoc_reset(self, voc_index):
        """根据RESET Air标准将VOC指数转换为TVOC浓度 (μg/m³)"""
        if voc_index is None or voc_index >= 501:
            return None
        import math
        try:
            # 公式: TVOC_Isobutylene[μg/m³] = (ln(501 - VOC_Index) - 6.24) × (-878.53)
            tvoc = (math.log(501 - voc_index) - 6.24) * (-878.53)
            return max(0, tvoc)  # 确保非负
        except (ValueError, TypeError) as e:
            logger.error(f"TVOC转换失败: {e}")
            return None
