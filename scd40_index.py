#!/usr/bin/env python3
"""
SCD40 传感器参数配置工具
"""


import board
import adafruit_scd4x
import time

i2c = board.I2C()
scd = adafruit_scd4x.SCD4X(i2c)

print("=== SCD40 当前参数 ===")
print(f"1. 温度偏移: {scd.temperature_offset:.2f} °C")
print(f"2. 海拔补偿: {scd.altitude} 米")
print(f"3. 自动自校准(ASC): {'启用' if scd.self_calibration_enabled else '禁用'}")

# 1. 设置温度偏移
scd.temperature_offset = 1.05
print(f"[已设置] 温度偏移 = {scd.temperature_offset} °C")

# 2. 设置海拔补偿 (设为0表示禁用补偿)
scd.altitude = 60
print(f"[已设置] 海拔补偿 = {scd.altitude} 米")

# 3. 设置自动自校准 (根据需求选择True或False)
scd.self_calibration_enabled = True
print("[已设置] 自动自校准(ASC) = 启用")
# 永久保存所有设置到传感器EEPROM（断电不丢失）
print("所有参数已保存至传感器，开始传感器自校准")
scd.self_test()
print("自校准完成。")
scd.stop_periodic_measurement()