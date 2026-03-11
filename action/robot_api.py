# 存放底层API接口

from big_brain.model.llm import JudgeLLM
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
    judge_llm.judge(f"Move to {Object} with offset ({dx}, {dy})")

def pick_up_xy(x: float, y: float):
    # 在指定坐标拾取物品
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

# region 类定义版操作
# class RobotAPI:
#     def __init__(self):
#         self.judge_llm = JudgeLLM()

#     def move_to_xy(self, x: float, y: float):
#         # 移动到指定坐标
#         print(f"Moving to coordinates: ({x}, {y})")
#         self.judge_llm.judge(f"Move to ({x}, {y})")

#     def move_to_obj(self, Object: str):
#         # 移动到指定物品旁边
#         print(f"Moving to object: {Object}")
#         self.judge_llm.judge(f"Move to {Object}")

#     def move_to_obj_by_offset(self, Object:str, dx:float, dy: float):
#         # 移动到指定物品旁边，并保持相对位置(dx, dy)
#         print(f"Moving to object: {Object} with offset ({dx}, {dy})")
#         self.judge_llm.judge(f"Move to {Object} with offset ({dx}, {dy})")

#     def pick_up_xy(self, x: float, y: float):
#         # 在指定坐标拾取物品
#         print(f"Picking up item at coordinates: ({x}, {y})")
#         self.judge_llm.judge(f"Pick up at ({x}, {y})")

#     def pick_up_obj(self, item):
#         # 拾取指定物品
#         print(f"Picking up item: {item}")
#         self.judge_llm.judge(f"Pick up {item}")

#     def put_down_xy(self, x: float, y: float):
#         # 在指定坐标放下物品
#         print(f"Putting down item at coordinates: ({x}, {y})")
#         self.judge_llm.judge(f"Put down at ({x}, {y})")
    
#     def put_down_obj_by_offset(self, target:str, dx:float, dy: float):
#         # 在指定物品旁边放下物品，并保持相对位置(dx, dy)
#         print(f"Putting down item near {target} with offset ({dx}, {dy})")
#         self.judge_llm.judge(f"Put down item near {target} with offset ({dx}, {dy})")
# endregion