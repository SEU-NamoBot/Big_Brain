# 存放底层API接口

from model.llm import JudgeLLM
judge_llm = JudgeLLM()

# 为了方便cap，这里抛弃类定义，改用方法
def move_to_xy(x: float, y: float):
    # 移动到指定坐标
    print(f"Moving to coordinates: ({x}, {y})")
    judge_llm.judge(f"Move to ({x}, {y})")

# def move_to_obj(Object: str):
#     # 移动到指定物品旁边
#     print(f"Moving to object: {Object}")
#     judge_llm.judge(f"Move to {Object}")

def move_to_obj_by_offset(Object:str, dx:float, dy: float):
    # 移动到指定物品旁边，并保持相对位置(dx, dy)
    print(f"Moving to object: {Object} with offset ({dx}, {dy})")
    # 1.尝试直接获取坐标
    # 2.尝试调用LLM生成获取坐标的代码并执行
    judge_llm.judge(f"Move to {Object} with offset ({dx}, {dy})")

def pick_up_xy(x: float, y: float):
    # 在指定坐标拾取物品
    # 1.检查xy是否机械臂可达
    
    # 可达
    print(f"Picking up item at coordinates: ({x}, {y})")
    judge_llm.judge(f"Pick up at ({x}, {y})")

def pick_up_obj(item):
    # 拾取指定物品
    print(f"Picking up item: {item}")
    judge_llm.judge(f"Pick up {item}")

def put_down_xy(x: float, y: float):
    # 在指定坐标放下物品
    print(f"Putting down item at coordinates: ({x}, {y})")
    judge_llm.judge(f"Put down at ({x}, {y})")

def put_down_obj_by_offset(target:str, dx:float, dy: float):
    # 在指定物品旁边放下物品，并保持相对位置(dx, dy)
    print(f"Putting down item near {target} with offset ({dx}, {dy})")
    judge_llm.judge(f"Put down item near {target} with offset ({dx}, {dy})")