# 视觉模型的prompt，用于判断任务是否成功以及如何微调
# pick up object apple
# 失败
# YOLO检测苹果位置
# 利用深度图和机器人本身计算苹果坐标2->3（未来可以写一个转换的函数直接提供调用）
# 重新夹起来

# move to
# 失败（比如读取机器人真实位置）
# 判断失败原因
# 修正move to 位置

ADJUST_PROMPT = """
import numpy as np
from action.robot_api import move_to_xy, move_to_obj_by_offset, pick_up_xy, pick_up_obj, put_down_xy, put_down_obj_by_offset
from utils.utils import get_obj_xy, get_obj_size, parse_obj_name, load_L2_memory

objects = load_L2_memory()

# Global Instruction: "pick up the bottle"
# Failed Action: pick_up_obj("bottle")
# VLM Feedback: {"error_type": "grasp_missed", "suggested_correction": "The gripper missed the bottle, it is slightly to the right."}
bottle_x,bottle_y = get_obj_xy("bottle")
pick_up_xy(bottle_x + 5.0, bottle_y)

# Global Instruction: "put the apple on the center of the desk"
# Failed Action: put_down_obj_by_offset("desk", 0, 0)
# VLM Feedback: {"error_type": "target_occupied", "suggested_correction": "The center of the desk is occupied by a laptop. Place the apple to the right of the laptop instead."}
laptop_obj = parse_obj_name("laptop", objects)
laptop_len, laptop_width, _ = get_obj_size(laptop_obj)
pick_up_obj("apple")
put_down_obj_by_offset(laptop_obj, laptop_len/2 + 10.0, 0)

# Global Instruction: "put the bottle between the apple and the banana"
# Failed Action: put_down_xy(150, 200)
# VLM Feedback: {"error_type": "wrong_relation", "suggested_correction": "The bottle is placed too close to the apple. It needs to be moved closer to the banana."}
pick_up_xy(150, 200)
apple_x, apple_y = get_obj_xy(parse_obj_name("apple", objects))
banana_x, banana_y = get_obj_xy(parse_obj_name("banana", objects))
mid_x = (apple_x + banana_x) / 2
mid_y = (apple_y + banana_y) / 2
move_to_xy(mid_x, mid_y)
put_down_xy(mid_x, mid_y)
"""