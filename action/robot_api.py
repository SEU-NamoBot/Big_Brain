# 存放底层API接口
import time

from roarm_sdk.roarm import roarm

from model.llm import JudgeLLM
from utils.utils import get_robot_pos

judge_llm = JudgeLLM()

# 为了方便cap，这里抛弃类定义，改用方法
def move_to_xy(x: float, y: float):
    # 移动到指定坐标
    print(f"Moving to coordinates: ({x}, {y})")
    judge_llm.judge(
        action_id=1,
        x=x,
        y=y,
        task_text=f"Move to ({x}, {y})",
    )

#region
# def move_to_obj(Object: str):
#     # 移动到指定物品旁边
#     print(f"Moving to object: {Object}")
#     judge_llm.judge(f"Move to {Object}")
#endregion

def move_to_obj_by_offset(Object:str, dx:float, dy: float):
    # 移动到指定物品旁边，并保持相对位置(dx, dy)
    print(f"Moving to object: {Object} with offset ({dx}, {dy})")
    # 1.尝试直接获取坐标
    # 2.尝试调用LLM生成获取坐标的代码并执行
    judge_llm.judge(
        action_id=2,
        target=Object,
        dx=dx,
        dy=dy,
        task_text=f"Move to {Object} with offset ({dx}, {dy})",
    )

def pick_up_xy(x: float, y: float):
    # 在指定坐标拾取物品

    # 可达
    print(f"Picking up item at coordinates: ({x}, {y})")
    judge_llm.judge(
        action_id=3,
        x=x,
        y=y,
        task_text=f"Pick up at ({x}, {y})",
    )


def pick_up_xy_arm(x: float, y: float):
    # 在指定坐标拾取物品
    # 1.检查xy是否机械臂可达
    # config 假设机械臂底座离小车质心为差距x10cm,y0cm,z5cm,机械臂肩离底座z=15cm，夹头位置是350，0，212
    robot_x,robot_y,robot_z = get_robot_pos()
    # 夹头位置
    hand_x = robot_x + 10 + 350 # 360
    hand_y = robot_y # 0
    hand_z = robot_z + 5 + 15 + 212 # 242
    # 目标位置 x,y,robot_z + 5 + config（自己设置的）目标物品高度
    dx = x - hand_x 
    dy = y - hand_y 
    # dz = robot_z + 5 + 15 +50 - hand_z
    dz = 100-242
    if dx > 450-350 or dz > 450-350 or abs(dy) > 450 - 350 or dx < -200 or dz < -225 :
        print(dx,dy,dz)
        return False
    t = 90
    r = 0
    g = 30

    # 填写机械臂的 IP 地址
    arm_ip = "192.168.4.1" 

    # 初始化 HTTP 无线通信 (注意这里使用的是 host= 而不是 port=)
    arm = roarm(roarm_type="roarm_m3", host=arm_ip) 
    arm.pose_ctrl([350+dx, 5+dy, 242+dz, 45, r, g]) # x-10,y,15 + 100 - 30
    # arm.pose_ctrl([350+dx, 5+dy, 242+dz, t*(1-(350+dx)/500), r, g]) # x-10,y,15 + 100 - 30
    # arm.pose_ctrl([350+dx, 5+dy, 212+dz, t, r, g]) # x-10,y,15 + 100 - 30
    time.sleep(3)
    arm.move_init()

    # 可达
    print(f"Picking up item at coordinates: ({x}, {y})")
    judge_llm.judge(
        action_id=3,
        x=x,
        y=y,
        task_text=f"Pick up at ({x}, {y})",
    )

def pick_up_obj(item):
    # 拾取指定物品
    print(f"Picking up item: {item}")
    judge_llm.judge(
        action_id=4,
        target=item,
        task_text=f"Pick up {item}",
    )

def put_down_xy(x: float, y: float):
    # 在指定坐标放下物品
    print(f"Putting down item at coordinates: ({x}, {y})")
    judge_llm.judge(
        action_id=5,
        x=x,
        y=y,
        task_text=f"Put down at ({x}, {y})",
    )

def put_down_obj_by_offset(target:str, dx:float, dy: float):
    # 在指定物品旁边放下物品，并保持相对位置(dx, dy)
    print(f"Putting down item near {target} with offset ({dx}, {dy})")
    judge_llm.judge(
        action_id=6,
        target=target,
        dx=dx,
        dy=dy,
        task_text=f"Put down item near {target} with offset ({dx}, {dy})",
    )

if __name__ == "__main__":
    # 测试
    pick_up_xy_arm(350, 0)  # x-10,y,15 + 100 - 30