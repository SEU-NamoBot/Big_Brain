from roarm_sdk.roarm import roarm
import time

# 填写机械臂的 IP 地址
arm_ip = "192.168.4.1" 

# 初始化 HTTP 无线通信 (注意这里使用的是 host= 而不是 port=)
arm = roarm(roarm_type="roarm_m3", host=arm_ip) 

print("✅ 成功通过 HTTP 连接到机械臂！")

# 回到初始安全位置

# ==========================================
# XYZ 抓取测试逻辑
# ==========================================

# print("-> 移动到物品上方准备...")
arm.pose_ctrl([200, 0, 200, -90, 0, 0])
time.sleep(2)
arm.move_init()
# print("-> 抓取物品...")
# arm.pose_ctrl([200, 0, 100, -90, 0, 0])
# time.sleep(1)

# print("-> 抬起物品...")
# arm.pose_ctrl([-100, 150, 150, -90, 0, 0])
# time.sleep(2)

# print("-> 放下物品...")
# arm.pose_ctrl([-100, 150, 150, -90, 0, 90])
# print("🎉 动作执行完毕！")