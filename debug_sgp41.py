#!/usr/bin/env python3
import smbus2
import time
import sys

def debug_sgp41():
    bus = smbus2.SMBus(1)  # 使用I2C总线1
    sgp41_addr = 0x59
    scd40_addr = 0x62

    print("=== SGP41 通信深度诊断 ===")

    # 1. 快速扫描，确认当前总线状态
    print("1. 快速I2C扫描 (0x50-0x70):")
    detected = []
    for addr in range(0x50, 0x71):
        try:
            bus.write_quick(addr)
            detected.append(hex(addr))
        except:
            pass
    print(f"   检测到的地址: {detected}")

    # 2. 重点检查 0x59
    print(f"\n2. 重点检查 SGP41 (0x{sgp41_addr:02x}):")
    try:
        bus.write_quick(sgp41_addr)
        print("   ✅ 基础响应测试通过 (设备在线)")
        device_online = True
    except Exception as e:
        print(f"   ❌ 无基础响应: {e}")
        device_online = False

    # 3. 尝试发送SGP41的“唤醒”和“获取序列号”命令
    if device_online:
        print("\n3. 尝试高级命令:")
        try:
            # 发送唤醒命令 (0x260F)
            bus.write_i2c_block_data(sgp41_addr, 0x26, [0x0F])
            time.sleep(0.05)  # 等待传感器准备
            print("   ✅ 唤醒命令(0x260F)发送成功")

            # 发送“获取序列号”命令 (0x3682)
            bus.write_i2c_block_data(sgp41_addr, 0x36, [0x82])
            time.sleep(0.05)

            # 读取响应（6字节序列号 + 3字节CRC）
            data = bus.read_i2c_block_data(sgp41_addr, 0, 9)
            serial = ''.join([f'{b:02x}' for b in data[:6]])
            print(f"   ✅ 序列号读取成功: {serial}")
            print("\n🎉 SGP41 功能完全正常！")

        except Exception as e:
            print(f"   ❌ 高级命令失败: {e}")
            print("\n💡 设备在线但指令错误，可能原因：")
            print("   - 传感器初始化顺序问题")
            print("   - 通信时序（时钟频率）仍不匹配")
    else:
        # 4. 如果设备不在线，进行硬件排查建议
        print("\n3. 硬件与连接排查:")
        print("   🔌 **请立即检查以下硬件连接**:")
        print("     1. **电源(VDD)**：SGP41的VDD引脚是否连接到树莓派的 **3.3V** (引脚1或17)")
        print("     2. **地线(GND)**：是否与SCD40和树莓派共地。")
        print("     3. **SDA/SCL**：是否与SCD40**并联**正确连接到树莓派引脚3(SDA)和5(SCL)。")
        print("     4. **接触不良**：轻轻摇动SGP41传感器与杜邦线的连接处。")
        print("\n   ⚠️  **如果以上无误，尝试**:")
        print("     a) **单独供电测试**: 将SGP41从总线上取下，仅接VCC、GND，再用I2C扫描。")
        print("     b) **地址冲突**：运行 'sudo i2cdetect -y 1' 查看是否有其他设备占用了0x59附近地址。")

    bus.close()

if __name__ == "__main__":
    debug_sgp41()