#!/usr/bin/env python3
"""
树莓派SCD40和DHT22传感器读取程序
用于比较SCD40和DHT22的温湿度数据
"""

import time
import json
import board
import busio
import adafruit_scd4x
import adafruit_dht
from datetime import datetime
from pathlib import Path

class DualSensorMonitor:
    def __init__(self, dht_pin=board.D4, scd4x_i2c_address=0x62):
        """
        初始化传感器
        参数:
        - dht_pin: DHT22的数据引脚 (默认GPIO4/board.D4)
        - scd4x_i2c_address: SCD40的I2C地址 (默认0x62)
        """
        self.dht_pin = dht_pin
        self.scd4x_address = scd4x_i2c_address
        
        # 初始化传感器
        self._init_scd4x()
        self._init_dht22()
        
        # 数据存储
        self.scd40_data = {"temperature": None, "humidity": None, "co2": None}
        self.dht22_data = {"temperature": None, "humidity": None}
        
        # 统计数据
        self.read_count = 0
        self.dht22_fail_count = 0
        self.scd40_ready_checks = 0
        
        print("传感器初始化完成!")
        print(f"DHT22 使用引脚: {dht_pin}")
        print(f"SCD40 I2C地址: {hex(scd4x_i2c_address)}")
        print("读取触发: SCD40 data_ready为True时自动读取\n")
    
    def _init_scd4x(self):
        """初始化SCD40传感器 - 修复版"""
        try:
            # 创建I2C连接
            i2c = busio.I2C(board.SCL, board.SDA)
            
            # 尝试创建传感器对象
            self.scd4x = adafruit_scd4x.SCD4X(i2c, address=self.scd4x_address)
            print("SCD40 对象创建成功")
            
            # 先尝试停止可能的测量
            try:
                self.scd4x.stop_periodic_measurement()
                print("已发送停止测量命令")
                time.sleep(1)  # 等待传感器停止
            except Exception as e:
                print(f"停止测量时可能已停止或无需停止: {e}")
            
            # 现在可以安全读取序列号等信息
            try:
                serial = [hex(i) for i in self.scd4x.serial_number]
                print(f"SCD40 序列号: {serial}")
            except Exception as e:
                print(f"无法读取序列号: {e}")
            
            # 启动传感器
            self.scd4x.start_periodic_measurement()
            print("已启动周期性测量")
            
            # 等待传感器预热
            print("SCD40 正在预热，首次测量需要约5秒...")
            
        except Exception as e:
            print(f"SCD40 初始化失败: {e}")
            print("请检查以下可能原因:")
            print("1. 传感器之前未正确关闭，尝试物理重启传感器（断开VCC再重新连接）")
            print("2. I2C地址不正确，尝试运行: sudo i2cdetect -y 1")
            print("3. I2C总线问题，检查接线:")
            print("   - SDA -> GPIO2 (引脚3)")
            print("   - SCL -> GPIO3 (引脚5)")
            print("   - VCC -> 3.3V (引脚1或17)")
            print("   - GND -> GND (引脚6、9、14、20或30)")
            self.scd4x = None
    
    def _init_dht22(self):
        """初始化DHT22传感器"""
        try:
            # 注意: DHT22使用GPIO引脚
            self.dht22 = adafruit_dht.DHT22(self.dht_pin, use_pulseio=False)
            print("DHT22 初始化成功")
        except Exception as e:
            print(f"DHT22 初始化失败: {e}")
            print("请检查:")
            print("1. 引脚连接 (默认GPIO4)")
            print("2. 是否需要上拉电阻（10kΩ到3.3V）")
            print("3. 电源是否稳定")
            self.dht22 = None
    
    def wait_for_scd40_ready(self, check_interval=5, max_checks=10):
        """
        等待SCD40数据就绪
        参数:
        - check_interval: 检查间隔(秒)
        - max_checks: 最大检查次数
        返回: True=数据就绪, False=超时或传感器不可用
        """
        if not self.scd4x:
            print("SCD40传感器未初始化")
            return False
            
        for i in range(max_checks):
            self.scd40_ready_checks += 1
            
            try:
                if self.scd4x.data_ready:
                    if i > 0:
                        print(f"SCD40数据就绪，等待了{i*check_interval:.1f}秒")
                    return True
            except Exception as e:
                print(f"检查数据就绪状态时出错: {e}")
                return False
                
            # 显示等待状态（每10次显示一次）
            if i % 10 == 0 and i > 0:
                print(f"等待SCD40数据就绪... 已等待{i*check_interval:.1f}秒")
                
            time.sleep(check_interval)
        
        print(f"SCD40数据等待超时 ({max_checks*check_interval}秒)")
        return False
    
    def read_scd4x(self):
        """读取SCD40数据（仅在data_ready为True时读取）"""
        if not self.scd4x:
            return False
            
        try:
            # 检查数据是否就绪
            if not self.scd4x.data_ready:
                return False
            
            # 读取所有数据
            self.scd40_data["co2"] = self.scd4x.CO2
            self.scd40_data["temperature"] = self.scd4x.temperature
            self.scd40_data["humidity"] = self.scd4x.relative_humidity
            return True
        except Exception as e:
            print(f"SCD40 读取错误: {e}")
            return False
    
    def read_dht22(self):
        """读取DHT22数据（需要错误处理）"""
        if not self.dht22:
            return False
            
        try:
            # DHT22读取可能失败，需要重试机制
            temperature = self.dht22.temperature
            humidity = self.dht22.humidity
            
            if temperature is not None and humidity is not None:
                self.dht22_data["temperature"] = temperature
                self.dht22_data["humidity"] = humidity
                return True
            else:
                self.dht22_fail_count += 1
                return False
                
        except RuntimeError as e:
            # DHT22常见的读取错误
            self.dht22_fail_count += 1
            return False
        except Exception as e:
            print(f"DHT22 读取异常: {e}")
            self.dht22_fail_count += 1
            return False
    
    def read_all_when_ready(self):
        """
        当SCD40数据就绪时读取两个传感器
        返回: 成功读取的传感器数量
        """
        # 等待SCD40数据就绪
        if not self.wait_for_scd40_ready():
            return 0
        
        success_count = 0
        
        # 读取SCD40
        if self.read_scd4x():
            success_count += 1
        
        # 读取DHT22
        if self.read_dht22():
            success_count += 1
            
        self.read_count += 1
        return success_count
    
    def format_output(self):
        """格式化输出数据"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        output = f"\n[{timestamp}] 第{self.read_count}次读取 (触发: SCD40数据就绪)\n"
        output += "=" * 50
        
        # SCD40数据
        output += "\n[SCD40 - 高精度传感器]\n"
        if self.scd40_data["co2"] is not None:
            output += f"  CO₂: {self.scd40_data['co2']:>6.0f} ppm\n"
            output += f"  温度: {self.scd40_data['temperature']:>6.1f} °C\n"
            output += f"  湿度: {self.scd40_data['humidity']:>6.1f} %RH\n"
        else:
            output += "  数据未就绪...\n"
        
        # DHT22数据
        output += "\n[DHT22 - 温湿度传感器]\n"
        if self.dht22_data["humidity"] is not None:
            output += f"  温度: {self.dht22_data['temperature']:>6.1f} °C\n"
            output += f"  湿度: {self.dht22_data['humidity']:>6.1f} %RH\n"
        else:
            output += f"  读取失败 (失败次数: {self.dht22_fail_count})\n"
        
        # 比较数据
        if (self.scd40_data["humidity"] is not None and 
            self.dht22_data["humidity"] is not None):
            scd_h = self.scd40_data["humidity"]
            dht_h = self.dht22_data["humidity"]
            diff = abs(scd_h - dht_h)
            
            output += "\n[数据对比]\n"
            output += f"  湿度差值: {diff:.1f} %RH\n"
            output += f"  湿度差异: {((scd_h - dht_h) / dht_h * 100):+.1f}%\n"
            
            scd_t = self.scd40_data["temperature"]
            dht_t = self.dht22_data["temperature"]
            if scd_t and dht_t:
                t_diff = abs(scd_t - dht_t)
                output += f"  温度差值: {t_diff:.1f} °C\n"
        
        output += "=" * 50
        return output
    
    def get_log_entry(self):
        """获取log格式的数据条目"""
        timestamp = datetime.now()
        
        log_entry = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_iso": timestamp.isoformat(),
            "read_count": self.read_count,
            "scd40": {
                "co2_ppm": self.scd40_data["co2"] if self.scd40_data["co2"] is not None else None,
                "temperature_c": round(self.scd40_data["temperature"], 1) if self.scd40_data["temperature"] is not None else None,
                "humidity_rh": round(self.scd40_data["humidity"], 1) if self.scd40_data["humidity"] is not None else None
            },
            "dht22": {
                "temperature_c": round(self.dht22_data["temperature"], 1) if self.dht22_data["temperature"] is not None else None,
                "humidity_rh": round(self.dht22_data["humidity"], 1) if self.dht22_data["humidity"] is not None else None
            }
        }
        
        # 如果有两个传感器的数据，添加对比信息
        if (self.scd40_data["humidity"] is not None and 
            self.dht22_data["humidity"] is not None):
            scd_h = self.scd40_data["humidity"]
            dht_h = self.dht22_data["humidity"]
            
            log_entry["comparison"] = {
                "humidity_diff": round(abs(scd_h - dht_h), 1),
                "humidity_percent_diff": round((scd_h - dht_h) / dht_h * 100, 1)
            }
            
        if (self.scd40_data["temperature"] is not None and 
            self.dht22_data["temperature"] is not None):
            scd_t = self.scd40_data["temperature"]
            dht_t = self.dht22_data["temperature"]
            
            if "comparison" not in log_entry:
                log_entry["comparison"] = {}
            log_entry["comparison"]["temperature_diff"] = round(abs(scd_t - dht_t), 1)
        
        return log_entry
    
    def cleanup(self):
        """清理资源"""
        print("\n正在关闭传感器...")
        if self.scd4x:
            try:
                self.scd4x.stop_periodic_measurement()
                print("SCD40测量已停止")
            except Exception as e:
                print(f"停止SCD40测量时出错: {e}")
        if self.dht22:
            try:
                self.dht22.exit()
                print("DHT22已清理")
            except Exception as e:
                print(f"清理DHT22时出错: {e}")
        print("完成!")

def create_log_file(filename="sensor_data.log"):
    """创建log文件并写入头部信息"""
    # 确保logs目录存在
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 创建带时间戳的文件名
    if "sensor_data" in filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sensor_data_{timestamp}.log"
    
    filepath = log_dir / filename
    
    # 写入log文件头部
    header = f"""# ============================================
# 双传感器监测日志 (SCD40 + DHT22)
# 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# 读取模式: SCD40数据就绪触发读取
# 文件格式: 每行一个JSON对象，便于解析
# ============================================

"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(header)
    
    print(f"Log文件已创建: {filepath}")
    print("数据将自动保存到logs目录")
    return filepath

def save_log_entry(filepath, log_entry):
    """保存log条目到文件"""
    try:
        with open(filepath, 'a', encoding='utf-8') as f:
            json_line = json.dumps(log_entry, ensure_ascii=False)
            f.write(json_line + "\n")
    except Exception as e:
        print(f"保存日志条目失败: {e}")

def save_readable_log(filepath, log_entry):
    """保存易读格式的日志"""
    try:
        timestamp = log_entry["timestamp"]
        scd = log_entry["scd40"]
        dht = log_entry["dht22"]
        
        line = f"[{timestamp}] "
        
        # SCD40数据
        if scd["co2_ppm"] is not None:
            line += f"SCD40: CO₂={scd['co2_ppm']:4.0f}ppm, "
            line += f"T={scd['temperature_c']:4.1f}°C, "
            line += f"H={scd['humidity_rh']:4.1f}%RH"
        else:
            line += "SCD40: No data"
        
        # DHT22数据
        if dht["humidity_rh"] is not None:
            line += f" | DHT22: T={dht['temperature_c']:4.1f}°C, "
            line += f"H={dht['humidity_rh']:4.1f}%RH"
        else:
            line += " | DHT22: No data"
        
        # 对比数据
        if "comparison" in log_entry:
            comp = log_entry["comparison"]
            line += f" | Diff: ΔH={comp['humidity_diff']:.1f}%RH"
            if "humidity_percent_diff" in comp:
                line += f" ({comp['humidity_percent_diff']:+.1f}%)"
            if "temperature_diff" in comp:
                line += f", ΔT={comp['temperature_diff']:.1f}°C"
        
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"保存易读日志失败: {e}")

def main():
    """主程序"""
    print("""
    ========================================
    双传感器监测系统 (SCD40 + DHT22) - 修复版
    ========================================
    修复内容: SCD40初始化问题
    读取模式: SCD40数据就绪触发读取
    数据格式: .log文件 (JSON + 易读文本)
    保存目录: ./logs/
    ========================================
    """)
    
    # 创建log文件
    json_log_file = create_log_file()
    readable_log_file = str(json_log_file).replace('.log', '_readable.log')
    
    # 创建易读日志文件头部
    with open(readable_log_file, 'w', encoding='utf-8') as f:
        f.write(f"# 双传感器监测日志 - 易读格式\n")
        f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 格式: [时间] SCD40数据 | DHT22数据 | 对比数据\n")
        f.write("#" * 70 + "\n\n")
    
    # 初始化传感器
    print("\n正在初始化传感器...")
    monitor = DualSensorMonitor(dht_pin=board.D4)
    
    # 检查传感器状态
    if not monitor.scd4x:
        print("\n警告: SCD40传感器初始化失败!")
        print("将尝试继续运行，但只能读取DHT22数据")
        print("按 Ctrl+C 停止程序\n")
    else:
        print("\n传感器初始化成功!")
        print("开始监测，等待SCD40数据就绪...")
        print("按 Ctrl+C 停止程序\n")
    
    try:
        while True:
            # 如果SCD40可用，使用数据就绪触发
            if monitor.scd4x:
                success_count = monitor.read_all_when_ready()
            else:
                # 如果SCD40不可用，只读取DHT22，等待2秒
                success_count = 0
                if monitor.read_dht22():
                    success_count += 1
                time.sleep(2)
            
            # 显示结果
            if success_count > 0:
                if monitor.scd4x:
                    print(monitor.format_output())
                
                # 保存到日志文件
                log_entry = monitor.get_log_entry()
                save_log_entry(json_log_file, log_entry)
                save_readable_log(readable_log_file, log_entry)
            #monitor.scd4x.stop_periodic_measurement()
            # 短暂延迟
            time.sleep(1)            
            #monitor.scd4x.start_low_periodic_measurement()
    except KeyboardInterrupt:
        print("\n\n监测停止")
    finally:
        # 显示统计数据
        print(f"\n统计信息:")
        print(f"  总读取次数: {monitor.read_count}")
        print(f"  SCD40就绪检查次数: {monitor.scd40_ready_checks}")
        print(f"  DHT22失败次数: {monitor.dht22_fail_count}")
        
        # 清理资源
        monitor.cleanup()
        print(f"\n数据已保存到:")
        print(f"  JSON格式: {json_log_file}")
        print(f"  易读格式: {readable_log_file}")

def debug_i2c():
    """调试I2C连接的辅助函数"""
    print("\n=== I2C调试信息 ===")
    try:
        # 导入必要的库
        import subprocess
        
        # 检查I2C设备
        print("运行 i2cdetect -y 1...")
        result = subprocess.run(['sudo', 'i2cdetect', '-y', '1'], 
                               capture_output=True, text=True)
        print(result.stdout)
        
        # 检查I2C工具是否安装
        print("\n检查I2C工具...")
        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'i2c-tools'], 
                       capture_output=True, text=True)
        
    except Exception as e:
        print(f"调试过程中出错: {e}")

if __name__ == "__main__":
    # 可以选择运行调试功能
   # debug_option = input("是否运行I2C调试? (y/N): ").strip().lower()
   # if debug_option == 'y':
    #    debug_i2c()
    
    # 运行主程序
    main()
